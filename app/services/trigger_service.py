from app.models.trigger import Trigger, TriggerCreate, TriggerUpdate, TriggerType, ScheduleType
from app.services.database import Database
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import logging
from app.utils.scheduler import add_scheduled_trigger, execute_api_trigger
from bson import ObjectId

class TriggerService:
    @staticmethod
    async def create_trigger(trigger: TriggerCreate, is_test: bool = False) -> str:
        """Create a new trigger"""
        now = datetime.now(timezone.utc)
        
        # Convert the trigger to dict and handle URL conversion
        trigger_dict = trigger.model_dump()
        
        trigger_doc = {
            "name": trigger_dict["name"],
            "description": trigger_dict.get("description"),
            "trigger_type": trigger_dict["trigger_type"],
            "is_test": is_test,
            "is_active": True,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now
        }

        if trigger.trigger_type == TriggerType.SCHEDULED:
            trigger_doc["schedule_config"] = trigger_dict["schedule_config"]
        else:
            # For API triggers
            api_config = trigger_dict["api_config"]
            # Ensure endpoint is string
            api_config["endpoint"] = str(api_config["endpoint"])
            trigger_doc["api_config"] = api_config

        # For test triggers, set expiry
        if is_test:
            if trigger.trigger_type == TriggerType.SCHEDULED:
                if trigger.schedule_config.specific_time:
                    trigger_doc["expires_at"] = trigger.schedule_config.specific_time
                else:
                    # For interval-based, calculate expiry
                    delta = {
                        trigger.schedule_config.interval_type: 
                        trigger.schedule_config.interval_value
                    }
                    trigger_doc["expires_at"] = now + timedelta(**delta)

        trigger_id = await Database.insert_one("triggers", trigger_doc)

        # Setup scheduler for scheduled triggers
        if trigger.trigger_type == TriggerType.SCHEDULED:
            await add_scheduled_trigger(
                trigger_id,
                trigger_doc["schedule_config"],
                is_test
            )

        return trigger_id

    @staticmethod
    async def get_trigger(trigger_id: str) -> Optional[Dict]:
        """Get a specific trigger"""
        try:
            # Validate ObjectId format first
            if not ObjectId.is_valid(trigger_id):
                return None
            
            query = {
                "_id": ObjectId(trigger_id),
                "is_deleted": False
            }
            return await Database.find_one("triggers", query)
        except Exception as e:
            logging.error(f"Error getting trigger: {str(e)}")
            return None

    @staticmethod
    async def get_all_triggers(active_only: bool = True) -> List[Dict]:
        """Get all triggers"""
        try:
            query = {"is_deleted": False}
            if active_only:
                query["is_active"] = True
            return await Database.find_many("triggers", query)
        except Exception as e:
            logging.error(f"Error getting triggers: {str(e)}")
            raise

    @staticmethod
    async def update_trigger(trigger_id: str, trigger: TriggerUpdate) -> bool:
        """Update a trigger"""
        try:
            # First get the existing trigger
            existing_trigger = await TriggerService.get_trigger(trigger_id)
            if not existing_trigger:
                return False

            # Don't allow updates if trigger is not active
            if not existing_trigger["is_active"]:
                logging.warning(f"Attempted to update inactive trigger {trigger_id}")
                return False

            now = datetime.now(timezone.utc)
            update_data = trigger.model_dump(exclude_unset=True)
            update_data["updated_at"] = now

            # Validate trigger type specific updates
            if "api_config" in update_data:
                if existing_trigger["trigger_type"] != "api":
                    logging.error(f"Cannot update api_config for non-API trigger {trigger_id}")
                    return False
                
                # Ensure endpoint is string and properly formatted
                api_config = update_data["api_config"]
                api_config["endpoint"] = str(api_config["endpoint"])
                
                # Merge with existing headers if present
                if "headers" in api_config and existing_trigger.get("api_config", {}).get("headers"):
                    existing_headers = existing_trigger["api_config"]["headers"]
                    api_config["headers"] = {**existing_headers, **api_config["headers"]}

            elif "schedule_config" in update_data:
                if existing_trigger["trigger_type"] != "scheduled":
                    logging.error(f"Cannot update schedule_config for non-scheduled trigger {trigger_id}")
                    return False

            query = {"_id": ObjectId(trigger_id), "is_deleted": False, "is_active": True}
            update = {"$set": update_data}
            
            success = await Database.update_one("triggers", query, update)
            
            if success:
                logging.info(f"Trigger {trigger_id} updated successfully")
            return success

        except Exception as e:
            logging.error(f"Error updating trigger: {str(e)}")
            return False

    @staticmethod
    async def delete_trigger(trigger_id: str) -> bool:
        """Soft delete a trigger"""
        try:
            query = {"_id": ObjectId(trigger_id)}
            update = {
                "$set": {
                    "is_deleted": True,
                    "is_active": False,
                    "deleted_at": datetime.now(timezone.utc)
                }
            }
            result = await Database.update_one("triggers", query, update)
            
            if result:
                # Deactivate any scheduled jobs
                from app.utils.scheduler import scheduler
                job_id = f"{trigger_id}_permanent"
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
            
            return result
        except Exception as e:
            logging.error(f"Error deleting trigger: {str(e)}")
            return False

    @staticmethod
    async def test_trigger(trigger: TriggerCreate) -> Dict:
        """Test a trigger without saving"""
        try:
            if trigger.trigger_type == TriggerType.API:
                await execute_api_trigger(
                    "test",
                    trigger.api_config.model_dump(),
                    is_test=True
                )
                return {"message": "API trigger tested successfully"}
            else:
                # For scheduled triggers, create a one-time test execution
                trigger_id = await TriggerService.create_trigger(trigger, is_test=True)
                return {
                    "message": "Scheduled trigger test created",
                    "trigger_id": trigger_id
                }
        except Exception as e:
            logging.error(f"Error testing trigger: {str(e)}")
            raise 