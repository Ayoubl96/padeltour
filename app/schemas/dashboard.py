from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


class TournamentTimelineItem(BaseModel):
    id: int
    name: str
    start_date: str
    end_date: str
    players_number: int
    status: str  # "active", "upcoming", "completed"


class NextTournament(BaseModel):
    id: int
    name: str
    start_date: str
    days_until_start: int


class LiveTournament(BaseModel):
    id: int
    name: str
    start_date: str
    end_date: str
    days_running: int


class TournamentEndingSoon(BaseModel):
    id: int
    name: str
    end_date: str
    days_remaining: int


class TournamentDetails(BaseModel):
    next_tournament: Optional[NextTournament]
    live_tournaments: List[LiveTournament]
    tournaments_ending_soon: List[TournamentEndingSoon]


class TournamentManagementOverview(BaseModel):
    active_tournaments: int
    upcoming_tournaments: int
    completed_this_month: int
    total_registered_players: int  # Total all-time registered players
    current_month_players: int     # Players registered this month
    player_change: int
    player_change_percentage: float
    matches_played_this_month: int  # Changed from matches_played_today
    pending_matches: int
    tournament_capacity_utilization: float  # Changed from court_utilization_rate
    tournament_timeline: List[TournamentTimelineItem]
    tournament_details: TournamentDetails


class StageProgress(BaseModel):
    stage_id: int
    stage_name: str
    stage_type: str
    completion_percentage: float
    order: int


class TournamentProgress(BaseModel):
    tournament_id: int
    tournament_name: str
    completion_percentage: float
    total_matches: int
    completed_matches: int
    stages_progress: List[StageProgress]


class MatchStatusDistribution(BaseModel):
    scheduled: int
    in_progress: int
    completed: int
    pending: int


class TopCouple(BaseModel):
    couple_id: int
    couple_name: str
    tournament_name: str
    matches_played: int
    matches_won: int
    win_rate: float
    total_points: int


class RealTimeTournamentProgress(BaseModel):
    tournament_progress: List[TournamentProgress]
    match_status_distribution: MatchStatusDistribution
    top_performing_couples: List[TopCouple]


class MatchResultsDistribution(BaseModel):
    wins: int
    draws: int
    time_expired: int
    forfeited: int


class MatchCourtAnalytics(BaseModel):
    # Removed matches_per_day_30d as requested
    average_match_duration_minutes: int
    court_efficiency_matches_per_court_per_day: int
    peak_playing_hours: Dict[str, int]  # hour -> match count
    match_results_distribution: MatchResultsDistribution


class ActivePlayer(BaseModel):
    player_id: int
    name: str
    tournament_count: int


class PerformingCouple(BaseModel):
    couple_id: int
    couple_name: str
    tournament_name: str
    matches_played: int
    win_rate: float
    total_points: int


class PlayerRegistrationTrends(BaseModel):
    current_month: int
    last_month: int
    change: int


class PlayerCouplePerformance(BaseModel):
    most_active_players: List[ActivePlayer]
    best_performing_couples: List[PerformingCouple]
    player_level_distribution: Dict[str, int]  # level -> count
    player_registration_trends: PlayerRegistrationTrends


class UpcomingMatch(BaseModel):
    match_id: int
    tournament_name: str
    couple1_name: str
    couple2_name: str
    scheduled_start: Optional[str]
    court_name: Optional[str]


class ConflictMatch(BaseModel):
    match_id: int
    tournament: str
    start_time: str
    end_time: str


class CourtConflict(BaseModel):
    court_name: str
    conflict_matches: List[ConflictMatch]


class TournamentDeadline(BaseModel):
    tournament_id: int
    tournament_name: str
    end_date: str
    days_remaining: int


class SystemAlerts(BaseModel):
    court_conflicts: int
    incomplete_matches: int
    upcoming_deadlines: int
    matches_next_24h: int


class OperationalDashboard(BaseModel):
    upcoming_matches_24h: List[UpcomingMatch]  # Now only shows scheduled matches
    court_conflicts: List[CourtConflict]
    incomplete_match_results: int
    tournament_deadlines: List[TournamentDeadline]
    system_alerts: SystemAlerts


class DashboardResponse(BaseModel):
    tournament_management: TournamentManagementOverview
    real_time_progress: RealTimeTournamentProgress
    match_court_analytics: MatchCourtAnalytics
    player_performance: PlayerCouplePerformance
    operational_dashboard: OperationalDashboard
    generated_at: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }