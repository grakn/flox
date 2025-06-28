import abc
import hashlib
import threading
import logging
from typing import Any, List, Dict, Optional, Sequence, Callable
from langchain.tools import Tool

import yaml
from .retriever import DocumentRetriever
from .schema import Document, Collection, DocumentSearchParams

logger = logging.getLogger(__name__)


class DocumentStore(abc.ABC):
    """
    Abstract class for managing collections of documents and indexing them into vector stores.
    """

    def __init__(
        self,
        model: Any,
        document_paths: List[str],
        vector_store_factory: Callable[[Any, Collection], Any],
        logger
    ) -> None:
        self.model = model
        self.document_paths = document_paths
        self.vector_store_factory = vector_store_factory
        self.logger = logger

        self._vector_stores: Dict[str, Any] = {}
        self._vector_stores_lock = threading.Lock()
        self.collections: Dict[str, Collection] = self._load_collections()

    def _load_collections(self) -> Dict[str, Collection]:
        """Parse and load all collections from provided YAML files."""
        collections = {}
        seen = {}
        for path in self.document_paths:
            doc = Document.load_yaml(path)
            for collection in doc.collections:
                if collection.name in seen:
                    raise ValueError(
                        f"Duplicate collection '{collection.name}' found in: "
                        f"'{path}' and '{seen[collection.name]}'"
                    )
                seen[collection.name] = path
                collections[collection.name] = collection

        return collections

    def find_collection(self, collection_name: str) -> Optional[Collection]:
        """Return the Collection definition by name, if it exists."""
        return self.collections.get(collection_name)

    def list_collections(self) -> List[str]:
        return list(self.collections.keys())

    def _get_vector_store(self, collection: Collection) -> Any:
        """Return or initialize a vector store for the given collection."""
        with self._vector_stores_lock:
            if collection.name not in self._vector_stores:
                self._vector_stores[collection.name] = self.vector_store_factory(self.model, collection)
            return self._vector_stores[collection.name]

    @staticmethod
    def _hash_text(text: str) -> str:
        """Create a stable hash for a piece of text."""
        return hashlib.blake2b(text.strip().lower().encode(), digest_size=16).hexdigest()

    def index_documents(self, collection_name: str) -> int:
        """
        Index documents from a collection into the associated vector store.
        Returns the number of documents indexed.
        """
        collection = self.find_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")

        vector_store = self._get_vector_store(collection)
        total_indexed = 0

        for data in collection.data:
            texts, metadata, ids = [], [], []

            for text in data.documents:
                doc_id = self._hash_text(text)
                ids.append(doc_id)
                meta = {"id": doc_id, **data.metadata}
                texts.append(text)
                metadata.append(meta)

            inserted_keys = vector_store.add_texts(texts, metadata, ids=ids)
            total_indexed += len(inserted_keys)

        return total_indexed

    def get_retriever(self, collection_name: str) -> DocumentRetriever:
        """Build a DocumentRetrieval instance for the given collection name."""
        collection = self.find_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        vector_store = self._get_vector_store(collection)
        return DocumentRetriever(vector_store, self.logger)

    def _tool_fn(self, params: DocumentSearchParams):
        retriever = self.get_retriever(params.collection_name)

        bm25_kwargs = {
            "k1": params.k1,
            "b": params.b,
            "epsilon": params.epsilon,
        }

        return retriever.get_relevant_documents(
            query=params.query,
            search_type=params.search_type,
            num_results=params.num_results,
            score_threshold=params.score_threshold,
            **{k: v for k, v in bm25_kwargs.items() if v is not None},
        )

    """
    Sample Agent Action Input
    {
      "action": "DocumentSearch",
      "action_input": {
        "query": "What is LangGraph?",
        "collection_name": "ai_docs",
        "search_type": "similarity_search_with_score_bm25_ranked",
        "num_results": 3,
        "score_threshold": 0.75,
        "k1": 1.5,
        "b": 0.9,
        "epsilon": 0.2
      }
    }
    """
    @property  # or use @cached_property if you want it cached
    def tool(self) -> Tool:
        return Tool(
            name="DocumentSearch",
            func=self._tool_fn,
            description="Search documents from a specific collection using vector similarity or BM25 re-ranking.",
            args_schema=DocumentSearchParams
        )
