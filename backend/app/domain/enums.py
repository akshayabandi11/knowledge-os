import enum


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class DocStatus(str, enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class SenderRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class GeminiModel(str, enum.Enum):
    FLASH = "gemini-1.5-flash"
    PRO = "gemini-1.5-pro"
