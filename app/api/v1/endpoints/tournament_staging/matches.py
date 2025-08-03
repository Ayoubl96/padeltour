from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.tournament_staging_service import TournamentStagingService
from app.services.match_scheduling_service import MatchSchedulingService

router = APIRouter()

# Match generation endpoints
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

@router.post("/group/{group_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_group_matches(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Generate matches for a specific group. This is a wrapper around the stage-level endpoint.
    """
    scheduling_service = MatchSchedulingService(db)
    staging_service = TournamentStagingService(db)
    
    # Get the group to find its stage
    group = staging_service.get_group_by_id(group_id, current_company.id)
    stage_id = group.stage_id
    
    # Generate matches for the entire stage
    matches = staging_service.generate_stage_matches(stage_id, current_company.id)
    
    # Return only the matches for this specific group (now using fixed ordering)
    return scheduling_service.get_group_matches(group_id, current_company.id)

@router.post("/bracket/{bracket_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_bracket_matches(
    bracket_id: int,
    couples: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Generate matches for a specific bracket. This is a wrapper around the stage-level endpoint.
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

# Match retrieval endpoints
@router.get("/stage/{stage_id}/matches", response_model=List[schemas.MatchOut])
def get_stage_matches(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get matches for a stage in proper display order"""
    scheduling_service = MatchSchedulingService(db)
    matches = scheduling_service.get_stage_matches(stage_id, current_company.id)
    
    # Sort by display_order for proper frontend ordering
    return sorted(matches, key=lambda m: (m.display_order or 999999, m.id))

@router.get("/tournament/{tournament_id}/matches", response_model=List[schemas.MatchOut])
def get_tournament_matches(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get all matches for a tournament in proper display order"""
    scheduling_service = MatchSchedulingService(db)
    matches = scheduling_service.get_tournament_matches(tournament_id, current_company.id)
    
    # Sort by display_order for proper frontend ordering
    return sorted(matches, key=lambda m: (m.display_order or 999999, m.id))

@router.get("/match/{match_id}", response_model=schemas.MatchOut)
def get_match_by_id(
    match_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get a specific match by ID"""
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