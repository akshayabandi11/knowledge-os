from typing import List
from app.infrastructure.ai.embedding_provider import BaseEmbeddingProvider


class EmbeddingService:
    """
    Service responsible for managing text chunk embedding operations.
    Delegates concrete execution to an injected BaseEmbeddingProvider.
    """

    def __init__(self, provider: BaseEmbeddingProvider):
        self.provider = provider

    def embed_query(self, query: str) -> List[float]:
        """
        Calculates vector representation for search query strings.
        """
        return self.provider.embed_query(query)

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Calculates vector representations for document text chunk lists.
        """
        return self.provider.embed_chunks(chunks)
