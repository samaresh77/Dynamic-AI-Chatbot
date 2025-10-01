import redis.asyncio as redis
from config.settings import settings
import json
from typing import Any, Optional

class CacheManager:
    def __init__(self):
        self.redis_pool = None

    async def get_redis_pool(self):
        if not self.redis_pool:
            self.redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)

    async def set(self, key: str, value: Any, expire: int = 3600):
        redis_client = await self.get_redis_pool()
        await redis_client.set(key, json.dumps(value), ex=expire)

    async def get(self, key: str) -> Optional[Any]:
        redis_client = await self.get_redis_pool()
        value = await redis_client.get(key)
        return json.loads(value) if value else None

    async def delete(self, key: str):
        redis_client = await self.get_redis_pool()
        await redis_client.delete(key)

# Global cache instance
cache_manager = CacheManager()

async def get_redis_pool():
    return await cache_manager.get_redis_pool()