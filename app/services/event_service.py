from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from app.models.event import Event, EventStatus
from app.services.database import Database
import logging
import uuid
import asyncio
from bson.objectid import ObjectId
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class EventService:
    change_stream = None

    @classmethod
    async def setup_change_stream(cls):
        """Setup change stream for event state management"""
        pipeline = [
            {
                '$match': {
                    'operationType': 'insert',
                    'fullDocument.retention_state': 'active'
                }
            }
        ]
        
        cls.change_stream = Database.db.events.watch(pipeline)
        
        async def process_changes():
            async with cls.change_stream as stream:
                async for change in stream:
                    doc = change['fullDocument']
                    # Schedule archival
                    archive_at = doc['archive_time']
                    scheduler.add_job(
                        cls.archive_event,
                        'date',
                        run_date=archive_at,
                        args=[str(doc['_id'])]
                    )

        asyncio.create_task(process_changes())

    @staticmethod
    async def archive_event(event_id: str):
        """Archive a single event"""
        now = datetime.now(timezone.utc)
        query = {
            "_id": ObjectId(event_id),
            "retention_state": "active"
        }
        update = {
            "$set": {
                "retention_state": "archived",
                "archived_at": now
            }
        }
        await Database.update_one("events", query, update)

    @staticmethod
    async def create_event(
        trigger_id: str,
        trigger_type: str,
        is_test: bool = False,
        is_manual: bool = False,
        api_payload: Optional[Dict] = None,
        response_data: Optional[Dict] = None
    ) -> str:
        """Create an event log with all required information"""
        now = datetime.now(timezone.utc)
        
        event = {
            "trigger_id": trigger_id,
            "trigger_type": trigger_type,
            "is_test": is_test,
            "is_manual": is_manual,
            "execution_time": now,
            "retention_state": "active",
            "api_payload": api_payload,
            "response_data": response_data,
            "created_at": now
        }
        
        return await Database.insert_one("events", event)

    @staticmethod
    async def get_recent_events() -> List[Dict]:
        """Get recent events (last 2 hours only)"""
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=2)
            query = {
                "created_at": {"$gte": time_threshold},
                "retention_state": "active"  # Only active events
            }
            return await Database.find_many("events", query)
        except Exception as e:
            logging.error(f"Error getting recent events: {str(e)}")
            raise

    @staticmethod
    async def get_archived_events() -> List[Dict]:
        """Get archived events (2-48 hours old)"""
        try:
            now = datetime.now(timezone.utc)
            query = {
                "created_at": {
                    "$gte": now - timedelta(hours=48),  # Not older than 48 hours
                    "$lt": now - timedelta(hours=2)     # At least 2 hours old
                },
                "retention_state": "archived"
            }
            return await Database.find_many("events", query)
        except Exception as e:
            logging.error(f"Error getting archived events: {str(e)}")
            raise

    @staticmethod
    async def archive_events():
        """Archive events older than 2 hours"""
        now = datetime.now(timezone.utc)
        archive_threshold = now - timedelta(hours=2)
        
        # Find active events older than 2 hours
        query = {
            "retention_state": "active",
            "created_at": {"$lt": archive_threshold}
        }
        update = {
            "$set": {
                "retention_state": "archived",
                "archived_at": now
            }
        }
        await Database.update_many("events", query, update)

    @staticmethod
    async def cleanup_events():
        """Delete events older than 48 hours"""
        now = datetime.now(timezone.utc)
        delete_threshold = now - timedelta(hours=48)
        
        query = {
            "created_at": {"$lt": delete_threshold}
        }
        await Database.delete_many("events", query)

    @staticmethod
    async def get_event_stats(hours: int = 48):
        """Get event statistics grouped by trigger"""
        try:
            db = Database.get_db()
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": time_threshold}
                    }
                },
                {
                    "$group": {
                        "_id": "$trigger_id",
                        "trigger_name": {"$first": "$trigger_name"},
                        "total_executions": {"$sum": 1},
                        "successful_executions": {
                            "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                        },
                        "failed_executions": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "test_executions": {
                            "$sum": {"$cond": ["$is_test", 1, 0]}
                        },
                        "manual_executions": {
                            "$sum": {"$cond": ["$is_manual", 1, 0]}
                        },
                        "last_execution": {"$max": "$execution_time"}
                    }
                }
            ]
            
            return await db.events.aggregate(pipeline).to_list(None)
        except Exception as e:
            logging.error(f"Error in get_event_stats: {str(e)}")
            return [] 