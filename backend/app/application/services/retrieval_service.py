import uuid
from typing import List, Tuple

from app.application.services.fusion_service import FusionService
from app.application.services.keyword_search_service import KeywordSearchService
from app.application.services.reranker_service import RerankerService
from app.application.services.vector_search_service import VectorSearchService
from app.core.exceptions import NoContextFound, RetrievalError
from app.domain.models import DocumentChunk


class RetrievalService:
    """
    Coordinator Service managing the Hybrid Retrieval Pipeline.
    Triggers concurrent Vector and Keyword FTS searches, fuses ranks via RRF,
    and applies reranking heuristics to return the top supporting chunks.
    """

    def __init__(
        self,
        vector_search_service: VectorSearchService,
        keyword_search_service: KeywordSearchService,
        fusion_service: FusionService,
        reranker_service: RerankerService,
    ):
        self.vector_search_service = vector_search_service
        self.keyword_search_service = keyword_search_service
        self.fusion_service = fusion_service
        self.reranker_service = reranker_service

    def retrieve_context(
        self,
        collection_id: uuid.UUID,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.50,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Executes hybrid search (Vector + Keyword), fuses lists, reranks,
        and returns the top context chunks.
        """
        try:
            # 1. Execute vector search
            vector_results = self.vector_search_service.search(
                collection_id=collection_id,
                query=query,
                limit=15,  # Oversample to allow rich fusion
                similarity_threshold=similarity_threshold,
            )

            # 2. Execute full-text keyword search
            keyword_results = self.keyword_search_service.search(
                collection_id=collection_id, query=query, limit=15
            )

            # If no matches found in either system, raise exception
            if not vector_results and not keyword_results:
                raise NoContextFound(
                    "No supporting context found in collection documents."
                )

            # 3. Fuse lists using Reciprocal Rank Fusion (RRF)
            fused_results = self.fusion_service.fuse_results(
                vector_results=vector_results, keyword_results=keyword_results
            )

            # 4. Rerank top results
            reranked_results = self.reranker_service.rerank(
                query=query, chunks=fused_results, limit=limit
            )

            return reranked_results
        except Exception as e:
            if not isinstance(e, RetrievalError):
                raise RetrievalError(f"RAG Retrieval failed: {str(e)}") from e
            raise
