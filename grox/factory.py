import re
from typing import Optional
from .config import BackendConfig
from .backends.memory import *
from .backends.redis_factory import *
from .backends.redis import *

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


def build_checkpoint_saver(tenant_id:str, project_code: str, config: BackendConfig):
    ttl_seconds = parse_ttl(config.ttl)

    if config.backend == "redis":
        if config.sync:
            redis_client = create_redis_instance(config.url.get_secret_value())
            return RedisCheckpointSaver(
                tenant_id=tenant_id,
                project_code=project_code,
                redis_client=redis_client,
                ttl=ttl_seconds
            )
        else:
            redis_client = create_async_redis_instance(config.url.get_secret_value())
            return AsyncRedisCheckpointSaver(
                tenant_id=tenant_id,
                project_code=project_code,
                redis_client=redis_client,
                ttl=ttl_seconds
            )

    elif config.backend == "memory":
        return InMemoryCheckpointSaver(tenant_id=tenant_id, project_code=project_code)

    else:
        raise ValueError(f"Unsupported backend for checkpoint saver: '{config.backend}'")
