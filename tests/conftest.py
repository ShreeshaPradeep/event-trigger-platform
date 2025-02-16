import pytest
import asyncio
from app.services.database import Database
from app.config import settings
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_database():
    # Connect to test database
    settings.DATABASE_NAME = "event_triggers_test"
    await Database.connect_db()
    await Database.setup_indexes()
    
    yield
    
    # Cleanup after tests
    await Database.db.triggers.delete_many({})
    await Database.db.events.delete_many({})
    await Database.close_db()

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
async def test_db():
    # Use a test database
    test_db_name = f"{settings.DATABASE_NAME}_test"
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[test_db_name]
    
    # Set up test database
    Database.client = client
    Database.db = db
    
    yield db
    
    # Cleanup after tests
    await client.drop_database(test_db_name)
    await client.close()

@pytest.fixture
async def sample_trigger_data():
    return {
        "name": "Test Trigger",
        "trigger_type": "api",
        "api_config": {
            "endpoint": "https://api.example.com/test",
            "method": "POST",
            "payload_schema": {
                "message": "string"
            }
        }
    }

@pytest.fixture
async def sample_schedule_data():
    return {
        "name": "Test Schedule",
        "trigger_type": "scheduled",
        "schedule_config": {
            "schedule_type": "one_time",
            "specific_date": "2024-12-31T23:59:59"
        }
    } 