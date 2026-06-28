from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

from app.domain.enums import UserRole, DocStatus, SenderRole, GeminiModel

# --- Domain Entities ---


class UserSettings(BaseModel):
    user_id: UUID
    preferred_model: GeminiModel
    temperature: float
    max_output_tokens: int
    top_p: float
    top_k: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Session(BaseModel):
    id: UUID
    user_id: UUID
    device_name: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    ip_address: str
    login_time: datetime
    last_activity: datetime
    token_family: UUID
    revoked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: UUID
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole

    # Account status & Security fields
    email_verified: bool
    verification_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires_at: Optional[datetime] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime
    settings: Optional[UserSettings] = None
    sessions: List[Session] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RefreshToken(BaseModel):
    id: UUID
    user_id: UUID
    token_hash: str
    token_family: UUID
    expires_at: datetime
    revoked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Collection(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Document(BaseModel):
    id: UUID
    collection_id: UUID
    name: str
    file_type: str
    file_size: int
    storage_key: str
    status: DocStatus
    error_message: Optional[str] = None

    # Metadata Fields
    page_count: Optional[int] = None
    language: Optional[str] = None
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    processing_time_ms: Optional[int] = None
    chunk_count: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunk(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    page_number: Optional[int] = None
    chunk_index: int
    embedding: List[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Conversation(BaseModel):
    id: UUID
    collection_id: UUID
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    id: UUID
    conversation_id: UUID
    role: SenderRole
    content: str
    citations: Optional[List[dict]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Summary(BaseModel):
    id: UUID
    document_id: UUID
    summary_text: str
    key_points: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Flashcard(BaseModel):
    id: UUID
    document_id: UUID
    front: str
    back: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizQuestion(BaseModel):
    id: UUID
    quiz_id: UUID
    question: str
    options: List[str]
    correct_option: int
    explanation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Quiz(BaseModel):
    id: UUID
    document_id: UUID
    title: str
    created_at: datetime
    questions: List[QuizQuestion] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AuditLog(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    timestamp: datetime
    action: str
    ip_address: str
    device: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class AIUsageLog(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    request_id: UUID
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    response_time_ms: int
    status: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
