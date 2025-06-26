from typing import Optional
from langgraph.checkpoint.memory import MemorySaver
from .common import PickleCheckpointSerializer

class AsyncRedisCheckpointSaver:

    def __init__(self, tenant_id: str, project_code: str, redis_client, ttl: Optional[int] = None):
        serializer = PickleCheckpointSerializer()
        namespace = f"{tenant_id}:{project_code}"
        super().__init__(serializer=serializer, namespace=namespace)
