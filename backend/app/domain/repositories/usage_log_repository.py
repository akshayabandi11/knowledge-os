import abc
from typing import List
from uuid import UUID
from app.domain.models import AIUsageLog
from app.domain.repositories.base import IRepository


class IUsageLogRepository(IRepository[AIUsageLog], abc.ABC):
    @abc.abstractmethod
    def get_by_user_id(self, user_id: UUID, limit: int = 100) -> List[AIUsageLog]:
        """Fetch tracking analytic usage metrics recorded for a user."""
        pass
