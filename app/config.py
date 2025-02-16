from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # MongoDB settings
    MONGODB_URL: str
    DATABASE_NAME: str = "event_trigger_db"
    ENVIRONMENT: str = "production"
    
    # Application settings
    APP_NAME: str = "Event Trigger Platform"
    DEBUG: bool = True
    
    # Event retention settings
    EVENT_ACTIVE_HOURS: int = 2
    EVENT_ARCHIVE_HOURS: int = 46
    EVENT_TOTAL_RETENTION_HOURS: int = 48
    
    # Scheduler settings - update these for testing
    MIN_INTERVAL_MINUTES: int = 5  # Allow minimum 5-minute intervals
    MIN_INTERVAL_HOURS: int = 1
    MIN_INTERVAL_DAYS: int = 1

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 