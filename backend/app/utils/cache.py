"""
Caching utilities for performance optimization
"""

import hashlib
import json
import pickle
import time
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
import redis
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management with Redis and in-memory fallback"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, default_ttl: int = 3600):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, Dict] = {}
        self.memory_cache_stats = {"hits": 0, "misses": 0, "sets": 0}
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        return pickle.loads(cached_data)
                except Exception as e:
                    logger.warning(f"Redis get error: {e}")
            
            # Fallback to memory cache
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if entry["expires_at"] > time.time():
                    self.memory_cache_stats["hits"] += 1
                    return entry["value"]
                else:
                    # Expired entry
                    del self.memory_cache[key]
            
            self.memory_cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    serialized_value = pickle.dumps(value)
                    self.redis_client.setex(key, ttl, serialized_value)
                    return True
                except Exception as e:
                    logger.warning(f"Redis set error: {e}")
            
            # Fallback to memory cache
            self.memory_cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
            self.memory_cache_stats["sets"] += 1
            
            # Cleanup old entries periodically
            if len(self.memory_cache) % 100 == 0:
                self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            # Delete from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete error: {e}")
            
            # Delete from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching a pattern"""
        count = 0
        
        try:
            # Clear from Redis
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        count += self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis pattern clear error: {e}")
            
            # Clear from memory cache
            keys_to_delete = [key for key in self.memory_cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.memory_cache[key]
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache pattern clear error for pattern {pattern}: {e}")
            return 0
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        current_time = time.time()
        keys_to_delete = [
            key for key, entry in self.memory_cache.items()
            if entry["expires_at"] <= current_time
        ]
        
        for key in keys_to_delete:
            del self.memory_cache[key]
        
        if keys_to_delete:
            logger.debug(f"Cleaned up {len(keys_to_delete)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        redis_stats = {}
        if self.redis_client:
            try:
                info = self.redis_client.info()
                redis_stats = {
                    "redis_used_memory": info.get("used_memory_human", "N/A"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_hits": info.get("keyspace_hits", 0),
                    "redis_misses": info.get("keyspace_misses", 0)
                }
            except Exception:
                redis_stats = {"redis_error": "Unable to get Redis stats"}
        
        return {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_stats": self.memory_cache_stats,
            "redis_stats": redis_stats,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global cache manager instance
cache_manager: Optional[CacheManager] = None


def initialize_cache(redis_client: Optional[redis.Redis] = None, default_ttl: int = 3600):
    """Initialize the global cache manager"""
    global cache_manager
    cache_manager = CacheManager(redis_client, default_ttl)
    logger.info("Cache manager initialized")


def cached(
    prefix: str = "default",
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_manager:
                # Cache not available, execute function directly
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        # Add cache management methods to the function
        wrapper.cache_clear = lambda: cache_manager.clear_pattern(f"{prefix}:*") if cache_manager else None
        wrapper.cache_key = lambda *args, **kwargs: cache_manager._generate_key(prefix, *args, **kwargs) if cache_manager else None
        
        return wrapper
    return decorator


class CacheWarmer:
    """Utility for warming up cache with commonly accessed data"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.warmup_tasks = []
    
    def register_warmup_task(self, func: Callable, *args, **kwargs):
        """Register a function to be called during cache warmup"""
        self.warmup_tasks.append((func, args, kwargs))
    
    async def warmup(self):
        """Execute all registered warmup tasks"""
        logger.info(f"Starting cache warmup with {len(self.warmup_tasks)} tasks")
        
        for func, args, kwargs in self.warmup_tasks:
            try:
                await func(*args, **kwargs)
                logger.debug(f"Completed warmup task: {func.__name__}")
            except Exception as e:
                logger.error(f"Warmup task failed {func.__name__}: {e}")
        
        logger.info("Cache warmup completed")


# Utility functions for common caching patterns
async def cache_api_response(
    endpoint: str,
    params: Dict[str, Any],
    response_data: Any,
    ttl: int = 300  # 5 minutes default for API responses
):
    """Cache API response data"""
    if cache_manager:
        key = f"api_response:{endpoint}:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        await cache_manager.set(key, response_data, ttl)


async def get_cached_api_response(endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
    """Get cached API response data"""
    if cache_manager:
        key = f"api_response:{endpoint}:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        return await cache_manager.get(key)
    return None


async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user"""
    if cache_manager:
        pattern = f"*user:{user_id}*"
        count = await cache_manager.clear_pattern(pattern)
        logger.info(f"Invalidated {count} cache entries for user {user_id}")


async def cache_computation_result(
    computation_id: str,
    result: Any,
    ttl: int = 3600  # 1 hour default for computation results
):
    """Cache expensive computation results"""
    if cache_manager:
        key = f"computation:{computation_id}"
        await cache_manager.set(key, result, ttl)


# Performance monitoring for cached functions
class CacheMetrics:
    """Track cache performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time_saved": 0.0,
            "functions": {}
        }
    
    def record_hit(self, func_name: str, time_saved: float = 0.0):
        """Record a cache hit"""
        self.metrics["total_calls"] += 1
        self.metrics["cache_hits"] += 1
        self.metrics["total_time_saved"] += time_saved
        
        if func_name not in self.metrics["functions"]:
            self.metrics["functions"][func_name] = {"hits": 0, "misses": 0}
        self.metrics["functions"][func_name]["hits"] += 1
    
    def record_miss(self, func_name: str):
        """Record a cache miss"""
        self.metrics["total_calls"] += 1
        self.metrics["cache_misses"] += 1
        
        if func_name not in self.metrics["functions"]:
            self.metrics["functions"][func_name] = {"hits": 0, "misses": 0}
        self.metrics["functions"][func_name]["misses"] += 1
    
    def get_hit_rate(self) -> float:
        """Get overall cache hit rate"""
        if self.metrics["total_calls"] == 0:
            return 0.0
        return self.metrics["cache_hits"] / self.metrics["total_calls"]
    
    def get_function_hit_rate(self, func_name: str) -> float:
        """Get hit rate for a specific function"""
        if func_name not in self.metrics["functions"]:
            return 0.0
        
        func_metrics = self.metrics["functions"][func_name]
        total = func_metrics["hits"] + func_metrics["misses"]
        
        if total == 0:
            return 0.0
        return func_metrics["hits"] / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            **self.metrics,
            "hit_rate": self.get_hit_rate(),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global metrics instance
cache_metrics = CacheMetrics()
