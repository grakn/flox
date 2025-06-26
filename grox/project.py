from typing import Dict, Any
from types import SimpleNamespace
from langfabric import ModelManager
from .config import GroxAppConfig, GroxProjectConfig
from .factory import build_checkpoint_saver

class GroxProject:

    def __init__(self, tenant_id:str, app: GroxAppConfig, config: GroxProjectConfig):
        self.tenant_id = tenant_id
        self.project_code = config.metadata.project
        self.app = app
        self.debug = app.log_level == "DEBUG"
        self.config = config
        self.model_manager = ModelManager(config.infrastructure.model_configs)
        self.defaults = SimpleNamespace(**config.infrastructure.defaults)

        self.checkpoint_saver = None

        backend_configs = config.infrastructure.backend_configs or {}
        checkpoint_cfg = backend_configs.get("checkpoint_saver")

        if checkpoint_cfg:
            self.checkpoint_saver = build_checkpoint_saver(self.tenant_id, self.project_code, checkpoint_cfg)
