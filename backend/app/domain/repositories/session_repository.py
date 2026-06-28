import abc
from typing import List, Optional
from uuid import UUID

from app.domain.models import Session
from app.domain.repositories.base import IRepository


class ISessionRepository(IRepository[Session], abc.ABC):
    @abc.abstractmethod
    def get_active_by_user_id(self, user_id: UUID) -> List[Session]:
        """Fetch all active (non-revoked) sessions for a user."""
        pass

    @abc.abstractmethod
    def get_by_token_family(self, token_family: UUID) -> Optional[Session]:
        """Fetch session matching a specified token family UUID."""
        pass

    @abc.abstractmethod
    def revoke_by_family(self, token_family: UUID) -> None:
        """Mark session associated with token family as revoked."""
        pass

    @abc.abstractmethod
    def revoke_all_by_user_id(self, user_id: UUID) -> None:
        """Mark all active sessions for a user as revoked."""
        pass
