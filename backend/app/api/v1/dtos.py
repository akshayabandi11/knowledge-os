from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.domain.enums import UserRole

# --- Request DTOs ---

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Must be secure and meet complexity criteria")
    full_name: Optional[str] = Field(None, max_length=100)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: Optional[str] = Field(None, max_length=100)
    browser: Optional[str] = Field(None, max_length=100)
    operating_system: Optional[str] = Field(None, max_length=100)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)

# --- Phase 4 RAG Request DTOs ---

class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection_id: UUID
    conversation_id: UUID
    preferred_model: Optional[str] = "gemini-1.5-flash"
    temperature: Optional[float] = 0.20


class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection_id: UUID
    limit: Optional[int] = 5


class QueryRewriteRequest(BaseModel):
    query: str = Field(..., min_length=1)
    conversation_id: UUID

# --- Response DTOs ---

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    role: UserRole
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    id: UUID
    device_name: Optional[str]
    browser: Optional[str]
    operating_system: Optional[str]
    ip_address: str
    login_time: datetime
    last_activity: datetime
    
    class Config:
        from_attributes = True

# --- Phase 4 RAG Response DTOs ---

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    citations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    collection_id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChunkSearchResponse(BaseModel):
    document_id: UUID
    content: str
    page_number: Optional[int]
    chunk_index: int
    score: float
