from pydantic import BaseModel
from datetime import datetime

class EventLogCreate(BaseModel):
    trigger_id: str
    payload: str

class EventLogResponse(BaseModel):
    id: str
    trigger_id: str
    triggered_at: datetime
    payload: str 