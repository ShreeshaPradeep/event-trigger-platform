import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.main import app
from app.models.event import Event, EventStatus
from app.services.database import Database
from app.services.event_service import EventService

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def sample_event():
    event_id = await EventService.create_event(
        trigger_id="test_trigger",
        trigger_type="scheduled",
        is_test=True
    )
    return event_id

async def test_get_recent_events(client, sample_event):
    response = await client.get("/api/v1/events/recent")
    assert response.status_code == 200
    events = response.json()
    assert len(events) > 0
    assert events[0]["trigger_id"] == "test_trigger"

async def test_get_archived_events(client):
    # Create an archived event
    now = datetime.now(timezone.utc)
    event_id = await EventService.create_event(
        trigger_id="archived_trigger",
        trigger_type="scheduled"
    )
    
    # Manually archive the event
    await Database.update_one(
        "events",
        {"id": event_id},
        {
            "$set": {
                "retention_state": "archived",
                "archived_at": now
            }
        }
    )
    
    response = await client.get("/api/v1/events/archived")
    assert response.status_code == 200
    events = response.json()
    assert len(events) > 0

@pytest.mark.asyncio
async def test_event_lifecycle():
    # Create test events with different timestamps
    now = datetime.utcnow()
    
    # Active event (recent)
    active_event = Event(
        trigger_id="test_trigger",
        trigger_name="Test Trigger",
        triggered_at=now,
        status=EventStatus.ACTIVE
    )
    
    # Should be archived (3 hours old)
    archive_event = Event(
        trigger_id="test_trigger",
        trigger_name="Test Trigger",
        triggered_at=now - timedelta(hours=3),
        status=EventStatus.ACTIVE
    )
    
    # Should be deleted (49 hours old)
    delete_event = Event(
        trigger_id="test_trigger",
        trigger_name="Test Trigger",
        triggered_at=now - timedelta(hours=49),
        status=EventStatus.ARCHIVED
    )
    
    # Run archival process
    await EventService.archive_and_cleanup_events()
    
    # Verify event states
    events = await EventService.get_recent_events(hours=48)
    
    assert any(e.id == active_event.id and e.status == EventStatus.ACTIVE for e in events)
    assert any(e.id == archive_event.id and e.status == EventStatus.ARCHIVED for e in events)
    assert not any(e.id == delete_event.id for e in events)

@pytest.mark.asyncio
async def test_event_creation():
    event_id = await EventService.create_event(
        trigger_id="test_trigger",
        trigger_type="api",
        is_test=True,
        api_payload={"test": "data"}
    )
    assert event_id is not None

@pytest.mark.asyncio
async def test_event_retention():
    # Create past event (3 hours ago)
    now = datetime.now(timezone.utc)
    past_time = now - timedelta(hours=3)
    
    event = {
        "trigger_id": "test_trigger",
        "trigger_type": "scheduled",
        "is_test": True,
        "execution_time": past_time,
        "retention_state": "active",
        "created_at": past_time
    }
    
    await Database.insert_one("events", event)
    
    # Run archival
    await EventService.archive_events()
    
    # Check archived events
    archived = await EventService.get_archived_events()
    assert len(archived) > 0
    
    # Create very old event (49 hours ago)
    old_time = now - timedelta(hours=49)
    old_event = {
        "trigger_id": "test_trigger",
        "trigger_type": "scheduled",
        "is_test": True,
        "execution_time": old_time,
        "retention_state": "archived",
        "created_at": old_time
    }
    
    await Database.insert_one("events", old_event)
    
    # Run cleanup
    await EventService.cleanup_events()
    
    # Verify old event is deleted
    all_events = await Database.find_many(
        "events",
        {"trigger_id": "test_trigger"}
    )
    assert all(e["created_at"] > now - timedelta(hours=48) for e in all_events)

@pytest.mark.asyncio
async def test_event_queries():
    # Recent events (last 2 hours)
    recent = await EventService.get_recent_events()
    assert all(
        e["retention_state"] == "active" 
        for e in recent
    )
    
    # Archived events (2-48 hours)
    archived = await EventService.get_archived_events()
    assert all(
        e["retention_state"] == "archived"
        for e in archived
    ) 