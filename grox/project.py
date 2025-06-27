from typing import Dict, Any
from types import SimpleNamespace
from langfabric import ModelManager, build_embeddings
from langgraph.graph import StateGraph, START, END
from operator import add

from .config import GroxAppConfig, GroxProjectConfig
from .factory import build_checkpoint_saver, build_chat_history_factory
from .state import GroxState

# Define your nodes
def node_a(state: GroxState) -> GroxState:
    return {"foo": "a", "bar": ["a"]}

def node_b(state: GroxState) -> GroxState:
    return {"foo": "b", "bar": ["b"]}


class GroxProject:

    def __init__(self, app: GroxAppConfig, tenant_id:str, config: GroxProjectConfig):
        self.app = app
        self.debug = app.log_level == "DEBUG"
        self.tenant_id = tenant_id
        self.config = config
        self.project_code = config.metadata.project

        self._initialize_models()
        self._initialize_backends()
        self._initialize_workflow()

    def _initialize_models(self):
        infra = self.config.infrastructure

        if not infra:
            self.model_manager = ModelManager({})
            self.embeddings = None
            return

        self.model_manager = ModelManager(infra.model_configs)
        self.defaults = infra.defaults or {}

        if self.defaults.chat_model:
            if not infra.model_configs.get(self.defaults.chat_model):
                raise ValueError(
                    f"Chat model '{self.defaults.chat_model}' not found for "
                    f"{self.tenant_id}:{self.project_code}"
                )
            return

        if not self.defaults.embedding_model:
            self.embeddings = None
            return

        model_config = infra.model_configs.get(self.defaults.embedding_model)
        if not model_config:
            raise ValueError(
                f"Embedding model '{self.defaults.embedding_model}' not found for "
                f"{self.tenant_id}:{self.project_code}"
            )

        self.embeddings = build_embeddings(model_config)

    def _initialize_backends(self):
        infra = self.config.infrastructure
        if not infra:
            return

        backend_configs = infra.backend_configs or {}

        checkpoint_cfg = backend_configs.get("checkpoint_saver")
        if checkpoint_cfg:
            self.checkpoint_saver = build_checkpoint_saver(checkpoint_cfg)

        chat_history_cfg = backend_configs.get("chat_history")
        if chat_history_cfg:
            self.chat_history_factory = build_chat_history_factory(
                self.tenant_id, self.project_code, chat_history_cfg
            )

    def _initialize_workflow(self):
        self.workflow = StateGraph(GroxState)
        self.workflow.add_node("node_a", node_a)
        self.workflow.add_node("node_b", node_b)
        self.workflow.add_edge(START, "node_a")
        self.workflow.add_edge("node_a", "node_b")
        self.workflow.add_edge("node_b", END)

        self.graph = self.workflow.compile(checkpointer=self.checkpoint_saver)
