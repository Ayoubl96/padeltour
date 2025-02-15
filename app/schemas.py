from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import Union, List, Optional


class CompanyBase(BaseModel):
    email: str
    password: str
    phone_number: str
    name: str
    address: str

    class Config:
        orm_mode = True


class CompanyOut(BaseModel):
    id: int
    login: str
    name: str
    address: str
    email: EmailStr
    phone_number: str
    created_at: datetime

    class Config:
        orm_mode = True


class CourtBase(BaseModel):
    name: str
    images: List[HttpUrl]

    class Config:
        orm_mode = True

class TournamentBase(BaseModel):
    name: str
    description: str
    images: List[HttpUrl]
    start_date: datetime
    end_date: datetime
    players_number: int

    class Config:
        orm_mode = True

class TournamentOut(BaseModel):
    id: int
    name: str
    description: str
    images: List[HttpUrl]
    company_id: int
    start_date: datetime
    end_date: datetime
    players_number: int

    class Config:
        orm_mode = True

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
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
