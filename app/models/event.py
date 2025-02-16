from enum import Enum
from typing import Optional, Dict, Literal
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import uuid

class EventStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

class Event(BaseModel):
    id: str
    trigger_id: str
    trigger_name: str
    trigger_type: Literal["scheduled", "api"]
    status: EventStatus
    execution_time: datetime
    is_test: bool = False
    is_manual: bool = False
    api_payload: Optional[Dict] = None
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    retention_state: Literal["active", "archived"] = "active"
    created_at: datetime
    archived_at: Optional[datetime] = None
    archive_time: datetime  # 2 hours from creation
    expiry_time: datetime  # 48 hours from creation
    trigger_details: Dict  # Store trigger configuration

    class Config:
        json_schema_extra = {
            "example": {
                "trigger_id": "123e4567-e89b-12d3-a456-426614174000",
                "trigger_type": "scheduled",
                "status": "success",
                "execution_time": "2024-04-01T12:00:00",
                "is_test": False
            }
        } 