from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
from ...models.event_log import EventLogCreate, EventLogResponse
from ...config.database import event_logs_collection

router = APIRouter()

@router.post("/event-logs", response_model=EventLogResponse)
def create_event_log(event: EventLogCreate):
    event_id = str(uuid.uuid4())
    event_data = {
        "id": event_id,
        "trigger_id": event.trigger_id,
        "triggered_at": datetime.now(),
        "payload": event.payload
    }
    event_logs_collection.insert_one(event_data)
    return event_data

@router.get("/event-logs/{event_id}", response_model=EventLogResponse)
def get_event_log(event_id: str):
    event = event_logs_collection.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event log not found")
    return event 