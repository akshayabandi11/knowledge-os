from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models import AuditLog
from app.domain.repositories.audit_log_repository import IAuditLogRepository
from app.infrastructure.db.models import AuditLogModel


class SQLAlchemyAuditLogRepository(IAuditLogRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[AuditLog]:
        db_log = self.db.query(AuditLogModel).filter(AuditLogModel.id == id).first()
        if not db_log:
            return None
        return AuditLog.model_validate(db_log)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        db_logs = (
            self.db.query(AuditLogModel)
            .order_by(AuditLogModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [AuditLog.model_validate(l) for l in db_logs]

    def add(self, entity: AuditLog) -> AuditLog:
        db_log = AuditLogModel(
            id=entity.id,
            user_id=entity.user_id,
            timestamp=entity.timestamp,
            action=entity.action,
            ip_address=entity.ip_address,
            device=entity.device,
            status=entity.status,
        )
        self.db.add(db_log)
        self.db.flush()
        return AuditLog.model_validate(db_log)

    def update(self, entity: AuditLog) -> AuditLog:
        raise NotImplementedError("Audit logs are write-only and cannot be updated.")

    def delete(self, id: UUID) -> None:
        raise NotImplementedError("Audit logs are write-only and cannot be deleted.")

    def get_by_user_id(self, user_id: UUID, limit: int = 100) -> List[AuditLog]:
        db_logs = (
            self.db.query(AuditLogModel)
            .filter(AuditLogModel.user_id == user_id)
            .order_by(AuditLogModel.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [AuditLog.model_validate(l) for l in db_logs]
