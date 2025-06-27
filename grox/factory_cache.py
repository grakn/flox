from typing import Any, Dict, Optional
from functools import lru_cache
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver

from langchain_core.chat_history import InMemoryChatMessageHistory
import threading

class ChatHistoryMemoryManager:
    def __init__(self):
        self._memory_lock = threading.Lock()
        self._memory_buckets = {}

    def get_intance(self, session_id: str) -> InMemoryChatMessageHistory:
        with self._memory_lock:
            if session_id not in self._memory_buckets:
                self._memory_buckets[session_id] = InMemoryChatMessageHistory()
            return self._memory_buckets[session_id]

@lru_cache(maxsize=None)
def create_chat_history_memory_manager(thread_id: str, project_code: str) -> ChatHistoryMemoryManager:
    return ChatHistoryMemoryManager()

@lru_cache(maxsize=None)
def create_memory_saver() -> MemorySaver:
    return MemorySaver()

@lru_cache(maxsize=None)
def create_redis_saver(redis_url: str, ttl: Optional[int] = None) -> RedisSaver:
    redis_client = create_redis_instance(redis_url)
    saver = RedisSaver(
        redis_client=redis_client,
        ttl={"default_ttl": ttl},
    )
    saver.setup()
    return saver

@lru_cache(maxsize=None)
def create_async_redis_saver(redis_url: str, ttl: Optional[int] = None) -> RedisSaver:
    redis_client = create_async_redis_instance(redis_url)
    saver = AsyncRedisSaver(
        redis_client=redis_client,
        ttl={"default_ttl": ttl},
    )
    asyncio.gather(
        saver.checkpoints_index.create(overwrite=False),
        saver.checkpoint_blobs_index.create(overwrite=False),
        saver.checkpoint_writes_index.create(overwrite=False),
    )
    return saver

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
