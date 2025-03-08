from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import Union, List, Optional, Any


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
    description: Optional[str] = None
    images: Optional[List[str]] = None
    start_date: datetime
    end_date: datetime
    players_number: int
    full_description: Optional[Any] = None

    class Config:
        orm_mode = True

class TournamentOut(TournamentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    players_number: Optional[int] = None
    full_description: Optional[Any] = None

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

class TournamentPlayerBase(BaseModel):
    tournament_id: int
    player_id: int

class TournamentPlayerCreate(TournamentPlayerBase):
    pass

class TournamentPlayerOut(TournamentPlayerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    player: PlayerOutFull

    class Config:
        from_attributes = True


class TournamentCoupleCreate(BaseModel):
    first_player_id: int
    second_player_id: int
    name: str

class TournamentCoupleOut(BaseModel):
    id: int
    tournament_id: int
    first_player_id: int
    second_player_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    name: str
    # Include related data
    first_player: Optional[PlayerOutFull] = None
    second_player: Optional[PlayerOutFull] = None

    class Config:
        orm_mode = True

class TournamentCoupleOutSimple(BaseModel):
    id: int
    tournament_id: int
    first_player_id: int
    second_player_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    name: str

    class Config:
        orm_mode = True

class TournamentCoupleUpdate(BaseModel):
    tournament_id: Optional[int] = None
    first_player_id: Optional[int] = None
    second_player_id: Optional[int] = None
    name: Optional[str] = None



class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
