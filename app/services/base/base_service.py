from typing import TypeVar, Generic, Type, List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.base import BaseRepository, EntityNotFoundError, UnauthorizedAccessError

# Generic type for models
T = TypeVar('T')

class BaseService(Generic[T]):
    """Base service class with common operations"""
    
    def __init__(self, db: Session, repository_class: Type[BaseRepository]):
        self.db = db
        self.repository = repository_class(db)
    
    def get_by_id(self, model_class: Type[T], entity_id: int) -> Optional[T]:
        """Get an entity by ID"""
        try:
            return self.repository.get_by_id(model_class, entity_id)
        except Exception as e:
            self._handle_exception(e)
    
    def get_by_id_with_company_check(self, model_class: Type[T], entity_id: int, company_id: int) -> T:
        """Get an entity by ID and verify company ownership"""
        try:
            return self.repository.get_by_id_with_company_check(model_class, entity_id, company_id)
        except Exception as e:
            self._handle_exception(e)
    
    def get_all(self, model_class: Type[T], skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities of a type with pagination"""
        try:
            return self.repository.get_all(model_class, skip, limit)
        except Exception as e:
            self._handle_exception(e)
    
    def filter(self, model_class: Type[T], **kwargs) -> List[T]:
        """Filter entities based on criteria"""
        try:
            return self.repository.filter(model_class, **kwargs)
        except Exception as e:
            self._handle_exception(e)
    
    def create(self, model_class: Type[T], **kwargs) -> T:
        """Create a new entity"""
        try:
            return self.repository.create(model_class, **kwargs)
        except Exception as e:
            self._handle_exception(e)
    
    def update(self, entity: T, update_data: Dict[str, Any]) -> T:
        """Update an existing entity"""
        try:
            return self.repository.update(entity, update_data)
        except Exception as e:
            self._handle_exception(e)
    
    def delete(self, entity: T) -> None:
        """Delete an entity"""
        try:
            self.repository.delete(entity)
        except Exception as e:
            self._handle_exception(e)
    
    def soft_delete(self, entity: T) -> T:
        """Soft delete an entity"""
        try:
            return self.repository.soft_delete(entity)
        except Exception as e:
            self._handle_exception(e)
    
    def _handle_exception(self, exception: Exception) -> None:
        """Handle exceptions by converting to HTTP exceptions"""
        if isinstance(exception, (EntityNotFoundError, UnauthorizedAccessError)):
            http_exception = self.repository.convert_exception_to_http(exception)
            raise http_exception
        else:
            # For other exceptions, re-raise
            raise exception 