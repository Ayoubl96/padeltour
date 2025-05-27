from typing import TypeVar, Generic, Type
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db

T = TypeVar('T')

class BaseService:
    """Base class for all services"""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db 