from typing import Optional
import structlog
from .context import GroxExecutionContext

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

    async def handle_event(self, data: dict):
        self.logger.info("event_received", data=data)
        await self._process(data)

    async def _process(self, data: dict):
        self.logger.debug("processing_data", data=data)
        # Your async processing here
