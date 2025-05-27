from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.tournament import (
    Match, Tournament, TournamentStage, TournamentCourt
)
from app.repositories.match_repository import MatchRepository
from app.repositories.tournament_repository import TournamentRepository
from app.utils.time_utils import ensure_timezone_compatible, safe_max, safe_min
from app.core.constants import MatchResultStatus

class SchedulingStrategy(ABC):
    """Abstract base class for match scheduling strategies"""
    
    def __init__(self, db: Session):
        self.db = db
        self.match_repo = MatchRepository(db)
        self.tournament_repo = TournamentRepository(db)
    
    @abstractmethod
    def schedule(self, tournament_id: int, company_id: int, **kwargs) -> List[Match]:
        """
        Schedule matches using the strategy.
        Returns the scheduled matches.
        """
        pass
    
    def _validate_tournament_ownership(self, tournament_id: int, company_id: int) -> Tournament:
        """Validate tournament ownership"""
        return self.tournament_repo.get_tournament_with_check(tournament_id, company_id)
        
    def _get_courts(self, tournament_id: int) -> List[TournamentCourt]:
        """Get available courts for a tournament"""
        return self.tournament_repo.get_tournament_courts(tournament_id)
        
    def _get_unscheduled_matches(self, tournament_id: int) -> List[Match]:
        """Get unscheduled matches for a tournament"""
        return self.match_repo.get_unscheduled_matches(tournament_id)
        
    def _group_matches_by_stage_and_group(self, matches: List[Match]) -> Tuple[Dict[int, List[Match]], Dict[int, List[Match]], Dict[int, List[Match]], List[Match]]:
        """Group matches by stage, group, and bracket for organized scheduling"""
        # Initialize dictionaries to store matches by group and bracket
        matches_by_stage = defaultdict(list)
        matches_by_group = defaultdict(list)
        matches_by_bracket = defaultdict(list)
        
        # Group matches by their stage
        for match in matches:
            matches_by_stage[match.stage_id].append(match)
            
            # Also group by group or bracket if applicable
            if match.group_id:
                matches_by_group[match.group_id].append(match)
            elif match.bracket_id:
                matches_by_bracket[match.bracket_id].append(match)
                
        # Find any matches that don't belong to a group or bracket
        other_matches = [m for m in matches if not m.group_id and not m.bracket_id]
        
        return matches_by_stage, matches_by_group, matches_by_bracket, other_matches


class TimeBasedSchedulingStrategy(SchedulingStrategy):
    """
    Time-based scheduling strategy.
    Schedules matches with specific start and end times.
    """
    
    def schedule(self, tournament_id: int, company_id: int, start_date: datetime, end_date: Optional[datetime] = None, **kwargs) -> List[Match]:
        """Schedule matches with specific time slots"""
        # Validate tournament ownership
        tournament = self._validate_tournament_ownership(tournament_id, company_id)
        
        # If end date not provided, use start date (one day only)
        if not end_date:
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            
        # Get available courts
        courts = self._get_courts(tournament_id)
        if not courts:
            return []
            
        # Get unscheduled matches
        unscheduled_matches = self._get_unscheduled_matches(tournament_id)
        if not unscheduled_matches:
            return []
            
        # Get already scheduled matches
        scheduled_matches = self.match_repo.get_scheduled_matches(tournament_id, start_date, end_date)
        
        # Group scheduled matches by court
        court_schedules = {}
        for court in courts:
            court_schedules[court.court_id] = {
                "court": court,
                "matches": [m for m in scheduled_matches if m.court_id == court.court_id],
                "available_slots": []
            }
            
        # Calculate available slots for each court
        for court_id, schedule in court_schedules.items():
            court = schedule["court"]
            matches = schedule["matches"]
            
            # Set court availability for the requested period - handle timezone issues
            court_start = start_date
            if court.availability_start:
                court_start, start_date = ensure_timezone_compatible(court.availability_start, start_date)
                court_start = safe_max(court_start, start_date)
            
            court_end = end_date
            if court.availability_end:
                court_end, end_date = ensure_timezone_compatible(court.availability_end, end_date)
                court_end = safe_min(court_end, end_date)
            
            # Calculate free time slots
            free_slots = []
            last_end = court_start
            
            for match in sorted(matches, key=lambda m: m.scheduled_start):
                # If there's a gap between the last match end and this match start
                if last_end < match.scheduled_start:
                    free_slots.append({
                        "start": last_end,
                        "end": match.scheduled_start
                    })
                    
                # Update the last end time
                last_end = match.scheduled_end
                
            # Add the final slot if needed
            if last_end < court_end:
                free_slots.append({
                    "start": last_end,
                    "end": court_end
                })
                
            schedule["available_slots"] = free_slots
        
        # Organize matches for scheduling in a logical order
        matches_by_stage, matches_by_group, matches_by_bracket, other_matches = self._group_matches_by_stage_and_group(unscheduled_matches)
        
        # Create an ordered list of matches to schedule
        ordered_matches = []
        
        # First add group matches
        for group_id, group_matches in matches_by_group.items():
            ordered_matches.extend(group_matches)
            
        # Then add bracket matches with proper ordering
        for bracket_id, bracket_matches in matches_by_bracket.items():
            # Sort bracket matches by position
            sorted_bracket_matches = sorted(bracket_matches, key=lambda m: m.bracket_position or 0)
            ordered_matches.extend(sorted_bracket_matches)
            
        # Add any remaining matches
        for match in other_matches:
            if match not in ordered_matches:
                ordered_matches.append(match)
                
        # Schedule each match
        scheduled = []
        match_order = 1
        
        for match in ordered_matches:
            # Determine match duration based on the stage's configuration
            match_duration = self._get_match_duration(match)
                
            # Find the earliest available slot that can fit this match
            best_slot = None
            best_court_id = None
            best_start_time = None
            
            for court_id, schedule in court_schedules.items():
                for slot in schedule["available_slots"]:
                    slot_duration = slot["end"] - slot["start"]
                    
                    # If slot is long enough for the match
                    if slot_duration >= match_duration:
                        # This is a candidate - check if it's better than our current best
                        if not best_start_time or slot["start"] < best_start_time:
                            best_slot = slot
                            best_court_id = court_id
                            best_start_time = slot["start"]
            
            # If we found a slot, schedule the match
            if best_slot and best_court_id:
                match_end_time = best_start_time + match_duration
                
                # Update the match
                match.court_id = best_court_id
                match.scheduled_start = best_start_time
                match.scheduled_end = match_end_time
                match.display_order = match_order
                match.updated_at = datetime.now()
                
                match_order += 1
                
                # Update the available slots
                court_schedules[best_court_id]["matches"].append(match)
                court_schedules[best_court_id]["matches"].sort(key=lambda m: m.scheduled_start)
                
                # Remove or split the used slot
                court_schedules[best_court_id]["available_slots"].remove(best_slot)
                
                # Add back any remaining slot portion
                if match_end_time < best_slot["end"]:
                    court_schedules[best_court_id]["available_slots"].append({
                        "start": match_end_time,
                        "end": best_slot["end"]
                    })
                    
                # Sort slots by start time
                court_schedules[best_court_id]["available_slots"].sort(key=lambda s: s["start"])
                
                scheduled.append(match)
        
        # Commit all changes
        self.db.commit()
        
        return scheduled
    
    def _get_match_duration(self, match: Match) -> timedelta:
        """Determine match duration based on match configuration or stage settings"""
        # Default duration if none specified
        default_duration = timedelta(minutes=90)
        
        # Check if the match itself has a duration specified
        if match.time_limit_minutes:
            return timedelta(minutes=match.time_limit_minutes)
            
        # Check if the stage has match rules with duration
        if match.stage_id:
            stage = self.db.query(TournamentStage).filter(TournamentStage.id == match.stage_id).first()
            if stage:
                match_rules = stage.config.get("match_rules", {})
                if match_rules.get("time_limited", False) and match_rules.get("time_limit_minutes"):
                    return timedelta(minutes=match_rules.get("time_limit_minutes"))
                    
        # Return default duration if nothing found
        return default_duration


class OrderOnlySchedulingStrategy(SchedulingStrategy):
    """
    Order-only scheduling strategy.
    Assigns courts and display order without specific times.
    """
    
    def schedule(self, tournament_id: int, company_id: int, **kwargs) -> List[Match]:
        """Schedule matches by assigning courts and order only"""
        # Validate tournament ownership
        tournament = self._validate_tournament_ownership(tournament_id, company_id)
        
        # Get available courts
        courts = self._get_courts(tournament_id)
        if not courts:
            return []
            
        court_ids = [court.court_id for court in courts]
        num_courts = len(court_ids)
        
        # Get unscheduled matches
        unscheduled_matches = self._get_unscheduled_matches(tournament_id)
        if not unscheduled_matches:
            return []
            
        # Group matches for logical processing
        matches_by_stage, matches_by_group, matches_by_bracket, other_matches = self._group_matches_by_stage_and_group(unscheduled_matches)
        
        # Prepare for scheduling
        ordered_matches = []
        court_index = 0
        match_order = 1
        
        # Process group matches first
        for group_id, group_matches in matches_by_group.items():
            for match in group_matches:
                match.court_id = court_ids[court_index % num_courts]
                match.display_order = match_order
                match.updated_at = datetime.now()
                ordered_matches.append(match)
                
                match_order += 1
                court_index += 1
                
        # Process bracket matches next
        for bracket_id, bracket_matches in matches_by_bracket.items():
            # Sort bracket matches by position
            sorted_bracket_matches = sorted(bracket_matches, key=lambda m: m.bracket_position or 0)
            
            for match in sorted_bracket_matches:
                match.court_id = court_ids[court_index % num_courts]
                match.display_order = match_order
                match.updated_at = datetime.now()
                ordered_matches.append(match)
                
                match_order += 1
                court_index += 1
                
        # Process any remaining matches
        for match in other_matches:
            if match not in ordered_matches:
                match.court_id = court_ids[court_index % num_courts]
                match.display_order = match_order
                match.updated_at = datetime.now()
                ordered_matches.append(match)
                
                match_order += 1
                court_index += 1
                
        # Commit all changes
        self.db.commit()
        
        return ordered_matches 