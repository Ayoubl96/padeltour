from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.match_repository import MatchRepository
from app.db.models.match import Match
from app.schemas.match import MatchCreate, MatchUpdate, MatchRead

class MatchService:
    """Service for match operations"""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.repository = MatchRepository(db)
    
    def get_match(self, match_id: int) -> MatchRead:
        """Get a match by its ID"""
        match = self.repository.get(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return MatchRead.from_orm(match)
    
    def get_matches_by_tournament(self, tournament_id: int) -> List[MatchRead]:
        """Get all matches for a specific tournament"""
        matches = self.repository.get_matches_by_tournament_id(tournament_id)
        return [MatchRead.from_orm(match) for match in matches]
    
    def get_matches_by_round(self, tournament_id: int, round_number: int) -> List[MatchRead]:
        """Get all matches for a specific tournament round"""
        matches = self.repository.get_matches_by_round(tournament_id, round_number)
        return [MatchRead.from_orm(match) for match in matches]
    
    def get_matches_by_team(self, team_id: int) -> List[MatchRead]:
        """Get all matches for a specific team"""
        matches = self.repository.get_matches_by_team(team_id)
        return [MatchRead.from_orm(match) for match in matches]
    
    def create_match(self, match_data: MatchCreate) -> MatchRead:
        """Create a new match"""
        match = self.repository.create(match_data)
        return MatchRead.from_orm(match)
    
    def update_match(self, match_id: int, match_data: MatchUpdate) -> MatchRead:
        """Update an existing match"""
        match = self.repository.update(match_id, match_data)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return MatchRead.from_orm(match)
    
    def delete_match(self, match_id: int) -> None:
        """Delete a match"""
        result = self.repository.delete(match_id)
        if not result:
            raise HTTPException(status_code=404, detail="Match not found")
    
    def get_unscheduled_matches(self, tournament_id: int) -> List[MatchRead]:
        """Get all unscheduled matches for a tournament"""
        matches = self.repository.get_unscheduled_matches(tournament_id)
        return [MatchRead.from_orm(match) for match in matches]
    
    def get_scheduled_matches(self, tournament_id: int) -> List[MatchRead]:
        """Get all scheduled matches for a tournament"""
        matches = self.repository.get_scheduled_matches(tournament_id)
        return [MatchRead.from_orm(match) for match in matches] 