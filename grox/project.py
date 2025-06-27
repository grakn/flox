from typing import Dict, Any
from types import SimpleNamespace
from langfabric import ModelManager
from .config import GroxAppConfig, GroxProjectConfig
from .factory import build_checkpoint_saver

class GroxProject:

    def __init__(self, app: GroxAppConfig, tenant_id:str, config: GroxProjectConfig):
        self.app = app
        self.debug = app.log_level == "DEBUG"
        self.tenant_id = tenant_id
        self.config = config
        self.project_code = config.metadata.project
        if config.infrastructure:
            self.model_manager = ModelManager(config.infrastructure.model_configs)
            self.defaults = SimpleNamespace(**config.infrastructure.defaults)
        else:
            self.model_manager = ModelManager(dict())
            self.defaults = SimpleNamespace()

        self.checkpoint_saver = None

        if config.infrastructure:
            backend_configs = config.infrastructure.backend_configs or {}
            checkpoint_cfg = backend_configs.get("checkpoint_saver")

            if checkpoint_cfg:
                self.checkpoint_saver = build_checkpoint_saver(checkpoint_cfg)
