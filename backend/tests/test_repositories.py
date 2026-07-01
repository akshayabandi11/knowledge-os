import uuid
from datetime import datetime

from app.domain.enums import GeminiModel, UserRole
from app.domain.models import AuditLog, Collection, User, UserSettings
from app.infrastructure.repositories.sqlalchemy_audit import (
    SQLAlchemyAuditLogRepository,
)
from app.infrastructure.repositories.sqlalchemy_collection import (
    SQLAlchemyCollectionRepository,
)
from app.infrastructure.repositories.sqlalchemy_user import SQLAlchemyUserRepository


def test_user_repository_crud(db_session):
    repo = SQLAlchemyUserRepository(db_session)
    user_id = uuid.uuid4()

    user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashedpassword123",
        full_name="John Doe",
        role=UserRole.USER,
        email_verified=False,
        failed_login_attempts=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Add User
    added = repo.add(user)
    assert added.email == "test@example.com"
    assert added.role == UserRole.USER

    # Get User
    fetched = repo.get_by_id(user_id)
    assert fetched is not None
    assert fetched.full_name == "John Doe"

    # Get User by Email
    by_email = repo.get_by_email("test@example.com")
    assert by_email is not None
    assert by_email.id == user_id

    # Update User
    by_email.full_name = "Jane Doe"
    updated = repo.update(by_email)
    assert updated.full_name == "Jane Doe"

    # Delete User
    repo.delete(user_id)
    assert repo.get_by_id(user_id) is None


def test_user_settings_configuration(db_session):
    repo = SQLAlchemyUserRepository(db_session)
    user_id = uuid.uuid4()

    user = User(
        id=user_id,
        email="settings@example.com",
        hashed_password="password",
        role=UserRole.USER,
        email_verified=False,
        failed_login_attempts=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    repo.add(user)

    settings = UserSettings(
        user_id=user_id,
        preferred_model=GeminiModel.PRO,
        temperature=0.75,
        max_output_tokens=1024,
        top_p=0.90,
        top_k=30,
        updated_at=datetime.utcnow(),
    )

    created = repo.create_user_settings(settings)
    assert created.preferred_model == GeminiModel.PRO
    assert float(created.temperature) == 0.75

    fetched = repo.get_user_settings(user_id)
    assert fetched is not None
    assert fetched.max_output_tokens == 1024

    fetched.temperature = 0.50
    updated = repo.update_user_settings(fetched)
    assert float(updated.temperature) == 0.50


def test_collection_repository(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    coll_repo = SQLAlchemyCollectionRepository(db_session)

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="coll@example.com",
        hashed_password="password",
        role=UserRole.USER,
        email_verified=False,
        failed_login_attempts=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user_repo.add(user)

    coll_id = uuid.uuid4()
    collection = Collection(
        id=coll_id,
        user_id=user_id,
        name="Study Collection",
        description="Textbooks and notes",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    added = coll_repo.add(collection)
    assert added.name == "Study Collection"

    by_user = coll_repo.get_by_user_id(user_id)
    assert len(by_user) == 1
    assert by_user[0].id == coll_id

    by_id_auth = coll_repo.get_by_id_and_user_id(coll_id, user_id)
    assert by_id_auth is not None

    # Try fetching with incorrect user ID (tenant validation check)
    assert coll_repo.get_by_id_and_user_id(coll_id, uuid.uuid4()) is None


def test_audit_logs_repository(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    audit_repo = SQLAlchemyAuditLogRepository(db_session)

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="audit@example.com",
        hashed_password="password",
        role=UserRole.USER,
        email_verified=False,
        failed_login_attempts=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user_repo.add(user)

    log = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        timestamp=datetime.utcnow(),
        action="FILE_UPLOAD",
        ip_address="127.0.0.1",
        device="Mozilla/5.0",
        status="SUCCESS",
    )

    added = audit_repo.add(log)
    assert added.action == "FILE_UPLOAD"
    assert added.status == "SUCCESS"

    user_logs = audit_repo.get_by_user_id(user_id)
    assert len(user_logs) == 1
    assert user_logs[0].action == "FILE_UPLOAD"
