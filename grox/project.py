from typing import Dict, Any
from .config import GroxAppConfig, GroxProjectConfig
from langfabric import ModelManager
from types import SimpleNamespace

class GroxProject:

    def __init__(self, tenant_id:str, app: GroxAppConfig, config: GroxProjectConfig):
        self.tenant_id = tenant_id
        self.project_code = config.metadata.project
        self.app = app
        self.debug = app.log_level == "DEBUG"
        self.config = config
        self.model_manager = ModelManager(config.infrastructure.model_configs)
        self.defaults = SimpleNamespace(**config.infrastructure.defaults)
