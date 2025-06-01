from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.match_service import MatchService
from app.schemas.tournament import MatchCreate, MatchUpdate, MatchOut as MatchRead

router = APIRouter()

@router.get("/{match_id}", response_model=MatchRead)
def get_match(
    match_id: int,
    service: MatchService = Depends()
):
    """Get a specific match by ID"""
    return service.get_match(match_id)

@router.get("/tournament/{tournament_id}", response_model=List[MatchRead])
def get_matches_by_tournament(
    tournament_id: int,
    round_number: Optional[int] = None,
    service: MatchService = Depends()
):
    """Get matches for a tournament, optionally filtered by round"""
    if round_number is not None:
        return service.get_matches_by_round(tournament_id, round_number)
    return service.get_matches_by_tournament(tournament_id)

@router.get("/team/{team_id}", response_model=List[MatchRead])
def get_matches_by_team(
    team_id: int,
    service: MatchService = Depends()
):
    """Get all matches for a specific team"""
    return service.get_matches_by_team(team_id)

@router.get("/tournament/{tournament_id}/unscheduled", response_model=List[MatchRead])
def get_unscheduled_matches(
    tournament_id: int,
    service: MatchService = Depends()
):
    """Get all unscheduled matches for a tournament"""
    return service.get_unscheduled_matches(tournament_id)

@router.get("/tournament/{tournament_id}/scheduled", response_model=List[MatchRead])
def get_scheduled_matches(
    tournament_id: int,
    service: MatchService = Depends()
):
    """Get all scheduled matches for a tournament"""
    return service.get_scheduled_matches(tournament_id)

@router.post("/", response_model=MatchRead)
def create_match(
    match_data: MatchCreate,
    service: MatchService = Depends()
):
    """Create a new match"""
    return service.create_match(match_data)

@router.put("/{match_id}", response_model=MatchRead)
def update_match(
    match_id: int,
    match_data: MatchUpdate,
    service: MatchService = Depends()
):
    """Update an existing match"""
    return service.update_match(match_id, match_data)

@router.delete("/{match_id}", status_code=204)
def delete_match(
    match_id: int,
    service: MatchService = Depends()
):
    """Delete a match"""
    service.delete_match(match_id)
    return None 