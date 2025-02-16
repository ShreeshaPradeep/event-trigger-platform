import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.main import app
from app.services.database import Database
from app.models.trigger import TriggerCreate, TriggerType
from app.services.trigger_service import TriggerService
from app.utils.scheduler import execute_api_trigger

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def setup_database():
    await Database.connect_db()
    yield
    # Clean up test data
    await Database.db.triggers.delete_many({})
    await Database.db.events.delete_many({})
    await Database.close_db()

async def test_create_scheduled_trigger(client):
    # Test one-time trigger
    response = await client.post("/api/v1/triggers/", json={
        "name": "Test One-time Trigger",
        "description": "Test trigger",
        "trigger_type": "scheduled",
        "schedule_config": {
            "schedule_type": "one_time",
            "interval_type": "minutes",
            "interval_value": 30
        }
    })
    assert response.status_code == 200
    assert "trigger_id" in response.json()

@pytest.mark.asyncio
async def test_create_api_trigger(test_client, sample_trigger_data):
    response = test_client.post("/api/v1/triggers/", json=sample_trigger_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_trigger_data["name"]
    assert data["trigger_type"] == "api"
    assert "id" in data

async def test_test_trigger(client):
    response = await client.post("/api/v1/triggers/test", json={
        "name": "Test Trigger",
        "trigger_type": "scheduled",
        "schedule_config": {
            "schedule_type": "one_time",
            "interval_type": "minutes",
            "interval_value": 5
        }
    })
    assert response.status_code == 200

async def test_recurring_trigger(client):
    response = await client.post("/api/v1/triggers/", json={
        "name": "Recurring Trigger",
        "description": "Test recurring trigger",
        "trigger_type": "scheduled",
        "schedule_config": {
            "schedule_type": "recurring",
            "specific_time": {
                "hour": 14,
                "minute": 30
            }
        }
    })
    assert response.status_code == 200
    assert "trigger_id" in response.json()

async def test_update_trigger(test_client, sample_trigger_data):
    # Create a trigger
    create_response = test_client.post("/api/v1/triggers/", json=sample_trigger_data)
    trigger_id = create_response.json()["id"]
    
    # Update the trigger
    updated_data = sample_trigger_data.copy()
    updated_data["name"] = "Updated Test Trigger"
    
    response = test_client.put(f"/api/v1/triggers/{trigger_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Test Trigger"

async def test_delete_trigger(client):
    # First create a trigger
    create_response = await client.post("/api/v1/triggers/", json={
        "name": "Delete Test",
        "trigger_type": "api",
        "api_config": {
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
            "payload_schema": {"test": "value"}
        }
    })
    trigger_id = create_response.json()["trigger_id"]
    
    # Delete the trigger
    delete_response = await client.delete(f"/api/v1/triggers/{trigger_id}")
    assert delete_response.status_code == 200
    
    # Verify trigger is deleted
    get_response = await client.get(f"/api/v1/triggers/{trigger_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_create_scheduled_trigger(test_client, sample_schedule_data):
    response = test_client.post("/api/v1/triggers/", json=sample_schedule_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_schedule_data["name"]
    assert data["trigger_type"] == "scheduled"
    assert "id" in data

@pytest.mark.asyncio
async def test_trigger_lifecycle():
    # Create
    trigger = TriggerCreate(
        name="Lifecycle Test",
        trigger_type=TriggerType.API,
        api_config={
            "endpoint": "https://httpbin.org/post",
            "method": "POST",
            "payload_schema": {"test": "data"}
        }
    )
    trigger_id = await TriggerService.create_trigger(trigger)
    
    # Get
    saved_trigger = await TriggerService.get_trigger(trigger_id)
    assert saved_trigger["name"] == "Lifecycle Test"
    
    # Update
    update_success = await TriggerService.update_trigger(
        trigger_id,
        {"name": "Updated Name"}
    )
    assert update_success
    
    # Delete
    delete_success = await TriggerService.delete_trigger(trigger_id)
    assert delete_success

async def test_get_triggers(test_client, sample_trigger_data):
    # Create a trigger first
    create_response = test_client.post("/api/v1/triggers/", json=sample_trigger_data)
    assert create_response.status_code == 200
    
    # Get all triggers
    response = test_client.get("/api/v1/triggers/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

async def test_execute_api_trigger(test_client, sample_trigger_data):
    # Create a trigger
    create_response = test_client.post("/api/v1/triggers/", json=sample_trigger_data)
    trigger_id = create_response.json()["id"]
    
    # Execute the trigger
    payload = {"message": "test message"}
    response = test_client.post(f"/api/v1/triggers/{trigger_id}/execute", json=payload)
    assert response.status_code == 200 