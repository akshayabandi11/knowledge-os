import hashlib
import time
import uuid
from datetime import datetime
from typing import BinaryIO, List

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.application.services.chunking_service import ChunkingService
from app.application.services.embedding_service import EmbeddingService
from app.application.services.parsing_service import ParsingService

# Wait! Let's check the collections repository import name from Phase 1 deps.py:
# from app.domain.repositories.collection_repository import ICollectionRepository
# Let's import:
from app.application.services.storage_service import StorageService
from app.core.exceptions import EntityNotFoundError, ValidationError
from app.core.logging import logger
from app.domain.enums import DocStatus
from app.domain.models import Document, DocumentChunk
from app.domain.repositories.collection_repository import (
    ICollectionRepository,
)  # Ensure name matches setup
from app.domain.repositories.document_repository import IDocumentRepository
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.sqlalchemy_document import (
    SQLAlchemyDocumentRepository,
)


class DocumentService:
    """
    Service responsible for managing document lifecycles.
    Co-ordinates metadata registration, storage, and asynchronous parsing pipelines.
    """

    def __init__(
        self,
        db: Session,
        doc_repo: IDocumentRepository,
        collection_repo: ICollectionRepository,
        storage_service: StorageService,
        parsing_service: ParsingService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.doc_repo = doc_repo
        self.collection_repo = collection_repo
        self.storage_service = storage_service
        self.parsing_service = parsing_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service

    def upload_document(
        self,
        collection_id: uuid.UUID,
        user_id: uuid.UUID,
        file_name: str,
        file_type: str,
        file_size: int,
        file_data: BinaryIO,
        background_tasks: BackgroundTasks,
    ) -> Document:
        """
        Validates collection ownership, uploads the file to storage,
        saves metadata in DB with 'processing' status, and schedules async ingestion.
        """
        # 1. Enforce Collection Tenant Isolation
        collection = self.collection_repo.get_by_id_and_user_id(collection_id, user_id)
        if not collection:
            raise EntityNotFoundError(
                f"Collection {collection_id} not found or access denied."
            )

        # 2. File validation limits (e.g. max 25MB)
        if file_size > 25 * 1024 * 1024:
            raise ValidationError("File size exceeds maximum limit of 25MB.")

        ext = file_name.split(".")[-1].lower()
        if ext not in ["txt", "pdf", "png", "jpg", "jpeg", "webp"]:
            raise ValidationError(f"File extension .{ext} is not supported.")

        # 3. Calculate file hash and read mime type
        file_data.seek(0)
        file_bytes = file_data.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Reset stream pointer
        file_data.seek(0)

        # 4. Upload file to Storage
        document_id = uuid.uuid4()
        storage_key = f"collections/{collection_id}/{document_id}.{ext}"
        self.storage_service.upload(file_data, storage_key)

        # 5. Save metadata record (status: processing)
        doc_entity = Document(
            id=document_id,
            collection_id=collection_id,
            name=file_name,
            file_type=ext,
            file_size=file_size,
            storage_key=storage_key,
            status=DocStatus.processing,
            error_message=None,
            # Initial metadata overrides (completed by background process)
            mime_type=file_type,
            file_hash=file_hash,
            page_count=None,
            chunk_count=None,
            processing_time_ms=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        registered = self.doc_repo.add(doc_entity)
        self.db.commit()

        # NOTE on Asynchronous Workers:
        # We leverage FastAPI's built-in BackgroundTasks here for simple, out-of-the-box local setups.
        # To scale this to production, you can replace 'background_tasks.add_task' with a Celery task call:
        # e.g., ingest_document_celery.delay(document_id, storage_key, file_name, file_type)
        # Because all processing services are decoupled, no modifications to business logic will be required.
        background_tasks.add_task(
            self.ingest_document_background,
            document_id=document_id,
            storage_key=storage_key,
            file_name=file_name,
            file_type=file_type,
        )

        return registered

    def ingest_document_background(
        self, document_id: uuid.UUID, storage_key: str, file_name: str, file_type: str
    ) -> None:
        """
        Asynchronous pipeline worker: parses text, splits into chunks,
        calculates embeddings, indexes vectors in database, and updates document status with metadata.
        """
        logger.info(f"Starting async ingestion for document {document_id}")

        # Open fresh isolated DB session for background thread
        bg_db = SessionLocal()
        bg_doc_repo = SQLAlchemyDocumentRepository(bg_db)

        start_time_ms = int(time.time() * 1000)

        try:
            # 1. Download file stream from storage
            file_stream = self.storage_service.download(storage_key)

            # 2. Parse text content
            parsed_text = self.parsing_service.parse_file(
                file_stream, file_name, file_type
            )
            if not parsed_text.strip():
                raise ValidationError("Extracted text content is empty.")

            # 3. Segment by page markers (for citation tracking) if present
            chunk_entities: List[DocumentChunk] = []
            chunk_idx = 0
            page_count = 1

            if "--- PAGE " in parsed_text:
                # Enforce page-aware chunking for structured citation retrieval
                parts = parsed_text.split("--- PAGE ")
                # Update page count to total splits
                page_count = len(parts) - 1 if len(parts) > 1 else 1

                for part in parts:
                    if not part.strip():
                        continue
                    # Extract page number index: "1 ---\ntext content"
                    header_split = part.split("---\n", 1)
                    if len(header_split) == 2:
                        try:
                            page_num = int(header_split[0].strip())
                        except ValueError:
                            page_num = 1
                        page_text = header_split[1]
                    else:
                        page_num = 1
                        page_text = part

                    # Split page text into chunks recursively
                    page_chunks = self.chunking_service.split_text(page_text)
                    for content in page_chunks:
                        chunk_entities.append(
                            DocumentChunk(
                                id=uuid.uuid4(),
                                document_id=document_id,
                                content=content,
                                page_number=page_num,
                                chunk_index=chunk_idx,
                                embedding=[],  # Settled after batch API call
                                created_at=datetime.utcnow(),
                            )
                        )
                        chunk_idx += 1
            else:
                # Plain Text or Image OCR parsing (Single page boundary setup)
                text_chunks = self.chunking_service.split_text(parsed_text)
                for content in text_chunks:
                    chunk_entities.append(
                        DocumentChunk(
                            id=uuid.uuid4(),
                            document_id=document_id,
                            content=content,
                            page_number=1,
                            chunk_index=chunk_idx,
                            embedding=[],
                            created_at=datetime.utcnow(),
                        )
                    )
                    chunk_idx += 1

            # 4. Generate embeddings via AI Provider
            chunk_texts = [c.content for c in chunk_entities]
            embeddings = self.embedding_service.embed_chunks(chunk_texts)

            # Assign embeddings back to chunks
            for chunk, emb in zip(chunk_entities, embeddings,strict=False):
                chunk.embedding = emb

            # 5. Save chunks to Database
            bg_doc_repo.add_chunks(chunk_entities)

            # Calculate duration
            duration_ms = int(time.time() * 1000) - start_time_ms

            # 6. Update document status to completed
            db_doc = bg_doc_repo.get_by_id(document_id)
            if db_doc:
                db_doc.status = DocStatus.completed
                db_doc.page_count = page_count
                db_doc.chunk_count = len(chunk_entities)
                db_doc.processing_time_ms = duration_ms
                db_doc.updated_at = datetime.utcnow()
                bg_doc_repo.update(db_doc)

            bg_db.commit()
            logger.info(
                f"Ingestion successful for document {document_id} in {duration_ms}ms"
            )

        except Exception as e:
            bg_db.rollback()
            logger.error(f"Ingestion failed for document {document_id}: {str(e)}")

            # Record failure state
            try:
                db_doc = bg_doc_repo.get_by_id(document_id)
                if db_doc:
                    db_doc.status = DocStatus.failed
                    db_doc.error_message = str(e)
                    db_doc.processing_time_ms = int(time.time() * 1000) - start_time_ms
                    db_doc.updated_at = datetime.utcnow()
                    bg_doc_repo.update(db_doc)
                bg_db.commit()
            except Exception as inner_e:
                logger.error(
                    f"Failed to save document error state for {document_id}: {str(inner_e)}"
                )
        finally:
            bg_db.close()
