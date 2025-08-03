from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.tournament_staging_service import TournamentStagingService

router = APIRouter()

@router.post("/stage/{stage_id}/bracket", response_model=schemas.TournamentBracketOut, status_code=status.HTTP_201_CREATED)
def create_tournament_bracket(
    stage_id: int,
    bracket_data: schemas.TournamentBracketCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Create a new bracket in a stage"""
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
    """Get all brackets for a stage"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_stage_brackets(stage_id, current_company.id)

@router.get("/bracket/{bracket_id}", response_model=schemas.TournamentBracketOut)
def get_bracket_by_id(
    bracket_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get a specific bracket by ID"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_bracket_by_id(bracket_id, current_company.id)

@router.put("/bracket/{bracket_id}", response_model=schemas.TournamentBracketOut)
def update_tournament_bracket(
    bracket_id: int,
    bracket_data: schemas.TournamentBracketUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Update a tournament bracket"""
    staging_service = TournamentStagingService(db)
    return staging_service.update_bracket(bracket_id, current_company.id, bracket_data.bracket_type)

@router.delete("/bracket/{bracket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_bracket(
    bracket_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Delete a tournament bracket"""
    staging_service = TournamentStagingService(db)
    staging_service.delete_bracket(bracket_id, current_company.id)
    return None