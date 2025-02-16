from enum import Enum
from typing import Optional, Dict, Literal, Union, Any
from pydantic import BaseModel, Field, HttpUrl, validator, model_validator, AnyUrl
from datetime import datetime, timezone, time
from urllib.parse import urlparse

class TriggerType(str, Enum):
    SCHEDULED = "scheduled"
    API = "api"

class ScheduleType(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"

class IntervalType(str, Enum):
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

class TimeConfig(BaseModel):
    hour: int
    minute: int

    @validator('hour')
    def validate_hour(cls, v):
        if not 0 <= v <= 23:
            raise ValueError("Hour must be between 0 and 23")
        return v

    @validator('minute')
    def validate_minute(cls, v):
        if not 0 <= v <= 59:
            raise ValueError("Minute must be between 0 and 59")
        return v

class ScheduleConfig(BaseModel):
    schedule_type: ScheduleType
    interval_type: Optional[Literal["minutes", "hours", "days"]] = None
    interval_value: Optional[int] = None
    specific_time: Optional[Union[datetime, TimeConfig]] = None
    specific_date: Optional[datetime] = None  # For exact date-time scheduling

    @model_validator(mode='after')
    def validate_schedule(self) -> 'ScheduleConfig':
        if self.schedule_type:
            if self.specific_date and (self.interval_type or self.interval_value or self.specific_time):
                raise ValueError("Cannot specify both specific_date and other timing options")
            
            if not self.specific_date and not self.specific_time and not (self.interval_type and self.interval_value):
                raise ValueError("Must specify either specific_date, specific_time, or interval")
            
            # Validate intervals
            if self.interval_type and self.interval_value:
                if self.interval_type == "minutes" and self.interval_value < 5:
                    raise ValueError("Minimum interval is 5 minutes")
                elif self.interval_type == "hours" and self.interval_value < 1:
                    raise ValueError("Minimum interval is 1 hour")
                elif self.interval_type == "days" and self.interval_value < 1:
                    raise ValueError("Minimum interval is 1 day")
            
            # Validate specific_date is in future
            if self.specific_date and self.specific_date <= datetime.now(timezone.utc):
                raise ValueError("Specific date must be in the future")
                
        return self

class APIConfig(BaseModel):
    endpoint: str
    method: str = Field(default="POST")
    payload_schema: Dict[str, Any] = Field(default_factory=dict)

    @validator('endpoint')
    def validate_endpoint(cls, v):
        if not validate_url(v):
            raise ValueError('Invalid URL format')
        return v

    @validator('method')
    def validate_method(cls, v):
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE']
        if v.upper() not in valid_methods:
            raise ValueError(f'Method must be one of {valid_methods}')
        return v.upper()

class TriggerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType
    schedule_config: Optional[ScheduleConfig] = None
    api_config: Optional[APIConfig] = None

    @model_validator(mode='after')
    def validate_configs(self) -> 'TriggerCreate':
        if self.trigger_type == TriggerType.SCHEDULED and not self.schedule_config:
            raise ValueError("schedule_config is required for scheduled triggers")
        if self.trigger_type == TriggerType.API and not self.api_config:
            raise ValueError("api_config is required for API triggers")
        return self

class TriggerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_config: Optional[Dict] = None
    api_config: Optional[Dict] = None

    @validator('schedule_config')
    def validate_schedule_config(cls, v, values):
        if v:
            if 'schedule_type' not in v:
                raise ValueError("schedule_type is required in schedule_config")
            if v['schedule_type'] not in ['one_time', 'recurring']:
                raise ValueError("Invalid schedule_type")
        return v

    @validator('api_config')
    def validate_api_config(cls, v):
        if v:
            required_fields = ['endpoint', 'method', 'payload_schema']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"{field} is required in api_config")
            
            # Validate method
            if v['method'] not in ['GET', 'POST', 'PUT', 'DELETE']:
                raise ValueError("Invalid HTTP method")
            
            # Validate endpoint URL
            try:
                result = urlparse(v['endpoint'])
                if not all([result.scheme, result.netloc]):
                    raise ValueError("Invalid URL")
            except Exception:
                raise ValueError("Invalid URL format")
            
            # Validate payload schema
            if not isinstance(v['payload_schema'], dict):
                raise ValueError("payload_schema must be a dictionary")
            
            # Validate headers if present
            if 'headers' in v and not isinstance(v['headers'], dict):
                raise ValueError("headers must be a dictionary")
        return v

class Trigger(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType
    schedule_config: Optional[ScheduleConfig] = None
    api_config: Optional[APIConfig] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    last_triggered: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Daily Report",
                "type": "scheduled",
                "schedule_type": "fixed_time",
                "schedule_value": "0 9 * * *",
                "is_active": True
            }
        } 