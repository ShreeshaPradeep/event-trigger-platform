from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
import logging
from datetime import datetime, timezone, timedelta

from app.models.event import Event
from app.services.event_service import EventService
from app.services.database import Database

router = APIRouter()

@router.get("/recent")
async def get_recent_events():
    """Get active events from last 2 hours only"""
    return await EventService.get_recent_events()

@router.get("/archived")
async def get_archived_events():
    """Get archived events (2-48 hours old)"""
    return await EventService.get_archived_events()

@router.get("/stats", response_model=List[Dict])
async def get_event_stats(
    hours: int = Query(48, description="Hours to look back for statistics")
):
    """Get event statistics grouped by trigger"""
    try:
        return await EventService.get_event_stats(hours)
    except Exception as e:
        logging.error(f"Error getting event stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve event statistics: {str(e)}")

@router.post("/test/create_past_event", response_model=Dict)
async def create_past_event(hours_ago: int = Query(3, description="Hours in the past")):
    """Create a test event with timestamp in the past"""
    try:
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(hours=hours_ago)
        
        event = {
            "trigger_id": "test_trigger",
            "trigger_type": "scheduled",
            "is_test": True,
            "is_manual": False,
            "execution_time": past_time,
            "retention_state": "active",
            "created_at": past_time,
            "archive_time": past_time + timedelta(hours=2),
            "expiry_time": past_time + timedelta(hours=48)
        }
        
        event_id = await Database.insert_one("events", event)
        
        # Trigger archival check
        await EventService.archive_events()
        
        return {
            "message": "Past event created and archived",
            "event_id": event_id
        }
    except Exception as e:
        logging.error(f"Error creating past event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create past event: {str(e)}"
        )

@router.post("/test/trigger_archival")
async def trigger_test_archival():
    """Trigger archival process with shorter time threshold"""
    try:
        await EventService.archive_events(test_mode=True)
        return {"message": "Test archival process completed"}
    except Exception as e:
        logging.error(f"Error in test archival: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run test archival: {str(e)}"
        ) 