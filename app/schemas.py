from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import Union, List, Optional, Any, Dict


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
        from_attributes = True

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
        from_attributes = True

class TournamentCoupleOutWithPlayers(TournamentCoupleOutSimple):
    first_player: Optional[PlayerOutFull] = None
    second_player: Optional[PlayerOutFull] = None

    class Config:
        orm_mode = True
        from_attributes = True

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


# Tournament Stage Schemas
class TournamentStageBase(BaseModel):
    name: str
    description: Optional[str] = None
    stage_type: str  # 'group', 'elimination', 'round_robin', etc.
    order: int
    rules: Dict[str, Any]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class TournamentStageCreate(TournamentStageBase):
    pass


class TournamentStageOut(TournamentStageBase):
    id: int
    tournament_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TournamentStageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stage_type: Optional[str] = None
    order: Optional[int] = None
    rules: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        orm_mode = True


# Stage Group Schemas
class StageGroupBase(BaseModel):
    name: str

    class Config:
        orm_mode = True


class StageGroupCreate(StageGroupBase):
    pass


class StageGroupOut(StageGroupBase):
    id: int
    stage_id: int
    created_at: datetime
    updated_at: datetime
    group_couples: Optional[List[GroupCoupleOut]] = None

    class Config:
        orm_mode = True
        from_attributes = True


# Group Couple Schemas
class GroupCoupleBase(BaseModel):
    couple_id: int

    class Config:
        orm_mode = True


class GroupCoupleCreate(GroupCoupleBase):
    pass


class GroupCoupleOut(BaseModel):
    id: int
    couple_id: int
    group_id: int  # Keep in output schema for completeness
    created_at: datetime
    couple: Optional[TournamentCoupleOutWithPlayers] = None

    class Config:
        orm_mode = True
        from_attributes = True


# Stage Couple Stats Schemas
class StageCoupleStatsBase(BaseModel):
    matches_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    matches_drawn: int = 0
    games_won: int = 0
    games_lost: int = 0
    total_points: int = 0
    position: Optional[int] = None

    class Config:
        orm_mode = True


class StageCoupleStatsCreate(StageCoupleStatsBase):
    stage_id: int
    couple_id: int
    group_id: Optional[int] = None


class StageCoupleStatsOut(StageCoupleStatsBase):
    id: int
    stage_id: int
    couple_id: int
    group_id: Optional[int] = None
    last_updated: datetime
    couple: Optional[TournamentCoupleOutSimple] = None

    class Config:
        orm_mode = True


# Match Schemas
class MatchBase(BaseModel):
    couple1_id: int
    couple2_id: int
    games: Union[List[Dict[str, Any]], Dict[str, Any]] = []
    bracket_position: Optional[str] = None
    court_id: Optional[int] = None
    match_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class MatchCreate(MatchBase):
    stage_id: Optional[int] = None
    group_id: Optional[int] = None
    winner_couple_id: Optional[int] = None


class MatchUpdate(BaseModel):
    stage_id: Optional[int] = None
    group_id: Optional[int] = None
    couple1_id: Optional[int] = None
    couple2_id: Optional[int] = None
    winner_couple_id: Optional[int] = None
    court_id: Optional[int] = None
    match_date: Optional[datetime] = None
    games: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    bracket_position: Optional[str] = None

    class Config:
        orm_mode = True


class MatchOut(MatchBase):
    id: int
    tournament_id: int
    stage_id: Optional[int] = None
    group_id: Optional[int] = None
    winner_couple_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Include related data
    couple1: Optional[TournamentCoupleOutSimple] = None
    couple2: Optional[TournamentCoupleOutSimple] = None
    winner: Optional[TournamentCoupleOutSimple] = None
    stage: Optional[TournamentStageOut] = None
    group: Optional[StageGroupOut] = None
    court: Optional[CourtBase] = None

    class Config:
        orm_mode = True
