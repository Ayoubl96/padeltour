from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.tournament_staging_service import TournamentStagingService

router = APIRouter()

@router.post("/tournament/{tournament_id}/stage", response_model=schemas.TournamentStageOut, status_code=status.HTTP_201_CREATED)
def create_tournament_stage(
    tournament_id: int,
    stage_data: schemas.TournamentStageCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Create a new tournament stage"""
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
    """Get all stages for a tournament"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_tournament_stages(tournament_id, current_company.id)

@router.get("/stage/{stage_id}", response_model=schemas.TournamentStageOut)
def get_stage_by_id(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get a specific stage by ID"""
    staging_service = TournamentStagingService(db)
    return staging_service.get_stage_by_id(stage_id, current_company.id)

@router.put("/stage/{stage_id}", response_model=schemas.TournamentStageOut)
def update_tournament_stage(
    stage_id: int,
    stage_data: schemas.TournamentStageUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Update a tournament stage"""
    staging_service = TournamentStagingService(db)
    update_data = stage_data.dict(exclude_unset=True)
    return staging_service.update_stage(stage_id, current_company.id, update_data)

@router.delete("/stage/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Delete a tournament stage"""
    staging_service = TournamentStagingService(db)
    staging_service.delete_stage(stage_id, current_company.id)
    return None