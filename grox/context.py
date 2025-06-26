import contextvars
from typing import Optional
import threading
import structlog
from .config import GroxAppConfig, GroxProjectConfig
from .project import GroxProject
from .logger import setup_logging, register_log_callback

class GroxExecutionContext:
    """
    Per-request container holding the active Project plus
    request identifiers and infrastructure references
    """

    def __init__(self, project: GroxProject,
                input: dict = None,
                correlation_id: Optional[str] = None,
                user_id: Optional[str] = None):
        self.project = project
        if not input:
            input = {}
        self.input = input
        self.correlation_id = correlation_id
        self.user_id = user_id
        self.logger = structlog.get_logger().bind(
            tenant_id=project.tenant_id,
            project_code=project.project_code,
            correlation_id=correlation_id,
            user_id=user_id,
        )


class GroxContext:
    _instance = None
    _instance_lock = threading.Lock()
    _context_var = contextvars.ContextVar("grox_current_context")

    def __new__(cls, app: GroxAppConfig=None):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.__init_singleton__(app)
        return cls._instance

    def __init_singleton__(self, app: GroxAppConfig = None):
        """Initialize singleton only once"""
        if not app:
            app = GroxAppConfig()

        self._projects = {}
        self._projects_lock = threading.Lock()
        self.app = app

        # Automatically setup logging
        setup_logging(app.log_level)
        if app.log_callback:
            register_log_callback(app.log_callback)

    def register_all_projects(self):
        for tenant_id, project_paths in self.app.tenants.items():
            for project_path in project_paths:
                cfg = GroxProjectConfig.load_yaml(project_path)
                project = GroxProject(tenant_id, self.app, cfg)
                self.register_project(project)

    def register_project(self, project: GroxProject):
        key = (project.tenant_id, project.project_code)
        with self._projects_lock:
            self._projects[key] = project

    def unregister_project(self, tenant_id: str, project_code: str):
        key = (tenant_id, project_code)
        with self._projects_lock:
            self._projects.pop(key, None)

    def get_project(self, tenant_id: str, project_code: str) -> Optional[GroxProject]:
        key = (tenant_id, project_code)
        with self._projects_lock:
            return self._projects.get(key)

    def list_projects(self):
        with self._projects_lock:
            return list(self._projects.keys())

    def create_execution_context(
        self,
        tenant_id: str,
        project_code: str,
        input: Optional[dict] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> GroxExecutionContext:
        project = self.get_project(tenant_id, project_code)
        if project is None:
            raise RuntimeError(f"GroxProject not found: {tenant_id}/{project_code}")
        ctx = GroxExecutionContext(project=project, input=input, correlation_id=correlation_id, user_id=user_id)
        self._context_var.set(ctx)
        return ctx

    @staticmethod
    def get_instance() -> "GroxContext":
        with GroxContext._instance_lock:
            if GroxContext._instance is None:
                raise RuntimeError("GroxContext not initialized")
            return GroxContext._instance

    @staticmethod
    def get_current_context() -> Optional[GroxExecutionContext]:
        try:
            return GroxContext._context_var.get()
        except LookupError:
            return None
