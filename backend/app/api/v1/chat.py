import uuid
from typing import List

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from app.api.deps import (
    get_chat_service,
    get_conversation_memory_service,
    get_conversation_repository,
    get_current_user,
    get_query_rewrite_service,
    get_retrieval_service,
)
from app.api.v1.dtos import (
    ChatQueryRequest,
    ChunkSearchResponse,
    MessageResponse,
    QueryRewriteRequest,
    SearchQueryRequest,
)
from app.application.services.chat_service import ChatService
from app.application.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.application.services.query_rewrite_service import QueryRewriteService
from app.application.services.retrieval_service import RetrievalService
from app.core.exceptions import EntityNotFoundError
from app.domain.models import User
from app.domain.repositories.conversation_repository import IConversationRepository

router = APIRouter(prefix="/chat", tags=["RAG Chat & Search System"])


@router.post("/stream")
def stream_chat_endpoint(
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Core RAG Conversational streaming endpoint.
    Returns Server-Sent Events (SSE) token-by-token alongside citation payloads.
    """
    # Enforces database transaction boundaries inside generator
    generator = chat_service.stream_chat(
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        collection_id=payload.collection_id,
        user_query=payload.query,
        preferred_model=payload.preferred_model,
        temperature=payload.temperature,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.post("/rewrite", response_model=str)
def rewrite_query_endpoint(
    payload: QueryRewriteRequest,
    current_user: User = Depends(get_current_user),
    query_rewrite_service: QueryRewriteService = Depends(get_query_rewrite_service),
    memory_service: ConversationMemoryService = Depends(
        get_conversation_memory_service
    ),
):
    """
    Utility preprocessor. Normalizes questions resolving pronouns using history.
    """
    history_str = memory_service.get_history_as_string(
        payload.conversation_id, max_messages=8
    )
    return query_rewrite_service.rewrite_query(payload.query, history_str)


@router.post("/search", response_model=List[ChunkSearchResponse])
def hybrid_search_endpoint(
    payload: SearchQueryRequest,
    current_user: User = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Utility hybrid retrieval search endpoint.
    Performs Vector + Keyword FTS search fusion and returns ranked chunks.
    """
    results = retrieval_service.retrieve_context(
        collection_id=payload.collection_id, query=payload.query, limit=payload.limit
    )

    response_list = []
    for chunk, score in results:
        response_list.append(
            ChunkSearchResponse(
                document_id=chunk.document_id,
                content=chunk.content,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                score=score,
            )
        )
    return response_list


@router.get("/history/{conversation_id}", response_model=List[MessageResponse])
def get_chat_history_endpoint(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conv_repo: IConversationRepository = Depends(get_conversation_repository),
):
    """
    Retrieves complete past messages list for the conversation ID.
    """
    conv = conv_repo.get_by_id_and_user_id(conversation_id, current_user.id)
    if not conv:
        raise EntityNotFoundError("Conversation not found or access denied.")

    return conv_repo.get_messages(conversation_id)


@router.delete("/history/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_endpoint(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conv_repo: IConversationRepository = Depends(get_conversation_repository),
):
    """
    Permanently deletes conversation index and all its chat messages.
    """
    conv = conv_repo.get_by_id_and_user_id(conversation_id, current_user.id)
    if not conv:
        raise EntityNotFoundError("Conversation not found or access denied.")

    conv_repo.delete(conversation_id)
    conv_repo.db.commit()  # Flush use-case database transition boundaries
    return Response(status_code=status.HTTP_204_NO_CONTENT)
