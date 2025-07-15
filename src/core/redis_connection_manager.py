"""
Redis Connection Manager for Production Environment
Handles DigitalOcean managed Redis with SSL, connection pooling, and retry logic
"""

import os
import asyncio
import logging
import ssl
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis versions
    import redis
    redis.asyncio = redis

logger = logging.getLogger(__name__)

class ProductionRedisManager:
    """Production-ready Redis connection manager with enhanced error handling"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self.is_connected = False
        self.retry_count = 0
        self.max_retries = 5
        self.retry_delay = 2
        
        # Get Redis configuration from environment
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        
        # Check if SSL is required (DigitalOcean managed Redis)
        self.ssl_required = (
            'ondigitalocean.com' in self.redis_url or 
            self.redis_url.startswith('rediss://')
        )
        
        logger.info(f"Redis Manager initialized - Host: {self.redis_host}:{self.redis_port}, SSL: {self.ssl_required}")
    
    async def initialize(self) -> bool:
        """Initialize Redis connection with retry logic"""
        try:
            # Use from_url for all connections - it handles SSL automatically
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                socket_keepalive=True,
                health_check_interval=30,
                max_connections=10,
                retry_on_timeout=True
            )
            
            # Test connection with retry logic
            await self._test_connection_with_retry()
            
            self.is_connected = True
            logger.info("✅ Redis connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            self.is_connected = False
            return False
    
    async def _test_connection_with_retry(self):
        """Test Redis connection with exponential backoff retry"""
        for attempt in range(self.max_retries):
            try:
                if self.redis_client:
                    await self.redis_client.ping()
                    logger.info(f"✅ Redis connection test successful (attempt {attempt + 1})")
                    return
                else:
                    raise Exception("Redis client not initialized")
            except Exception as e:
                self.retry_count += 1
                if attempt == self.max_retries - 1:
                    raise e
                
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"⚠️ Redis connection failed (attempt {attempt + 1}): {e}")
                logger.info(f"🔄 Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

    async def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client, initialize if not connected"""
        if not self.is_connected:
            await self.initialize()
        return self.redis_client
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("✅ Redis connection closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for Redis operations"""
        client = await self.get_client()
        if not client:
            raise Exception("Redis client not available")
        try:
            yield client
        finally:
            # Connection is managed by the pool, no need to close
            pass
    
    async def set_with_retry(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    await client.set(key, value, ex=ex)
                    return True
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis SET failed after 3 attempts: {e}")
                    return False
                await asyncio.sleep(1)
        return False
    
    async def get_with_retry(self, key: str) -> Optional[Any]:
        """Get value with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    return await client.get(key)
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis GET failed after 3 attempts: {e}")
                    return None
                await asyncio.sleep(1)
        return None
    
    async def delete_with_retry(self, key: str) -> bool:
        """Delete key with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    await client.delete(key)
                    return True
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis DELETE failed after 3 attempts: {e}")
                    return False
                await asyncio.sleep(1)
        return False
    
    async def keys_with_retry(self, pattern: str) -> list:
        """Get keys matching pattern with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    return await client.keys(pattern)
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis KEYS failed after 3 attempts: {e}")
                    return []
                await asyncio.sleep(1)
        return []
    
    async def hset_with_retry(self, key: str, field: str, value: Any) -> bool:
        """Hash set with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    await client.hset(key, field, value)
                    return True
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis HSET failed after 3 attempts: {e}")
                    return False
                await asyncio.sleep(1)
        return False
    
    async def hget_with_retry(self, key: str, field: str) -> Optional[Any]:
        """Hash get with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    return await client.hget(key, field)
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis HGET failed after 3 attempts: {e}")
                    return None
                await asyncio.sleep(1)
        return None
    
    async def hgetall_with_retry(self, key: str) -> dict:
        """Hash get all with retry logic"""
        for attempt in range(3):
            try:
                async with self.get_connection() as client:
                    return await client.hgetall(key)
            except Exception as e:
                if attempt == 2:
                    logger.error(f"❌ Redis HGETALL failed after 3 attempts: {e}")
                    return {}
                await asyncio.sleep(1)
        return {}

# Global instance
redis_manager = ProductionRedisManager() 