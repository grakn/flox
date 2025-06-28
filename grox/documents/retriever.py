from typing import List, Tuple, Optional, Any
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document
from langchain_core.vectorstores import VectorStore


class DocumentRetriever:
    """Handles vector similarity search with optional score filtering and BM25 re-ranking."""

    def __init__(self, vector_store: VectorStore, logger) -> None:
        self.vector_store = vector_store
        self.logger = logger

    def get_relevant_documents(
        self,
        query: str,
        *,
        search_type: str = "similarity",
        num_results: int = 5,
        score_threshold: Optional[float] = 0.8,
        **kwargs: Any,
    ) -> List[Document]:
        if search_type in {"similarity", "mmr", "similarity_score_threshold"}:
            retriever = self.vector_store.as_retriever(
                search_type=search_type,
                search_kwargs={
                    "k": num_results,
                    "score_threshold": score_threshold,
                },
            )
            return retriever.invoke(query)

        if search_type == "similarity_search_with_score":
            return self._search_with_score(query, num_results, score_threshold)

        if search_type == "similarity_search_with_score_bm25_ranked":
            return self._search_with_score_bm25_ranked(query, num_results, score_threshold, **kwargs)

        raise ValueError(f"Unsupported search_type: {search_type}")

    def _search_with_score(
        self,
        query: str,
        num_results: int,
        score_threshold: Optional[float],
    ) -> List[Document]:
        results = self.vector_store.similarity_search_with_score(
            query, k=num_results, return_metadata=True
        )
        filtered = [
            (doc, score) for doc, score in results if score_threshold is None or score >= score_threshold
        ]

        self.logger.info(
            "similarity_search_with_score",
            total_results=len(results),
            filtered_results=len(filtered),
            score_threshold=score_threshold,
        )
        return [doc for doc, _ in filtered[:num_results]]

    def _search_with_score_bm25_ranked(
        self,
        query: str,
        num_results: int,
        score_threshold: Optional[float],
        **kwargs: Any,
    ) -> List[Document]:
        candidate_docs = self._search_with_score(query, num_results, score_threshold)
        if not candidate_docs:
            return []

        bm25_params = {
            "k1": float(kwargs.get("k1", 1.2)),
            "b": float(kwargs.get("b", 0.75)),
            "epsilon": float(kwargs.get("epsilon", 0.25)),
        }

        retriever = BM25Retriever.from_documents(
            candidate_docs,
            k=num_results,
            bm25_params=bm25_params,
        )
        ranked = retriever.invoke(query)

        self.logger.info(
            "similarity_search_with_score_bm25_ranked",
            initial_candidates=len(candidate_docs),
            ranked_results=len(ranked),
            bm25_params=bm25_params,
        )
        return ranked
