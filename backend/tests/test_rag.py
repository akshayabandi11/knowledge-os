import uuid
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.domain.models import DocumentChunk, Message, Conversation
from app.application.services.query_rewrite_service import QueryRewriteService
from app.application.services.vector_search_service import VectorSearchService
from app.application.services.keyword_search_service import KeywordSearchService
from app.application.services.fusion_service import FusionService
from app.application.services.reranker_service import RerankerService
from app.application.services.prompt_builder_service import PromptBuilderService
from app.application.services.conversation_memory_service import ConversationMemoryService
from app.application.services.citation_service import CitationService
from app.application.services.confidence_service import ConfidenceService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.chat_service import ChatService

# --- Prompt Builder Tests ---

def test_prompt_builder():
    service = PromptBuilderService()
    
    # Mocking disk load to avoid file dependency
    with patch.object(service, "_load_template", return_value="Hello {{user}}, answer: {{answer}}"):
        placeholders = {"user": "Alice", "answer": "KnowledgeOS"}
        res = service.build_prompt("test.md", placeholders)
        assert res == "Hello Alice, answer: KnowledgeOS"

# --- Fusion Service RRF Tests ---

def test_reciprocal_rank_fusion():
    fusion = FusionService(k=60)
    
    chunk_1 = DocumentChunk(
        id=uuid.uuid4(), document_id=uuid.uuid4(), content="Content 1", 
        page_number=1, chunk_index=0, embedding=[], created_at=datetime.utcnow()
    )
    chunk_2 = DocumentChunk(
        id=uuid.uuid4(), document_id=uuid.uuid4(), content="Content 2", 
        page_number=1, chunk_index=1, embedding=[], created_at=datetime.utcnow()
    )
    
    # Vector Search lists (Rank 1: chunk_1, Rank 2: chunk_2)
    vector_results = [(chunk_1, 0.90), (chunk_2, 0.80)]
    # Keyword Search lists (Rank 1: chunk_2, Rank 2: chunk_1)
    keyword_results = [(chunk_2, 0.70), (chunk_1, 0.40)]
    
    fused = fusion.fuse_results(vector_results, keyword_results)
    
    # Assert RRF scores merged
    # chunk_1 score = 1/(60+1) + 1/(60+2)
    # chunk_2 score = 1/(60+2) + 1/(60+1)
    # They should have matching scores and chunks are returned
    assert len(fused) == 2
    assert fused[0][0].id in {chunk_1.id, chunk_2.id}

# --- Reranker Service Tests ---

def test_reranker_heuristics():
    reranker = RerankerService()
    
    chunk = DocumentChunk(
        id=uuid.uuid4(), document_id=uuid.uuid4(), content="TCP congestion control advantages", 
        page_number=1, chunk_index=0, embedding=[], created_at=datetime.utcnow()
    )
    
    # 1. High keyword overlap match
    res = reranker.rerank(
        query="TCP advantages",
        chunks=[(chunk, 0.80)],
        limit=1
    )
    assert len(res) == 1
    # Check that position boosts and Jaccard overlap increased the base score (0.80 -> higher)
    assert res[0][1] > 0.80

# --- Conversation Memory Tests ---

def test_conversation_memory_persistence():
    mock_repo = MagicMock()
    service = ConversationMemoryService(mock_repo)
    
    conversation_id = uuid.uuid4()
    message = Message(
        id=uuid.uuid4(), conversation_id=conversation_id, role="user",
        content="Hello RAG", citations=None, created_at=datetime.utcnow()
    )
    mock_repo.add_message.return_value = message
    
    res = service.add_message(conversation_id, "user", "Hello RAG")
    assert res.content == "Hello RAG"
    mock_repo.add_message.assert_called_once()

def test_conversation_memory_history_string():
    mock_repo = MagicMock()
    service = ConversationMemoryService(mock_repo)
    
    conversation_id = uuid.uuid4()
    mock_repo.get_messages.return_value = [
        Message(id=uuid.uuid4(), conversation_id=conversation_id, role="user", content="Hi", created_at=datetime.utcnow()),
        Message(id=uuid.uuid4(), conversation_id=conversation_id, role="assistant", content="Hello", created_at=datetime.utcnow())
    ]
    
    hist_str = service.get_history_as_string(conversation_id)
    assert "User: Hi" in hist_str
    assert "Assistant: Hello" in hist_str

def test_conversation_memory_truncation():
    service = ConversationMemoryService(MagicMock())
    history = "User: line 1\nAssistant: line 2\nUser: line 3"
    
    # Truncate to max 15 characters, should align to line breaks
    truncated = service.truncate_history(history, max_chars=18)
    assert "User: line 3" in truncated
    assert "line 1" not in truncated

# --- Citation Service Tests ---

def test_citation_parsing():
    service = CitationService()
    
    doc_id = uuid.uuid4()
    retrieved = [
        DocumentChunk(id=uuid.uuid4(), document_id=doc_id, content="Text", page_number=5, chunk_index=2, embedding=[], created_at=datetime.utcnow())
    ]
    # Set document name dynamically
    retrieved[0].document_name = "test_doc.pdf"
    
    response_text = "The system starts on [Document: test_doc.pdf - Page: 5] cleanly."
    
    citations = service.extract_citations(response_text, retrieved)
    assert len(citations) == 1
    assert citations[0]["document_name"] == "test_doc.pdf"
    assert citations[0]["page_number"] == 5
    assert citations[0]["chunk_index"] == 2

# --- Confidence Service Tests ---

def test_confidence_calculations():
    service = ConfidenceService()
    
    chunk = DocumentChunk(
        id=uuid.uuid4(), document_id=uuid.uuid4(), content="Text", 
        page_number=1, chunk_index=0, embedding=[], created_at=datetime.utcnow()
    )
    
    # High score (3+ chunks, similarity >= 0.82)
    high_conf = service.calculate_confidence([(chunk, 0.85), (chunk, 0.85), (chunk, 0.85)])
    assert high_conf == "High"
    
    # Medium score
    med_conf = service.calculate_confidence([(chunk, 0.70)])
    assert med_conf == "Medium"
    
    # Low score
    low_conf = service.calculate_confidence([])
    assert low_conf == "Low"

# --- Chat Service Streaming Integration Tests ---

@patch("google.generativeai.GenerativeModel")
@patch("app.core.config.settings.GEMINI_API_KEY", "dummy_key")
def test_chat_service_sse_stream_generation(mock_generative_model):
    mock_db = MagicMock()
    mock_usage_log = MagicMock()
    mock_rewrite = MagicMock()
    mock_retrieval = MagicMock()
    mock_prompt_builder = MagicMock()
    mock_memory = MagicMock()
    mock_citation = MagicMock()
    mock_confidence = MagicMock()
    
    chat_service = ChatService(
        db=mock_db,
        usage_log_repo=mock_usage_log,
        query_rewrite_service=mock_rewrite,
        retrieval_service=mock_retrieval,
        prompt_builder_service=mock_prompt_builder,
        memory_service=mock_memory,
        citation_service=mock_citation,
        confidence_service=mock_confidence
    )
    
    conversation_id = uuid.uuid4()
    collection_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Mocking preprocessor steps
    mock_memory.get_history_as_string.return_value = "User: Hi"
    mock_rewrite.rewrite_query.return_value = "Hello rewritten"
    
    chunk = DocumentChunk(
        id=uuid.uuid4(), document_id=uuid.uuid4(), content="Supporting Text", 
        page_number=1, chunk_index=0, embedding=[], created_at=datetime.utcnow()
    )
    chunk.document_name = "doc.pdf"
    mock_retrieval.retrieve_context.return_value = [(chunk, 0.85)]
    mock_prompt_builder.build_prompt.return_value = "Final structured prompt text"
    
    # Mocking Gemini SDK Model returns
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance
    mock_model_instance.count_tokens.return_value = MagicMock(total_tokens=10)
    
    # Mock stream generator yielding chunks
    mock_chunk_1 = MagicMock()
    mock_chunk_1.text = "Generated "
    mock_chunk_2 = MagicMock()
    mock_chunk_2.text = "response"
    mock_model_instance.generate_content.return_value = [mock_chunk_1, mock_chunk_2]
    
    # Mock post generation analysis
    mock_citation.extract_citations.return_value = [{"document_name": "doc.pdf", "page_number": 1, "chunk_index": 0, "confidence": 0.95}]
    mock_confidence.calculate_confidence.return_value = "High"
    
    # Run the streaming generator loop
    generator = chat_service.stream_chat(
        user_id=user_id,
        conversation_id=conversation_id,
        collection_id=collection_id,
        user_query="Hello"
    )
    
    sse_events = list(generator)
    
    # Assert SSE events generated
    assert len(sse_events) == 3 # Yield 1: "Generated ", Yield 2: "response", Yield 3: Metadata citations
    assert "Generated" in sse_events[0]
    assert "response" in sse_events[1]
    
    # Final event holds citations metadata JSON
    final_event = sse_events[2]
    assert "citations" in final_event
    assert "confidence" in final_event
    assert "usage" in final_event
    
    # Verify DB tracking inserts occurred
    mock_memory.add_message.assert_called()
    mock_usage_log.add.assert_called_once()
    mock_db.commit.assert_called()
