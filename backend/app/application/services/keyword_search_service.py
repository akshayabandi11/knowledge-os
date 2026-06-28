import uuid
from typing import List, Tuple
from app.domain.models import DocumentChunk
from app.domain.repositories.document_repository import IDocumentRepository

class KeywordSearchService:
    """
    Service responsible for executing full-text keyword searches
    using PostgreSQL native full text queries (ts_vector/ts_rank).
    """
    def __init__(self, doc_repo: IDocumentRepository):
        self.doc_repo = doc_repo

    def search(self, collection_id: uuid.UUID, query: str, limit: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """
        Executes Full Text search and returns matching chunks and their rank score.
        """
        if not query.strip():
            return []
            
        return self.doc_repo.search_keyword_chunks(
            collection_id=collection_id,
            query=query,
            limit=limit
        )
