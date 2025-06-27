import re
from typing import Optional
from .config import BackendConfig
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver
from langgraph.checkpoint.memory import MemorySaver
from .factory_cache import *

def parse_ttl(ttl: Optional[str]) -> Optional[int]:
    if not ttl:
        return None
    match = re.fullmatch(r"(\d+)([smhdw])", ttl.strip().lower())
    if not match:
        raise ValueError(f"Invalid TTL format: '{ttl}'")

    value, unit = match.groups()
    value = int(value)
    return {
        "s": value,
        "m": value * 60,
        "h": value * 3600,
        "d": value * 86400,
        "w": value * 604800,
    }[unit]


def build_checkpoint_saver(config: BackendConfig):
    ttl_seconds = parse_ttl(config.ttl)

    if config.backend == "redis":
        if config.sync:
            return create_redis_saver(config.url.get_secret_value(), ttl_seconds)
        else:
            return create_async_redis_saver(config.url.get_secret_value(), ttl_seconds)

    elif config.backend == "memory":
        return create_memory_saver()

    else:
        raise ValueError(f"Unsupported backend for checkpoint saver: '{config.backend}'")


def build_chat_history_factory(tenant_id:str, project_code:str, config: BackendConfig):
    ttl_seconds = parse_ttl(config.ttl)

    if config.backend == "redis":
        redis_client = create_redis_instance(config.url.get_secret_value())
        def _factory(session_id:str):
            chat_history = RedisChatMessageHistory(
                session_id,
                redis_client=redis_client,
                key_prefix=f"chat_history:{tenant_id}:{project_code}",
                ttl=ttl_seconds
            )
            return chat_history
        return _factory

    elif config.backend == "memory":
        return create_chat_history_memory_manager(tenant_id, project_code).get_instance

    else:
        raise ValueError(f"Unsupported backend for checkpoint saver: '{config.backend}'")
