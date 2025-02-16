from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from app.models.trigger import TriggerCreate, TriggerUpdate, TriggerType
from app.services.trigger_service import TriggerService
from app.utils.scheduler import execute_api_trigger
import logging
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/", response_model=Dict)
async def create_trigger(trigger: TriggerCreate):
    """Create a new trigger"""
    try:
        trigger_id = await TriggerService.create_trigger(trigger)
        return {
            "trigger_id": trigger_id,
            "message": "Trigger created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error creating trigger: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create trigger")

@router.get("/", response_model=List[Dict])
async def get_all_triggers(
    active_only: bool = Query(True, description="Only show active triggers")
):
    """Get all non-deleted triggers"""
    try:
        triggers = await TriggerService.get_all_triggers(active_only=active_only)
        return triggers
    except Exception as e:
        logging.error(f"Error getting triggers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve triggers: {str(e)}")

@router.get("/{trigger_id}", response_model=Dict)
async def get_trigger(trigger_id: str):
    """Get a specific non-deleted trigger"""
    try:
        # First validate ObjectId format
        if not ObjectId.is_valid(trigger_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid trigger ID format"
            )
            
        trigger = await TriggerService.get_trigger(trigger_id)
        if not trigger:
            raise HTTPException(
                status_code=404,
                detail="Trigger not found or has been deleted"
            )
        return trigger
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting trigger: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve trigger: {str(e)}"
        )

@router.put("/{trigger_id}")
async def update_trigger(trigger_id: str, trigger: TriggerUpdate):
    """Update a trigger"""
    try:
        # First validate ObjectId format
        if not ObjectId.is_valid(trigger_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid trigger ID format"
            )

        # Get existing trigger to check status
        existing = await TriggerService.get_trigger(trigger_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Trigger not found"
            )

        if not existing["is_active"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot update inactive trigger"
            )

        success = await TriggerService.update_trigger(trigger_id, trigger)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update trigger"
            )

        return {
            "message": "Trigger updated successfully",
            "trigger_id": trigger_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating trigger: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update trigger: {str(e)}"
        )

@router.delete("/{trigger_id}")
async def delete_trigger(trigger_id: str):
    """Soft delete a trigger while preserving its events"""
    try:
        trigger = await TriggerService.get_trigger(trigger_id)
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")

        success = await TriggerService.delete_trigger(trigger_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete trigger")

        return {
            "message": "Trigger deleted successfully",
            "trigger_id": trigger_id
        }
    except Exception as e:
        logging.error(f"Error deleting trigger: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete trigger: {str(e)}")

@router.post("/test")
async def test_trigger(trigger: TriggerCreate):
    """Test a trigger without permanent storage"""
    try:
        if trigger.trigger_type == TriggerType.API:
            # Test API trigger once
            await execute_api_trigger(
                "test",
                trigger.api_config.model_dump(),
                is_test=True
            )
            return {"message": "API trigger tested successfully"}
        else:
            # Create one-time test scheduled trigger
            trigger_id = await TriggerService.create_trigger(trigger, is_test=True)
            return {
                "message": "Scheduled trigger test created",
                "trigger_id": trigger_id
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{trigger_id}/execute")
async def execute_trigger(trigger_id: str, payload: Optional[Dict] = None):
    """Manually execute an API trigger"""
    try:
        trigger = await TriggerService.get_trigger(trigger_id)
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")

        if trigger["trigger_type"] == "api":
            await execute_api_trigger(
                trigger_id,
                trigger["api_config"],
                payload,
                is_manual=True
            )
            return {"message": "Trigger executed successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Only API triggers can be executed manually"
            )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error executing trigger: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute trigger: {str(e)}") 