from fastapi import APIRouter, HTTPException
from app.services.event_service import EventService
from typing import List
from app.models.event import Event

router = APIRouter()

@router.get("/recent")
async def get_recent_events(hours: int = 2):
    """Get recent events from the last N hours"""
    try:
        events = await EventService.get_recent_events(hours)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_event_stats(hours: int = 48):
    """Get aggregated event statistics"""
    try:
        stats = await EventService.get_aggregated_events(hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/archived")
async def get_archived_events(hours: int = 46):
    """Get archived events from the last N hours"""
    try:
        events = await EventService.get_archived_events(hours)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 