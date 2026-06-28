import io
import uuid
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.domain.models import Document, Collection
from app.domain.enums import DocStatus
from app.infrastructure.storage.base import IStorageProvider
from app.infrastructure.ai.embedding_provider import BaseEmbeddingProvider, GeminiEmbeddingProvider
from app.application.services.storage_service import StorageService
from app.application.services.chunking_service import ChunkingService
from app.application.services.parsing_service import ParsingService
from app.application.services.embedding_service import EmbeddingService
from app.application.services.document_service import DocumentService
from app.core.exceptions import ValidationError, EntityNotFoundError

# --- Storage Service Tests ---

def test_storage_service_delegates():
    mock_provider = MagicMock(spec=IStorageProvider)
    service = StorageService(mock_provider)
    
    file_stream = io.BytesIO(b"Hello Storage")
    storage_key = "test_key.txt"
    
    mock_provider.upload_file.return_value = "local://test_key.txt"
    
    # Test Upload
    res = service.upload(file_stream, storage_key)
    mock_provider.upload_file.assert_called_once_with(file_stream, storage_key)
    assert res == "local://test_key.txt"
    
    # Test Download
    service.download(storage_key)
    mock_provider.get_file.assert_called_once_with(storage_key)
    
    # Test Delete
    service.delete(storage_key)
    mock_provider.delete_file.assert_called_once_with(storage_key)

# --- Chunking Service Tests ---

def test_chunking_service_split():
    service = ChunkingService(chunk_size=10, chunk_overlap=2)
    text = "hello world how are you"
    chunks = service.split_text(text)
    assert len(chunks) > 0
    assert all(isinstance(c, str) for c in chunks)
    assert all(len(c) <= 10 for c in chunks)

def test_chunking_service_empty_text():
    service = ChunkingService()
    assert service.split_text("") == []

# --- Parsing Service Tests ---

def test_parsing_service_txt():
    service = ParsingService()
    file_stream = io.BytesIO("plain text content".encode("utf-8"))
    parsed = service.parse_txt(file_stream)
    assert parsed == "plain text content"

@patch("google.generativeai.GenerativeModel")
@patch("app.core.config.settings.GEMINI_API_KEY", "dummy_key")
def test_parsing_service_image_ocr(mock_generative_model):
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance
    mock_model_instance.generate_content.return_value = MagicMock(text="extracted OCR text")
    
    # Setup prompts directory locally for testing
    with patch.object(ParsingService, "_get_prompt_template", return_value="perform OCR"):
        service = ParsingService()
        file_stream = io.BytesIO(b"image_bytes")
        res = service.parse_image_ocr(file_stream, "image/png")
        assert res == "extracted OCR text"
        mock_model_instance.generate_content.assert_called_once()

# --- Embedding Service Tests ---

def test_embedding_service_delegation():
    mock_provider = MagicMock(spec=BaseEmbeddingProvider)
    mock_provider.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_provider.embed_chunks.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    service = EmbeddingService(mock_provider)
    
    # Test query embedding
    q_emb = service.embed_query("query string")
    assert q_emb == [0.1, 0.2, 0.3]
    mock_provider.embed_query.assert_called_once_with("query string")
    
    # Test chunks embedding
    c_emb = service.embed_chunks(["chunk 1", "chunk 2"])
    assert c_emb == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_provider.embed_chunks.assert_called_once_with(["chunk 1", "chunk 2"])

# --- Document Service Tests ---

@patch("app.application.services.document_service.SessionLocal")
def test_document_service_upload(mock_session_local):
    mock_db = MagicMock()
    mock_doc_repo = MagicMock()
    mock_coll_repo = MagicMock()
    mock_storage = MagicMock()
    mock_parsing = MagicMock()
    mock_chunking = MagicMock()
    mock_embedding = MagicMock()
    mock_background_tasks = MagicMock()
    
    service = DocumentService(
        db=mock_db,
        doc_repo=mock_doc_repo,
        collection_repo=mock_coll_repo,
        storage_service=mock_storage,
        parsing_service=mock_parsing,
        chunking_service=mock_chunking,
        embedding_service=mock_embedding
    )
    
    collection_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # 1. Test collection not found
    mock_coll_repo.get_by_id_and_user_id.return_value = None
    with pytest.raises(EntityNotFoundError):
        service.upload_document(
            collection_id=collection_id,
            user_id=user_id,
            file_name="test.txt",
            file_type="text/plain",
            file_size=100,
            file_data=io.BytesIO(b"data"),
            background_tasks=mock_background_tasks
        )
        
    # 2. Test successful upload
    mock_coll_repo.get_by_id_and_user_id.return_value = Collection(
        id=collection_id,
        user_id=user_id,
        name="Test Coll",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_storage.upload.return_value = "local://test.txt"
    mock_doc_repo.add.side_effect = lambda x: x
    
    file_data = io.BytesIO(b"data")
    res = service.upload_document(
        collection_id=collection_id,
        user_id=user_id,
        file_name="test.txt",
        file_type="text/plain",
        file_size=100,
        file_data=file_data,
        background_tasks=mock_background_tasks
    )
    
    assert res.name == "test.txt"
    assert res.status == DocStatus.processing
    mock_storage.upload.assert_called_once()
    mock_doc_repo.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_background_tasks.add_task.assert_called_once()
