from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models import Collection
from app.domain.repositories.collection_repository import ICollectionRepository
from app.infrastructure.db.models import CollectionModel

class SQLAlchemyCollectionRepository(ICollectionRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[Collection]:
        db_coll = self.db.query(CollectionModel).filter(CollectionModel.id == id).first()
        if not db_coll:
            return None
        return Collection.model_validate(db_coll)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Collection]:
        db_colls = self.db.query(CollectionModel).offset(skip).limit(limit).all()
        return [Collection.model_validate(c) for c in db_colls]

    def add(self, entity: Collection) -> Collection:
        db_coll = CollectionModel(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
        self.db.add(db_coll)
        self.db.flush()
        return Collection.model_validate(db_coll)

    def update(self, entity: Collection) -> Collection:
        db_coll = self.db.query(CollectionModel).filter(CollectionModel.id == entity.id).first()
        if not db_coll:
            raise ValueError(f"Collection {entity.id} not found")
        db_coll.name = entity.name
        db_coll.description = entity.description
        db_coll.updated_at = entity.updated_at
        self.db.flush()
        return Collection.model_validate(db_coll)

    def delete(self, id: UUID) -> None:
        db_coll = self.db.query(CollectionModel).filter(CollectionModel.id == id).first()
        if db_coll:
            self.db.delete(db_coll)
            self.db.flush()

    def get_by_user_id(self, user_id: UUID) -> List[Collection]:
        db_colls = self.db.query(CollectionModel).filter(CollectionModel.user_id == user_id).all()
        return [Collection.model_validate(c) for c in db_colls]

    def get_by_id_and_user_id(self, collection_id: UUID, user_id: UUID) -> Optional[Collection]:
        db_coll = self.db.query(CollectionModel).filter(
            CollectionModel.id == collection_id, 
            CollectionModel.user_id == user_id
        ).first()
        if not db_coll:
            return None
        return Collection.model_validate(db_coll)
