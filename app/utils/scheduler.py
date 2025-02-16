from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
import httpx
from app.utils.logger import logger
from app.services.event_service import EventService

scheduler = AsyncIOScheduler()

async def execute_scheduled_trigger(trigger_id: str, is_test: bool = False):
    """Execute a scheduled trigger"""
    try:
        logger.info(f"Executing scheduled trigger: {trigger_id}")
        await EventService.create_event(
            trigger_id=trigger_id,
            trigger_type="scheduled",
            is_test=is_test,
            is_manual=False
        )
        logger.info(f"Successfully executed trigger: {trigger_id}")
    except Exception as e:
        logger.error(f"Failed to execute scheduled trigger {trigger_id}: {str(e)}")
        raise

async def execute_api_trigger(
    trigger_id: str,
    api_config: dict,
    payload: dict = None,
    is_test: bool = False,
    is_manual: bool = False
):
    """Execute an API trigger"""
    try:
        logger.info(f"Executing API trigger: {trigger_id}")
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=api_config["method"],
                url=api_config["endpoint"],
                json=payload or api_config["payload_schema"],
                headers=api_config.get("headers", {})
            )
            response.raise_for_status()
            logger.info(f"API trigger {trigger_id} executed successfully")

        await EventService.create_event(
            trigger_id=trigger_id,
            trigger_type="api",
            is_test=is_test,
            is_manual=is_manual,
            api_payload=payload,
            response_data=response.json()
        )
    except Exception as e:
        logger.error(f"Failed to execute API trigger {trigger_id}: {str(e)}")
        raise

async def add_scheduled_trigger(trigger_id: str, schedule_config: dict, is_test: bool = False):
    """Add a scheduled trigger to the scheduler"""
    now = datetime.now(timezone.utc)

    if schedule_config["schedule_type"] == "one_time":
        if schedule_config.get("specific_date"):
            # Use exact date-time
            trigger = DateTrigger(run_date=schedule_config["specific_date"])
            cleanup_time = schedule_config["specific_date"] + timedelta(minutes=1)
        elif schedule_config.get("specific_time"):
            trigger = DateTrigger(run_date=schedule_config["specific_time"])
            cleanup_time = schedule_config["specific_time"] + timedelta(minutes=1)
        else:
            run_date = now + timedelta(
                **{schedule_config["interval_type"]: schedule_config["interval_value"]}
            )
            trigger = DateTrigger(run_date=run_date)
            cleanup_time = run_date + timedelta(minutes=1)
    else:  # recurring
        if schedule_config.get("specific_time"):
            time_config = schedule_config["specific_time"]
            trigger = CronTrigger(
                hour=time_config["hour"],
                minute=time_config["minute"]
            )
            cleanup_time = None
        else:
            trigger = IntervalTrigger(
                **{schedule_config["interval_type"]: schedule_config["interval_value"]}
            )
            cleanup_time = None

    job = scheduler.add_job(
        execute_scheduled_trigger,
        trigger=trigger,
        args=[trigger_id, is_test],
        id=f"{trigger_id}_{'test' if is_test else 'permanent'}",
        replace_existing=True
    )

    if (schedule_config["schedule_type"] == "one_time" or is_test) and cleanup_time:
        scheduler.add_job(
            cleanup_trigger,
            trigger=DateTrigger(run_date=cleanup_time),
            args=[trigger_id, is_test],
            id=f"{trigger_id}_cleanup"
        )

    return job

async def cleanup_trigger(trigger_id: str, is_test: bool):
    """Remove one-time or test triggers"""
    try:
        job_id = f"{trigger_id}_{'test' if is_test else 'permanent'}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        logger.info(f"Cleaned up trigger {trigger_id}")
    except Exception as e:
        logger.error(f"Error cleaning up trigger {trigger_id}: {str(e)}")

async def setup_scheduler():
    """Initialize the scheduler"""
    # Archive events every 15 minutes
    scheduler.add_job(
        EventService.archive_events,
        'interval',
        minutes=15,
        id='archive_events'
    )

    # Cleanup old events every hour
    scheduler.add_job(
        EventService.cleanup_events,
        'interval',
        hours=1,
        id='cleanup_events'
    )

    scheduler.start() 