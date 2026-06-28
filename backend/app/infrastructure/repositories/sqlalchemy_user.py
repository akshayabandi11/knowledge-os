from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models import User, UserSettings, RefreshToken
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.db.models import UserModel, UserSettingsModel, RefreshTokenModel

class SQLAlchemyUserRepository(IUserRepository):
    """
    SQLAlchemy implementation of the User Repository.
    Translates raw database model responses to clean business domain entities.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.id == id).first()
        if not db_user:
            return None
        return User.model_validate(db_user)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        db_users = self.db.query(UserModel).offset(skip).limit(limit).all()
        return [User.model_validate(u) for u in db_users]

    def add(self, entity: User) -> User:
        db_user = UserModel(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            full_name=entity.full_name,
            role=entity.role,
            
            # Map security columns
            email_verified=entity.email_verified,
            verification_token=entity.verification_token,
            password_reset_token=entity.password_reset_token,
            password_reset_expires_at=entity.password_reset_expires_at,
            failed_login_attempts=entity.failed_login_attempts,
            locked_until=entity.locked_until,
            
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
        self.db.add(db_user)
        self.db.flush()
        return User.model_validate(db_user)

    def update(self, entity: User) -> User:
        db_user = self.db.query(UserModel).filter(UserModel.id == entity.id).first()
        if not db_user:
            raise ValueError(f"User with ID {entity.id} not found")
        
        db_user.email = entity.email
        db_user.hashed_password = entity.hashed_password
        db_user.full_name = entity.full_name
        db_user.role = entity.role
        
        # Update security properties
        db_user.email_verified = entity.email_verified
        db_user.verification_token = entity.verification_token
        db_user.password_reset_token = entity.password_reset_token
        db_user.password_reset_expires_at = entity.password_reset_expires_at
        db_user.failed_login_attempts = entity.failed_login_attempts
        db_user.locked_until = entity.locked_until
        db_user.updated_at = entity.updated_at
        
        self.db.flush()
        return User.model_validate(db_user)

    def delete(self, id: UUID) -> None:
        db_user = self.db.query(UserModel).filter(UserModel.id == id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.flush()

    def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not db_user:
            return None
        return User.model_validate(db_user)

    def get_user_settings(self, user_id: UUID) -> Optional[UserSettings]:
        db_settings = self.db.query(UserSettingsModel).filter(UserSettingsModel.user_id == user_id).first()
        if not db_settings:
            return None
        return UserSettings.model_validate(db_settings)

    def create_user_settings(self, settings: UserSettings) -> UserSettings:
        db_settings = UserSettingsModel(
            user_id=settings.user_id,
            preferred_model=settings.preferred_model,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            top_p=settings.top_p,
            top_k=settings.top_k,
            updated_at=settings.updated_at
        )
        self.db.add(db_settings)
        self.db.flush()
        return UserSettings.model_validate(db_settings)

    def update_user_settings(self, settings: UserSettings) -> UserSettings:
        db_settings = self.db.query(UserSettingsModel).filter(UserSettingsModel.user_id == settings.user_id).first()
        if not db_settings:
            raise ValueError(f"Settings for user {settings.user_id} not found")
        
        db_settings.preferred_model = settings.preferred_model
        db_settings.temperature = settings.temperature
        db_settings.max_output_tokens = settings.max_output_tokens
        db_settings.top_p = settings.top_p
        db_settings.top_k = settings.top_k
        db_settings.updated_at = settings.updated_at
        
        self.db.flush()
        return UserSettings.model_validate(db_settings)

    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        db_token = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token_hash == token_hash).first()
        if not db_token:
            return None
        return RefreshToken.model_validate(db_token)

    def add_refresh_token(self, token: RefreshToken) -> RefreshToken:
        db_token = RefreshTokenModel(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            token_family=token.token_family,
            expires_at=token.expires_at,
            revoked=token.revoked,
            created_at=token.created_at
        )
        self.db.add(db_token)
        self.db.flush()
        return RefreshToken.model_validate(db_token)

    def update_refresh_token(self, token: RefreshToken) -> RefreshToken:
        db_token = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.id == token.id).first()
        if not db_token:
            raise ValueError(f"Refresh token not found")
        db_token.revoked = token.revoked
        self.db.flush()
        return RefreshToken.model_validate(db_token)

    def revoke_token_family(self, token_family: UUID) -> None:
        self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token_family == token_family).update(
            {RefreshTokenModel.revoked: True}, synchronize_session=False
        )
        self.db.flush()
