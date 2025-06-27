from typing import Dict, Any
from types import SimpleNamespace
from langfabric import ModelManager
from .config import GroxAppConfig, GroxProjectConfig
from .factory import build_checkpoint_saver, build_chat_history_factory

class GroxProject:

    def __init__(self, app: GroxAppConfig, tenant_id:str, config: GroxProjectConfig):
        self.app = app
        self.debug = app.log_level == "DEBUG"
        self.tenant_id = tenant_id
        self.config = config
        self.project_code = config.metadata.project

        # initialize models
        if config.infrastructure:
            # initialize model manager and default models
            self.model_manager = ModelManager(config.infrastructure.model_configs)
            self.defaults = SimpleNamespace(**config.infrastructure.defaults)
        else:
            self.model_manager = ModelManager(dict())
            self.defaults = SimpleNamespace()

        # initialize backends
        self.checkpoint_saver = None
        def null_chat_history_factory(session_id: str):
            return None
        self.chat_history_factory = null_chat_history_factory

        if config.infrastructure:
            # initialize backends
            backend_configs = config.infrastructure.backend_configs or {}

            checkpoint_cfg = backend_configs.get("checkpoint_saver")
            if checkpoint_cfg:
                self.checkpoint_saver = build_checkpoint_saver(checkpoint_cfg)

            history_cfg = backend_configs.get("chat_history")
            if history_cfg:
                self.chat_history_factory = build_chat_history_factory(self.tenant_id, self.project_code, history_cfg)
