from typing import Optional, TypedDict
import structlog

from langgraph.graph import StateGraph, START, END
from operator import add

from .context import GroxExecutionContext

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

    def _make_thread_id(self, session_id: str) -> str:
        return f"{self.context.tenant_id}{THREAD_ID_SEPARATOR}{self.context.project_code}{THREAD_ID_SEPARATOR}{session_id}"

    async def handle_event(self, data: dict):
        # Invoke the graph with a thread_id
        self.logger.info("event_received", data=data)
        config = {"configurable": {"thread_id": self._make_thread_id(data["session_id"])}}
        result = await self.context.graph.ainvoke({"foo": ""}, config)
        await self._process(result)

    async def _process(self, data: dict):
        self.logger.debug("processing_data", data=data)
        prompt = data.get("prompt", "What is the weather today?")
        docs = self.context.document_store.as_retrieval("weather").similarity_search_with_score(prompt)
        self.logger.info("retrieved docs", documents=[doc.page_content for doc in docs])

        # Your async processing here
