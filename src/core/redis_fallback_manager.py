"""
Production Redis Manager with Fallback Support
Handles Redis connection failures gracefully in production
"""

import os
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

class ProductionRedisFallback:
    """Redis manager with in-memory fallback for production resilience"""
    
    def __init__(self):
        self.redis_client = None
        self.is_connected = False
        self.fallback_cache = {}  # In-memory fallback
        self.connection_attempts = 0
        self.max_attempts = 3
        
    def connect(self) -> bool:
        """Attempt to connect to Redis with fallback to in-memory cache"""
        if self.connection_attempts >= self.max_attempts:
            logger.warning("Max Redis connection attempts reached, using fallback mode")
            return True  # Use fallback mode
        
        try:
            import redis
            
            # Try to get Redis configuration from environment
            redis_url = os.getenv('REDIS_URL')
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_password = os.getenv('REDIS_PASSWORD')
            
            if redis_url:
                # Use URL-based connection
                self.redis_client = redis.Redis.from_url(
                    redis_url,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=1,
                    socket_connect_timeout=1
                )
            else:
                # Use host/port connection
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=1,
                    socket_connect_timeout=1
                )
            
            # Test connection
            if self.redis_client is not None:
                self.redis_client.ping()
                self.is_connected = True
                logger.info("Redis connection established")
                return True
            else:
                raise Exception("Redis client not initialized")
            
        except Exception as e:
            self.connection_attempts += 1
            logger.warning(f"Redis connection failed (attempt {self.connection_attempts}): {e}")
            logger.info("Falling back to in-memory cache")
            self.redis_client = None
            self.is_connected = False
            return True  # Still return True to use fallback
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis or fallback cache"""
        try:
            if self.redis_client and self.is_connected:
                result = self.redis_client.get(key)
                return str(result) if result is not None else None
            else:
                # Use fallback cache
                return self.fallback_cache.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed for key {key}: {e}")
            return self.fallback_cache.get(key)
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis or fallback cache"""
        try:
            if self.redis_client and self.is_connected:
                result = self.redis_client.set(key, value, ex=ex)
                # Also store in fallback cache
                self.fallback_cache[key] = value
                return bool(result) if result is not None else True
            else:
                # Use fallback cache
                self.fallback_cache[key] = value
                return True
        except Exception as e:
            logger.warning(f"Redis set failed for key {key}: {e}")
            self.fallback_cache[key] = value
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis or fallback cache"""
        try:
            if self.redis_client and self.is_connected:
                result = self.redis_client.delete(key)
                # Also remove from fallback cache
                self.fallback_cache.pop(key, None)
                return bool(result)
            else:
                # Use fallback cache
                self.fallback_cache.pop(key, None)
                return True
        except Exception as e:
            logger.warning(f"Redis delete failed for key {key}: {e}")
            self.fallback_cache.pop(key, None)
            return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis or fallback cache"""
        try:
            if self.redis_client and self.is_connected:
                return bool(self.redis_client.exists(key))
            else:
                return key in self.fallback_cache
        except Exception as e:
            logger.warning(f"Redis exists failed for key {key}: {e}")
            return key in self.fallback_cache
    
    def get_status(self) -> Dict[str, Any]:
        """Get Redis connection status"""
        return {
            'connected': self.is_connected,
            'fallback_mode': not self.is_connected,
            'fallback_cache_size': len(self.fallback_cache),
            'connection_attempts': self.connection_attempts
        }

# Global instance
redis_fallback_manager = ProductionRedisFallback()

# Convenience functions
def get_redis_client():
    """Get Redis client with fallback support"""
    if not redis_fallback_manager.is_connected:
        redis_fallback_manager.connect()
    return redis_fallback_manager

def get_redis_fallback():
    """Get Redis fallback manager"""
    return redis_fallback_manager