from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.tournament_staging_service import TournamentStagingService
from app.services.couple_stats_service import CoupleStatsService
from app.core.constants import AssignmentMethod

router = APIRouter()

@router.post("/stage/{stage_id}/group", response_model=schemas.TournamentGroupOut, status_code=status.HTTP_201_CREATED)
def create_tournament_group(
    stage_id: int,
    group_data: schemas.TournamentGroupCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Create a new group in a stage"""
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
    """Get all groups for a stage"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_stage_groups(stage_id, current_company.id)

@router.get("/group/{group_id}", response_model=schemas.TournamentGroupOut)
def get_group_by_id(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get a specific group by ID"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_group_by_id(group_id, current_company.id)

@router.put("/group/{group_id}", response_model=schemas.TournamentGroupOut)
def update_tournament_group(
    group_id: int,
    group_data: schemas.TournamentGroupUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Update a tournament group"""
    staging_service = TournamentStagingService(db)
    return staging_service.update_group(group_id, current_company.id, group_data.name)

@router.delete("/group/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Delete a tournament group"""
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
    """Add a couple to a group"""
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
    """Get all couples in a group"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_group_couples(group_id, current_company.id)

@router.delete("/group/{group_id}/couple/{couple_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_couple_from_group(
    group_id: int,
    couple_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Remove a couple from a group"""
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
    """Automatically assign couples to groups in a stage"""
    staging_service = TournamentStagingService(db)
    return staging_service.assign_couples_to_groups(stage_id, current_company.id, method)

# Group standings endpoints
@router.get("/group/{group_id}/standings", response_model=schemas.GroupStandings)
def get_group_standings(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get basic group standings"""
    staging_service = TournamentStagingService(db)
    group = staging_service.get_group_by_id(group_id, current_company.id)
    standings = staging_service.calculate_group_standings(group_id, current_company.id)
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "standings": standings
    }

@router.get("/group/{group_id}/standings/detailed", response_model=schemas.GroupStandings)
def get_group_standings_with_stats(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get detailed group standings with complete statistics"""
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