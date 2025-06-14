from app.schemas.base import *


class CourtBase(BaseModel):
    id: int
    name: str
    images: Optional[List[str]] = None

    class Config:
        from_attributes = True


class CourtOut(CourtBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 