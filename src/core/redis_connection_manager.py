"""
Redis Connection Manager for Production Environment
Handles DigitalOcean managed Redis with SSL, connection pooling, and retry logic
"""

import os
import asyncio
import logging
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
            # Create connection pool with production settings
            pool_config = {
                'host': self.redis_host,
                'port': self.redis_port,
                'password': self.redis_password,
                'db': self.redis_db,
                'decode_responses': True,
                'socket_timeout': 10,
                'socket_connect_timeout': 10,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
                'max_connections': 10,
                'retry_on_timeout': True
            }
            
            # Add error handling for different Redis versions
            try:
                pool_config['retry_on_error'] = [
                    redis.ConnectionError,
                    redis.TimeoutError,
                    redis.BusyLoadingError
                ]
            except AttributeError:
                # Fallback for older Redis versions
                pass
            
            # Add SSL configuration for DigitalOcean
            if self.ssl_required:
                pool_config.update({
                    'ssl': True,
                    'ssl_cert_reqs': None,
                    'ssl_check_hostname': False,
                    'ssl_ca_certs': None
                })
            
            self.connection_pool = redis.ConnectionPool(**pool_config)
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
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
    
    async def ping(self) -> bool:
        """Ping Redis to test connection"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Redis ping failed: {e}")
            return False
    
    async def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client with connection validation"""
        if not self.is_connected or not self.redis_client:
            logger.warning("⚠️ Redis not connected, attempting to reconnect...")
            success = await self.initialize()
            if not success:
                return None
        
        return self.redis_client if self.is_connected else None
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for Redis operations with automatic cleanup"""
        client = await self.get_client()
        if not client:
            yield None
            return
        
        try:
            yield client
        except Exception as e:
            # Handle connection errors generically
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                logger.error(f"❌ Redis connection error: {e}")
                self.is_connected = False
            else:
                logger.error(f"❌ Redis operation error: {e}")
            yield None
    
    async def safe_get(self, key: str, default=None) -> Any:
        """Safely get value from Redis with error handling"""
        try:
            async with self.get_connection() as client:
                if client:
                    result = await client.get(key)
                    return result if result is not None else default
                return default
        except Exception as e:
            logger.error(f"❌ Redis GET failed for key '{key}': {e}")
            return default
    
    async def safe_set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Safely set value in Redis with error handling"""
        try:
            async with self.get_connection() as client:
                if client:
                    await client.set(key, value, ex=ex)
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Redis SET failed for key '{key}': {e}")
            return False
    
    async def safe_keys(self, pattern: str) -> list:
        """Safely get keys matching pattern with error handling"""
        try:
            async with self.get_connection() as client:
                if client:
                    keys = await client.keys(pattern)
                    return [key.decode() if isinstance(key, bytes) else key for key in keys]
                return []
        except Exception as e:
            logger.error(f"❌ Redis KEYS failed for pattern '{pattern}': {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive Redis health check"""
        try:
            async with self.get_connection() as client:
                if not client:
                    return {
                        'status': 'disconnected',
                        'connected': False,
                        'error': 'No Redis connection available'
                    }
                
                # Test basic operations
                await client.ping()
                info = await client.info()
                
                return {
                    'status': 'connected',
                    'connected': True,
                    'host': self.redis_host,
                    'port': self.redis_port,
                    'ssl_enabled': self.ssl_required,
                    'memory_usage': info.get('used_memory_human', 'unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                    'retry_count': self.retry_count
                }
        except Exception as e:
            return {
                'status': 'error',
                'connected': False,
                'error': str(e),
                'retry_count': self.retry_count
            }
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        self.is_connected = False
        logger.info("Redis connection closed")

# Global instance
redis_manager = ProductionRedisManager()

async def get_redis_manager() -> ProductionRedisManager:
    """Get the global Redis manager instance"""
    return redis_manager 