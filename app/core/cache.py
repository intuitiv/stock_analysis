"""
Redis cache implementation for NAETRA
"""
import aioredis
from typing import Optional, Any
from .config import settings

class RedisCache:
    """Redis cache implementation"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection"""
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None

    async def connect(self) -> None:
        """Connect to Redis"""
        if not self._redis:
            try:
                # Ensure URL is string and add connection options
                redis_url = str(self.redis_url)
                self._redis = await aioredis.from_url(
                    redis_url,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                    retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                    db=settings.REDIS_DB
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Any:
        """Get value from cache"""
        if not self._redis:
            await self.connect()
        return await self._redis.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL in seconds"""
        if not self._redis:
            await self.connect()
        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        if not self._redis:
            await self.connect()
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._redis:
            await self.connect()
        return await self._redis.exists(key)

    async def ping(self) -> bool:
        """Check Redis connection"""
        if not self._redis:
            await self.connect()
        try:
            return await self._redis.ping()
        except:
            return False

    async def close(self) -> None:
        """Close Redis connection"""
        await self.disconnect()

# Create default cache instance
default_cache = RedisCache()

async def get_redis_client() -> RedisCache:
    """Get Redis client instance"""
    await default_cache.connect()
    return default_cache
