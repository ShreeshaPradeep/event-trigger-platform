from app.models.trigger import Trigger, TriggerType
from app.models.event import Event
from app.services.event_service import EventService
from datetime import datetime, timedelta
import asyncio
import logging
import httpx
from typing import Optional

class TriggerExecutor:
    @staticmethod
    async def execute_trigger(trigger: Trigger, is_test: bool = False) -> Optional[Event]:
        try:
            event_data = {
                "trigger_id": trigger.id,
                "trigger_name": trigger.name,
                "is_test": is_test,
                "triggered_at": datetime.utcnow()
            }

            if trigger.type == TriggerType.API:
                # For API triggers, store the API schema as payload
                event_data["payload"] = trigger.api_schema

            # Create and save the event
            event = await EventService.create_event(event_data)
            
            # If it's a test execution, don't schedule future executions
            if is_test:
                return event

            # Schedule next execution if it's a recurring trigger
            if (trigger.type == TriggerType.SCHEDULED and 
                trigger.schedule_type == "interval" and 
                not is_test):
                await TriggerExecutor._schedule_next_execution(trigger)

            return event

        except Exception as e:
            logging.error(f"Error executing trigger {trigger.id}: {str(e)}")
            return None

    @staticmethod
    async def execute_api_trigger(trigger: Trigger, payload: dict) -> Optional[Event]:
        try:
            # Validate payload against schema
            if not TriggerExecutor._validate_payload(trigger.api_schema, payload):
                raise ValueError("Invalid payload for trigger schema")

            event_data = {
                "trigger_id": trigger.id,
                "trigger_name": trigger.name,
                "payload": payload,
                "triggered_at": datetime.utcnow()
            }

            return await EventService.create_event(event_data)

        except Exception as e:
            logging.error(f"Error executing API trigger {trigger.id}: {str(e)}")
            return None

    @staticmethod
    def _validate_payload(schema: dict, payload: dict) -> bool:
        """
        Validate that the payload matches the expected schema
        """
        try:
            for key, value_type in schema.items():
                if key not in payload:
                    return False
                if not isinstance(payload[key], eval(value_type)):
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    async def _schedule_next_execution(trigger: Trigger):
        """
        Schedule the next execution for interval-based triggers
        """
        try:
            interval_minutes = int(trigger.schedule_value)
            next_run = datetime.utcnow() + timedelta(minutes=interval_minutes)
            
            # Use APScheduler to schedule the next run
            from app.utils.scheduler import scheduler
            scheduler.add_job(
                TriggerExecutor.execute_trigger,
                'date',
                run_date=next_run,
                args=[trigger, False],
                id=f'trigger_{trigger.id}_{next_run.timestamp()}'
            )
        except Exception as e:
            logging.error(f"Error scheduling next execution for trigger {trigger.id}: {str(e)}") 