import abc
from typing import Optional, List
from uuid import UUID
from app.domain.models import User, UserSettings, RefreshToken
from app.domain.repositories.base import IRepository

class IUserRepository(IRepository[User], abc.ABC):
    @abc.abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user profile matching specified email address."""
        pass

    @abc.abstractmethod
    def get_user_settings(self, user_id: UUID) -> Optional[UserSettings]:
        """Fetch settings configurations for a user."""
        pass

    @abc.abstractmethod
    def create_user_settings(self, settings: UserSettings) -> UserSettings:
        """Initialize settings configurations for a user."""
        pass

    @abc.abstractmethod
    def update_user_settings(self, settings: UserSettings) -> UserSettings:
        """Update configurations settings for a user."""
        pass

    @abc.abstractmethod
    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Fetch refresh token using its encrypted hash."""
        pass

    @abc.abstractmethod
    def add_refresh_token(self, token: RefreshToken) -> RefreshToken:
        """Persist fresh refresh token in database store."""
        pass

    @abc.abstractmethod
    def update_refresh_token(self, token: RefreshToken) -> RefreshToken:
        """Update properties of an existing refresh token."""
        pass

    @abc.abstractmethod
    def revoke_token_family(self, token_family: UUID) -> None:
        """Revoke all tokens associated with a specific family UUID."""
        pass
