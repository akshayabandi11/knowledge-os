import abc
from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.models import Document, DocumentChunk, Flashcard, Quiz, Summary
from app.domain.repositories.base import IRepository


class IDocumentRepository(IRepository[Document], abc.ABC):
    @abc.abstractmethod
    def get_by_collection_id(self, collection_id: UUID) -> List[Document]:
        """Fetch all documents within a given collection workspace."""
        pass

    @abc.abstractmethod
    def get_by_id_and_user_id(
        self, document_id: UUID, user_id: UUID
    ) -> Optional[Document]:
        """Fetch a specific document verifying user ownership mapping."""
        pass

    @abc.abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Bulk save chunked document text segments and their generated embeddings."""
        pass

    @abc.abstractmethod
    def search_similar_chunks(
        self, collection_id: UUID, query_embedding: List[float], limit: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Execute custom cosine similarity vector search using pgvector.
        Returns document chunks and their distance metric.
        """
        pass

    @abc.abstractmethod
    def search_keyword_chunks(
        self, collection_id: UUID, query: str, limit: int = 10
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Execute full-text keyword search using PostgreSQL native FTS.
        Returns document chunks and their relevance rank.
        """
        pass

    @abc.abstractmethod
    def create_summary(self, summary: Summary) -> Summary:
        pass

    @abc.abstractmethod
    def get_summary(self, document_id: UUID) -> Optional[Summary]:
        pass

    @abc.abstractmethod
    def add_flashcards(self, flashcards: List[Flashcard]) -> List[Flashcard]:
        pass

    @abc.abstractmethod
    def get_flashcards(self, document_id: UUID) -> List[Flashcard]:
        pass

    @abc.abstractmethod
    def create_quiz(self, quiz: Quiz) -> Quiz:
        pass

    @abc.abstractmethod
    def get_quizzes_by_document(self, document_id: UUID) -> List[Quiz]:
        pass
