from typing import Generic, TypeVar, Optional, List, Any
from uuid import UUID

T = TypeVar("T")

class IRepository(Generic[T]):
    """Generic interface for repository classes."""
    
    def get_by_id(self, id: UUID) -> Optional[T]:
        raise NotImplementedError
        
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        raise NotImplementedError
        
    def add(self, entity: T) -> T:
        raise NotImplementedError
        
    def update(self, entity: T) -> T:
        raise NotImplementedError
        
    def delete(self, id: UUID) -> None:
        raise NotImplementedError
