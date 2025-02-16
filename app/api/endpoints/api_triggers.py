from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...config.database import event_logs_collection
from datetime import datetime
import uuid

router = APIRouter()

class APITriggerCreate(BaseModel):
    trigger_id: str
    payload: str

@router.post("/api-triggers")
def create_api_trigger(trigger: APITriggerCreate):
    # Log the event directly to the database
    event_data = {
        "id": str(uuid.uuid4()),
        "trigger_id": trigger.trigger_id,
        "triggered_at": datetime.now(),
        "payload": trigger.payload
    }
    event_logs_collection.insert_one(event_data)
    return {"message": "API trigger executed"} 