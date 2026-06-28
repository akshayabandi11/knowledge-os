import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt

from app.core.config import settings
from app.core.exceptions import (
    TokenExpired,
    TokenRevoked,
    TokenReuseDetected,
    AuthenticationError,
)
from app.domain.models import RefreshToken
from app.domain.repositories.user_repository import IUserRepository


class TokenService:
    """
    Service responsible for creating, parsing, and validating JWT access tokens,
    managing refresh token lifecycles, and implementing Token Family Rotation.
    """

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM

    def create_access_token(
        self, user_id: uuid.UUID, role: str, token_family: uuid.UUID
    ) -> str:
        """
        Generates a short-lived access JWT token.
        """
        payload = {
            "sub": str(user_id),
            "role": role,
            "token_family": str(token_family),
            "type": "access",
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self, user_id: uuid.UUID, token_family: uuid.UUID
    ) -> tuple[str, RefreshToken]:
        """
        Generates a long-lived refresh JWT token and returns both the raw token string
        and its database domain representation.
        """
        token_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        payload = {
            "sub": str(user_id),
            "jti": str(token_id),
            "token_family": str(token_family),
            "type": "refresh",
            "exp": expires_at,
            "iat": datetime.utcnow(),
        }
        raw_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        token_hash = self._hash_token(raw_token)

        token_entity = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            token_family=token_family,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.utcnow(),
        )
        return raw_token, token_entity

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Decodes and validates signature, type, and expiration of access tokens.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                raise AuthenticationError("Invalid token type. Access token expected.")
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpired("Access token expired.")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid access token.")

    def rotate_refresh_token(self, raw_refresh_token: str) -> tuple[str, str]:
        """
        Implements Token Family Rotation.
        If a refresh token is reused, invalidates the entire token family session immediately.
        Returns a new (access_token, refresh_token) pair.
        """
        try:
            payload = jwt.decode(
                raw_refresh_token, self.secret_key, algorithms=[self.algorithm]
            )
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type. Refresh token expected.")
        except jwt.ExpiredSignatureError:
            raise TokenExpired("Refresh token expired. Please log in again.")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid refresh token.")

        user_id = uuid.UUID(payload["sub"])
        token_family = uuid.UUID(payload["token_family"])
        token_hash = self._hash_token(raw_refresh_token)

        # Retrieve token record from DB
        token_record = self.user_repo.get_refresh_token(token_hash)

        # Security Threat: Reuse Detection
        if not token_record or token_record.revoked:
            # If the token is revoked, someone is trying to reuse a previously rotated token!
            # Revoke entire token family to block the breach
            self.user_repo.revoke_token_family(token_family)
            logger_message = (
                f"Refresh token reuse detected! Revoking token family: {token_family}"
            )
            # Logger import deferred to avoid circular references
            from app.core.logging import logger

            logger.warning(logger_message)
            raise TokenReuseDetected(
                "Token reuse detected. All sessions associated with this key have been revoked."
            )

        # Revoke the used token
        token_record.revoked = True
        self.user_repo.update_refresh_token(token_record)

        # Generate new credentials under same token family
        new_raw_refresh, new_token_entity = self.create_refresh_token(
            user_id, token_family
        )
        self.user_repo.add_refresh_token(new_token_entity)

        # Load user role to bind to access token claims
        user = self.user_repo.get_by_id(user_id)
        role = user.role.value if user else "USER"

        new_access = self.create_access_token(user_id, role, token_family)
        return new_access, new_raw_refresh

    def revoke_token_family(self, token_family: uuid.UUID) -> None:
        """
        Revokes an entire token family (invaliding all rotated refresh tokens).
        """
        self.user_repo.revoke_token_family(token_family)

    def _hash_token(self, token: str) -> str:
        """
        Hashes token value securely using SHA-256 before writing to database.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
