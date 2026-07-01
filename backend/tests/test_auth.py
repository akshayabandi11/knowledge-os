from datetime import datetime
import uuid
from unittest.mock import MagicMock

import pytest

from app.application.services.audit_service import AuditService
from app.application.services.auth_service import AuthService
from app.application.services.authorization_service import AuthorizationService
from app.application.services.password_service import PasswordService
from app.application.services.session_service import SessionService
from app.application.services.token_service import TokenService
from app.core.exceptions import (
    AccountLocked,
    Forbidden,
    InvalidCredentials,
    TokenReuseDetected,
    WeakPassword,
)
from app.domain.enums import UserRole
from app.domain.models import User
from app.infrastructure.repositories.sqlalchemy_session import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.sqlalchemy_user import SQLAlchemyUserRepository

# --- Password Validation Tests ---


def test_password_validation_rules():
    pw_service = PasswordService()

    # 1. Test Weak password length
    with pytest.raises(WeakPassword) as exc:
        pw_service.validate_password_strength("Ab1!")
    assert "at least 8" in str(exc.value)

    # 2. Test missing uppercase
    with pytest.raises(WeakPassword) as exc:
        pw_service.validate_password_strength("ab1!asdfg")
    assert "uppercase" in str(exc.value)

    # 3. Test missing lowercase
    with pytest.raises(WeakPassword) as exc:
        pw_service.validate_password_strength("AB1!ASDFG")
    assert "lowercase" in str(exc.value)

    # 4. Test missing digit
    with pytest.raises(WeakPassword) as exc:
        pw_service.validate_password_strength("Ab!asdfghj")
    assert "digit" in str(exc.value)

    # 5. Test missing special character
    with pytest.raises(WeakPassword) as exc:
        pw_service.validate_password_strength("Ab1asdfghj")
    assert "special character" in str(exc.value)

    # 6. Test valid password
    pw_service.validate_password_strength("Ab1!asdfghj")  # Should pass without raises


def test_password_hash_and_verify():
    pw_service = PasswordService()
    password = "SecurePassword123!"

    hashed = pw_service.hash_password(password)
    assert hashed != password
    assert pw_service.verify_password(password, hashed) is True
    assert pw_service.verify_password("wrong_password", hashed) is False


# --- JWT & Token Service Tests ---


def test_jwt_generation_and_verification(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    token_service = TokenService(user_repo)

    user_id = uuid.uuid4()
    token_family = uuid.uuid4()

    # Create access token
    token = token_service.create_access_token(user_id, "USER", token_family)
    payload = token_service.verify_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "USER"
    assert payload["token_family"] == str(token_family)


# --- Session Service Tests ---


def test_session_lifecycle(db_session):
    sess_repo = SQLAlchemySessionRepository(db_session)
    service = SessionService(sess_repo)

    user_id = uuid.uuid4()
    user_repo = SQLAlchemyUserRepository(db_session)

    user_repo.add(
        User(
            id=user_id,
            email="session@example.com",
            hashed_password="password",
            full_name="Session User",
            role=UserRole.USER,
            email_verified=False,
            failed_login_attempts=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    token_family = uuid.uuid4()

    # Create Session
    session = service.create_session(
        user_id=user_id,
        token_family=token_family,
        device_name="Test Device",
        browser="Chrome",
        operating_system="Windows",
        ip_address="127.0.0.1",
    )

    assert session.device_name == "Test Device"
    assert session.revoked is False

    # Get Active sessions
    active = service.get_active_sessions(user_id)
    assert len(active) == 1
    assert active[0].id == session.id

    # Revoke session
    service.revoke_session(session.id, user_id)
    active_after = service.get_active_sessions(user_id)
    assert len(active_after) == 0


# --- Authorization Service Tests ---


def test_authorization_rbac():
    authz = AuthorizationService()

    # 1. Admin accessing admin page (Clearance check)
    authz.authorize_role(UserRole.ADMIN, UserRole.ADMIN)  # Should pass

    # 2. Admin accessing user page
    authz.authorize_role(UserRole.ADMIN, UserRole.USER)  # Should pass

    # 3. User accessing user page
    authz.authorize_role(UserRole.USER, UserRole.USER)  # Should pass

    # 4. User accessing admin page
    with pytest.raises(Forbidden) as exc:
        authz.authorize_role(UserRole.USER, UserRole.ADMIN)
    assert "Admin clearance is required" in str(exc.value)


# --- Auth Service Lockout & Login Integration Tests ---


def test_auth_failed_logins_lockout(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    pw_service = PasswordService()

    # Mock Token, Session, and Audit services
    mock_token = MagicMock(spec=TokenService)
    mock_session = MagicMock(spec=SessionService)
    mock_audit = MagicMock(spec=AuditService)

    auth_service = AuthService(
        db=db_session,
        user_repo=user_repo,
        password_service=pw_service,
        token_service=mock_token,
        session_service=mock_session,
        audit_service=mock_audit,
    )

    email = "lockout@example.com"
    password = "SecurePassword123!"

    # Register user
    auth_service.register_user(
        email=email,
        password=password,
        full_name="Locked User",
        ip_address="127.0.0.1",
        device="Mozilla",
    )

    # Failed logins loop to trigger lockout limit (5 attempts)
    for _ in range(4):
        with pytest.raises(InvalidCredentials):
            auth_service.login_user(
                email=email,
                password="wrongpassword",
                device_name="Device",
                browser="Chrome",
                operating_system="Windows",
                ip_address="127.0.0.1",
                user_agent_str="Mozilla",
            )

    # The 5th attempt triggers lockout
    with pytest.raises(InvalidCredentials):
        auth_service.login_user(
            email=email,
            password="wrongpassword",
            device_name="Device",
            browser="Chrome",
            operating_system="Windows",
            ip_address="127.0.0.1",
            user_agent_str="Mozilla",
        )

    # The 6th attempt should raise AccountLocked lockout warnings
    with pytest.raises(AccountLocked):
        auth_service.login_user(
            email=email,
            password=password,  # Correct password now, but account is locked!
            device_name="Device",
            browser="Chrome",
            operating_system="Windows",
            ip_address="127.0.0.1",
            user_agent_str="Mozilla",
        )


# --- Token Family Rotation & Reuse Detection Tests ---


def test_token_family_rotation_theft_detection(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    pw_service = PasswordService()
    mock_audit = MagicMock(spec=AuditService)

    token_service = TokenService(user_repo)
    session_service = SessionService(SQLAlchemySessionRepository(db_session))

    auth_service = AuthService(
        db=db_session,
        user_repo=user_repo,
        password_service=pw_service,
        token_service=token_service,
        session_service=session_service,
        audit_service=mock_audit,
    )

    email = "rotation@example.com"
    password = "SecurePassword123!"

    # Register and Login
    auth_service.register_user(email, password, "Rotation User", "127.0.0.1", "Mozilla")
    access, refresh_token_1, user = auth_service.login_user(
        email, password, "Device", "Chrome", "Windows", "127.0.0.1", "Mozilla"
    )

    # First rotation request (token rotated, refresh_token_1 becomes revoked, fresh refresh_token_2 generated)
    access_2, refresh_token_2 = token_service.rotate_refresh_token(refresh_token_1)
    assert refresh_token_1 != refresh_token_2

    # Verify first token record is now marked as revoked in database
    hashed_1 = token_service._hash_token(refresh_token_1)
    token_rec_1 = user_repo.get_refresh_token(hashed_1)
    assert token_rec_1.revoked is True

    # Verify second token is active (not revoked)
    hashed_2 = token_service._hash_token(refresh_token_2)
    token_rec_2 = user_repo.get_refresh_token(hashed_2)
    assert token_rec_2.revoked is False

    # SECURITY THREAT: Try reusing refresh_token_1 again!
    # Reusing the old rotated token must trigger TokenReuseDetected
    with pytest.raises(TokenReuseDetected):
        token_service.rotate_refresh_token(refresh_token_1)

    # Verify second token is now automatically revoked as family compromise cascade response
    token_rec_2_after = user_repo.get_refresh_token(hashed_2)
    assert token_rec_2_after.revoked is True
