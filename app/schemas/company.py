from app.schemas.base import *
from typing import Optional


class CompanyBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    players_count: Optional[int] = None
    courts_count: Optional[int] = None
    tournaments_count: Optional[int] = None

    class Config:
        from_attributes = True 