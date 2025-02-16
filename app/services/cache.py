import redis
from app.config import settings
import json
import logging

class RedisCache:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                cls._client = redis.from_url(settings.REDIS_URL)
                logging.info("Connected to Redis.")
            except Exception as e:
                logging.error(f"Failed to connect to Redis: {e}")
                raise
        return cls._client

    @classmethod
    async def set_cache(cls, key: str, value: dict, expiry: int = 3600):
        try:
            client = cls.get_client()
            client.setex(key, expiry, json.dumps(value))
        except Exception as e:
            logging.error(f"Cache set error: {e}")

    @classmethod
    async def get_cache(cls, key: str):
        try:
            client = cls.get_client()
            data = client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None 