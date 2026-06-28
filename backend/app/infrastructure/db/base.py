# Import all models so that Base.metadata has all definitions registered before Alembic runs autogenerate.
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import (
    UserModel,
    RefreshTokenModel,
    UserSettingsModel,
    CollectionModel,
    DocumentModel,
    DocumentChunkModel,
    ConversationModel,
    MessageModel,
    SummaryModel,
    FlashcardModel,
    QuizModel,
    QuizQuestionModel,
    AuditLogModel,
    AIUsageLogModel
)
# Ensure pgvector is registered
import pgvector.sqlalchemy
