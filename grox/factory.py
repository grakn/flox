import re
from typing import Optional
from .config import BackendConfig
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.vectorstores.in_memory import InMemoryVectorStore
from langchain_redis import RedisVectorStore, RedisConfig
from redisvl.schema import IndexSchema, IndexInfo, TextField
from langchain_core.vectorstores import VectorStore

from .factory_cache import *
from .documents import *

def parse_ttl(ttl: Optional[str]) -> Optional[int]:
    if not ttl:
        return None
    match = re.fullmatch(r"(\d+)([smhdw])", ttl.strip().lower())
    if not match:
        raise ValueError(f"Invalid TTL format: '{ttl}'")

    value, unit = match.groups()
    value = int(value)
    return {
        "s": value,
        "m": value * 60,
        "h": value * 3600,
        "d": value * 86400,
        "w": value * 604800,
    }[unit]


def build_checkpoint_saver(config: BackendConfig):
    ttl_seconds = parse_ttl(config.ttl)

    if config.backend == "memory":
        return create_memory_saver()

    elif config.backend == "redis":
        if config.sync:
            return create_redis_saver(config.url.get_secret_value(), ttl_seconds)
        else:
            return create_async_redis_saver(config.url.get_secret_value(), ttl_seconds)

    else:
        raise ValueError(f"Unsupported backend for checkpoint saver: '{config.backend}'")


def build_chat_history_factory(tenant_id:str, project_code:str, config: BackendConfig):
    ttl_seconds = parse_ttl(config.ttl)

    if config.backend == "memory":
        return create_chat_history_memory_manager(tenant_id, project_code).get_instance

    elif config.backend == "redis":
        redis_client = create_redis_instance(config.url.get_secret_value())
        def _factory(session_id:str):
            chat_history = RedisChatMessageHistory(
                session_id,
                redis_client=redis_client,
                key_prefix=f"chat_history:{tenant_id}:{project_code}",
                ttl=ttl_seconds
            )
            return chat_history
        return _factory

    else:
        raise ValueError(f"Unsupported backend for checkpoint saver: '{config.backend}'")


def build_document_store(model, tenant_id:str, project_code: str, document_paths: list, config: BackendConfig, logger):
    if config.backend == "memory":

        def _factory(model, collection: Collection) -> VectorStore:
            return InMemoryVectorStore(model)

        store = DocumentStore(
            model=model,
            document_paths=document_paths,
            vector_store_factory=_factory,
            logger=logger
        )

        return store

    if config.backend == "redis":
        redis_client = create_redis_instance(config.url.get_secret_value())
        def new_redis_vector_store_factory(model, collection: Collection) -> VectorStore:

            prefix = f"vector:{tenant_id}:{project_code}:{collection.name}"
            if collection.index:
                collection.index.name = collection.name
                collection.index.prefix = prefix
            else:
                collection.index=IndexSettings(name=collection.name,prefix=prefix)

            if not collection.shema:
                default_schema = {
                    "fields": [
                        {"name": "id", "type": "text"},
                        {"name": "content", "type": "text"},
                        {"name": "content_vector", "type": "vector", "attrs": {"dims": 1536, "algorithm": "flat", "distance_metric": "cosine"}}
                    ]
                }
                collection.shema=CollectionIndexSchema.from_dict(default_schema)

            schema = IndexSchema.from_dict(collection.to_schema_dict())

            config = RedisConfig(
                redis_client=redis_client,
                index_name=collection.name,
                key_prefix=prefix,
                index_schema=schema,
                embedding_field=collection.get_embedding_field_name("content_vector"),
                content_field=collection.get_content_field_name("content"),
            )
            return RedisVectorStore(
                embeddings=model,
                config=config
            )

        return DocumentStore(
            model=model,
            document_paths=document_paths,
            vector_store_factory=new_redis_vector_store_factory,
            logger=logger
        )
    raise ValueError(f"unknown backend type '{backend}' for the vector_store in the project '{project_code}'")
