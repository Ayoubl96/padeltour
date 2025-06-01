from typing import Dict
from app.schemas.base import *
from app.schemas.player import PlayerOutFull
from app.schemas.court import CourtBase
from pydantic import validator


class TournamentBase(BaseModel):
    name: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    start_date: datetime
    end_date: datetime
    players_number: int
    full_description: Optional[Any] = None

    class Config:
        from_attributes = True


class TournamentOut(TournamentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    players_number: Optional[int] = None
    full_description: Optional[Any] = None

    class Config:
        from_attributes = True


# Tournament Stage Schemas
class TournamentStageBase(BaseModel):
    tournament_id: int
    name: str
    stage_type: str  # Using string instead of enum for flexibility
    order: int
    config: dict[str, Any]


class TournamentStageCreate(TournamentStageBase):
    pass


class TournamentStageUpdate(BaseModel):
    name: Optional[str] = None
    stage_type: Optional[str] = None
    order: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class TournamentStageOut(TournamentStageBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Tournament Group Schemas
class TournamentGroupBase(BaseModel):
    stage_id: int
    name: str


class TournamentGroupCreate(TournamentGroupBase):
    pass


class TournamentGroupUpdate(BaseModel):
    name: Optional[str] = None


class TournamentGroupOut(TournamentGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Tournament Group Couple Schemas
class TournamentGroupCoupleBase(BaseModel):
    group_id: int
    couple_id: int


class TournamentGroupCoupleCreate(TournamentGroupCoupleBase):
    pass


class TournamentGroupCoupleOut(TournamentGroupCoupleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Tournament Bracket Schemas
class TournamentBracketBase(BaseModel):
    stage_id: int
    bracket_type: str  # Using string instead of enum for flexibility


class TournamentBracketCreate(TournamentBracketBase):
    pass


class TournamentBracketUpdate(BaseModel):
    bracket_type: Optional[str] = None


class TournamentBracketOut(TournamentBracketBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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
        from_attributes = True


class TournamentCoupleUpdate(BaseModel):
    tournament_id: Optional[int] = None
    first_player_id: Optional[int] = None
    second_player_id: Optional[int] = None
    name: Optional[str] = None


# Match Schema
class MatchGameBase(BaseModel):
    game_number: int
    couple1_score: int
    couple2_score: int
    winner_id: Optional[int] = None
    duration_minutes: Optional[int] = None


class MatchBase(BaseModel):
    tournament_id: int
    couple1_id: int
    couple2_id: int
    winner_couple_id: Optional[int] = None
    games: List[Dict[str, Any]]
    stage_id: Optional[int] = None
    group_id: Optional[int] = None
    bracket_id: Optional[int] = None
    court_id: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    is_time_limited: bool = False
    time_limit_minutes: Optional[int] = None
    match_result_status: Optional[str] = None


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    winner_couple_id: Optional[int] = None
    games: Optional[List[Dict[str, Any]]] = None
    stage_id: Optional[int] = None
    group_id: Optional[int] = None
    bracket_id: Optional[int] = None
    court_id: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    is_time_limited: Optional[bool] = None
    time_limit_minutes: Optional[int] = None
    match_result_status: Optional[str] = None


class MatchOut(MatchBase):
    id: int
    created_at: datetime
    updated_at: datetime
    couple1: Optional[TournamentCoupleOutSimple] = None
    couple2: Optional[TournamentCoupleOutSimple] = None
    winner: Optional[TournamentCoupleOutSimple] = None
    court: Optional[CourtBase] = None

    class Config:
        from_attributes = True


# Tournament Court Schemas
class TournamentCourtCreate(BaseModel):
    court_id: int
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None


class TournamentCourtOut(BaseModel):
    id: int
    tournament_id: int
    court_id: int
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    court: Optional[CourtBase] = None

    class Config:
        from_attributes = True


class TournamentCourtUpdate(BaseModel):
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None


# Group Standings Schema
class GroupStandingsEntry(BaseModel):
    couple_id: int
    couple_name: str
    matches_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    matches_drawn: int = 0
    games_won: int = 0
    games_lost: int = 0
    total_points: int = 0
    position: Optional[int] = None


class GroupStandings(BaseModel):
    group_id: int
    group_name: str
    standings: List[GroupStandingsEntry]


# Couple Stats Schemas
class CoupleStatsBase(BaseModel):
    tournament_id: int
    couple_id: int
    group_id: Optional[int] = None
    matches_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    matches_drawn: int = 0
    games_won: int = 0
    games_lost: int = 0
    total_points: int = 0


class CoupleStatsOut(CoupleStatsBase):
    id: int
    last_updated: datetime
    couple: Optional[TournamentCoupleOutSimple] = None
    games_diff: Optional[int] = None
    win_percentage: Optional[float] = None
    position: Optional[int] = None

    class Config:
        from_attributes = True
    
    @validator('games_diff', always=True)
    def calculate_games_diff(cls, v, values):
        return values.get('games_won', 0) - values.get('games_lost', 0)
    
    @validator('win_percentage', always=True)
    def calculate_win_percentage(cls, v, values):
        matches_played = values.get('matches_played', 0)
        if matches_played == 0:
            return 0.0
        matches_won = values.get('matches_won', 0)
        return round((matches_won / matches_played) * 100, 2)


class CoupleStatsUpdate(BaseModel):
    matches_played: Optional[int] = None
    matches_won: Optional[int] = None
    matches_lost: Optional[int] = None
    matches_drawn: Optional[int] = None
    games_won: Optional[int] = None
    games_lost: Optional[int] = None
    total_points: Optional[int] = None


class TournamentStandingsOut(BaseModel):
    tournament_id: int
    tournament_name: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    stats: List[CoupleStatsOut]
    last_updated: datetime

    class Config:
        from_attributes = True 