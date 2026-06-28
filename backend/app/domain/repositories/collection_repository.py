import abc
from typing import List, Optional
from uuid import UUID
from app.domain.models import Collection
from app.domain.repositories.base import IRepository


class ICollectionRepository(IRepository[Collection], abc.ABC):
    @abc.abstractmethod
    def get_by_user_id(self, user_id: UUID) -> List[Collection]:
        """Fetch all collections belonging to a specific user."""
        pass

    @abc.abstractmethod
    def get_by_id_and_user_id(
        self, collection_id: UUID, user_id: UUID
    ) -> Optional[Collection]:
        """Fetch a specific collection checking ownership constraints."""
        pass
