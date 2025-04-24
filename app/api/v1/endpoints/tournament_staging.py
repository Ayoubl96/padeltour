from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.tournament_staging_service import TournamentStagingService
from app.services.match_scheduling_service import MatchSchedulingService
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

@router.post("/bracket/{bracket_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_bracket_matches(
    bracket_id: int,
    couples: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    staging_service = TournamentStagingService(db)
    return staging_service.generate_bracket_matches(bracket_id, current_company.id, couples)

# Match generation and scheduling endpoints
@router.post("/group/{group_id}/generate-matches", response_model=List[schemas.MatchOut])
def generate_group_matches(
    group_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.generate_group_matches(group_id, current_company.id)

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
    start_date: date,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    # Convert dates to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = None
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.auto_schedule_matches(
        tournament_id=tournament_id,
        company_id=current_company.id,
        start_date=start_datetime,
        end_date=end_datetime
    ) 