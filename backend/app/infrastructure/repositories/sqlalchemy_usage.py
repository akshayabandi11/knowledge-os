from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models import AIUsageLog
from app.domain.repositories.usage_log_repository import IUsageLogRepository
from app.infrastructure.db.models import AIUsageLogModel

class SQLAlchemyUsageLogRepository(IUsageLogRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[AIUsageLog]:
        db_log = self.db.query(AIUsageLogModel).filter(AIUsageLogModel.id == id).first()
        if not db_log:
            return None
        return AIUsageLog.model_validate(db_log)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[AIUsageLog]:
        db_logs = self.db.query(AIUsageLogModel).order_by(AIUsageLogModel.timestamp.desc()).offset(skip).limit(limit).all()
        return [AIUsageLog.model_validate(l) for l in db_logs]

    def add(self, entity: AIUsageLog) -> AIUsageLog:
        db_log = AIUsageLogModel(
            id=entity.id,
            user_id=entity.user_id,
            request_id=entity.request_id,
            model=entity.model,
            prompt_tokens=entity.prompt_tokens,
            completion_tokens=entity.completion_tokens,
            total_tokens=entity.total_tokens,
            estimated_cost=entity.estimated_cost,
            response_time_ms=entity.response_time_ms,
            status=entity.status,
            timestamp=entity.timestamp
        )
        self.db.add(db_log)
        self.db.flush()
        return AIUsageLog.model_validate(db_log)

    def update(self, entity: AIUsageLog) -> AIUsageLog:
        raise NotImplementedError("AI usage logs are write-only and cannot be updated.")

    def delete(self, id: UUID) -> None:
        raise NotImplementedError("AI usage logs are write-only and cannot be deleted.")

    def get_by_user_id(self, user_id: UUID, limit: int = 100) -> List[AIUsageLog]:
        db_logs = self.db.query(AIUsageLogModel).filter(
            AIUsageLogModel.user_id == user_id
        ).order_by(AIUsageLogModel.timestamp.desc()).limit(limit).all()
        return [AIUsageLog.model_validate(l) for l in db_logs]
