import uuid
from typing import List, Tuple

from app.application.services.embedding_service import EmbeddingService
from app.domain.models import DocumentChunk
from app.domain.repositories.document_repository import IDocumentRepository


class VectorSearchService:
    """
    Service executing semantic vector search queries on PostgreSQL pgvector database tables.
    """

    def __init__(
        self, doc_repo: IDocumentRepository, embedding_service: EmbeddingService
    ):
        self.doc_repo = doc_repo
        self.embedding_service = embedding_service

    def search(
        self,
        collection_id: uuid.UUID,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.70,  # Exclude poor similarity matches
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Calculates search query embedding and fetches similar vector chunks from pgvector.
        Transforms distance metrics (where 0 is identical and 2 is opposite) to similarity:
        similarity = 1.0 - cosine_distance.
        """
        # Generate query vector
        query_vector = self.embedding_service.embed_query(query)

        # Query repository
        results = self.doc_repo.search_similar_chunks(
            collection_id=collection_id, query_embedding=query_vector, limit=limit
        )

        filtered_results: List[Tuple[DocumentChunk, float]] = []
        for chunk, distance in results:
            # Cosine similarity calculation: similarity = 1 - distance
            similarity = 1.0 - distance
            if similarity >= similarity_threshold:
                filtered_results.append((chunk, similarity))

        return filtered_results
