from typing import Optional, TypedDict
import structlog

from langgraph.graph import StateGraph, START, END
from operator import add

from .context import GroxExecutionContext

# Define the state of your graph
class GroxState(TypedDict):
    foo: str
    bar: list[str]

# Define your nodes
def node_a(state: GroxState) -> GroxState:
    return {"foo": "a", "bar": ["a"]}

def node_b(state: GroxState) -> GroxState:
    return {"foo": "b", "bar": ["b"]}

THREAD_ID_SEPARATOR: str = ":"

class Grox:
    """
    Per-request action class holding the active flows and executions
    """

    def __init__(
        self,
        context: GroxExecutionContext
    ):
        self.context = context
        self.logger = context.logger

        # Build the graph
        self.workflow = StateGraph(GroxState)
        self.workflow.add_node("node_a", node_a)
        self.workflow.add_node("node_b", node_b)
        self.workflow.add_edge(START, "node_a")
        self.workflow.add_edge("node_a", "node_b")
        self.workflow.add_edge("node_b", END)

        # Compile the graph with the checkpointer
        self.graph = self.workflow.compile(checkpointer=context.checkpoint_saver)

    def _make_thread_id(self, session_id: str) -> str:
        return f"{self.context.tenant_id}{THREAD_ID_SEPARATOR}{self.context.project_code}{THREAD_ID_SEPARATOR}{session_id}"

    async def handle_event(self, data: dict):
        # Invoke the graph with a thread_id
        self.logger.info("event_received", data=data)
        config = {"configurable": {"thread_id": self._make_thread_id(data["session_id"])}}
        result = await self.graph.ainvoke({"foo": ""}, config)
        await self._process(result)

    async def _process(self, data: dict):
        self.logger.debug("processing_data", data=data)
        # Your async processing here
