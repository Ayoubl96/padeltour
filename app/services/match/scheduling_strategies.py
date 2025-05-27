from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from app.models.tournament import Match, TournamentCourt, Tournament


class SchedulingStrategy(ABC):
    """
    Abstract base class for match scheduling strategies
    """
    
    @abstractmethod
    def schedule_matches(
        self,
        db: Session,
        tournament_id: int,
        matches: List[Match],
        tournament_courts: List[TournamentCourt],
        parameters: Dict[str, Any]
    ) -> List[Match]:
        """
        Schedule a list of matches using tournament courts
        
        Args:
            db: Database session
            tournament_id: The tournament ID
            matches: List of matches to schedule
            tournament_courts: List of tournament courts available
            parameters: Additional parameters for the scheduling algorithm
            
        Returns:
            List of scheduled matches
        """
        pass


class TimeBasedSchedulingStrategy(SchedulingStrategy):
    """
    Strategy that schedules matches based on time constraints and court availability
    """
    
    DEFAULT_MATCH_DURATION = 60  # Default match duration in minutes
    
    def schedule_matches(
        self,
        db: Session,
        tournament_id: int,
        matches: List[Match],
        tournament_courts: List[TournamentCourt],
        parameters: Dict[str, Any]
    ) -> List[Match]:
        """
        Schedule matches with time blocks
        
        Args:
            db: Database session
            tournament_id: The tournament ID
            matches: List of matches to schedule
            tournament_courts: List of tournament courts available
            parameters: Additional parameters including:
                - start_date: Start date for scheduling (ISO format string or datetime)
                - end_date: Optional end date for scheduling
                - daily_start_time: Daily start time (HH:MM format)
                - daily_end_time: Daily end time (HH:MM format)
                - match_duration: Duration in minutes for each match (default: 60)
            
        Returns:
            List of scheduled matches
        """
        # Extract parameters with defaults
        start_date = self._parse_date_param(parameters.get('start_date', datetime.now()))
        end_date = self._parse_date_param(parameters.get('end_date'))
        daily_start_time = self._parse_time_param(parameters.get('daily_start_time', '09:00'))
        daily_end_time = self._parse_time_param(parameters.get('daily_end_time', '21:00'))
        match_duration = int(parameters.get('match_duration', self.DEFAULT_MATCH_DURATION))
        
        # Get the tournament from the database to check for existing settings
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise ValueError(f"Tournament with ID {tournament_id} not found")
            
        # Use tournament settings if available and not overridden
        if tournament.start_date and 'start_date' not in parameters:
            start_date = tournament.start_date
            
        if tournament.end_date and 'end_date' not in parameters:
            end_date = tournament.end_date
            
        # Sort matches by stage sequence and order within stage
        matches.sort(key=lambda m: (m.stage.sequence, m.order_in_stage or 999))
        
        # Define available time slots
        time_slots = self._generate_time_slots(
            start_date=start_date,
            end_date=end_date,
            daily_start_time=daily_start_time,
            daily_end_time=daily_end_time,
            match_duration=match_duration
        )
        
        # Schedule matches
        scheduled_matches = []
        slot_index = 0
        court_index = 0
        
        for match in matches:
            if slot_index >= len(time_slots):
                # We've run out of time slots
                break
                
            # Assign court and time
            start_time, end_time = time_slots[slot_index]
            court = tournament_courts[court_index]
            
            match.start_time = start_time
            match.end_time = end_time
            match.court_id = court.court_id
            scheduled_matches.append(match)
            
            # Move to next court for next match
            court_index = (court_index + 1) % len(tournament_courts)
            
            # If we've used all courts for this time slot, move to the next time slot
            if court_index == 0:
                slot_index += 1
        
        return scheduled_matches
    
    def _parse_date_param(self, date_param) -> Optional[datetime]:
        """Convert string date parameter to datetime object"""
        if not date_param:
            return None
            
        if isinstance(date_param, datetime):
            return date_param
            
        try:
            if isinstance(date_param, str):
                # Try ISO format parsing
                return datetime.fromisoformat(date_param.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid date format: {date_param}")
            
        return None
        
    def _parse_time_param(self, time_param: str) -> Tuple[int, int]:
        """Parse time string in HH:MM format to hour and minute"""
        try:
            hour, minute = map(int, time_param.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
            return hour, minute
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format: {time_param}. Expected HH:MM")
    
    def _generate_time_slots(
        self,
        start_date: datetime,
        end_date: Optional[datetime],
        daily_start_time: Tuple[int, int],
        daily_end_time: Tuple[int, int],
        match_duration: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Generate available time slots between start_date and end_date
        
        Args:
            start_date: Start date and time
            end_date: Optional end date and time
            daily_start_time: Tuple of (hour, minute) for daily start time
            daily_end_time: Tuple of (hour, minute) for daily end time
            match_duration: Duration in minutes for each match
            
        Returns:
            List of (start_time, end_time) tuples representing available slots
        """
        # Default end date to 7 days after start if not provided
        if not end_date:
            end_date = start_date + timedelta(days=7)
            
        # Ensure start_date includes the start time for the first day
        start_hour, start_minute = daily_start_time
        current_date = start_date.replace(
            hour=start_hour,
            minute=start_minute,
            second=0,
            microsecond=0
        )
        
        # If start_date is already past the daily start time, move to next slot
        if start_date > current_date:
            current_date = start_date
        
        slots = []
        match_delta = timedelta(minutes=match_duration)
        
        # Loop through each day until end_date
        while current_date < end_date:
            day_end_hour, day_end_minute = daily_end_time
            day_end = current_date.replace(
                hour=day_end_hour,
                minute=day_end_minute,
                second=0,
                microsecond=0
            )
            
            # Generate slots for the current day
            while current_date + match_delta <= day_end:
                slots.append((current_date, current_date + match_delta))
                current_date += match_delta
            
            # Move to the next day's start time
            current_date = (current_date.replace(
                hour=start_hour,
                minute=start_minute,
                second=0,
                microsecond=0
            ) + timedelta(days=1))
            
        return slots


class OrderOnlySchedulingStrategy(SchedulingStrategy):
    """
    Strategy that schedules matches in sequential order without time constraints
    """
    
    def schedule_matches(
        self,
        db: Session,
        tournament_id: int,
        matches: List[Match],
        tournament_courts: List[TournamentCourt],
        parameters: Dict[str, Any]
    ) -> List[Match]:
        """
        Schedule matches by order only (no specific times)
        
        Args:
            db: Database session
            tournament_id: The tournament ID
            matches: List of matches to schedule
            tournament_courts: List of tournament courts available
            parameters: Additional parameters (not used in this strategy)
            
        Returns:
            List of scheduled matches
        """
        if not matches or not tournament_courts:
            return []
            
        # Sort matches by stage sequence and order within stage
        matches.sort(key=lambda m: (m.stage.sequence, m.order_in_stage or 999))
        
        # Assign courts in rotation (no times)
        scheduled_matches = []
        court_index = 0
        
        for match in matches:
            court = tournament_courts[court_index]
            match.court_id = court.court_id
            # Don't set times for this strategy
            match.start_time = None
            match.end_time = None
            scheduled_matches.append(match)
            
            # Rotate through courts
            court_index = (court_index + 1) % len(tournament_courts)
            
        return scheduled_matches 