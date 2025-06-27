import uuid
import pytest
from grox.factory_cache import create_memory_saver, create_redis_saver
from graph_builder import build_graph

@pytest.mark.parametrize("checkpointer_factory", [
    lambda: create_memory_saver(),
    #lambda: create_redis_saver(redis_url="redis://localhost:6379/0", ttl=600)
])
def test_checkpoint_saver_behavior(checkpointer_factory):
    checkpointer = checkpointer_factory()

    graph = build_graph(checkpointer)

    config = {"configurable": {"thread_id": "1"}}
    input_data = {"foo": ""}

    result1 = graph.invoke(input_data, config)
    result2 = graph.invoke(input_data, config)

    assert result1 == result2
