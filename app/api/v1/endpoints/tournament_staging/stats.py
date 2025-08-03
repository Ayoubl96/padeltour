from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.couple_stats_service import CoupleStatsService

router = APIRouter()

# Couple statistics endpoints
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

# Tournament standings endpoints
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