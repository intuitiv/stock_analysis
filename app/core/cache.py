from typing import Any, Optional, Union
import json
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings
import logging # For logger usage in event handlers
logger = logging.getLogger(__name__) # For main app logging

class RedisCache:
    """Redis cache utility class. Handles optional Redis configuration."""
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    def __init__(self):
        """Initialize Redis client if REDIS_URL is configured."""
        self.default_ttl = 3600  # Default TTL: 1 hour
        
        if settings.REDIS_URL:
            if RedisCache._pool is None: # Initialize pool only once
                try:
                    RedisCache._pool = ConnectionPool.from_url(
                        str(settings.REDIS_URL), # Ensure it's a string
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=settings.REDIS_POOL_SIZE
                    )
                    print("Redis connection pool initialized.")
                except ValueError as e:
                    print(f"Error initializing Redis connection pool: {e}. REDIS_URL: '{settings.REDIS_URL}'")
                    RedisCache._pool = None # Ensure pool is None if init fails
            
            if RedisCache._pool:
                RedisCache._client = Redis(connection_pool=RedisCache._pool)
            else:
                RedisCache._client = None # Ensure client is None if pool failed
        else:
            print("REDIS_URL not configured. RedisCache will be a no-op.")
            RedisCache._client = None
        
        self.redis: Optional[Redis] = RedisCache._client


    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except (json.JSONDecodeError, Exception) as e:
            print(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        expire: Optional[int] = None # Add expire for compatibility
    ) -> bool:
        """Set value in cache. Accepts 'ttl' (preferred) or 'expire' for compatibility."""
        if not self.redis:
            return False
        
        actual_ttl = ttl
        if expire is not None:
            if ttl is not None:
                logger.warning(f"RedisCache.set called with both ttl ({ttl}) and expire ({expire}) for key '{key}'. Using 'ttl'.")
            else:
                logger.warning(f"RedisCache.set called with 'expire' ({expire}) for key '{key}'. Please use 'ttl' instead.")
                actual_ttl = expire # Use expire if ttl is not provided
        
        effective_ttl = actual_ttl if actual_ttl is not None else self.default_ttl
        
        try:
            serialized = json.dumps(value)
            logger.debug(f"RedisCache: Calling self.redis.set for key '{key}' with ex={effective_ttl}")
            return await self.redis.set(
                key,
                serialized,
                ex=effective_ttl # redis-py uses 'ex' for seconds
            )
        except (json.JSONDecodeError, Exception) as e:
            # Log the type of exception and the key for better debugging
            logger.error(f"Cache set error for key '{key}' (Type: {type(e).__name__}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis:
            return False
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis:
            return False
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in cache"""
        if not self.redis:
            return None
        try:
            return await self.redis.incr(key, amount)
        except Exception as e:
            print(f"Cache increment error: {e}")
            return None

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value in cache"""
        if not self.redis:
            return None
        try:
            return await self.redis.decr(key, amount)
        except Exception as e:
            print(f"Cache decrement error: {e}")
            return None

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache"""
        if not self.redis:
            return False
        try:
            pipeline = self.redis.pipeline()
            for key, value in mapping.items():
                serialized = json.dumps(value)
                pipeline.set(key, serialized, ex=ttl or self.default_ttl)
            await pipeline.execute()
            return True
        except Exception as e:
            print(f"Cache set_many error: {e}")
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache"""
        if not self.redis:
            return {key: None for key in keys}
        try:
            pipeline = self.redis.pipeline()
            for key in keys:
                pipeline.get(key)
            values = await pipeline.execute()
            return {
                key: json.loads(value) if value else None
                for key, value in zip(keys, values)
            }
        except Exception as e:
            print(f"Cache get_many error: {e}")
            return {key: None for key in keys}

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple values from cache"""
        if not self.redis:
            return 0
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache delete_many error: {e}")
            return 0

    async def clear(self, pattern: str = "*") -> bool:
        """Clear cache matching pattern"""
        if not self.redis:
            return False # Or True, as there's nothing to clear
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.redis:
            return -2 # Consistent with Redis TTL for non-existent key or no Redis
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            print(f"Cache ttl error: {e}")
            return -1

    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """Extend TTL for key"""
        if not self.redis:
            return False
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            print(f"Cache extend_ttl error: {e}")
            return False

    async def ping(self) -> bool:
        """Check Redis connection"""
        if not self.redis:
            return False # No Redis configured, so "ping" fails in a sense
        try:
            return await self.redis.ping()
        except Exception as e:
            print(f"Cache ping error: {e}")
            return False

# Create global cache instance
cache = RedisCache()

# Example usage:
"""
# In your FastAPI endpoint:
@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    # Try to get from cache first
    cache_key = f"market_data:{symbol}"
    data = await cache.get(cache_key)
    
    if data is None:
        # If not in cache, fetch from database/API
        data = await fetch_market_data(symbol)
        # Store in cache for future requests
        await cache.set(cache_key, data, ttl=300)  # Cache for 5 minutes
    
    return data

# Rate limiting example:
async def check_rate_limit(user_id: str, limit: int, window: int) -> bool:
    key = f"rate_limit:{user_id}"
    count = await cache.increment(key)
    
    if count == 1:
        await cache.expire(key, window)
    
    return count <= limit
"""
