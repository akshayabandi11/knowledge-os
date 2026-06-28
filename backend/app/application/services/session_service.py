import uuid
from datetime import datetime
from typing import List, Optional
from app.domain.models import Session
from app.domain.repositories.session_repository import ISessionRepository
from app.core.exceptions import SessionNotFoundError, Forbidden


class SessionService:
    """
    Service responsible for managing user login sessions.
    Coordinates creation, validation, active lists, and session revoking.
    """

    def __init__(self, session_repo: ISessionRepository):
        self.session_repo = session_repo

    def create_session(
        self,
        user_id: uuid.UUID,
        token_family: uuid.UUID,
        device_name: Optional[str],
        browser: Optional[str],
        operating_system: Optional[str],
        ip_address: str,
    ) -> Session:
        """
        Registers a new user session on successful logins.
        """
        session_entity = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
            login_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            token_family=token_family,
            revoked=False,
            created_at=datetime.utcnow(),
        )
        return self.session_repo.add(session_entity)

    def get_active_sessions(self, user_id: uuid.UUID) -> List[Session]:
        """
        Retrieves all non-revoked sessions belonging to the user.
        """
        return self.session_repo.get_active_by_user_id(user_id)

    def update_activity(self, token_family: uuid.UUID) -> None:
        """
        Updates the last activity timestamp of the session tied to the token family.
        """
        session = self.session_repo.get_by_token_family(token_family)
        if session and not session.revoked:
            session.last_activity = datetime.utcnow()
            self.session_repo.update(session)

    def revoke_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Revokes a specific session. Verifies user owns the session before revoking.
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError("Session not found.")

        if session.user_id != user_id:
            raise PermissionDeniedError("Cannot terminate another user's session.")

        session.revoked = True
        self.session_repo.update(session)

        # Revoke associated refresh token family
        # We trigger cascade invalidation of refresh tokens by revoking the token family
        from app.infrastructure.repositories.sqlalchemy_user import (
            SQLAlchemyUserRepository,
        )

        # To keep DI clean, we let session service revoke the family on repository
        # (This is handled by AuthService or TokenService cascade, but revoking the family here is safe)
        self.session_repo.revoke_by_family(session.token_family)

    def revoke_by_family(self, token_family: uuid.UUID) -> None:
        """
        Revokes session tied to specific token family.
        """
        self.session_repo.revoke_by_family(token_family)

    def revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        """
        Revokes all active sessions for the user (logout from all devices).
        """
        self.session_repo.revoke_all_by_user_id(user_id)
