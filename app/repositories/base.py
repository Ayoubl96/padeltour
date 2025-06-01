from typing import List, Type, TypeVar, Generic, Optional, Any, Dict, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from pydantic import BaseModel

from app.models.tournament import Tournament
from app.db.database import Base

# Generic type for database models
T = TypeVar('T', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)

class EntityNotFoundError(Exception):
    """Exception raised when an entity is not found in the database"""
    pass

class UnauthorizedAccessError(Exception):
    """Exception raised when attempting to access an unauthorized resource"""
    pass

class BaseRepository(Generic[T, CreateSchemaType, UpdateSchemaType]):
    """Base class for all repositories"""
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def get(self, id: Any) -> Optional[T]:
        """Retrieve an entity by id"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self) -> List[T]:
        """Retrieve all entities of this type"""
        return self.db.query(self.model).all()
    
    def create(self, obj_in: Union[CreateSchemaType, dict]) -> T:
        """Create a new entity"""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.dict(exclude_unset=True)
            
        db_obj = self.model(**create_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: T, obj_in: Union[UpdateSchemaType, dict]) -> T:
        """Update an entity"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, db_obj: T) -> None:
        """Delete an entity"""
        self.db.delete(db_obj)
        self.db.commit()
    
    def get_by_id(self, model_class: Type[T], entity_id: int) -> Optional[T]:
        """Get an entity by ID"""
        return self.db.query(model_class).filter(model_class.id == entity_id).first()
    
    def get_by_id_with_company_check(self, model_class: Type[T], entity_id: int, company_id: int) -> T:
        """
        Get an entity by ID and verify company ownership.
        Raises appropriate exceptions if entity not found or unauthorized.
        """
        entity = self.get_by_id(model_class, entity_id)
        
        if not entity:
            raise EntityNotFoundError(f"{model_class.__name__} not found with ID {entity_id}")
        
        # Handle different entity types for company validation
        if hasattr(entity, 'company_id'):
            # Direct company_id field
            if entity.company_id != company_id:
                raise UnauthorizedAccessError(f"Unauthorized access to {model_class.__name__}")
        elif hasattr(entity, 'tournament') and hasattr(entity.tournament, 'company_id'):
            # Entity belongs to a tournament which has a company_id
            if entity.tournament.company_id != company_id:
                raise UnauthorizedAccessError(f"Unauthorized access to {model_class.__name__}")
        elif hasattr(entity, 'stage') and hasattr(entity.stage, 'tournament') and hasattr(entity.stage.tournament, 'company_id'):
            # Entity belongs to a stage which belongs to a tournament
            if entity.stage.tournament.company_id != company_id:
                raise UnauthorizedAccessError(f"Unauthorized access to {model_class.__name__}")
        
        return entity
    
    def filter(self, model_class: Type[T], **kwargs) -> List[T]:
        """Filter entities based on attribute values"""
        query = self.db.query(model_class)
        for key, value in kwargs.items():
            if hasattr(model_class, key):
                query = query.filter(getattr(model_class, key) == value)
        return query.all()
    
    def soft_delete(self, entity: T) -> T:
        """Soft delete an entity by setting its deleted_at field"""
        if hasattr(entity, 'deleted_at'):
            entity.deleted_at = datetime.now()
            self.db.commit()
            self.db.refresh(entity)
        else:
            raise ValueError(f"Entity {type(entity).__name__} doesn't support soft delete")
        return entity
    
    def convert_exception_to_http(self, exception: Exception) -> HTTPException:
        """Convert repository exceptions to appropriate HTTP exceptions"""
        if isinstance(exception, EntityNotFoundError):
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exception))
        elif isinstance(exception, UnauthorizedAccessError):
            return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exception))
        else:
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception)) 