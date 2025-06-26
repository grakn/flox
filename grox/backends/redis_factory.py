from typing import Any, Dict
from functools import lru_cache


@lru_cache(maxsize=None)
def create_redis_instance(url: str, **kwargs: Any) -> "redis.Redis":
    try:
        import redis
    except ImportError:
        raise ImportError("Missing 'redis' package. Install it with `pip install redis`.")

    try:
        return redis.Redis.from_url(url, **kwargs)
    except redis.exceptions.RedisError as error:
        raise ValueError(f"Redis connection error: {error}")


@lru_cache(maxsize=None)
def create_async_redis_instance(url: str, **kwargs: Any) -> "redis.asyncio.Redis":
    try:
        import redis.asyncio as async_redis
    except ImportError:
        raise ImportError("Missing 'redis[asyncio]' package. Install it with `pip install redis`.")

    try:
        return async_redis.from_url(url, **kwargs)
    except async_redis.exceptions.RedisError as error:
        raise ValueError(f"Async Redis connection error: {error}")
