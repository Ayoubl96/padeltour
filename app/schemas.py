from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from datetime import datetime
from typing import List


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
    type: int
    start_date: datetime
    end_date: datetime
    player_type: int
    participants: int
    is_couple: int

    class Config:
        orm_mode = True

class TournamentOut(BaseModel):
    id: int
    name: str
    description: str
    images: List[HttpUrl]
    company_id: int
    type: int
    start_date: datetime
    end_date: datetime
    player_type: int
    participants: int
    is_couple: int

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
class PlayerPlaytomic(BaseModel):
    user_id: int

    class Config:
        orm_mode = True
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
