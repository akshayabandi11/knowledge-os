from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import Conversation, Message
from app.domain.repositories.conversation_repository import IConversationRepository
from app.infrastructure.db.models import ConversationModel, MessageModel


class SQLAlchemyConversationRepository(IConversationRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[Conversation]:
        db_conv = (
            self.db.query(ConversationModel).filter(ConversationModel.id == id).first()
        )
        if not db_conv:
            return None
        return Conversation.model_validate(db_conv)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        db_convs = self.db.query(ConversationModel).offset(skip).limit(limit).all()
        return [Conversation.model_validate(c) for c in db_convs]

    def add(self, entity: Conversation) -> Conversation:
        db_conv = ConversationModel(
            id=entity.id,
            collection_id=entity.collection_id,
            user_id=entity.user_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.db.add(db_conv)
        self.db.flush()
        return Conversation.model_validate(db_conv)

    def update(self, entity: Conversation) -> Conversation:
        db_conv = (
            self.db.query(ConversationModel)
            .filter(ConversationModel.id == entity.id)
            .first()
        )
        if not db_conv:
            raise ValueError(f"Conversation {entity.id} not found")
        db_conv.title = entity.title
        db_conv.updated_at = entity.updated_at
        self.db.flush()
        return Conversation.model_validate(db_conv)

    def delete(self, id: UUID) -> None:
        db_conv = (
            self.db.query(ConversationModel).filter(ConversationModel.id == id).first()
        )
        if db_conv:
            self.db.delete(db_conv)
            self.db.flush()

    def get_by_user_id(self, user_id: UUID) -> List[Conversation]:
        db_convs = (
            self.db.query(ConversationModel)
            .filter(ConversationModel.user_id == user_id)
            .order_by(ConversationModel.created_at.desc())
            .all()
        )
        return [Conversation.model_validate(c) for c in db_convs]

    def get_messages(self, conversation_id: UUID, limit: int = 50) -> List[Message]:
        db_msgs = (
            self.db.query(MessageModel)
            .filter(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
            .all()
        )
        return [Message.model_validate(m) for m in db_msgs]

    def add_message(self, message: Message) -> Message:
        db_msg = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at,
        )
        self.db.add(db_msg)
        self.db.flush()
        return Message.model_validate(db_msg)

    def get_by_id_and_user_id(
        self, conversation_id: UUID, user_id: UUID
    ) -> Optional[Conversation]:
        db_conv = (
            self.db.query(ConversationModel)
            .filter(
                ConversationModel.id == conversation_id,
                ConversationModel.user_id == user_id,
            )
            .first()
        )
        if not db_conv:
            return None
        return Conversation.model_validate(db_conv)
