from app.schemas.base import *


class PlayersBase(BaseModel):
    nickname: str
    gender: int

    class Config:
        orm_mode = True


class PlayerOut(BaseModel):
    id: int
    nickname: str
    gender: int

    class Config:
        orm_mode = True


class PlayerOutFull(PlayerOut):
    name: Optional[str] = None
    surname: Optional[str] = None
    number: Optional[int] = None
    email: Optional[str] = None
    playtomic_id: Optional[int] = None
    level: Optional[int] = None
    picture: Optional[Union[List[HttpUrl], HttpUrl]] = None


class PlayerCompany(BaseModel):
    company_id: int
    player_id: int


class PlayerPlaytomic(BaseModel):
    user_id: int
    gender: int

    class Config:
        orm_mode = True 