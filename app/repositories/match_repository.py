from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime
from fastapi import Depends

from app.repositories.base import BaseRepository, EntityNotFoundError, UnauthorizedAccessError
from app.models.tournament import (
    Match, Tournament, TournamentStage, TournamentGroup, 
    TournamentBracket, TournamentCourt
)
from app.core.constants import MatchResultStatus
from app.models.court import Court
from app.schemas.match import MatchCreate, MatchUpdate

class MatchRepository(BaseRepository[Match, MatchCreate, MatchUpdate]):
    """Repository for match-related operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Match)
    
    def get_match_with_check(self, match_id: int, company_id: int) -> Match:
        """Get a match by ID with company ownership check"""
        match = (
            self.db.query(Match)
            .options(
                joinedload(Match.tournament),
                joinedload(Match.couple1),
                joinedload(Match.couple2),
                joinedload(Match.court)
            )
            .filter(Match.id == match_id)
            .first()
        )
        
        if not match:
            raise EntityNotFoundError(f"Match not found with ID {match_id}")
        
        if match.tournament.company_id != company_id:
            raise UnauthorizedAccessError(f"Unauthorized access to match {match_id}")
            
        return match
    
    def get_tournament_matches(self, tournament_id: int) -> List[Match]:
        """Get all matches for a tournament"""
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.couple1),
                joinedload(Match.couple2),
                joinedload(Match.court)
            )
            .filter(Match.tournament_id == tournament_id)
            .order_by(Match.scheduled_start, Match.id)
            .all()
        )
    
    def get_stage_matches(self, stage_id: int) -> List[Match]:
        """Get all matches for a stage"""
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.couple1),
                joinedload(Match.couple2),
                joinedload(Match.court)
            )
            .filter(Match.stage_id == stage_id)
            .order_by(Match.scheduled_start, Match.id)
            .all()
        )
    
    def get_group_matches(self, group_id: int) -> List[Match]:
        """Get all matches for a group"""
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.couple1),
                joinedload(Match.couple2),
                joinedload(Match.court)
            )
            .filter(Match.group_id == group_id)
            .order_by(Match.scheduled_start, Match.id)
            .all()
        )
    
    def get_bracket_matches(self, bracket_id: int) -> List[Match]:
        """Get all matches for a bracket"""
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.couple1),
                joinedload(Match.couple2),
                joinedload(Match.court)
            )
            .filter(Match.bracket_id == bracket_id)
            .order_by(Match.bracket_position)
            .all()
        )
    
    def get_unscheduled_matches(self, tournament_id: int) -> List[Match]:
        """Get all unscheduled matches for a tournament"""
        return (
            self.db.query(Match)
            .filter(
                Match.tournament_id == tournament_id,
                Match.scheduled_start.is_(None),
                Match.match_result_status == MatchResultStatus.PENDING
            )
            .order_by(Match.id)
            .all()
        )
    
    def get_scheduled_matches(self, tournament_id: int, start_date: datetime, end_date: datetime) -> List[Match]:
        """Get all scheduled matches within a date range"""
        return (
            self.db.query(Match)
            .filter(
                Match.tournament_id == tournament_id,
                Match.scheduled_start.isnot(None),
                Match.scheduled_start >= start_date,
                Match.scheduled_start <= end_date
            )
            .order_by(Match.scheduled_start)
            .all()
        )
    
    def get_matches_by_stage_id(self, stage_id: int) -> List[Match]:
        """Get all matches for a stage"""
        return (
            self.db.query(Match)
            .filter(Match.stage_id == stage_id)
            .all()
        )
    
    def get_matches_by_court(self, court_id: int) -> List[Match]:
        """Get all matches scheduled on a specific court"""
        return (
            self.db.query(Match)
            .filter(
                Match.court_id == court_id,
                Match.scheduled_start.isnot(None)
            )
            .order_by(Match.scheduled_start)
            .all()
        )
    
    def create_match(self, **kwargs) -> Match:
        """Create a new match"""
        return self.create(Match, **kwargs)
    
    def create_matches(self, matches_data: List[Dict[str, Any]]) -> List[Match]:
        """Create multiple matches at once"""
        matches = []
        for data in matches_data:
            match = Match(**data)
            self.db.add(match)
            matches.append(match)
            
        self.db.commit()
        
        # Refresh all matches to get their IDs
        for match in matches:
            self.db.refresh(match)
            
        return matches
    
    def check_match_conflicts(self, court_id: int, start_time: datetime, end_time: datetime, exclude_match_id: Optional[int] = None) -> List[Match]:
        """Check for conflicting matches on a court during a time period"""
        query = (
            self.db.query(Match)
            .filter(
                Match.court_id == court_id,
                Match.scheduled_start.isnot(None),
                Match.scheduled_end.isnot(None)
            )
        )
        
        if exclude_match_id:
            query = query.filter(Match.id != exclude_match_id)
            
        return query.filter(
            or_(
                # New match starts during an existing match
                and_(
                    Match.scheduled_start <= start_time,
                    Match.scheduled_end > start_time
                ),
                # New match ends during an existing match
                and_(
                    Match.scheduled_start < end_time,
                    Match.scheduled_end >= end_time
                ),
                # New match completely contains an existing match
                and_(
                    Match.scheduled_start >= start_time,
                    Match.scheduled_end <= end_time
                )
            )
        ).all()

    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        """Get a match by its ID"""
        return self.db.query(Match).filter(Match.id == match_id).first()
    
    def get_matches_by_tournament_id(self, tournament_id: int, **filters) -> List[Match]:
        """
        Get all matches for a tournament with optional filters
        
        Args:
            tournament_id: The tournament ID
            **filters: Additional filters like stage_id, scheduled, etc.
            
        Returns:
            List of matches matching the criteria
        """
        query = self.db.query(Match).filter(Match.tournament_id == tournament_id)
        
        # Apply additional filters
        if 'stage_id' in filters:
            query = query.filter(Match.stage_id == filters['stage_id'])
            
        if 'scheduled' in filters:
            if filters['scheduled']:
                query = query.filter(Match.scheduled_start != None)
            else:
                query = query.filter(Match.scheduled_start == None)
                
        if 'completed' in filters:
            if filters['completed']:
                query = query.filter(Match.is_completed == True)
            else:
                query = query.filter(or_(Match.is_completed == False, Match.is_completed == None))
                
        # Add joinedloads for commonly accessed relationships
        query = query.options(
            joinedload(Match.stage),
            joinedload(Match.court)
        )
                
        return query.all()
    
    def get_unscheduled_matches(self, tournament_id: int, stage_id: Optional[int] = None) -> List[Match]:
        """
        Get all unscheduled matches for a tournament
        
        Args:
            tournament_id: The tournament ID
            stage_id: Optional stage ID to filter by
            
        Returns:
            List of unscheduled matches
        """
        query = self.db.query(Match).filter(
            Match.tournament_id == tournament_id,
            Match.scheduled_start == None
        )
        
        if stage_id:
            query = query.filter(Match.stage_id == stage_id)
            
        return query.all()
    
    def get_tournament_courts(self, tournament_id: int) -> List[TournamentCourt]:
        """
        Get all courts assigned to a tournament
        
        Args:
            tournament_id: The tournament ID
            
        Returns:
            List of tournament courts
        """
        query = self.db.query(TournamentCourt).filter(
            TournamentCourt.tournament_id == tournament_id
        ).options(
            joinedload(TournamentCourt.court)
        )
        
        return query.all()
    
    def get_tournament_stages(self, tournament_id: int) -> List[TournamentStage]:
        """Get all stages for a tournament ordered by their sequence"""
        return self.db.query(TournamentStage).filter(
            TournamentStage.tournament_id == tournament_id
        ).order_by(TournamentStage.order).all()
    
    def save_match(self, match: Match) -> Match:
        """
        Save or update a match
        
        Args:
            match: The match to save or update
            
        Returns:
            The saved match
        """
        if match.id is None:
            self.db.add(match)
        self.db.flush()
        return match
    
    def save_matches(self, matches: List[Match]) -> List[Match]:
        """
        Save or update multiple matches
        
        Args:
            matches: The matches to save or update
            
        Returns:
            The saved matches
        """
        for match in matches:
            if match.id is None:
                self.db.add(match)
        self.db.flush()
        return matches
    
    def clear_match_schedule(self, match_id: int) -> Match:
        """
        Clear the schedule for a match
        
        Args:
            match_id: The match ID
            
        Returns:
            The updated match
        """
        match = self.get_match_by_id(match_id)
        if match:
            match.scheduled_start = None
            match.scheduled_end = None
            match.court_id = None
            self.db.flush()
        return match
    
    def clear_tournament_schedule(self, tournament_id: int, stage_id: Optional[int] = None) -> int:
        """
        Clear the schedule for all matches in a tournament or stage
        
        Args:
            tournament_id: The tournament ID
            stage_id: Optional stage ID
            
        Returns:
            Number of matches affected
        """
        query = self.db.query(Match).filter(Match.tournament_id == tournament_id)
        
        if stage_id:
            query = query.filter(Match.stage_id == stage_id)
            
        matches = query.all()
        count = 0
        
        for match in matches:
            match.scheduled_start = None
            match.scheduled_end = None
            match.court_id = None
            count += 1
            
        self.db.flush()
        return count

    def get_matches_by_round(self, tournament_id: int, round_number: int) -> List[Match]:
        """Get all matches for a specific tournament round"""
        return (self.db.query(self.model)
                .filter(self.model.tournament_id == tournament_id)
                .filter(self.model.round == round_number)
                .all())
    
    def get_matches_by_team(self, team_id: int) -> List[Match]:
        """Get all matches for a specific team"""
        return (self.db.query(self.model)
                .filter((self.model.team1_id == team_id) | (self.model.team2_id == team_id))
                .all())
    
    def get_unscheduled_matches(self, tournament_id: int) -> List[Match]:
        """Get all unscheduled matches for a tournament"""
        return (self.db.query(self.model)
                .filter(self.model.tournament_id == tournament_id)
                .filter(self.model.court_id == None)
                .filter(self.model.start_time == None)
                .all())
    
    def get_scheduled_matches(self, tournament_id: int) -> List[Match]:
        """Get all scheduled matches for a tournament"""
        return (self.db.query(self.model)
                .filter(self.model.tournament_id == tournament_id)
                .filter(self.model.court_id != None)
                .filter(self.model.start_time != None)
                .all()) 