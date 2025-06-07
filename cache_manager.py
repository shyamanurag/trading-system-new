"""
Multi-Layer Cache Manager
Implements Redis + In-Memory caching strategy for optimal performance
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List, Callable
from dataclasses import dataclass, asdict
import hashlib
import redis.asyncio as redis
from collections import OrderedDict
import threading
import weakref

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    # Redis settings
    redis_enabled: bool = True
    redis_default_ttl: int = 3600  # 1 hour
    redis_prefix: str = "trading_cache:"
    
    # In-memory cache settings
    memory_cache_enabled: bool = True
    memory_cache_size: int = 10000  # Max items
    memory_default_ttl: int = 300  # 5 minutes
    
    # Performance settings
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    hit_ratio_tracking: bool = True
    
    # Cache warming settings
    auto_warm_enabled: bool = True
    warm_up_keys: List[str] = None
    
    def __post_init__(self):
        if self.warm_up_keys is None:
            self.warm_up_keys = [
                'market_data:*',
                'user_positions:*',
                'elite_recommendations',
                'system_stats'
            ]

@dataclass
class CacheStats:
    """Cache performance statistics"""
    redis_hits: int = 0
    redis_misses: int = 0
    memory_hits: int = 0
    memory_misses: int = 0
    total_operations: int = 0
    avg_response_time: float = 0.0
    cache_size_bytes: int = 0
    evictions: int = 0
    last_reset: datetime = None
    
    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.now()
    
    @property
    def redis_hit_ratio(self) -> float:
        total_redis = self.redis_hits + self.redis_misses
        return (self.redis_hits / total_redis * 100) if total_redis > 0 else 0.0
    
    @property
    def memory_hit_ratio(self) -> float:
        total_memory = self.memory_hits + self.memory_misses
        return (self.memory_hits / total_memory * 100) if total_memory > 0 else 0.0
    
    @property
    def overall_hit_ratio(self) -> float:
        total_hits = self.redis_hits + self.memory_hits
        return (total_hits / self.total_operations * 100) if self.total_operations > 0 else 0.0

class InMemoryCache:
    """Thread-safe in-memory LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.ttl_data: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.stats = {'hits': 0, 'misses': 0, 'evictions': 0}
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.ttl_data:
            return False
        return time.time() > self.ttl_data[key]
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.ttl_data.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            self._remove_key(key)
    
    def _remove_key(self, key: str):
        """Remove key from cache and TTL data"""
        self.cache.pop(key, None)
        self.ttl_data.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            self._cleanup_expired()
            
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.stats['hits'] += 1
                return value
            else:
                self.stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL"""
        with self.lock:
            self._cleanup_expired()
            
            # Remove if exists
            if key in self.cache:
                self._remove_key(key)
            
            # Add new entry
            self.cache[key] = value
            if ttl:
                self.ttl_data[key] = time.time() + ttl
            
            # Evict if over size limit
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self._remove_key(oldest_key)
                self.stats['evictions'] += 1
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.ttl_data.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            self._cleanup_expired()
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_ops = self.stats['hits'] + self.stats['misses']
            hit_ratio = (self.stats['hits'] / total_ops * 100) if total_ops > 0 else 0.0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'hit_ratio': round(hit_ratio, 2)
            }

class CacheManager:
    """Multi-layer cache manager with Redis and in-memory caching"""
    
    def __init__(self, redis_client: redis.Redis, config: CacheConfig):
        self.redis_client = redis_client
        self.config = config
        self.memory_cache = InMemoryCache(config.memory_cache_size) if config.memory_cache_enabled else None
        self.stats = CacheStats()
        self.response_times = []
        
        # Cache invalidation callbacks
        self.invalidation_callbacks: Dict[str, List[Callable]] = {}
        
        # Compression support
        self._compression_enabled = config.enable_compression
        if self._compression_enabled:
            try:
                import gzip
                self._compress = gzip.compress
                self._decompress = gzip.decompress
            except ImportError:
                logger.warning("gzip not available, compression disabled")
                self._compression_enabled = False
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            json_str = json.dumps(value, default=str)
            data = json_str.encode('utf-8')
            
            # Compress if enabled and data is large enough
            if (self._compression_enabled and 
                len(data) > self.config.compression_threshold):
                data = self._compress(data)
                # Add compression marker
                data = b'GZIP:' + data
            
            return data
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Check for compression marker
            if data.startswith(b'GZIP:'):
                data = self._decompress(data[5:])
            
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    def _generate_key(self, key: str) -> str:
        """Generate prefixed cache key"""
        return f"{self.config.redis_prefix}{key}"
    
    def _track_operation(self, operation_time: float):
        """Track operation performance"""
        self.response_times.append(operation_time)
        self.stats.total_operations += 1
        
        # Keep only last 1000 operations for average calculation
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        # Update average response time
        if self.response_times:
            self.stats.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (multi-layer)"""
        start_time = time.time()
        
        try:
            # Try memory cache first
            if self.memory_cache:
                value = self.memory_cache.get(key)
                if value is not None:
                    self.stats.memory_hits += 1
                    self._track_operation(time.time() - start_time)
                    return value
                else:
                    self.stats.memory_misses += 1
            
            # Try Redis cache
            if self.config.redis_enabled and self.redis_client:
                redis_key = self._generate_key(key)
                data = await self.redis_client.get(redis_key)
                
                if data:
                    value = self._deserialize_value(data)
                    self.stats.redis_hits += 1
                    
                    # Store in memory cache for faster access
                    if self.memory_cache:
                        self.memory_cache.set(key, value, self.config.memory_default_ttl)
                    
                    self._track_operation(time.time() - start_time)
                    return value
                else:
                    self.stats.redis_misses += 1
            
            self._track_operation(time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._track_operation(time.time() - start_time)
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (multi-layer)"""
        start_time = time.time()
        
        try:
            # Use default TTL if not specified
            redis_ttl = ttl or self.config.redis_default_ttl
            memory_ttl = min(ttl or self.config.memory_default_ttl, self.config.memory_default_ttl)
            
            # Store in memory cache
            if self.memory_cache:
                self.memory_cache.set(key, value, memory_ttl)
            
            # Store in Redis cache
            if self.config.redis_enabled and self.redis_client:
                redis_key = self._generate_key(key)
                data = self._serialize_value(value)
                await self.redis_client.setex(redis_key, redis_ttl, data)
            
            self._track_operation(time.time() - start_time)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._track_operation(time.time() - start_time)
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache (multi-layer)"""
        start_time = time.time()
        
        try:
            # Delete from memory cache
            memory_deleted = False
            if self.memory_cache:
                memory_deleted = self.memory_cache.delete(key)
            
            # Delete from Redis cache
            redis_deleted = False
            if self.config.redis_enabled and self.redis_client:
                redis_key = self._generate_key(key)
                result = await self.redis_client.delete(redis_key)
                redis_deleted = result > 0
            
            # Call invalidation callbacks
            if key in self.invalidation_callbacks:
                for callback in self.invalidation_callbacks[key]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(key)
                        else:
                            callback(key)
                    except Exception as e:
                        logger.error(f"Invalidation callback error: {e}")
            
            self._track_operation(time.time() - start_time)
            return memory_deleted or redis_deleted
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._track_operation(time.time() - start_time)
            return False
    
    async def get_or_set(self, key: str, factory: Callable, ttl: Optional[int] = None) -> Any:
        """Get value from cache or set it using factory function"""
        # Try to get from cache first
        value = await self.get(key)
        if value is not None:
            return value
        
        # Generate value using factory
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            # Store in cache
            await self.set(key, value, ttl)
            return value
            
        except Exception as e:
            logger.error(f"Factory function error for key {key}: {e}")
            raise
    
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        result = {}
        
        # Check memory cache first
        memory_keys = []
        if self.memory_cache:
            for key in keys:
                value = self.memory_cache.get(key)
                if value is not None:
                    result[key] = value
                    self.stats.memory_hits += 1
                else:
                    memory_keys.append(key)
                    self.stats.memory_misses += 1
        else:
            memory_keys = keys
        
        # Check Redis for remaining keys
        if memory_keys and self.config.redis_enabled and self.redis_client:
            redis_keys = [self._generate_key(key) for key in memory_keys]
            redis_values = await self.redis_client.mget(redis_keys)
            
            for i, (key, data) in enumerate(zip(memory_keys, redis_values)):
                if data:
                    try:
                        value = self._deserialize_value(data)
                        result[key] = value
                        self.stats.redis_hits += 1
                        
                        # Store in memory cache
                        if self.memory_cache:
                            self.memory_cache.set(key, value, self.config.memory_default_ttl)
                    except Exception as e:
                        logger.error(f"Error deserializing key {key}: {e}")
                        self.stats.redis_misses += 1
                else:
                    self.stats.redis_misses += 1
        
        return result
    
    async def mset(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        try:
            # Set in memory cache
            if self.memory_cache:
                memory_ttl = min(ttl or self.config.memory_default_ttl, self.config.memory_default_ttl)
                for key, value in data.items():
                    self.memory_cache.set(key, value, memory_ttl)
            
            # Set in Redis cache
            if self.config.redis_enabled and self.redis_client:
                redis_ttl = ttl or self.config.redis_default_ttl
                redis_data = {}
                
                for key, value in data.items():
                    redis_key = self._generate_key(key)
                    serialized_value = self._serialize_value(value)
                    redis_data[redis_key] = serialized_value
                
                # Use pipeline for batch operations
                pipe = self.redis_client.pipeline()
                await pipe.mset(redis_data)
                
                # Set TTL for each key
                for redis_key in redis_data.keys():
                    await pipe.expire(redis_key, redis_ttl)
                
                await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            deleted_count = 0
            
            # Clear from Redis
            if self.config.redis_enabled and self.redis_client:
                redis_pattern = self._generate_key(pattern)
                keys = await self.redis_client.keys(redis_pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
            
            # Clear from memory cache (simple pattern matching)
            if self.memory_cache:
                # Convert Redis pattern to simple string matching
                simple_pattern = pattern.replace('*', '')
                keys_to_delete = [
                    key for key in self.memory_cache.cache.keys()
                    if simple_pattern in key
                ]
                for key in keys_to_delete:
                    self.memory_cache.delete(key)
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0
    
    def register_invalidation_callback(self, key_pattern: str, callback: Callable):
        """Register callback for cache invalidation"""
        if key_pattern not in self.invalidation_callbacks:
            self.invalidation_callbacks[key_pattern] = []
        self.invalidation_callbacks[key_pattern].append(callback)
    
    async def warm_up_cache(self, warm_up_data: Dict[str, Callable]):
        """Warm up cache with commonly accessed data"""
        if not self.config.auto_warm_enabled:
            return
        
        logger.info("Starting cache warm-up...")
        
        try:
            for key, factory in warm_up_data.items():
                try:
                    if asyncio.iscoroutinefunction(factory):
                        value = await factory()
                    else:
                        value = factory()
                    
                    await self.set(key, value)
                    logger.debug(f"Warmed up cache key: {key}")
                    
                except Exception as e:
                    logger.error(f"Error warming up key {key}: {e}")
            
            logger.info("Cache warm-up completed")
            
        except Exception as e:
            logger.error(f"Cache warm-up failed: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        redis_info = {}
        if self.config.redis_enabled and self.redis_client:
            try:
                redis_info = await self.redis_client.info('memory')
                redis_info = {
                    'used_memory': redis_info.get('used_memory', 0),
                    'used_memory_human': redis_info.get('used_memory_human', '0B'),
                    'connected_clients': redis_info.get('connected_clients', 0)
                }
            except Exception:
                redis_info = {'status': 'unavailable'}
        
        memory_stats = {}
        if self.memory_cache:
            memory_stats = self.memory_cache.get_stats()
        
        return {
            'redis': {
                'enabled': self.config.redis_enabled,
                'hits': self.stats.redis_hits,
                'misses': self.stats.redis_misses,
                'hit_ratio': round(self.stats.redis_hit_ratio, 2),
                'info': redis_info
            },
            'memory': {
                'enabled': self.config.memory_cache_enabled,
                'hits': self.stats.memory_hits,
                'misses': self.stats.memory_misses,
                'hit_ratio': round(self.stats.memory_hit_ratio, 2),
                'stats': memory_stats
            },
            'overall': {
                'total_operations': self.stats.total_operations,
                'hit_ratio': round(self.stats.overall_hit_ratio, 2),
                'avg_response_time_ms': round(self.stats.avg_response_time * 1000, 2),
                'uptime_hours': (datetime.now() - self.stats.last_reset).total_seconds() / 3600
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        health_status = {'status': 'healthy', 'components': {}}
        
        # Test memory cache
        if self.memory_cache:
            try:
                test_key = f"health_check_{time.time()}"
                self.memory_cache.set(test_key, "test_value", 60)
                value = self.memory_cache.get(test_key)
                self.memory_cache.delete(test_key)
                
                health_status['components']['memory_cache'] = {
                    'status': 'healthy' if value == "test_value" else 'unhealthy',
                    'size': self.memory_cache.size(),
                    'max_size': self.memory_cache.max_size
                }
            except Exception as e:
                health_status['components']['memory_cache'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'degraded'
        
        # Test Redis cache
        if self.config.redis_enabled and self.redis_client:
            try:
                test_key = f"health_check_{time.time()}"
                await self.redis_client.setex(test_key, 60, "test_value")
                value = await self.redis_client.get(test_key)
                await self.redis_client.delete(test_key)
                
                health_status['components']['redis_cache'] = {
                    'status': 'healthy' if value == b"test_value" else 'unhealthy',
                    'connected': True
                }
            except Exception as e:
                health_status['components']['redis_cache'] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'connected': False
                }
                health_status['status'] = 'degraded'
        
        return health_status
    
    async def optimize_performance(self):
        """Run performance optimization tasks"""
        try:
            # Clean up expired memory cache entries
            if self.memory_cache:
                self.memory_cache._cleanup_expired()
            
            # Reset statistics if they're getting too large
            if self.stats.total_operations > 1000000:
                self.stats = CacheStats()
                self.response_times = []
                logger.info("Cache statistics reset")
            
            logger.info("Cache performance optimization completed")
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")

# Global cache manager instance
cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    return cache_manager

def init_cache_manager(redis_client: redis.Redis, config: Optional[CacheConfig] = None) -> CacheManager:
    """Initialize the global cache manager"""
    global cache_manager
    
    if config is None:
        config = CacheConfig()
    
    cache_manager = CacheManager(redis_client, config)
    logger.info("✅ Cache manager initialized successfully")
    return cache_manager

# Decorator for caching function results
def cached(key_pattern: str, ttl: Optional[int] = None):
    """Decorator to cache function results"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            if not cache_manager:
                return await func(*args, **kwargs)
            
            # Generate cache key
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = f"{key_pattern}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Try to get from cache
            result = await cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache operations
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator 