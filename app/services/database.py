from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.config import settings
import asyncio

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        if cls.client is None:
            try:
                # Add retry logic
                for attempt in range(3):
                    try:
                        cls.client = AsyncIOMotorClient(
                            settings.MONGODB_URL,
                            serverSelectionTimeoutMS=5000,
                            connectTimeoutMS=5000,
                            retryWrites=True
                        )
                        cls.db = cls.client[settings.DATABASE_NAME]
                        # Test the connection
                        await cls.client.admin.command('ping')
                        logging.info("Connected to MongoDB Atlas")
                        break
                    except Exception as e:
                        if attempt == 2:  # Last attempt
                            raise
                        logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
                raise

    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logging.info("Closed MongoDB connection")

    @classmethod
    def get_db(cls):
        """Get database instance"""
        return cls.db

    @staticmethod
    def _convert_id(document: Dict) -> Dict:
        """Convert MongoDB _id to string id"""
        if document and '_id' in document:
            document['id'] = str(document['_id'])
            del document['_id']
        return document

    @classmethod
    async def insert_one(cls, collection: str, document: Dict) -> str:
        """Insert a document and return its ID"""
        result = await cls.db[collection].insert_one(document)
        return str(result.inserted_id)

    @classmethod
    async def find_one(cls, collection: str, query: Dict) -> Optional[Dict]:
        """Find a single document"""
        try:
            result = await cls.db[collection].find_one(query)
            if result:
                return cls._convert_id(result)
            return None
        except Exception as e:
            logging.error(f"Database find_one error: {str(e)}")
            raise

    @classmethod
    async def find_many(cls, collection: str, query: Dict) -> List[Dict]:
        """Find multiple documents"""
        try:
            cursor = cls.db[collection].find(query)
            documents = []
            async for document in cursor:
                documents.append(cls._convert_id(document))
            return documents
        except Exception as e:
            logging.error(f"Database find_many error: {str(e)}")
            raise

    @classmethod
    async def update_one(cls, collection: str, query: Dict, update: Dict) -> bool:
        """Update a single document"""
        try:
            result = await cls.db[collection].update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Database update_one error: {str(e)}")
            return False

    @classmethod
    async def update_many(cls, collection: str, query: Dict, update: Dict):
        """Update multiple documents"""
        result = await cls.db[collection].update_many(query, update)
        return result.modified_count

    @classmethod
    async def delete_one(cls, collection: str, query: Dict) -> bool:
        """Delete a document"""
        result = await cls.db[collection].delete_one(query)
        return result.deleted_count > 0

    @classmethod
    async def delete_many(cls, collection: str, query: Dict) -> int:
        """Delete multiple documents"""
        result = await cls.db[collection].delete_many(query)
        return result.deleted_count

    @classmethod
    async def setup_indexes(cls):
        """Setup database indexes"""
        try:
            # First, drop existing indexes that we want to recreate with TTL
            try:
                await cls.db.events.drop_index("archive_time_ttl")
                await cls.db.events.drop_index("expiry_time_ttl")
            except Exception as e:
                logging.info(f"Indexes don't exist yet or already dropped: {str(e)}")

            # Triggers collection indexes
            await cls.db.triggers.create_index([("is_active", 1)])
            await cls.db.triggers.create_index([("trigger_type", 1)])
            
            # Events collection indexes
            await cls.db.events.create_index([("trigger_id", 1)])
            await cls.db.events.create_index([("retention_state", 1)])
            await cls.db.events.create_index([("created_at", -1)])
            
            # TTL indexes for strict retention rules
            await cls.db.events.create_index(
                [("created_at", 1)],
                expireAfterSeconds=7200,  # 2 hours - active to archived
                partialFilterExpression={"retention_state": "active"},
                name="active_retention_ttl"
            )
            
            await cls.db.events.create_index(
                [("created_at", 1)],
                expireAfterSeconds=172800,  # 48 hours - total lifetime
                name="event_expiry_ttl"
            )
            
            logging.info("Database indexes created successfully")
        except Exception as e:
            logging.error(f"Failed to create indexes: {str(e)}")
            raise 