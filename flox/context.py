import contextvars
from typing import Optional
import threading
import structlog
from .config import FloxConfig
from .projects import Project


class Context:
    """
    Per-request container holding the active Project plus
    request identifiers and infrastructure references
    """

    def __init__(self, project: Project, correlation_id: str, user_id: Optional[str] = None):
        self.project = project
        self.correlation_id = correlation_id
        self.user_id = user_id
        self.logger = structlog.get_logger().bind(
            correlation_id=correlation_id,
            tenant_id=project.tenant_id,
            project_code=project.project_code,
            user_id=user_id,
        )


class FloxContext:
    _instance = None
    _instance_lock = threading.Lock()
    _context_var = contextvars.ContextVar("flox_current_context")

    def __new__(cls, config: FloxConfig=None):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._projects = {}
                    cls._instance._projects_lock = threading.Lock()
                    cls._instance.config = config
        return cls._instance

    def register_project(self, project: Project):
        key = (project.tenant_id, project.project_code)
        with self._projects_lock:
            self._projects[key] = project

    def unregister_project(self, tenant_id: str, project_code: str):
        key = (tenant_id, project_code)
        with self._projects_lock:
            self._projects.pop(key, None)

    def get_project(self, tenant_id: str, project_code: str) -> Optional[Project]:
        key = (tenant_id, project_code)
        with self._projects_lock:
            return self._projects.get(key)

    def create_request_context(
        self,
        tenant_id: str,
        project_code: str,
        correlation_id: str,
        user_id: Optional[str] = None,
    ) -> Context:
        project = self.get_project(tenant_id, project_code)
        if project is None:
            raise RuntimeError(f"Project not found: {tenant_id}/{project_code}")
        ctx = Context(project, correlation_id, user_id)
        self._context_var.set(ctx)
        return ctx

    @staticmethod
    def get_current_context() -> Optional[Context]:
        try:
            return FloxContext._context_var.get()
        except LookupError:
            return None
