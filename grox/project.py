from typing import Dict, Any
from types import SimpleNamespace
from langfabric import ModelManager, build_embeddings
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from operator import add
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain.tools import Tool

from .config import GroxAppConfig, GroxProjectConfig, DefaultsConfig
from .factory import build_checkpoint_saver, build_chat_history_factory, build_document_store
from .state import GroxState



class GroxProject:

    def __init__(self, app: GroxAppConfig, tenant_id:str, config: GroxProjectConfig, extra_tools=None):
        self.app = app
        self.debug = app.log_level == "DEBUG"
        self.tenant_id = tenant_id
        self.config = config
        self.project_code = config.metadata.project

        self._initialize_logger()
        self._initialize_models()
        self._initialize_backends()
        #self._initialize_workflow()

        if hasattr(self, 'chat_model_with_tools'):

            tools=[self.check_weather]
            if hasattr(self, 'document_store'):
                tools.append(self.document_store.tool)

            if extra_tools:
                tools.extend(extra_tools)

            self.graph = create_react_agent(
                self.chat_model_with_tools,
                tools=tools,
                prompt="You are a helpful assistant",
            )

    def check_weather(self, location: str) -> str:
        '''Return the weather forecast for the specified location.'''

        return f"It's always sunny in {location}"

    def _initialize_logger(self):
        logger_metadata = {
            "tenant_id": self.tenant_id,
            "project_code": self.project_code,
            "service": self.app.service,
            "version": self.app.version,
            "environment": self.app.environment,
        }

        # Filter out None values
        filtered_metadata = {k: v for k, v in logger_metadata.items() if v is not None}

        # Bind to logger
        self.logger = structlog.get_logger().bind(**filtered_metadata)


    def _initialize_models(self):

        infra = self.config.infrastructure
        if not infra:
            self.model_manager = ModelManager({})
            self.defaults = DefaultsConfig()
            return

        self.model_manager = ModelManager(infra.model_configs)
        self.defaults = infra.defaults or DefaultsConfig()

        #
        # chat_model
        #
        if self.defaults.chat_model and self.defaults.chat_model not in infra.model_configs:
            raise ValueError(
                f"Chat model '{self.defaults.chat_model}' not found in model config for "
                f"{self.tenant_id}:{self.project_code}"
            )

        self.chat_model = self.model_manager.load(self.defaults.chat_model)

        if self.defaults.chat_model:
            if self.debug:
                self.logger.info("using chat model", model=self.defaults.chat_model)
        else:
            self.logger.warning("chat model is empty, please define infrastructure->defaults->chat_model")

        #
        # chat_model_with_tools
        #
        if self.defaults.chat_model_with_tools and self.defaults.chat_model_with_tools not in infra.model_configs:
            raise ValueError(
                f"Chat model with tools '{self.defaults.chat_model_with_tools}' not found in model config for "
                f"{self.tenant_id}:{self.project_code}"
            )

        self.chat_model_with_tools = self.model_manager.load(self.defaults.chat_model_with_tools)

        if self.defaults.chat_model_with_tools:
            if self.debug:
                self.logger.info("using chat model with tools", model=self.defaults.chat_model_with_tools)
        else:
            self.logger.warning("chat model with tools is empty, please define infrastructure->defaults->chat_model_with_tools")

        #
        # embedding_model
        #
        if self.defaults.embedding_model and self.defaults.embedding_model not in infra.model_configs:
            raise ValueError(
                f"Embedding model '{self.defaults.embedding_model}' not found in model config for "
                f"{self.tenant_id}:{self.project_code}"
            )

        if self.defaults.embedding_model:
            if self.debug:
                self.logger.info("using embedding model", model=self.defaults.embedding_model)
        else:
            self.logger.warning("embedding model is empty, please define infrastructure->defaults->embedding_model")
            return

        #
        # load embedding_model
        #
        model_config = infra.model_configs.get(self.defaults.embedding_model)
        if not model_config:
            raise ValueError(
                f"Embedding model '{self.defaults.embedding_model}' not found for "
                f"{self.tenant_id}:{self.project_code}"
            )

        self.embedding_model = build_embeddings(model_config)

    def _initialize_backends(self):
        self.logger.debug("_initialize_backends")

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

        vector_store_cfg = backend_configs.get("vector_store")
        if vector_store_cfg:

            if not hasattr(self, 'embedding_model'):
                raise ValueError(
                    f"Embedding model not defined for vector store in "
                    f"{self.tenant_id}:{self.project_code}"
                )

            if not self.config.orchestration or not self.config.orchestration.documents:
                raise ValueError(
                    f"Documents not defined for vector store in "
                    f"{self.tenant_id}:{self.project_code}"
                )

            self.document_store = build_document_store(
                self.embedding_model, self.tenant_id, self.project_code, self.config.orchestration.documents, vector_store_cfg, self.logger
            )

            if vector_store_cfg.backend == "memory":
                asyncio.create_task(self.index_all_collections())

    def _index_documents(self, collection_name:str):
        total = self.document_store.index_documents(collection_name)
        self.logger.info("Indexed documents", collection_name=collection_name, total=total)


    async def index_all_collections(self):
        self.logger.info("Indexing all documents")

        if not hasattr(self, 'document_store'):
            self.logger.error("Document store not initialized.")
            return

        executor = ThreadPoolExecutor()  # optionally: limit max_workers
        loop = asyncio.get_running_loop()

        tasks = []
        for collection_name in self.document_store.list_collections():
            self.logger.info("Indexing collection", collection_name=collection_name)
            task = loop.run_in_executor(executor, self._index_documents, collection_name)
            tasks.append(task)

        await asyncio.gather(*tasks)
        self.logger.info("All in-memory indexes initialized.")
