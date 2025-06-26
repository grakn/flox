import pickle
from typing import Protocol, cast

from langgraph.checkpoint.base import Checkpoint


class CheckpointSerializer(Protocol):
    """A serializer interface for serializing and deserializing Checkpoints."""

    def dumps(self, obj: Checkpoint) -> bytes:
        ...

    def loads(self, data: bytes) -> Checkpoint:
        ...


class PickleCheckpointSerializer:
    """Serialize and deserialize Checkpoints using the pickle module.

    *Security Warning*: Only use with trusted data.
    """

    def dumps(self, obj: Checkpoint) -> bytes:
        return pickle.dumps(obj)

    def loads(self, data: bytes) -> Checkpoint:
        return cast(Checkpoint, pickle.loads(data))
