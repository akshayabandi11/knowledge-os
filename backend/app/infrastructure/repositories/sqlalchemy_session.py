from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session as SqlSession
from app.domain.models import Session
from app.domain.repositories.session_repository import ISessionRepository
from app.infrastructure.db.models import SessionModel


class SQLAlchemySessionRepository(ISessionRepository):
    """
    SQLAlchemy implementation of the Session Repository.
    """

    def __init__(self, db: SqlSession):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[Session]:
        db_sess = self.db.query(SessionModel).filter(SessionModel.id == id).first()
        if not db_sess:
            return None
        return Session.model_validate(db_sess)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Session]:
        db_sess = self.db.query(SessionModel).offset(skip).limit(limit).all()
        return [Session.model_validate(s) for s in db_sess]

    def add(self, entity: Session) -> Session:
        db_sess = SessionModel(
            id=entity.id,
            user_id=entity.user_id,
            device_name=entity.device_name,
            browser=entity.browser,
            operating_system=entity.operating_system,
            ip_address=entity.ip_address,
            login_time=entity.login_time,
            last_activity=entity.last_activity,
            token_family=entity.token_family,
            revoked=entity.revoked,
            created_at=entity.created_at,
        )
        self.db.add(db_sess)
        self.db.flush()
        return Session.model_validate(db_sess)

    def update(self, entity: Session) -> Session:
        db_sess = (
            self.db.query(SessionModel).filter(SessionModel.id == entity.id).first()
        )
        if not db_sess:
            raise ValueError(f"Session {entity.id} not found")
        db_sess.last_activity = entity.last_activity
        db_sess.revoked = entity.revoked
        self.db.flush()
        return Session.model_validate(db_sess)

    def delete(self, id: UUID) -> None:
        db_sess = self.db.query(SessionModel).filter(SessionModel.id == id).first()
        if db_sess:
            self.db.delete(db_sess)
            self.db.flush()

    def get_active_by_user_id(self, user_id: UUID) -> List[Session]:
        db_sess = (
            self.db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.revoked == False)
            .order_by(SessionModel.last_activity.desc())
            .all()
        )
        return [Session.model_validate(s) for s in db_sess]

    def get_by_token_family(self, token_family: UUID) -> Optional[Session]:
        db_sess = (
            self.db.query(SessionModel)
            .filter(SessionModel.token_family == token_family)
            .first()
        )
        if not db_sess:
            return None
        return Session.model_validate(db_sess)

    def revoke_by_family(self, token_family: UUID) -> None:
        self.db.query(SessionModel).filter(
            SessionModel.token_family == token_family
        ).update({SessionModel.revoked: True}, synchronize_session=False)
        self.db.flush()

    def revoke_all_by_user_id(self, user_id: UUID) -> None:
        self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id, SessionModel.revoked == False
        ).update({SessionModel.revoked: True}, synchronize_session=False)
        self.db.flush()
