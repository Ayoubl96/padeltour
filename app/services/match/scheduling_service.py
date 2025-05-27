from typing import List, Dict, Any, Optional, Type
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.tournament import Match, TournamentStage, TournamentCourt, Tournament
from app.services.base.base_service import BaseService
from app.repositories.match_repository import MatchRepository
from app.repositories.tournament_repository import TournamentRepository
from app.services.match.scheduling_strategies import (
    SchedulingStrategy,
    TimeBasedSchedulingStrategy,
    OrderOnlySchedulingStrategy
)
from app.utils.time_utils import parse_iso_date

class MatchSchedulingService:
    """
    Service responsible for scheduling tournament matches
    """
    
    # Strategy mapping for easy lookup
    STRATEGY_MAP = {
        'time_based': TimeBasedSchedulingStrategy,
        'order_only': OrderOnlySchedulingStrategy
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.match_repository = MatchRepository(db)
        self.tournament_repo = TournamentRepository(db)
    
    def schedule_tournament_matches(
        self,
        tournament_id: int,
        strategy_name: str = 'time_based',
        stage_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Match]:
        """
        Schedule matches for a tournament using the specified strategy
        
        Args:
            tournament_id: The tournament ID
            strategy_name: Name of the scheduling strategy to use
            stage_id: Optional stage ID to filter matches
            parameters: Optional parameters for the scheduling algorithm
            
        Returns:
            List of scheduled matches
        """
        # Get the strategy class
        strategy_class = self._get_strategy_class(strategy_name)
        
        # Create strategy instance
        strategy = strategy_class()
        
        # Get unscheduled matches
        matches = self.match_repository.get_unscheduled_matches(tournament_id, stage_id)
        
        if not matches:
            return []
            
        # Get tournament courts
        tournament_courts = self.match_repository.get_tournament_courts(tournament_id)
        
        if not tournament_courts:
            raise ValueError("No courts assigned to this tournament")
            
        # Apply scheduling strategy
        scheduled_matches = strategy.schedule_matches(
            db=self.db,
            tournament_id=tournament_id,
            matches=matches,
            tournament_courts=tournament_courts,
            parameters=parameters or {}
        )
        
        # Save the scheduled matches
        return self.match_repository.save_matches(scheduled_matches)
    
    def clear_match_schedule(self, match_id: int) -> Match:
        """
        Clear the schedule for a match
        
        Args:
            match_id: The match ID
            
        Returns:
            The updated match
        """
        return self.match_repository.clear_match_schedule(match_id)
    
    def clear_tournament_schedule(self, tournament_id: int, stage_id: Optional[int] = None) -> int:
        """
        Clear the schedule for all matches in a tournament or stage
        
        Args:
            tournament_id: The tournament ID
            stage_id: Optional stage ID
            
        Returns:
            Number of matches affected
        """
        return self.match_repository.clear_tournament_schedule(tournament_id, stage_id)
    
    def reschedule_tournament(
        self,
        tournament_id: int,
        strategy_name: str = 'time_based',
        stage_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Match]:
        """
        Clear existing schedule and create a new one
        
        Args:
            tournament_id: The tournament ID
            strategy_name: Name of the scheduling strategy to use
            stage_id: Optional stage ID to filter matches
            parameters: Optional parameters for the scheduling algorithm
            
        Returns:
            List of rescheduled matches
        """
        # Clear existing schedule
        self.clear_tournament_schedule(tournament_id, stage_id)
        
        # Create new schedule
        return self.schedule_tournament_matches(
            tournament_id,
            strategy_name,
            stage_id,
            parameters
        )
    
    def get_available_scheduling_strategies(self) -> Dict[str, str]:
        """
        Get a map of available scheduling strategies
        
        Returns:
            Dictionary mapping strategy names to descriptions
        """
        return {
            'time_based': 'Schedule matches based on court availability and time constraints',
            'order_only': 'Schedule matches in sequential order without time constraints'
        }
    
    def _get_strategy_class(self, strategy_name: str) -> Type[SchedulingStrategy]:
        """
        Get the strategy class by name
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            The strategy class
            
        Raises:
            ValueError: If strategy name is not recognized
        """
        strategy_class = self.STRATEGY_MAP.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown scheduling strategy: {strategy_name}")
        return strategy_class

class SchedulingService(BaseService):
    """Service for scheduling matches with different strategies"""
    
    def __init__(self, db: Session):
        super().__init__(db, MatchRepository)
        self.tournament_repo = TournamentRepository(db)
        self.time_based_strategy = TimeBasedSchedulingStrategy(db)
        self.order_only_strategy = OrderOnlySchedulingStrategy(db)
    
    def auto_schedule_matches(
        self, 
        tournament_id: int, 
        company_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_only: bool = False
    ) -> List[Match]:
        """
        Schedule matches using the appropriate strategy.
        If order_only is True, will only assign courts and order.
        Otherwise, will try to assign specific times.
        """
        # Validate tournament existence and ownership
        tournament = self.tournament_repo.get_tournament_with_check(tournament_id, company_id)
        
        # If order_only mode is requested, use that strategy
        if order_only:
            return self.order_only_strategy.schedule(tournament_id, company_id)
        
        # For time-based scheduling, we need date parameters
        if not start_date:
            raise ValueError("start_date is required for time-based scheduling")
            
        # Check if all stages have time limits configured
        if not self._all_stages_have_time_limits(tournament_id):
            # If any stage doesn't have time limits, switch to order-only mode
            return self.order_only_strategy.schedule(tournament_id, company_id)
            
        # Use time-based scheduling
        return self.time_based_strategy.schedule(
            tournament_id=tournament_id,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
    
    def _all_stages_have_time_limits(self, tournament_id: int) -> bool:
        """Check if all stages for this tournament have time limits configured"""
        # Get all stages with matches
        stages_with_matches = (
            self.db.query(TournamentStage)
            .join(Match, TournamentStage.id == Match.stage_id)
            .filter(
                Match.tournament_id == tournament_id,
                Match.scheduled_start.is_(None)  # Only check stages with unscheduled matches
            )
            .distinct()
            .all()
        )
        
        # Check if each stage has time limits configured
        for stage in stages_with_matches:
            match_rules = stage.config.get("match_rules", {})
            is_time_limited = match_rules.get("time_limited", False)
            has_time_limit = is_time_limited and match_rules.get("time_limit_minutes") is not None
            
            if not has_time_limit:
                return False
                
        return True
    
    def schedule_match(
        self,
        match_id: int,
        company_id: int,
        court_id: int,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        is_time_limited: bool = False,
        time_limit_minutes: Optional[int] = None
    ) -> Match:
        """Schedule a specific match on a court at a specific time"""
        # Get match with ownership validation
        match = self.repository.get_match_with_check(match_id, company_id)
        
        # Verify court exists and belongs to the tournament
        court = (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == match.tournament_id,
                TournamentCourt.court_id == court_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .first()
        )
        
        if not court:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Court not found or not associated with this tournament"
            )
        
        # Check court availability during the requested time
        if court.availability_start and start_time < court.availability_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Court is not available at this start time"
            )
            
        if court.availability_end and end_time and end_time > court.availability_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Court is not available until this end time"
            )
            
        # If end time is not provided but we have a time limit, calculate it
        if not end_time and time_limit_minutes:
            end_time = start_time + timedelta(minutes=time_limit_minutes)
            
        # Check for conflicts with other matches
        if start_time and end_time:
            conflicting_matches = self.repository.check_match_conflicts(
                court_id=court_id,
                start_time=start_time,
                end_time=end_time,
                exclude_match_id=match_id
            )
            
            if conflicting_matches:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Court is already booked during this time (conflicts with match ID: {conflicting_matches[0].id})"
                )
                
        # Update the match scheduling
        update_data = {
            "court_id": court_id,
            "scheduled_start": start_time,
            "scheduled_end": end_time,
            "is_time_limited": is_time_limited,
            "time_limit_minutes": time_limit_minutes,
            "updated_at": datetime.now()
        }
        
        return self.repository.update(match, update_data)
    
    def unschedule_match(self, match_id: int, company_id: int) -> Match:
        """Remove scheduling information from a match"""
        # Get match with ownership validation
        match = self.repository.get_match_with_check(match_id, company_id)
        
        # Clear the scheduling information
        update_data = {
            "court_id": None,
            "scheduled_start": None,
            "scheduled_end": None,
            "is_time_limited": False,
            "time_limit_minutes": None,
            "updated_at": datetime.now()
        }
        
        return self.repository.update(match, update_data)
        
    def get_tournament_matches(self, tournament_id: int, company_id: int) -> List[Match]:
        """Get all matches for a tournament"""
        # Validate tournament ownership
        self.tournament_repo.get_tournament_with_check(tournament_id, company_id)
        return self.repository.get_tournament_matches(tournament_id)
        
    def get_stage_matches(self, stage_id: int, company_id: int) -> List[Match]:
        """Get all matches for a stage"""
        # Validate stage ownership
        self.tournament_repo.get_stage_with_check(stage_id, company_id)
        return self.repository.get_stage_matches(stage_id)
        
    def get_group_matches(self, group_id: int, company_id: int) -> List[Match]:
        """Get all matches for a group"""
        # Validate group ownership
        self.tournament_repo.get_group_with_check(group_id, company_id)
        return self.repository.get_group_matches(group_id)
        
    def get_bracket_matches(self, bracket_id: int, company_id: int) -> List[Match]:
        """Get all matches for a bracket"""
        # Validate bracket ownership
        self.tournament_repo.get_bracket_with_check(bracket_id, company_id)
        return self.repository.get_bracket_matches(bracket_id) 