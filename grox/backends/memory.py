from langgraph.checkpoint.memory import MemorySaver
from .common import PickleCheckpointSerializer


class InMemoryCheckpointSaver(MemorySaver):
    """
    An in-memory checkpoint saver that uses PickleCheckpointSerializer
    for checkpoint serialization.
    Suitable for local development and testing.

    Namespacing is based on both tenant_id and project_code to support multi-tenancy.
    """

    def __init__(self, tenant_id: str, project_code: str):
        serializer = PickleCheckpointSerializer()
        namespace = f"{tenant_id}:{project_code}"
        super().__init__(serializer=serializer, namespace=namespace)
