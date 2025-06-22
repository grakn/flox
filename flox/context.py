import contextvars
from typing import Optional
from dataclasses import dataclass
import threading
from .config import FloxConfig
from .projects import Project

@dataclass
class Context:
    project: Project

class FloxContext:
    _instance = None
    _instance_lock = threading.Lock()
    _context_var = contextvars.ContextVar("flox_current_context")

    def __new__(cls, config: FloxConfig):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._projects = {}
                cls._instance.config = config
                cls._instance._projects_lock = threading.Lock()
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
        self, tenant_id: str, project_code: str, correlation_id: str, user_id: Optional[str] = None
    ) -> Context:
        project = self.get_project(tenant_id, project_code)
        if not project:
            raise RuntimeError(f"Project not found: tenant={tenant_id}, project={project_code}")
        ctx = Context(project=project)
        self._context_var.set(ctx)
        return ctx

    @staticmethod
    def get_current_context() -> Optional[Context]:
        try:
            return FloxContext._context_var.get()
        except LookupError:
            return None
