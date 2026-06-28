from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import Session

from app.domain.models import Document, DocumentChunk, Flashcard, Quiz, Summary
from app.domain.repositories.document_repository import IDocumentRepository
from app.infrastructure.db.models import (
    CollectionModel,
    DocumentChunkModel,
    DocumentModel,
    FlashcardModel,
    QuizModel,
    QuizQuestionModel,
    SummaryModel,
)


class SQLAlchemyDocumentRepository(IDocumentRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[Document]:
        db_doc = self.db.query(DocumentModel).filter(DocumentModel.id == id).first()
        if not db_doc:
            return None
        return Document.model_validate(db_doc)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        db_docs = self.db.query(DocumentModel).offset(skip).limit(limit).all()
        return [Document.model_validate(d) for d in db_docs]

    def add(self, entity: Document) -> Document:
        db_doc = DocumentModel(
            id=entity.id,
            collection_id=entity.collection_id,
            name=entity.name,
            file_type=entity.file_type,
            file_size=entity.file_size,
            storage_key=entity.storage_key,
            status=entity.status,
            error_message=entity.error_message,
            # Map Ingest metadata properties
            page_count=entity.page_count,
            language=entity.language,
            mime_type=entity.mime_type,
            file_hash=entity.file_hash,
            processing_time_ms=entity.processing_time_ms,
            chunk_count=entity.chunk_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.db.add(db_doc)
        self.db.flush()
        return Document.model_validate(db_doc)

    def update(self, entity: Document) -> Document:
        db_doc = (
            self.db.query(DocumentModel).filter(DocumentModel.id == entity.id).first()
        )
        if not db_doc:
            raise ValueError(f"Document {entity.id} not found")
        db_doc.status = entity.status
        db_doc.error_message = entity.error_message

        # Update metadata properties
        db_doc.page_count = entity.page_count
        db_doc.language = entity.language
        db_doc.mime_type = entity.mime_type
        db_doc.file_hash = entity.file_hash
        db_doc.processing_time_ms = entity.processing_time_ms
        db_doc.chunk_count = entity.chunk_count

        db_doc.updated_at = entity.updated_at
        self.db.flush()
        return Document.model_validate(db_doc)

    def delete(self, id: UUID) -> None:
        db_doc = self.db.query(DocumentModel).filter(DocumentModel.id == id).first()
        if db_doc:
            self.db.delete(db_doc)
            self.db.flush()

    def get_by_collection_id(self, collection_id: UUID) -> List[Document]:
        db_docs = (
            self.db.query(DocumentModel)
            .filter(DocumentModel.collection_id == collection_id)
            .all()
        )
        return [Document.model_validate(d) for d in db_docs]

    def get_by_id_and_user_id(
        self, document_id: UUID, user_id: UUID
    ) -> Optional[Document]:
        db_doc = (
            self.db.query(DocumentModel)
            .join(CollectionModel, DocumentModel.collection_id == CollectionModel.id)
            .filter(DocumentModel.id == document_id, CollectionModel.user_id == user_id)
            .first()
        )
        if not db_doc:
            return None
        return Document.model_validate(db_doc)

    def add_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        db_chunks = [
            DocumentChunkModel(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                embedding=c.embedding,
                created_at=c.created_at,
            )
            for c in chunks
        ]
        self.db.add_all(db_chunks)
        self.db.flush()
        return chunks

    def search_similar_chunks(
        self, collection_id: UUID, query_embedding: List[float], limit: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        stmt = (
            select(
                DocumentChunkModel,
                DocumentChunkModel.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),
            )
            .join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)
            .where(DocumentModel.collection_id == collection_id)
            .order_by("distance")
            .limit(limit)
        )
        results = self.db.execute(stmt).all()

        chunk_pairs = []
        for row in results:
            chunk_model = row[0]
            distance = row[1]
            chunk_pairs.append(
                (DocumentChunk.model_validate(chunk_model), float(distance))
            )

        return chunk_pairs

    def search_keyword_chunks(
        self, collection_id: UUID, query: str, limit: int = 10
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Executes a PostgreSQL Full Text Search (FTS) query.
        Returns document chunks and their ts_rank.
        """
        # Convert plain text space separated query to FTS plainto_tsquery format
        stmt = (
            select(
                DocumentChunkModel,
                func.ts_rank(
                    func.to_tsvector("english", DocumentChunkModel.content),
                    func.plainto_tsquery("english", query),
                ).label("rank"),
            )
            .join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)
            .where(
                and_(
                    DocumentModel.collection_id == collection_id,
                    func.to_tsvector("english", DocumentChunkModel.content).op("@@")(
                        func.plainto_tsquery("english", query)
                    ),
                )
            )
            .order_by(text("rank DESC"))
            .limit(limit)
        )

        results = self.db.execute(stmt).all()

        chunk_pairs = []
        for row in results:
            chunk_model = row[0]
            rank = row[1]
            chunk_pairs.append((DocumentChunk.model_validate(chunk_model), float(rank)))

        return chunk_pairs

    def create_summary(self, summary: Summary) -> Summary:
        db_summary = SummaryModel(
            id=summary.id,
            document_id=summary.document_id,
            summary_text=summary.summary_text,
            key_points=summary.key_points,
            created_at=summary.created_at,
        )
        self.db.add(db_summary)
        self.db.flush()
        return Summary.model_validate(db_summary)

    def get_summary(self, document_id: UUID) -> Optional[Summary]:
        db_summary = (
            self.db.query(SummaryModel)
            .filter(SummaryModel.document_id == document_id)
            .first()
        )
        if not db_summary:
            return None
        return Summary.model_validate(db_summary)

    def add_flashcards(self, flashcards: List[Flashcard]) -> List[Flashcard]:
        db_cards = [
            FlashcardModel(
                id=f.id,
                document_id=f.document_id,
                front=f.front,
                back=f.back,
                created_at=f.created_at,
            )
            for f in flashcards
        ]
        self.db.add_all(db_cards)
        self.db.flush()
        return flashcards

    def get_flashcards(self, document_id: UUID) -> List[Flashcard]:
        db_cards = (
            self.db.query(FlashcardModel)
            .filter(FlashcardModel.document_id == document_id)
            .all()
        )
        return [Flashcard.model_validate(f) for f in db_cards]

    def create_quiz(self, quiz: Quiz) -> Quiz:
        db_quiz = QuizModel(
            id=quiz.id,
            document_id=quiz.document_id,
            title=quiz.title,
            created_at=quiz.created_at,
        )
        self.db.add(db_quiz)

        db_questions = [
            QuizQuestionModel(
                id=q.id,
                quiz_id=quiz.id,
                question=q.question,
                options=q.options,
                correct_option=q.correct_option,
                explanation=q.explanation,
                created_at=q.created_at,
            )
            for q in quiz.questions
        ]
        self.db.add_all(db_questions)
        self.db.flush()

        reloaded = self.db.query(QuizModel).filter(QuizModel.id == quiz.id).first()
        return Quiz.model_validate(reloaded)

    def get_quizzes_by_document(self, document_id: UUID) -> List[Quiz]:
        db_quizzes = (
            self.db.query(QuizModel).filter(QuizModel.document_id == document_id).all()
        )
        return [Quiz.model_validate(q) for q in db_quizzes]
