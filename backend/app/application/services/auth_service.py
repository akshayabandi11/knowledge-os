import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session as SqlSession

from app.application.services.audit_service import AuditService
from app.application.services.password_service import PasswordService
from app.application.services.session_service import SessionService
from app.application.services.token_service import TokenService
from app.core.exceptions import (
    AccountLocked,
    InvalidCredentials,
    UserNotFoundError,
    ValidationError,
)
from app.core.logging import logger
from app.domain.enums import GeminiModel, UserRole
from app.domain.models import User, UserSettings
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.db.models import UserModel


class AuthService:
    """
    Main authentication orchestrator.
    Manages accounts, failed login lockouts, password resets, and audit integration.
    """

    def __init__(
        self,
        db: SqlSession,
        user_repo: IUserRepository,
        password_service: PasswordService,
        token_service: TokenService,
        session_service: SessionService,
        audit_service: AuditService,
    ):
        self.db = db
        self.user_repo = user_repo
        self.password_service = password_service
        self.token_service = token_service
        self.session_service = session_service
        self.audit_service = audit_service

    def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str],
        ip_address: str,
        device: str,
    ) -> User:
        """
        Validates password strength, hashes password, saves new user,
        initializes profile settings, and writes an audit log.
        """
        # Check if email is unique
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            self.audit_service.log_action(
                None, "REGISTER", ip_address, device, "FAILED_EMAIL_TAKEN"
            )
            raise ValidationError("Email address is already registered.")

        # Validate password rules
        self.password_service.validate_password_strength(password)

        # Generate encryption hashes
        hashed_password = self.password_service.hash_password(password)
        verification_token = str(uuid.uuid4())
        user_id = uuid.uuid4()

        user_entity = User(
            id=user_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.USER,
            email_verified=False,
            verification_token=verification_token,
            password_reset_token=None,
            password_reset_expires_at=None,
            failed_login_attempts=0,
            locked_until=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Add user and initialize default configuration settings
        added_user = self.user_repo.add(user_entity)

        default_settings = UserSettings(
            user_id=user_id,
            preferred_model=GeminiModel.FLASH,
            temperature=0.20,
            max_output_tokens=2048,
            top_p=0.95,
            top_k=40,
            updated_at=datetime.utcnow(),
        )
        self.user_repo.create_user_settings(default_settings)

        # Flush/Commit transaction boundary inside the use case
        self.db.commit()

        self.audit_service.log_action(
            user_id, "REGISTER", ip_address, device, "SUCCESS"
        )

        # Mocking email delivery (Log details in development console)
        logger.info(
            f"[SECURITY] Email Verification link generated for {email}: /verify-email?token={verification_token}"
        )

        return added_user

    def login_user(
        self,
        email: str,
        password: str,
        device_name: Optional[str],
        browser: Optional[str],
        operating_system: Optional[str],
        ip_address: str,
        user_agent_str: str,
    ) -> Tuple[str, str, User]:
        """
        Validates credentials, implements lockouts on repeated failures,
        starts family rotation sessions, and generates JWT credentials.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            self.audit_service.log_action(
                None, "LOGIN_FAILED", ip_address, user_agent_str, "USER_NOT_FOUND"
            )
            raise InvalidCredentials("Invalid email or password.")

        # Check Account Lockout State
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            self.audit_service.log_action(
                user.id, "ACCOUNT_LOCKED", ip_address, user_agent_str, "BLOCKED"
            )
            locked_duration_min = int(
               (user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
)
            raise AccountLocked(
                f"Account locked due to consecutive failures. Try again in {locked_duration_min} minutes."
            )

        # Verify Password credentials
        is_valid_pw = self.password_service.verify_password(
            password, user.hashed_password
        )
        if not is_valid_pw:
            # Increment lockout counter
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                # Lockout account for 15 minutes
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                self.audit_service.log_action(
                    user.id, "ACCOUNT_LOCKED", ip_address, user_agent_str, "LOCKED"
                )
                logger.warning(
                    f"[SECURITY] Account locked for email: {email} due to successive failures."
                )

            self.user_repo.update(user)
            self.db.commit()

            self.audit_service.log_action(
                user.id, "LOGIN_FAILED", ip_address, user_agent_str, "BAD_PASSWORD"
            )
            raise InvalidCredentials("Invalid email or password.")

        # Check if email is verified (optional security flag, standard warning)
        # We don't block login for MVP, but log warning details
        if not user.email_verified:
            logger.warning(f"[SECURITY] Unverified email logged in: {email}")

        # Reset lockout trackers on success
        user.failed_login_attempts = 0
        user.locked_until = None
        self.user_repo.update(user)

        # Generate fresh token rotation family and credentials
        token_family = uuid.uuid4()
        access_token = self.token_service.create_access_token(
            user.id, user.role.value, token_family
        )
        raw_refresh_token, token_entity = self.token_service.create_refresh_token(
            user.id, token_family
        )

        # Save refresh token
        self.user_repo.add_refresh_token(token_entity)

        # Save session tracking details
        self.session_service.create_session(
            user_id=user.id,
            token_family=token_family,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
        )

        self.db.commit()

        self.audit_service.log_action(
            user.id, "LOGIN_SUCCESS", ip_address, user_agent_str, "SUCCESS"
        )
        return access_token, raw_refresh_token, user

    def logout_user(
        self, user_id: uuid.UUID, token_family: uuid.UUID, ip_address: str, device: str
    ) -> None:
        """
        Revokes the active refresh token family and terminates the associated session.
        """
        self.token_service.revoke_token_family(token_family)
        self.session_service.revoke_by_family(token_family)
        self.db.commit()

        self.audit_service.log_action(user_id, "LOGOUT", ip_address, device, "SUCCESS")

    def logout_all_sessions(
        self, user_id: uuid.UUID, ip_address: str, device: str
    ) -> None:
        """
        Revokes all active sessions and refresh tokens for a user.
        """
        # Revoke all sessions
        self.session_service.revoke_all_sessions(user_id)
        # Fetch active refresh token families for user and revoke them
        # (This is handled by SQL Session revoke query inside SessionRepository cascading to families)
        self.db.commit()

        self.audit_service.log_action(
            user_id, "LOGOUT_ALL", ip_address, device, "SUCCESS"
        )

    def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
        ip_address: str,
        device: str,
    ) -> None:
        """
        Verifies old password strength, validates new password complexity,
        hashes new password, updates database record, and writes audit logs.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User profile not found.")

        # Check old password matches
        if not self.password_service.verify_password(
            old_password, user.hashed_password
        ):
            self.audit_service.log_action(
                user_id,
                "PASSWORD_CHANGED",
                ip_address,
                device,
                "FAILED_BAD_OLD_PASSWORD",
            )
            raise ValidationError("Existing password provided is incorrect.")

        # Validate new password complexity rules
        self.password_service.validate_password_strength(new_password)

        user.hashed_password = self.password_service.hash_password(new_password)
        user.updated_at = datetime.utcnow()

        self.user_repo.update(user)
        self.db.commit()

        self.audit_service.log_action(
            user_id, "PASSWORD_CHANGED", ip_address, device, "SUCCESS"
        )

    def forgot_password(self, email: str, ip_address: str, device: str) -> None:
        """
        Generates a reset token if the email exists.
        Simulates email notification by writing token URL to logger console.
        """
        user = self.user_repo.get_by_email(email)
        # Avoid user enumeration attacks: respond identically if email not found
        if not user:
            self.audit_service.log_action(
                None, "PASSWORD_RESET_REQUESTED", ip_address, device, "SUCCESS"
            )
            logger.info(
                f"[SECURITY] Forgot password requested for non-existent email: {email}"
            )
            return

        reset_token = str(uuid.uuid4())
        user.password_reset_token = reset_token
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)

        self.user_repo.update(user)
        self.db.commit()

        self.audit_service.log_action(
            user.id, "PASSWORD_RESET_REQUESTED", ip_address, device, "SUCCESS"
        )
        logger.info(
            f"[SECURITY] Password reset link generated for {email}: /reset-password?token={reset_token}"
        )

    def reset_password(
        self, token: str, new_password: str, ip_address: str, device: str
    ) -> None:
        """
        Finds user by reset token, checks expiration, hashes new password,
        and invalidates reset token properties.
        """
        # Scan user table for matching token
        # In a real environment, we'd add an IUserRepository method get_by_reset_token,
        # but scanning all users is avoided by executing a session query
        db_user = (
            self.db.query(UserModel)
            .filter(UserModel.password_reset_token == token)
            .first()
        )

        if not db_user:
            raise ValidationError("Invalid or expired password reset token.")

        user = User.model_validate(db_user)

        if (
            not user.password_reset_expires_at
            or user.password_reset_expires_at < datetime.utcnow()
        ):
            raise ValidationError("Password reset token has expired.")

        self.password_service.validate_password_strength(new_password)

        user.hashed_password = self.password_service.hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        user.updated_at = datetime.utcnow()

        self.user_repo.update(user)
        self.db.commit()

        self.audit_service.log_action(
            user.id, "PASSWORD_RESET", ip_address, device, "SUCCESS"
        )

    def verify_email(self, token: str, ip_address: str, device: str) -> None:
        """
        Validates email verification token and marks profile as verified.
        """
        db_user = (
            self.db.query(UserModel)
            .filter(UserModel.verification_token == token)
            .first()
        )

        if not db_user:
            raise ValidationError("Invalid email verification token.")

        user = User.model_validate(db_user)
        user.email_verified = True
        user.verification_token = None
        user.updated_at = datetime.utcnow()

        self.user_repo.update(user)
        self.db.commit()

        self.audit_service.log_action(
            user.id, "EMAIL_VERIFICATION", ip_address, device, "SUCCESS"
        )
