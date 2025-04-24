from app.schemas.base import *


class CourtBase(BaseModel):
    id: int
    name: str
    images: List[HttpUrl]

    class Config:
        orm_mode = True 