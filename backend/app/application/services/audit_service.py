import uuid
from datetime import datetime
from typing import Optional
from app.domain.models import AuditLog
from app.domain.repositories.audit_log_repository import IAuditLogRepository

class AuditService:
    """
    Service responsible for writing write-only audit logs.
    Captures user mutations and security events.
    """
    def __init__(self, audit_repo: IAuditLogRepository):
        self.audit_repo = audit_repo

    def log_action(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        ip_address: str,
        device: str,
        status: str
    ) -> AuditLog:
        """
        Persists a security audit log record.
        """
        log_entity = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            timestamp=datetime.utcnow(),
            action=action,
            ip_address=ip_address,
            device=device,
            status=status
        )
        return self.audit_repo.add(log_entity)
