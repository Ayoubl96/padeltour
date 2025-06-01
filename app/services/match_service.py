from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.match_repository import MatchRepository
from app.models.tournament import Match
from app.schemas.tournament import MatchCreate, MatchUpdate, MatchOut
from app.services.couple_stats_service import CoupleStatsService

class MatchService:
    """Service for match operations"""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.repository = MatchRepository(db)
        self.couple_stats_service = CoupleStatsService(db)
    
    def get_match(self, match_id: int) -> MatchOut:
        """Get a match by its ID"""
        match = self.repository.get(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return MatchOut.from_orm(match)
    
    def get_matches_by_tournament(self, tournament_id: int) -> List[MatchOut]:
        """Get all matches for a specific tournament"""
        matches = self.repository.get_matches_by_tournament_id(tournament_id)
        return [MatchOut.from_orm(match) for match in matches]
    
    def get_matches_by_round(self, tournament_id: int, round_number: int) -> List[MatchOut]:
        """Get all matches for a specific tournament round"""
        matches = self.repository.get_matches_by_round(tournament_id, round_number)
        return [MatchOut.from_orm(match) for match in matches]
    
    def get_matches_by_team(self, team_id: int) -> List[MatchOut]:
        """Get all matches for a specific team"""
        matches = self.repository.get_matches_by_team(team_id)
        return [MatchOut.from_orm(match) for match in matches]
    
    def create_match(self, match_data: MatchCreate) -> MatchOut:
        """Create a new match"""
        match = self.repository.create(match_data)
        
        # Always initialize couple stats when a match is created
        self.couple_stats_service.initialize_couple_stats_for_match(match)
        
        # Update couple stats if match is already completed
        if match.winner_couple_id and match.games:
            self.couple_stats_service.update_couple_stats_from_match(match)
        
        return MatchOut.from_orm(match)
    
    def update_match(self, match_id: int, match_data: MatchUpdate) -> MatchOut:
        """Update an existing match"""
        # Get the current match before update
        current_match = self.repository.get_match_by_id(match_id)
        if not current_match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Store the old match state to potentially remove its stats contribution
        old_match_had_result = current_match.winner_couple_id is not None and current_match.games
        
        # Update the match (pass the actual match object, not the ID)
        match = self.repository.update(current_match, match_data)
        
        # Handle couple stats updates
        new_match_has_result = match.winner_couple_id is not None and match.games
        
        if old_match_had_result and new_match_has_result:
            # Match result was updated - recalculate stats for both couples
            self._recalculate_stats_for_couples(match)
        elif old_match_had_result and not new_match_has_result:
            # Match result was removed - subtract old stats
            self.couple_stats_service.remove_match_from_stats(current_match)
        elif not old_match_had_result and new_match_has_result:
            # New match result was added - add stats
            self.couple_stats_service.update_couple_stats_from_match(match)
        
        return MatchOut.from_orm(match)
    
    def delete_match(self, match_id: int) -> None:
        """Delete a match"""
        # Get the match before deletion to remove its stats contribution
        match = self.repository.get_match_by_id(match_id)
        if match and match.winner_couple_id and match.games:
            self.couple_stats_service.remove_match_from_stats(match)
        
        result = self.repository.delete(match_id)
        if not result:
            raise HTTPException(status_code=404, detail="Match not found")
    
    def get_unscheduled_matches(self, tournament_id: int) -> List[MatchOut]:
        """Get all unscheduled matches for a tournament"""
        matches = self.repository.get_unscheduled_matches(tournament_id)
        return [MatchOut.from_orm(match) for match in matches]
    
    def get_scheduled_matches(self, tournament_id: int) -> List[MatchOut]:
        """Get all scheduled matches for a tournament"""
        matches = self.repository.get_scheduled_matches(tournament_id)
        return [MatchOut.from_orm(match) for match in matches]
    
    def _recalculate_stats_for_couples(self, match: Match) -> None:
        """Recalculate stats for both couples involved in a match"""
        # Recalculate stats for couple1
        self.couple_stats_service.recalculate_couple_stats(
            couple_id=match.couple1_id,
            tournament_id=match.tournament_id,
            group_id=match.group_id
        )
        
        # Recalculate stats for couple2
        self.couple_stats_service.recalculate_couple_stats(
            couple_id=match.couple2_id,
            tournament_id=match.tournament_id,
            group_id=match.group_id
        )
    
    def recalculate_tournament_stats(self, tournament_id: int, group_id: Optional[int] = None) -> None:
        """Recalculate all couple stats for a tournament or group"""
        # Get all couples in the tournament/group
        from app.models.tournament import TournamentCouple, TournamentGroupCouple
        
        if group_id:
            # Get couples in the specific group
            couple_ids = self.db.query(TournamentGroupCouple.couple_id).filter(
                TournamentGroupCouple.group_id == group_id,
                TournamentGroupCouple.deleted_at.is_(None)
            ).distinct().all()
            couple_ids = [c[0] for c in couple_ids]
        else:
            # Get all couples in the tournament
            couple_ids = self.db.query(TournamentCouple.id).filter(
                TournamentCouple.tournament_id == tournament_id,
                TournamentCouple.deleted_at.is_(None)
            ).all()
            couple_ids = [c[0] for c in couple_ids]
        
        # Recalculate stats for each couple
        for couple_id in couple_ids:
            self.couple_stats_service.recalculate_couple_stats(
                couple_id=couple_id,
                tournament_id=tournament_id,
                group_id=group_id
            )
    
    def initialize_missing_couple_stats(self, tournament_id: int, group_id: Optional[int] = None) -> int:
        """Initialize couple stats for all matches that don't have them yet"""
        # Get all matches for the tournament/group
        matches_query = self.db.query(Match).filter(Match.tournament_id == tournament_id)
        
        if group_id:
            matches_query = matches_query.filter(Match.group_id == group_id)
        
        matches = matches_query.all()
        
        if not matches:
            return 0
        
        # Initialize couple stats for all matches
        self.couple_stats_service.initialize_couple_stats_for_matches(matches)
        
        return len(matches)
    
    def ensure_couple_stats_exist(self, tournament_id: int, group_id: Optional[int] = None) -> Dict[str, int]:
        """Ensure all couple stats exist for a tournament/group, return counts of what was done"""
        # First initialize any missing stats
        matches_initialized = self.initialize_missing_couple_stats(tournament_id, group_id)
        
        # Then recalculate all stats to make sure they're accurate
        self.recalculate_tournament_stats(tournament_id, group_id)
        
        # Get count of couple stats records
        stats_count = self.db.query(self.couple_stats_service.repository.model).filter(
            self.couple_stats_service.repository.model.tournament_id == tournament_id
        )
        
        if group_id:
            stats_count = stats_count.filter(
                self.couple_stats_service.repository.model.group_id == group_id
            )
        
        stats_count = stats_count.count()
        
        return {
            "matches_processed": matches_initialized,
            "couple_stats_records": stats_count,
            "tournament_id": tournament_id,
            "group_id": group_id
        } 