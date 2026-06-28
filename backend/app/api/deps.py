import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.services.audit_service import AuditService
from app.application.services.auth_service import AuthService
from app.application.services.authorization_service import AuthorizationService
from app.application.services.chat_service import ChatService
from app.application.services.chunking_service import ChunkingService
from app.application.services.citation_service import CitationService
from app.application.services.confidence_service import ConfidenceService
from app.application.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.application.services.document_service import DocumentService
from app.application.services.embedding_service import EmbeddingService
from app.application.services.fusion_service import FusionService
from app.application.services.keyword_search_service import KeywordSearchService
from app.application.services.parsing_service import ParsingService
from app.application.services.password_service import PasswordService
from app.application.services.prompt_builder_service import PromptBuilderService

# Phase 4 RAG Services
from app.application.services.query_rewrite_service import QueryRewriteService
from app.application.services.reranker_service import RerankerService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.session_service import SessionService

# Services
from app.application.services.storage_service import StorageService
from app.application.services.token_service import TokenService
from app.application.services.vector_search_service import VectorSearchService
from app.core.config import settings
from app.core.exceptions import Unauthorized
from app.core.logging import user_id_var
from app.domain.enums import UserRole
from app.domain.models import User
from app.domain.repositories.audit_log_repository import IAuditLogRepository
from app.domain.repositories.collection_repository import ICollectionRepository
from app.domain.repositories.conversation_repository import IConversationRepository
from app.domain.repositories.document_repository import IDocumentRepository
from app.domain.repositories.session_repository import ISessionRepository
from app.domain.repositories.usage_log_repository import IUsageLogRepository

# Repositories Abstractions
from app.domain.repositories.user_repository import IUserRepository

# AI Embedding Providers
from app.infrastructure.ai.embedding_provider import (
    BaseEmbeddingProvider,
    GeminiEmbeddingProvider,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.sqlalchemy_audit import (
    SQLAlchemyAuditLogRepository,
)
from app.infrastructure.repositories.sqlalchemy_collection import (
    SQLAlchemyCollectionRepository,
)
from app.infrastructure.repositories.sqlalchemy_conversation import (
    SQLAlchemyConversationRepository,
)
from app.infrastructure.repositories.sqlalchemy_document import (
    SQLAlchemyDocumentRepository,
)
from app.infrastructure.repositories.sqlalchemy_session import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.sqlalchemy_usage import (
    SQLAlchemyUsageLogRepository,
)

# Concrete Repositories
from app.infrastructure.repositories.sqlalchemy_user import SQLAlchemyUserRepository

# Storage Providers
from app.infrastructure.storage.base import IStorageProvider
from app.infrastructure.storage.local import LocalStorageProvider
from app.infrastructure.storage.s3 import S3StorageProvider

# --- Security Mappings ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Repository Injection ---


def get_user_repository(db: Session = Depends(get_db)) -> IUserRepository:
    return SQLAlchemyUserRepository(db)


def get_collection_repository(db: Session = Depends(get_db)) -> ICollectionRepository:
    return SQLAlchemyCollectionRepository(db)


def get_document_repository(db: Session = Depends(get_db)) -> IDocumentRepository:
    return SQLAlchemyDocumentRepository(db)


def get_audit_log_repository(db: Session = Depends(get_db)) -> IAuditLogRepository:
    return SQLAlchemyAuditLogRepository(db)


def get_usage_log_repository(db: Session = Depends(get_db)) -> IUsageLogRepository:
    return SQLAlchemyUsageLogRepository(db)


def get_session_repository(db: Session = Depends(get_db)) -> ISessionRepository:
    return SQLAlchemySessionRepository(db)


def get_conversation_repository(
    db: Session = Depends(get_db),
) -> IConversationRepository:
    return SQLAlchemyConversationRepository(db)


# --- Storage Provider Injection ---


def get_storage_provider() -> IStorageProvider:
    if settings.STORAGE_PROVIDER == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()


# --- AI Embedding Provider Injection ---


def get_embedding_provider() -> BaseEmbeddingProvider:
    return GeminiEmbeddingProvider()


# --- Service Injection ---


def get_storage_service(
    provider: IStorageProvider = Depends(get_storage_provider),
) -> StorageService:
    return StorageService(provider)


def get_parsing_service() -> ParsingService:
    return ParsingService()


def get_chunking_service() -> ChunkingService:
    return ChunkingService()


def get_embedding_service(
    provider: BaseEmbeddingProvider = Depends(get_embedding_provider),
) -> EmbeddingService:
    return EmbeddingService(provider)


def get_document_service(
    db: Session = Depends(get_db),
    doc_repo: IDocumentRepository = Depends(get_document_repository),
    collection_repo: ICollectionRepository = Depends(get_collection_repository),
    storage_service: StorageService = Depends(get_storage_service),
    parsing_service: ParsingService = Depends(get_parsing_service),
    chunking_service: ChunkingService = Depends(get_chunking_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> DocumentService:
    return DocumentService(
        db=db,
        doc_repo=doc_repo,
        collection_repo=collection_repo,
        storage_service=storage_service,
        parsing_service=parsing_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
    )


def get_password_service() -> PasswordService:
    return PasswordService()


def get_token_service(
    user_repo: IUserRepository = Depends(get_user_repository),
) -> TokenService:
    return TokenService(user_repo)


def get_session_service(
    session_repo: ISessionRepository = Depends(get_session_repository),
) -> SessionService:
    return SessionService(session_repo)


def get_audit_service(
    audit_repo: IAuditLogRepository = Depends(get_audit_log_repository),
) -> AuditService:
    return AuditService(audit_repo)


def get_authorization_service() -> AuthorizationService:
    return AuthorizationService()


def get_auth_service(
    db: Session = Depends(get_db),
    user_repo: IUserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
    token_service: TokenService = Depends(get_token_service),
    session_service: SessionService = Depends(get_session_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuthService:
    return AuthService(
        db=db,
        user_repo=user_repo,
        password_service=password_service,
        token_service=token_service,
        session_service=session_service,
        audit_service=audit_service,
    )


# --- Phase 4 RAG Services Injection ---


def get_query_rewrite_service() -> QueryRewriteService:
    return QueryRewriteService()


def get_vector_search_service(
    doc_repo: IDocumentRepository = Depends(get_document_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> VectorSearchService:
    return VectorSearchService(doc_repo, embedding_service)


def get_keyword_search_service(
    doc_repo: IDocumentRepository = Depends(get_document_repository),
) -> KeywordSearchService:
    return KeywordSearchService(doc_repo)


def get_fusion_service() -> FusionService:
    return FusionService()


def get_reranker_service() -> RerankerService:
    return RerankerService()


def get_prompt_builder_service() -> PromptBuilderService:
    return PromptBuilderService()


def get_conversation_memory_service(
    conv_repo: IConversationRepository = Depends(get_conversation_repository),
) -> ConversationMemoryService:
    return ConversationMemoryService(conv_repo)


def get_citation_service() -> CitationService:
    return CitationService()


def get_confidence_service() -> ConfidenceService:
    return ConfidenceService()


def get_retrieval_service(
    vector_search: VectorSearchService = Depends(get_vector_search_service),
    keyword_search: KeywordSearchService = Depends(get_keyword_search_service),
    fusion: FusionService = Depends(get_fusion_service),
    reranker: RerankerService = Depends(get_reranker_service),
) -> RetrievalService:
    return RetrievalService(
        vector_search_service=vector_search,
        keyword_search_service=keyword_search,
        fusion_service=fusion,
        reranker_service=reranker,
    )


def get_chat_service(
    db: Session = Depends(get_db),
    usage_log_repo: IUsageLogRepository = Depends(get_usage_log_repository),
    query_rewrite: QueryRewriteService = Depends(get_query_rewrite_service),
    retrieval: RetrievalService = Depends(get_retrieval_service),
    prompt_builder: PromptBuilderService = Depends(get_prompt_builder_service),
    memory: ConversationMemoryService = Depends(get_conversation_memory_service),
    citation: CitationService = Depends(get_citation_service),
    confidence: ConfidenceService = Depends(get_confidence_service),
) -> ChatService:
    return ChatService(
        db=db,
        usage_log_repo=usage_log_repo,
        query_rewrite_service=query_rewrite,
        retrieval_service=retrieval,
        prompt_builder_service=prompt_builder,
        memory_service=memory,
        citation_service=citation,
        confidence_service=confidence,
    )


# --- Authentication & Authorization Request Filters ---



def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: IUserRepository = Depends(get_user_repository),
    token_service: TokenService = Depends(get_token_service),
    session_service: SessionService = Depends(get_session_service),
) -> User:
    try:
        payload = token_service.verify_access_token(token)
        user_id = uuid.UUID(payload["sub"])
        token_family = uuid.UUID(payload["token_family"])
    except Exception as e:
        raise Unauthorized(f"Authentication failed: {str(e)}") from e

    user = user_repo.get_by_id(user_id)
    if not user:
        raise Unauthorized("Authenticated user profile was not found.")

    active_sessions = session_service.get_active_sessions(user_id)
    session_families = {s.token_family for s in active_sessions}
    if token_family not in session_families:
        raise Unauthorized("Your session has expired or been terminated.")

    user_id_var.set(str(user.id))
    session_service.update_activity(token_family)

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
) -> User:
    authorization_service.authorize_role(current_user.role, UserRole.ADMIN)
    return current_user
