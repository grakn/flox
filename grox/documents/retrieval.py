from typing import Dict, List, Tuple, Any, Optional

from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document
from langchain_core.vectorstores import VectorStore

class DocumentRetrieval:
    """
    Handles vector similarity search with optional score filtering and BM25 re-ranking.

    Parameters
    ----------
    vector_store :VectorStore
        the VectorStore instance
    """

    def __init__(self, vector_store: VectorStore, logger) -> None:
        self._vector_store = vector_store
        self.logger = logger

    @staticmethod
    def top_k_by_similarity_threshold(
        sorted_results: List[Tuple[Document, float]],
        threshold: float,
        k: int
    ) -> List[Tuple[Document, float]]:
        """
        Sorts, filters, and returns top-k similarity search results.

        Args:
            results: List of (Document, similarity_score) tuples.
            threshold: Minimum similarity score to include.
            k: Maximum number of results to return.

        Returns:
            Top-k sorted and filtered (Document, score) tuples.
        """
        # Sort descending by score, usually not needed, keep just in case
        #sorted_results = sorted(sorted_results, key=lambda x: x[1], reverse=True)

        # Filter by threshold
        filtered = [(doc, score) for doc, score in sorted_results if score >= threshold]

        # Return top-k results
        return filtered[:k]

    def similarity_search(
        self,
        query: str,
        *,
        search_type: str = "similarity",
        num_results: int = 5,
        score_threshold: Optional[float] = 0.8,
        **kwargs: Any,
    ) -> List[Document]:
        if search_type in ("similarity", "mmr", "similarity_score_threshold"):
            retriever = self._vector_store.as_retriever(
                search_type=search_type,
                search_kwargs={
                    "k": num_results,
                    "score_threshold": score_threshold,
                },
            )
            return retriever.invoke(query)

        elif search_type == "similarity_search_with_score":
            return self.similarity_search_with_score(
                query=query,
                num_results=num_results,
                score_threshold=score_threshold,
            )

        elif search_type == "similarity_search_with_score_bm25_ranked":
            return self.similarity_search_with_score_bm25_ranked(
                query=query,
                num_results=num_results,
                score_threshold=score_threshold,
                **kwargs,
            )

        else:
            raise ValueError(f"Unsupported search_type: {search_type}")

    def similarity_search_with_score(
        self,
        query: str,
        *,
        num_results: int = 5,
        score_threshold: Optional[float] = 0.8,
    ) -> List[Document]:
        docs_with_scores = self._vector_store.similarity_search_with_score(
            query,
            k=num_results,
            return_metadata=True,
        )

        filtered = self.top_k_by_similarity_threshold(
            docs_with_scores, threshold=score_threshold, k=num_results
        )

        self.logger.info(
            "similarity_search_with_score",
            docs_with_scores=len(docs_with_scores),
            filtered=len(filtered),
            score_threshold=score_threshold,
        )
        return [doc for doc, _ in filtered]

    def similarity_search_with_score_bm25_ranked(
        self,
        query: str,
        *,
        num_results: int = 5,
        score_threshold: Optional[float] = 0.8,
        **kwargs: Any,
    ) -> List[Document]:
        candidate_docs = self.similarity_search_with_score(
            query,
            num_results=num_results,
            score_threshold=score_threshold,
        )
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
            candidate_docs=len(candidate_docs),
            ranked=len(ranked),
            k=num_results,
            bm25_params=bm25_params,
        )
        return ranked
