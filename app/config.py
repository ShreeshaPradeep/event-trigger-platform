from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # MongoDB settings
    MONGODB_URL: str = os.getenv('MONGODB_URL', '')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME', 'event_triggers')
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'production')
    
    # Application settings
    APP_NAME: str = "Event Trigger Platform"
    DEBUG: bool = False
    
    # Event retention settings
    EVENT_ACTIVE_HOURS: int = 2
    EVENT_ARCHIVE_HOURS: int = 46
    EVENT_TOTAL_RETENTION_HOURS: int = 48
    
    # Scheduler settings
    MIN_INTERVAL_MINUTES: int = 5
    MIN_INTERVAL_HOURS: int = 1
    MIN_INTERVAL_DAYS: int = 1

    class Config:
        env_file = ".env"

settings = Settings() 