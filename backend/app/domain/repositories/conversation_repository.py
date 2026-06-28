import abc
from typing import List, Optional
from uuid import UUID
from app.domain.models import Conversation, Message
from app.domain.repositories.base import IRepository

class IConversationRepository(IRepository[Conversation], abc.ABC):
    @abc.abstractmethod
    def get_by_user_id(self, user_id: UUID) -> List[Conversation]:
        """Fetch all conversations belonging to a specific user."""
        pass

    @abc.abstractmethod
    def get_messages(self, conversation_id: UUID, limit: int = 50) -> List[Message]:
        """Fetch message history for a specific conversation ID."""
        pass

    @abc.abstractmethod
    def add_message(self, message: Message) -> Message:
        """Append a new user or assistant message to conversation history."""
        pass

    @abc.abstractmethod
    def get_by_id_and_user_id(self, conversation_id: UUID, user_id: UUID) -> Optional[Conversation]:
        """Fetch conversation details checking ownership validation."""
        pass
