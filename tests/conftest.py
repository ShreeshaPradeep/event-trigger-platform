import pytest
import asyncio
from app.services.database import Database
from app.config import settings

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