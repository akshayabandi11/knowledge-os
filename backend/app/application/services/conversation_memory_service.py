import uuid
from datetime import datetime
from typing import List, Optional
from app.domain.models import Message
from app.domain.repositories.conversation_repository import IConversationRepository
from app.core.exceptions import ConversationError


class ConversationMemoryService:
    """
    Service responsible for managing conversation history memory,
    formatting history for prompt context, and executing token budgeting.
    """

    def __init__(self, conv_repo: IConversationRepository):
        self.conv_repo = conv_repo

    def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        citations: Optional[List[dict]] = None,
    ) -> Message:
        """
        Persists a new message in the conversation history.
        """
        try:
            message_entity = Message(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role=role,
                content=content,
                citations=citations,
                created_at=datetime.utcnow(),
            )
            return self.conv_repo.add_message(message_entity)
        except Exception as e:
            raise ConversationError(f"Failed to record message to history: {str(e)}")

    def get_history_as_string(
        self, conversation_id: uuid.UUID, max_messages: int = 10
    ) -> str:
        """
        Retrieves recent conversation messages and formats them into a clean string context:
        e.g.,
        User: Hello
        Assistant: Hello! How can I help you?
        """
        messages = self.conv_repo.get_messages(conversation_id, limit=max_messages)

        # Budgeting constraint: take only the most recent N messages
        # Since SQL returns asc, we just format the list directly
        formatted_history = []
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            formatted_history.append(f"{role_label}: {msg.content}")

        return "\n".join(formatted_history)

    def truncate_history(self, history_str: str, max_chars: int = 4000) -> str:
        """
        Simple, token-safe character truncation.
        Prevents context bloating by truncating old entries if history exceeds limits.
        """
        if len(history_str) <= max_chars:
            return history_str

        # Truncate from beginning to keep recent turns intact
        truncated = history_str[-max_chars:]
        # Align truncation cleanly to start at the next line boundary
        newline_idx = truncated.find("\n")
        if newline_idx != -1:
            return truncated[newline_idx + 1 :]
        return truncated
