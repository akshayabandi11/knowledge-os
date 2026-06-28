from typing import Any, Optional


class DomainError(Exception):
    """Base exception for all domain-related errors."""

    code: str = "INTERNAL_SERVER_ERROR"
    status_code: int = 500
    title: str = "Internal Server Error"

    def __init__(self, detail: str, payload: Optional[Any] = None):
        super().__init__(detail)
        self.detail = detail
        self.payload = payload


# --- Entity Not Found Errors ---
class EntityNotFoundError(DomainError):
    status_code: int = 404
    code: str = "ENTITY_NOT_FOUND"
    title: str = "Entity Not Found"


class UserNotFoundError(EntityNotFoundError):
    code: str = "USER_NOT_FOUND"
    title: str = "User Profile Not Found"


class CollectionNotFoundError(EntityNotFoundError):
    code: str = "COLLECTION_NOT_FOUND"
    title: str = "Collection Workspace Not Found"


class DocumentNotFoundError(EntityNotFoundError):
    code: str = "DOCUMENT_NOT_FOUND"
    title: str = "Document Not Found"


class ConversationNotFoundError(EntityNotFoundError):
    code: str = "CONVERSATION_NOT_FOUND"
    title: str = "Conversation Not Found"


class SessionNotFoundError(EntityNotFoundError):
    code: str = "SESSION_NOT_FOUND"
    title: str = "Session Not Found"


# --- Authentication & Authorization Errors ---
class AuthenticationError(DomainError):
    status_code: int = 401
    code: str = "AUTHENTICATION_FAILED"
    title: str = "Authentication Failed"


class InvalidCredentials(AuthenticationError):
    code: str = "INVALID_CREDENTIALS"
    title: str = "Invalid Credentials"


class AccountLocked(AuthenticationError):
    code: str = "ACCOUNT_LOCKED"
    title: str = "Account Lockout Warning"


class TokenExpired(AuthenticationError):
    code: str = "TOKEN_EXPIRED"
    title: str = "Authentication Token Expired"


class TokenRevoked(AuthenticationError):
    code: str = "TOKEN_REVOKED"
    title: str = "Authentication Token Revoked"


class TokenReuseDetected(AuthenticationError):
    status_code: int = 403
    code: str = "TOKEN_REUSE_DETECTED"
    title: str = "Token Reuse Attempt Detected"


class SessionExpired(AuthenticationError):
    code: str = "SESSION_EXPIRED"
    title: str = "User Session Expired"


class Unauthorized(DomainError):
    status_code: int = 401
    code: str = "UNAUTHORIZED"
    title: str = "Unauthorized Access"


class Forbidden(DomainError):
    status_code: int = 403
    code: str = "FORBIDDEN"
    title: str = "Access Forbidden"


# --- Storage Errors ---
class StorageError(DomainError):
    status_code: int = 500
    code: str = "STORAGE_ERROR"
    title: str = "Storage Interface Error"


class StorageUploadFailed(StorageError):
    code: str = "STORAGE_UPLOAD_FAILED"
    title: str = "Upload Failed"


class StorageDeletionFailed(StorageError):
    code: str = "STORAGE_DELETION_FAILED"
    title: str = "Deletion Failed"


# --- AI Provider Errors ---
class AIProviderError(DomainError):
    status_code: int = 502
    code: str = "AI_PROVIDER_ERROR"
    title: str = "AI Provider Error"


class EmbeddingGenerationFailed(AIProviderError):
    code: str = "EMBEDDING_GENERATION_FAILED"
    title: str = "Embedding Generation Failed"


class LLMCompletionFailed(AIProviderError):
    code: str = "LLM_COMPLETION_FAILED"
    title: str = "LLM Completion Failed"


class ContextLengthExceeded(AIProviderError):
    status_code: int = 400
    code: str = "CONTEXT_LENGTH_EXCEEDED"
    title: str = "Context Window Exceeded"


# --- Validation Errors ---
class ValidationError(DomainError):
    status_code: int = 400
    code: str = "VALIDATION_FAILED"
    title: str = "Validation Failed"


class WeakPassword(ValidationError):
    code: str = "WEAK_PASSWORD"
    title: str = "Weak Password Strength Rejected"


class InvalidFileTypeLimit(ValidationError):
    code: str = "INVALID_FILE_TYPE"
    title: str = "Unsupported File Type"


class FileSizeLimitExceeded(ValidationError):
    code: str = "FILE_SIZE_LIMIT_EXCEEDED"
    title: str = "File Size Limit Exceeded"


# --- Phase 4 RAG Pipeline Errors ---
class RetrievalError(DomainError):
    status_code: int = 500
    code: str = "RETRIEVAL_ERROR"
    title: str = "Document Retrieval Failed"


class NoContextFound(RetrievalError):
    status_code: int = 404
    code: str = "NO_CONTEXT_FOUND"
    title: str = "No Supporting Documents Found"


class EmbeddingError(DomainError):
    status_code: int = 502
    code: str = "EMBEDDING_ERROR"
    title: str = "Embedding Execution Failure"


class PromptBuildError(DomainError):
    status_code: int = 500
    code: str = "PROMPT_BUILD_ERROR"
    title: str = "Prompt Template Formatting Failed"


class ConversationError(DomainError):
    status_code: int = 400
    code: str = "CONVERSATION_ERROR"
    title: str = "Conversation Process Failure"


class StreamingError(DomainError):
    status_code: int = 500
    code: str = "STREAMING_ERROR"
    title: str = "Response Streaming Failed"


class CitationError(DomainError):
    status_code: int = 500
    code: str = "CITATION_ERROR"
    title: str = "Citation Extraction Failed"
