from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
from app.utils.scheduler import add_scheduled_trigger, execute_api_trigger
from app.services.database import Database
from app.models.trigger import TriggerCreate, Trigger, ScheduleConfig, TriggerUpdate
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/")
async def create_trigger(trigger: TriggerCreate):
    """Create a new trigger"""
    try:
        # Prepare trigger document
        trigger_doc = trigger.model_dump()
        trigger_doc["created_at"] = datetime.utcnow()
        trigger_doc["updated_at"] = datetime.utcnow()

        # Save trigger to database
        trigger_id = await Database.insert_one(
            "triggers",
            trigger_doc
        )
        
        # Add to scheduler if it's a scheduled trigger
        if trigger.trigger_type == "scheduled" and trigger.schedule_config:
            schedule_config = trigger.schedule_config.model_dump()
            await add_scheduled_trigger(
                trigger_id,
                schedule_config,
                is_test=False
            )
        
        return {"trigger_id": str(trigger_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{trigger_id}")
async def get_trigger(trigger_id: str):
    """Get a trigger by ID"""
    trigger = await Database.find_one("triggers", {"_id": trigger_id})
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return trigger

@router.delete("/{trigger_id}")
async def delete_trigger(trigger_id: str):
    """Delete a trigger while preserving its events"""
    try:
        # First, deactivate the trigger
        await Database.update_one(
            "triggers",
            {"_id": trigger_id},
            {
                "$set": {
                    "is_active": False,
                    "deleted_at": datetime.utcnow()
                }
            }
        )

        # Remove from scheduler if it exists
        try:
            scheduler.remove_job(f"{trigger_id}_permanent")
        except:
            pass  # Job might not exist in scheduler

        # Mark trigger as deleted but keep the record
        await Database.update_one(
            "triggers",
            {"_id": trigger_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow()
                }
            }
        )

        return {"message": "Trigger deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_trigger(trigger: TriggerCreate):
    """Test a trigger without saving it"""
    try:
        if trigger.trigger_type == "scheduled":
            # Create temporary trigger for testing
            schedule_config = trigger.schedule_config.model_dump()
            # Force one-time execution
            schedule_config["schedule_type"] = "one_time"
            await add_scheduled_trigger(
                "test_" + str(uuid.uuid4()),
                schedule_config,
                is_test=True
            )
        else:  # API trigger
            await execute_api_trigger(
                "test_" + str(uuid.uuid4()),
                trigger.api_config.model_dump(),
                is_test=True
            )
        return {"message": "Test trigger created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{trigger_id}/execute")
async def execute_trigger(trigger_id: str, payload: Dict[str, Any] = None):
    """Execute an API trigger manually"""
    trigger = await Database.find_one("triggers", {"_id": trigger_id})
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    if trigger["trigger_type"] != "api":
        raise HTTPException(status_code=400, detail="Only API triggers can be executed manually")

    try:
        await execute_api_trigger(
            trigger_id,
            trigger["api_config"],
            payload,
            is_test=False,
            is_manual=True
        )
        return {"message": "Trigger executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{trigger_id}")
async def update_trigger(trigger_id: str, trigger: TriggerUpdate):
    """Update a trigger"""
    try:
        existing_trigger = await Database.find_one("triggers", {"_id": trigger_id})
        if not existing_trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")

        update_data = trigger.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await Database.update_one(
            "triggers",
            {"_id": trigger_id},
            {"$set": update_data}
        )

        # Update scheduler if it's a scheduled trigger
        if existing_trigger["trigger_type"] == "scheduled" and trigger.schedule_config:
            await add_scheduled_trigger(
                trigger_id,
                trigger.schedule_config.model_dump(),
                is_test=False
            )

        return {"message": "Trigger updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_all_triggers():
    """Get all active triggers"""
    try:
        triggers = await Database.find(
            "triggers", 
            {
                "is_deleted": {"$ne": True}
            }
        )
        return triggers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))