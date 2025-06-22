from typing import Optional
import structlog
from .context import Context

class Flox:
    def __init__(
        self,
        context: Context,
        correlation_id: str,
        user_id: Optional[str] = None,
    ):
        self.context = context
        self.correlation_id = correlation_id
        self.user_id = user_id
        self.logger = structlog.get_logger().bind(
            correlation_id=correlation_id,
            tenant_id=context.project.tenant_id,
            project_code=context.project.project_code,
            user_id=user_id,
        )

    async def handle_event(self, data: dict):
        self.logger.info("event_received", event=data)
        await self._process(data)

    async def _process(self, data: dict):
        self.logger.debug("processing_data", data=data)
        # Your async processing here
