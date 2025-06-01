from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, date, timezone

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.tournament_staging_service import TournamentStagingService
from app.services.match_scheduling_service import MatchSchedulingService
from app.services.couple_stats_service import CoupleStatsService
from app.core.constants import StageType, BracketType, AssignmentMethod

router = APIRouter()

# Stage endpoints
@router.post("/tournament/{tournament_id}/stage", response_model=schemas.TournamentStageOut, status_code=status.HTTP_201_CREATED)
def create_tournament_stage(
    tournament_id: int,
    stage_data: schemas.TournamentStageCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.create_stage(
        tournament_id=tournament_id,
        company_id=current_company.id,
        name=stage_data.name,
        stage_type=stage_data.stage_type,
        order=stage_data.order,
        config=stage_data.config
    )

@router.get("/tournament/{tournament_id}/stage", response_model=List[schemas.TournamentStageOut])
def get_tournament_stages(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_tournament_stages(tournament_id, current_company.id)

@router.get("/stage/{stage_id}", response_model=schemas.TournamentStageOut)
def get_stage_by_id(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_stage_by_id(stage_id, current_company.id)

@router.put("/stage/{stage_id}", response_model=schemas.TournamentStageOut)
def update_tournament_stage(
    stage_id: int,
    stage_data: schemas.TournamentStageUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    update_data = stage_data.dict(exclude_unset=True)
    return staging_service.update_stage(stage_id, current_company.id, update_data)

@router.delete("/stage/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    staging_service.delete_stage(stage_id, current_company.id)
    return None

# Group endpoints
@router.post("/stage/{stage_id}/group", response_model=schemas.TournamentGroupOut, status_code=status.HTTP_201_CREATED)
def create_tournament_group(
    stage_id: int,
    group_data: schemas.TournamentGroupCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.create_group(
        stage_id=stage_id,
        company_id=current_company.id,
        name=group_data.name
    )

@router.get("/stage/{stage_id}/group", response_model=List[schemas.TournamentGroupOut])
def get_stage_groups(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_stage_groups(stage_id, current_company.id)

@router.get("/group/{group_id}", response_model=schemas.TournamentGroupOut)
def get_group_by_id(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_group_by_id(group_id, current_company.id)

@router.put("/group/{group_id}", response_model=schemas.TournamentGroupOut)
def update_tournament_group(
    group_id: int,
    group_data: schemas.TournamentGroupUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.update_group(group_id, current_company.id, group_data.name)

@router.delete("/group/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    staging_service.delete_group(group_id, current_company.id)
    return None

# Group couple assignment endpoints
@router.post("/group/{group_id}/couple", response_model=schemas.TournamentGroupCoupleOut, status_code=status.HTTP_201_CREATED)
def add_couple_to_group(
    group_id: int,
    couple_data: schemas.TournamentGroupCoupleCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.add_couple_to_group(
        group_id=group_id,
        couple_id=couple_data.couple_id,
        company_id=current_company.id
    )

@router.get("/group/{group_id}/couple", response_model=List[schemas.TournamentCoupleOut])
def get_group_couples(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_group_couples(group_id, current_company.id)

@router.delete("/group/{group_id}/couple/{couple_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_couple_from_group(
    group_id: int,
    couple_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    staging_service.remove_couple_from_group(group_id, couple_id, current_company.id)
    return None

@router.post("/stage/{stage_id}/assign-couples", response_model=List[schemas.TournamentGroupCoupleOut])
def assign_couples_to_groups(
    stage_id: int,
    method: Optional[str] = Query(AssignmentMethod.RANDOM, description="Assignment method"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.assign_couples_to_groups(stage_id, current_company.id, method)

# Group standings endpoint
@router.get("/group/{group_id}/standings", response_model=schemas.GroupStandings)
def get_group_standings(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    group = staging_service.get_group_by_id(group_id, current_company.id)
    standings = staging_service.calculate_group_standings(group_id, current_company.id)
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "standings": standings
    }

# Bracket endpoints
@router.post("/stage/{stage_id}/bracket", response_model=schemas.TournamentBracketOut, status_code=status.HTTP_201_CREATED)
def create_tournament_bracket(
    stage_id: int,
    bracket_data: schemas.TournamentBracketCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.create_bracket(
        stage_id=stage_id,
        company_id=current_company.id,
        bracket_type=bracket_data.bracket_type
    )

@router.get("/stage/{stage_id}/bracket", response_model=List[schemas.TournamentBracketOut])
def get_stage_brackets(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_stage_brackets(stage_id, current_company.id)

@router.get("/bracket/{bracket_id}", response_model=schemas.TournamentBracketOut)
def get_bracket_by_id(
    bracket_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.get_bracket_by_id(bracket_id, current_company.id)

@router.put("/bracket/{bracket_id}", response_model=schemas.TournamentBracketOut)
def update_tournament_bracket(
    bracket_id: int,
    bracket_data: schemas.TournamentBracketUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.update_bracket(bracket_id, current_company.id, bracket_data.bracket_type)

@router.delete("/bracket/{bracket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_bracket(
    bracket_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    staging_service.delete_bracket(bracket_id, current_company.id)
    return None

# Match generation endpoint at the stage level
@router.post("/stage/{stage_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_stage_matches(
    stage_id: int,
    couples: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Generate matches for a stage. Works for both group stages and elimination stages.
    For group stages, it generates matches for all groups.
    For elimination stages, it generates matches for the main bracket.
    """
    staging_service = TournamentStagingService(db)
    return staging_service.generate_stage_matches(stage_id, current_company.id, couples)

# Match retrieval endpoints
@router.get("/stage/{stage_id}/matches", response_model=List[schemas.MatchOut])
def get_stage_matches(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_stage_matches(stage_id, current_company.id)

@router.get("/tournament/{tournament_id}/matches", response_model=List[schemas.MatchOut])
def get_tournament_matches(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_tournament_matches(tournament_id, current_company.id)

@router.get("/group/{group_id}/matches", response_model=List[schemas.MatchOut])
def get_group_matches(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_group_matches(group_id, current_company.id)

@router.get("/bracket/{bracket_id}/matches", response_model=List[schemas.MatchOut])
def get_bracket_matches(
    bracket_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_bracket_matches(bracket_id, current_company.id)

@router.get("/match/{match_id}", response_model=schemas.MatchOut)
def get_match_by_id(
    match_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_match_by_id(match_id, current_company.id)

@router.put("/match/{match_id}", response_model=schemas.MatchOut)
def update_match(
    match_id: int,
    match_data: schemas.MatchUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Update a match (including results) - this will automatically update couple statistics"""
    from app.services.match_service import MatchService
    
    # Validate match ownership through scheduling service first
    scheduling_service = MatchSchedulingService(db)
    match = scheduling_service.get_match_by_id(match_id, current_company.id)
    
    # Use MatchService to update the match (which includes couple stats updates)
    match_service = MatchService(db)
    return match_service.update_match(match_id, match_data)

# Match generation and scheduling endpoints
@router.post("/group/{group_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_group_matches(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Generate matches for a specific group. This is now a wrapper around the stage-level endpoint.
    """
    scheduling_service = MatchSchedulingService(db)
    staging_service = TournamentStagingService(db)
    
    # Get the group to find its stage
    group = staging_service.get_group_by_id(group_id, current_company.id)
    stage_id = group.stage_id
    
    # Generate matches for the entire stage
    matches = staging_service.generate_stage_matches(stage_id, current_company.id)
    
    # Return only the matches for this specific group
    return scheduling_service.get_group_matches(group_id, current_company.id)

@router.post("/match/{match_id}/schedule", response_model=schemas.MatchOut)
def schedule_match(
    match_id: int,
    court_id: int,
    start_time: datetime,
    end_time: Optional[datetime] = None,
    is_time_limited: bool = False,
    time_limit_minutes: Optional[int] = None,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.schedule_match(
        match_id=match_id,
        company_id=current_company.id,
        court_id=court_id,
        start_time=start_time,
        end_time=end_time,
        is_time_limited=is_time_limited,
        time_limit_minutes=time_limit_minutes
    )

@router.delete("/match/{match_id}/schedule", response_model=schemas.MatchOut)
def unschedule_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.unschedule_match(match_id, current_company.id)

@router.get("/tournament/{tournament_id}/court-availability", response_model=List[dict])
def get_court_availability(
    tournament_id: int,
    date: date,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    # Convert date to datetime
    date_as_datetime = datetime.combine(date, datetime.min.time())
    
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_court_availability(tournament_id, current_company.id, date_as_datetime)

@router.post("/tournament/{tournament_id}/auto-schedule", response_model=List[schemas.MatchOut])
def auto_schedule_matches(
    tournament_id: int,
    start_date: Optional[str] = None,  # Make it optional for order-only mode
    end_date: Optional[str] = None,
    order_only: bool = False,  # Add order-only parameter
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Auto-schedule matches for a tournament.
    
    - order_only: If True, only assign courts and sequence order without specific times.
    - start_date: Required if order_only=False. Date in YYYY-MM-DD format or ISO datetime.
    - end_date: Optional end date in YYYY-MM-DD format or ISO datetime.
    """
    scheduling_service = MatchSchedulingService(db)
    
    # If order_only mode is requested, don't need date parameters
    if order_only:
        return scheduling_service.auto_order_matches(tournament_id, current_company.id)
        
    # For timed scheduling, we need at least a start date
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date is required for timed scheduling. Use order_only=True for order-only scheduling."
        )
        
    try:
        # Parse dates as naive datetime objects (no timezone)
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        # Strip timezone info to make it naive
        start_datetime = start_datetime.replace(tzinfo=None)
        
        end_datetime = None
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Strip timezone info to make it naive
            end_datetime = end_datetime.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
        )
        
    return scheduling_service.auto_schedule_matches(
        tournament_id=tournament_id,
        company_id=current_company.id,
        start_date=start_datetime,
        end_date=end_datetime,
        order_only=order_only
    )

@router.post("/bracket/{bracket_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_bracket_matches(
    bracket_id: int,
    couples: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Generate matches for a specific bracket. This is now a wrapper around the stage-level endpoint.
    """
    scheduling_service = MatchSchedulingService(db)
    staging_service = TournamentStagingService(db)
    
    # Get the bracket to find its stage
    bracket = staging_service.get_bracket_by_id(bracket_id, current_company.id)
    stage_id = bracket.stage_id
    
    # Generate matches for the entire stage, specifying couples if provided
    matches = staging_service.generate_stage_matches(stage_id, current_company.id, couples)
    
    # Return only the matches for this specific bracket
    return scheduling_service.get_bracket_matches(bracket_id, current_company.id)

# Couple Stats endpoints
@router.get("/tournament/{tournament_id}/stats", response_model=List[schemas.CoupleStatsOut])
def get_tournament_stats(
    tournament_id: int,
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get couple statistics for a tournament"""
    couple_stats_service = CoupleStatsService(db)
    stats = couple_stats_service.get_tournament_stats(tournament_id, group_id)
    
    # Convert to output format and add position
    result = []
    for i, stat in enumerate(stats, 1):
        stat_out = schemas.CoupleStatsOut.from_orm(stat)
        stat_out.position = i
        result.append(stat_out)
    
    return result

@router.get("/couple/{couple_id}/tournament/{tournament_id}/stats", response_model=schemas.CoupleStatsOut)
def get_couple_stats(
    couple_id: int,
    tournament_id: int,
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get statistics for a specific couple in a tournament"""
    couple_stats_service = CoupleStatsService(db)
    stats = couple_stats_service.get_couple_stats(couple_id, tournament_id, group_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couple stats not found"
        )
    
    return schemas.CoupleStatsOut.from_orm(stats)

@router.post("/tournament/{tournament_id}/stats/recalculate", status_code=status.HTTP_200_OK)
def recalculate_tournament_stats(
    tournament_id: int,
    group_id: Optional[int] = Query(None, description="Recalculate for specific group only"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Recalculate all couple statistics for a tournament"""
    from app.services.match_service import MatchService
    
    match_service = MatchService(db)
    match_service.recalculate_tournament_stats(tournament_id, group_id)
    
    return {"message": "Tournament statistics recalculated successfully"}

@router.post("/tournament/{tournament_id}/stats/initialize", status_code=status.HTTP_200_OK)
def initialize_missing_couple_stats(
    tournament_id: int,
    group_id: Optional[int] = Query(None, description="Initialize for specific group only"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Initialize missing couple statistics for a tournament (useful for existing tournaments)"""
    from app.services.match_service import MatchService
    
    match_service = MatchService(db)
    result = match_service.ensure_couple_stats_exist(tournament_id, group_id)
    
    return {
        "message": "Couple statistics initialized successfully",
        "details": result
    }

@router.get("/group/{group_id}/standings", response_model=schemas.GroupStandings)
def get_group_standings_with_stats(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get group standings with detailed couple statistics"""
    staging_service = TournamentStagingService(db)
    couple_stats_service = CoupleStatsService(db)
    
    # Get the group
    group = staging_service.get_group_by_id(group_id, current_company.id)
    
    # Get couple stats for this group
    stats = couple_stats_service.get_tournament_stats(group.stage.tournament_id, group_id)
    
    # Sort by ranking criteria
    sorted_stats = sorted(
        stats,
        key=lambda s: (
            s.total_points,
            s.games_won - s.games_lost,
            s.games_won,
            s.matches_won
        ),
        reverse=True
    )
    
    # Convert to standings entries
    standings_entries = []
    for i, stat in enumerate(sorted_stats, 1):
        entry = schemas.GroupStandingsEntry(
            couple_id=stat.couple_id,
            couple_name=stat.couple.name if stat.couple else f"Couple {stat.couple_id}",
            matches_played=stat.matches_played,
            matches_won=stat.matches_won,
            matches_lost=stat.matches_lost,
            matches_drawn=stat.matches_drawn,
            games_won=stat.games_won,
            games_lost=stat.games_lost,
            total_points=stat.total_points,
            position=i
        )
        standings_entries.append(entry)
    
    return schemas.GroupStandings(
        group_id=group_id,
        group_name=group.name,
        standings=standings_entries
    )

@router.get("/tournament/{tournament_id}/standings", response_model=schemas.TournamentStandingsOut)
def get_tournament_standings(
    tournament_id: int,
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get complete tournament standings"""
    from app.models.tournament import Tournament, TournamentGroup
    
    couple_stats_service = CoupleStatsService(db)
    
    # Get tournament
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    if tournament.company_id != current_company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to this tournament"
        )
    
    # Get group info if specified
    group_name = None
    if group_id:
        group = db.query(TournamentGroup).filter(TournamentGroup.id == group_id).first()
        if group:
            group_name = group.name
    
    # Get stats
    stats = couple_stats_service.get_tournament_stats(tournament_id, group_id)
    
    # Sort by ranking criteria
    sorted_stats = sorted(
        stats,
        key=lambda s: (
            s.total_points,
            s.games_won - s.games_lost,
            s.games_won,
            s.matches_won
        ),
        reverse=True
    )
    
    # Convert to output format with positions
    stats_out = []
    for i, stat in enumerate(sorted_stats, 1):
        stat_out = schemas.CoupleStatsOut.from_orm(stat)
        stat_out.position = i
        stats_out.append(stat_out)
    
    return schemas.TournamentStandingsOut(
        tournament_id=tournament_id,
        tournament_name=tournament.name,
        group_id=group_id,
        group_name=group_name,
        stats=stats_out,
        last_updated=datetime.now()
    ) 