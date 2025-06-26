import re
from typing import Optional
from .config import BackendConfig

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
        from .backends.redis import RedisCheckpointSaver
        return RedisCheckpointSaver(
            tenant_id=tenant_id,
            project_code=project_code,
            redis_url=config.url.get_secret_value(),
            ttl=ttl_seconds
        )

    elif config.backend == "memory":
        from .backends.memory import InMemoryCheckpointSaver
        return InMemoryCheckpointSaver(tenant_id=tenant_id, project_code=project_code)

    else:
        raise ValueError(f"Unsupported backend for checkpoint saver: '{config.backend}'")
