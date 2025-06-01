from app.schemas.base import *


class PlayersBase(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    nickname: Optional[str] = None
    class Config:
        from_attributes = True


class PlayerOut(PlayersBase):
    id: int
    picture: Optional[Union[str, List[str]]] = None
    
    class Config:
        from_attributes = True


class PlayerOutFull(PlayersBase):
    id: int
    name: Optional[str] = None
    surname: Optional[str] = None
    nickname: Optional[str] = None
    number: Optional[int] = None
    email: Optional[str] = None
    picture: Optional[Union[str, List[str]]] = None
    playtomic_id: Optional[int] = None
    level: Optional[int] = None
    gender: Optional[int] = None


class PlayerCompany(BaseModel):
    player_id: int
    company_id: int


class PlayerPlaytomic(BaseModel):
    playtomic_id: int
    name: str
    
    class Config:
        from_attributes = True 