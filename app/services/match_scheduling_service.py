from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status
from collections import defaultdict

from app.models.tournament import (
    Tournament, TournamentGroupCouple, TournamentStage, TournamentGroup, 
    TournamentBracket, Match, TournamentCourt
)
from app.core.constants import MatchResultStatus, SchedulingPriority


class MatchSchedulingService:
    def __init__(self, db: Session):
        self.db = db
        
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
        """Schedule a match on a court at a specific time"""
        # Get the match with ownership validation
        match = (
            self.db.query(Match)
            .options(joinedload(Match.tournament))
            .filter(Match.id == match_id)
            .first()
        )
        
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        
        if match.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this match")
            
        # Check if the court is valid and available for this tournament
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
            
        # Check if there are any conflicts with other matches on this court
        conflicting_matches = self.db.query(Match).filter(
            Match.court_id == court_id,
            Match.id != match_id,
            Match.scheduled_start.isnot(None),
            Match.scheduled_end.isnot(None),
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
        
        if conflicting_matches:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Court is already booked during this time (conflicts with match ID: {conflicting_matches[0].id})"
            )
            
        # Update the match scheduling
        match.court_id = court_id
        match.scheduled_start = start_time
        match.scheduled_end = end_time
        match.is_time_limited = is_time_limited
        match.time_limit_minutes = time_limit_minutes
        match.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(match)
        
        return match
        
    def unschedule_match(self, match_id: int, company_id: int) -> Match:
        """Remove scheduling information from a match"""
        # Get the match with ownership validation
        match = (
            self.db.query(Match)
            .options(joinedload(Match.tournament))
            .filter(Match.id == match_id)
            .first()
        )
        
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        
        if match.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this match")
            
        # Clear the scheduling information
        match.court_id = None
        match.scheduled_start = None
        match.scheduled_end = None
        match.is_time_limited = False
        match.time_limit_minutes = None
        match.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(match)
        
        return match
        
    def get_court_availability(
        self, 
        tournament_id: int, 
        company_id: int, 
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Get court availability for a specific date"""
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
            
        # Get all courts for this tournament
        courts = (
            self.db.query(TournamentCourt)
            .options(joinedload(TournamentCourt.court))
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .all()
        )
        
        if not courts:
            return []
            
        # Calculate date range (entire day)
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)
        
        # Get scheduled matches for this date
        matches = (
            self.db.query(Match)
            .filter(
                Match.tournament_id == tournament_id,
                Match.court_id.isnot(None),
                Match.scheduled_start.isnot(None),
                Match.scheduled_start >= start_of_day,
                Match.scheduled_start <= end_of_day
            )
            .order_by(Match.scheduled_start)
            .all()
        )
        
        # Prepare the result
        result = []
        
        for court in courts:
            # Calculate court's available time range for this day
            court_start = court.availability_start
            court_end = court.availability_end
            
            # If court doesn't have explicit availability, use tournament dates
            if not court_start:
                court_start = tournament.start_date
            if not court_end:
                court_end = tournament.end_date
                
            # Adjust to this specific day
            if court_start < start_of_day:
                court_start = start_of_day
            if court_end > end_of_day:
                court_end = end_of_day
                
            # Get matches scheduled on this court
            court_matches = [m for m in matches if m.court_id == court.court_id]
            
            # Calculate free time slots
            free_slots = []
            last_end = court_start
            
            for match in court_matches:
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
                
            # Build the court result
            court_result = {
                "court_id": court.court_id,
                "court_name": court.court.name,
                "day_availability": {
                    "start": court_start,
                    "end": court_end
                },
                "scheduled_matches": [
                    {
                        "match_id": m.id,
                        "start": m.scheduled_start,
                        "end": m.scheduled_end,
                        "couple1_id": m.couple1_id,
                        "couple2_id": m.couple2_id
                    }
                    for m in court_matches
                ],
                "free_slots": free_slots
            }
            
            result.append(court_result)
            
        return result
        
    def auto_assign_courts(self, matches: List[Match], tournament_id: int) -> List[Match]:
        """
        Automatically assign courts to matches with group-aware distribution.
        
        For group stages:
        - Keeps matches from the same group on the same court when possible
        - If there are more courts than groups, allows for parallel play
        - Tries to maintain similar timelines for all groups
        
        For bracket/elimination stages:
        - Distributes matches in a round-robin fashion
        """
        # Get available courts for this tournament
        courts = (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .all()
        )
        
        if not courts or not matches:
            # No courts available or no matches to assign, return matches as is
            return matches
            
        # Extract court IDs
        court_ids = [court.court_id for court in courts]
        num_courts = len(court_ids)
        
        # First check if these are group matches or bracket matches
        # Group matches will have a group_id set
        group_matches = [match for match in matches if match.group_id is not None]
        
        if len(group_matches) == len(matches):
            # These are group matches, use group-aware assignment
            
            # Group matches by group_id
            groups_to_matches = defaultdict(list)
            for match in matches:
                groups_to_matches[match.group_id].append(match)
            
            # Get list of group IDs
            group_ids = list(groups_to_matches.keys())
            num_groups = len(group_ids)
            
            if num_courts >= num_groups:
                # We have at least one court per group
                # Assign primary courts to groups
                group_to_court = {}
                for i, group_id in enumerate(group_ids):
                    group_to_court[group_id] = court_ids[i % num_courts]
                
                if num_courts > num_groups:
                    # We have extra courts that can be used for parallel play
                    # Create a round-robin assignment for the extra courts
                    extra_courts = court_ids[num_groups:]
                    
                    # Distribute some matches to extra courts for parallel play
                    # Start with the groups that have the most matches
                    groups_by_match_count = sorted(
                        group_ids, 
                        key=lambda g: len(groups_to_matches[g]),
                        reverse=True
                    )
                    
                    # Create a round-robin assignment for extra courts
                    extra_court_index = 0
                    for group_id in groups_by_match_count:
                        matches_in_group = groups_to_matches[group_id]
                        # For each group, assign some matches to extra courts
                        # to enable parallel play
                        num_extra = min(len(extra_courts), len(matches_in_group) // 2)
                        
                        if num_extra > 0:
                            for i in range(num_extra):
                                # Assign every other match to an extra court
                                match_index = (i + 1) * 2  # Use even indices (2, 4, 6...)
                                if match_index < len(matches_in_group):
                                    # Assign to next extra court in rotation
                                    extra_court = extra_courts[extra_court_index % len(extra_courts)]
                                    matches_in_group[match_index].court_id = extra_court
                                    extra_court_index += 1
                
                # Assign remaining matches to their group's primary court
                for group_id, group_matches in groups_to_matches.items():
                    primary_court = group_to_court[group_id]
                    for match in group_matches:
                        if match.court_id is None:  # Only assign if not already assigned
                            match.court_id = primary_court
            else:
                # We have more groups than courts
                # Distribute groups evenly across available courts
                for i, group_id in enumerate(group_ids):
                    court_id = court_ids[i % num_courts]
                    for match in groups_to_matches[group_id]:
                        match.court_id = court_id
        else:
            # These are bracket matches or mixed matches
            # Use simple round-robin assignment
            for i, match in enumerate(matches):
                court_index = i % num_courts
                match.court_id = court_ids[court_index]
        
        # Commit changes
        self.db.commit()
        
        # Refresh all matches
        for match in matches:
            self.db.refresh(match)
            
        return matches
    
    def generate_group_matches(self, group_id: int, company_id: int) -> List[Match]:
        """Generate all matches for a group based on its stage configuration"""
        # Get the group with ownership validation
        group = (
            self.db.query(TournamentGroup)
            .options(
                joinedload(TournamentGroup.stage).joinedload(TournamentStage.tournament)
            )
            .filter(TournamentGroup.id == group_id)
            .filter(TournamentGroup.deleted_at.is_(None))
            .first()
        )
        
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
        if group.stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this group")
            
        # Get stage configuration
        stage = group.stage
        match_rules = stage.config.get("match_rules", {})
        matches_per_opponent = match_rules.get("matches_per_opponent", 1)
        games_per_match = match_rules.get("games_per_match", 3)
        is_time_limited = match_rules.get("time_limited", False)
        time_limit_minutes = match_rules.get("time_limit_minutes", 90)
        
        # Get all couples in this group
        couples = (
            self.db.query(TournamentGroup)
            .options(joinedload(TournamentGroup.couples).joinedload(TournamentGroupCouple.couple))
            .filter(TournamentGroup.id == group_id)
            .filter(TournamentGroup.deleted_at.is_(None))
            .first()
        )
        
        if not couples or not couples.couples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No couples found in this group"
            )
            
        couple_ids = [gc.couple_id for gc in couples.couples if gc.deleted_at is None]
        
        if len(couple_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 couples are required to generate matches"
            )
            
        # Check if matches already exist for this group
        existing_matches = self.db.query(Match).filter(Match.group_id == group_id).count()
        if existing_matches > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{existing_matches} matches already exist for this group"
            )
            
        # Generate matches
        matches = []
        tournament_id = stage.tournament_id
        
        # Create pairings for all couples
        for i in range(len(couple_ids)):
            for j in range(i + 1, len(couple_ids)):
                for _ in range(matches_per_opponent):
                    # Create a match between the two couples
                    match = Match(
                        tournament_id=tournament_id,
                        stage_id=stage.id,
                        group_id=group_id,
                        couple1_id=couple_ids[i],
                        couple2_id=couple_ids[j],
                        games=[],  # Empty games for now
                        is_time_limited=is_time_limited,
                        time_limit_minutes=time_limit_minutes,
                        match_result_status=MatchResultStatus.PENDING
                    )
                    
                    matches.append(match)
        
        # Add all matches to the database
        for match in matches:
            self.db.add(match)
            
        self.db.commit()
        
        # Refresh all matches to get their IDs
        for match in matches:
            self.db.refresh(match)
            
        # Automatically assign courts to the matches
        matches = self.auto_assign_courts(matches, tournament_id)
            
        return matches
        
    def auto_order_matches(
        self, 
        tournament_id: int, 
        company_id: int
    ) -> List[Match]:
        """
        Automatically assign courts and sequence order to unscheduled matches without specific times.
        This is useful when match durations are unknown.
        """
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
            
        # Get available courts
        courts = (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .all()
        )
        
        if not courts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No courts available for this tournament"
            )
            
        court_ids = [court.court_id for court in courts]
        num_courts = len(court_ids)
            
        # Get unscheduled matches
        unscheduled_matches = (
            self.db.query(Match)
            .filter(
                Match.tournament_id == tournament_id,
                Match.scheduled_start.is_(None),
                Match.match_result_status == MatchResultStatus.PENDING
            )
            .all()
        )
        
        if not unscheduled_matches:
            return []
        
        # Organize matches by stage, then group/bracket
        matches_by_stage = defaultdict(list)
        for match in unscheduled_matches:
            matches_by_stage[match.stage_id].append(match)
        
        # For each stage, further organize by group or bracket
        ordered_matches = []
        court_index = 0
        match_order = 1
        
        # First process matches with a group_id (group stage matches)
        for stage_id, stage_matches in matches_by_stage.items():
            group_matches = [m for m in stage_matches if m.group_id is not None]
            
            # Group the matches by group_id
            matches_by_group = defaultdict(list)
            for match in group_matches:
                matches_by_group[match.group_id].append(match)
                
            # Assign courts and order to group matches
            for group_id, group_matches in matches_by_group.items():
                for match in group_matches:
                    match.court_id = court_ids[court_index % num_courts]
                    match.display_order = match_order
                    match.updated_at = datetime.now()
                    ordered_matches.append(match)
                    
                    match_order += 1
                    court_index += 1
                    
        # Then process bracket matches
        for stage_id, stage_matches in matches_by_stage.items():
            bracket_matches = [m for m in stage_matches if m.bracket_id is not None]
            
            # Group the matches by bracket_id
            matches_by_bracket = defaultdict(list)
            for match in bracket_matches:
                matches_by_bracket[match.bracket_id].append(match)
                
            # Assign courts and order to bracket matches
            for bracket_id, bracket_matches in matches_by_bracket.items():
                # Sort bracket matches by bracket_position to ensure proper ordering
                sorted_bracket_matches = sorted(bracket_matches, key=lambda m: m.bracket_position or 0)
                
                for match in sorted_bracket_matches:
                    match.court_id = court_ids[court_index % num_courts]
                    match.display_order = match_order
                    match.updated_at = datetime.now()
                    ordered_matches.append(match)
                    
                    match_order += 1
                    court_index += 1
                    
        # Process any remaining matches
        remaining_matches = [m for m in unscheduled_matches if m not in ordered_matches]
        for match in remaining_matches:
            match.court_id = court_ids[court_index % num_courts]
            match.display_order = match_order
            match.updated_at = datetime.now()
            ordered_matches.append(match)
            
            match_order += 1
            court_index += 1
            
        # Commit changes
        self.db.commit()
        
        # Refresh matches
        for match in ordered_matches:
            self.db.refresh(match)
            
        return ordered_matches
    
    def auto_schedule_matches(
        self, 
        tournament_id: int, 
        company_id: int,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        order_only: bool = False
    ) -> List[Match]:
        """
        Automatically schedule unscheduled matches within a date range.
        If order_only=True, will only assign courts and display order without times.
        """
        # Check if order-only mode is requested
        if order_only:
            return self.auto_order_matches(tournament_id, company_id)
            
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
            
        # If end date not provided, use start date (one day only)
        if not end_date:
            end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
            
        # Get available courts during this period
        courts = (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .all()
        )
        
        if not courts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No courts available for this tournament"
            )
            
        # Get unscheduled matches
        unscheduled_matches = (
            self.db.query(Match)
            .filter(
                Match.tournament_id == tournament_id,
                Match.scheduled_start.is_(None),
                Match.match_result_status == MatchResultStatus.PENDING
            )
            .order_by(Match.id)  # Order by match ID for now
            .all()
        )
        
        if not unscheduled_matches:
            return []
        
        # Check if matches have time limits specified in the stage configuration
        # Group matches by stage to check stage configurations
        matches_by_stage = defaultdict(list)
        for match in unscheduled_matches:
            matches_by_stage[match.stage_id].append(match)
            
        # Check if any stage doesn't have time limits configured
        stages_without_time_limits = []
        for stage_id in matches_by_stage.keys():
            stage = self.db.query(TournamentStage).filter(TournamentStage.id == stage_id).first()
            if stage:
                match_rules = stage.config.get("match_rules", {})
                is_time_limited = match_rules.get("time_limited", False)
                has_time_limit = is_time_limited and match_rules.get("time_limit_minutes") is not None
                
                if not has_time_limit:
                    stages_without_time_limits.append(stage_id)
                    
        # If any stages don't have time limits, switch to order-only mode
        if stages_without_time_limits:
            return self.auto_order_matches(tournament_id, company_id)
            
        # Continue with timed scheduling if all stages have time limits
        # Get already scheduled matches
        scheduled_matches = (
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
                # Convert both to naive or make both aware to avoid timezone comparison errors
                if court.availability_start.tzinfo is not None and start_date.tzinfo is None:
                    # Make start_date timezone-aware
                    aware_start_date = start_date.replace(tzinfo=court.availability_start.tzinfo)
                    court_start = max(aware_start_date, court.availability_start)
                elif court.availability_start.tzinfo is None and start_date.tzinfo is not None:
                    # Make court.availability_start timezone-aware
                    aware_court_start = court.availability_start.replace(tzinfo=start_date.tzinfo)
                    court_start = max(start_date, aware_court_start)
                else:
                    # Both are already compatible (both naive or both aware)
                    court_start = max(start_date, court.availability_start)
            
            court_end = end_date
            if court.availability_end:
                # Convert both to naive or make both aware to avoid timezone comparison errors
                if court.availability_end.tzinfo is not None and end_date.tzinfo is None:
                    # Make end_date timezone-aware
                    aware_end_date = end_date.replace(tzinfo=court.availability_end.tzinfo)
                    court_end = min(aware_end_date, court.availability_end)
                elif court.availability_end.tzinfo is None and end_date.tzinfo is not None:
                    # Make court.availability_end timezone-aware
                    aware_court_end = court.availability_end.replace(tzinfo=end_date.tzinfo)
                    court_end = min(end_date, aware_court_end)
                else:
                    # Both are already compatible (both naive or both aware)
                    court_end = min(end_date, court.availability_end)
            
            # Calculate free time slots
            free_slots = []
            last_end = court_start
            
            for match in matches:
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
            
        # Try to schedule each match
        scheduled = []
        match_order = 1  # Also assign a display order
        
        # First organize matches by stage, group, and bracket to maintain logical ordering
        ordered_unscheduled = []
        
        # Process group matches first
        for stage_id, stage_matches in matches_by_stage.items():
            group_matches = [m for m in stage_matches if m.group_id is not None]
            
            # Group the matches by group_id
            matches_by_group = defaultdict(list)
            for match in group_matches:
                matches_by_group[match.group_id].append(match)
                
            # Add group matches to the ordered list
            for group_id, group_matches in matches_by_group.items():
                ordered_unscheduled.extend(group_matches)
        
        # Then process bracket matches
        for stage_id, stage_matches in matches_by_stage.items():
            bracket_matches = [m for m in stage_matches if m.bracket_id is not None]
            
            # Group the matches by bracket_id
            matches_by_bracket = defaultdict(list)
            for match in bracket_matches:
                matches_by_bracket[match.bracket_id].append(match)
                
            # Add bracket matches to the ordered list in bracket_position order
            for bracket_id, bracket_matches in matches_by_bracket.items():
                sorted_bracket_matches = sorted(bracket_matches, key=lambda m: m.bracket_position or 0)
                ordered_unscheduled.extend(sorted_bracket_matches)
        
        # Add any remaining matches
        remaining = [m for m in unscheduled_matches if m not in ordered_unscheduled]
        ordered_unscheduled.extend(remaining)
        
        # Now schedule each match in the ordered list
        for match in ordered_unscheduled:
            # Determine match duration based on the stage's configuration
            stage = self.db.query(TournamentStage).filter(TournamentStage.id == match.stage_id).first()
            match_duration = timedelta(minutes=90)  # Default
            
            if stage:
                match_rules = stage.config.get("match_rules", {})
                if match_rules.get("time_limited", False) and match_rules.get("time_limit_minutes"):
                    match_duration = timedelta(minutes=match_rules.get("time_limit_minutes"))
            elif match.time_limit_minutes:
                match_duration = timedelta(minutes=match.time_limit_minutes)
                
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
        
        # Return the scheduled matches
        return scheduled
    
    def update_match(self, match_id: int, company_id: int, update_data: Dict[str, Any]) -> Match:
        """Update match details including results and scheduling"""
        # Get the match with ownership validation
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        
        if match.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this match")
        
        # Handle court_id updates
        if "court_id" in update_data and update_data["court_id"] != match.court_id:
            # Verify court exists and belongs to the tournament
            if update_data["court_id"] is not None:
                court = (
                    self.db.query(TournamentCourt)
                    .filter(
                        TournamentCourt.tournament_id == match.tournament_id,
                        TournamentCourt.court_id == update_data["court_id"],
                        TournamentCourt.deleted_at.is_(None)
                    )
                    .first()
                )
                
                if not court:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail="Court not found or not associated with this tournament"
                    )
        
        # Handle scheduling updates
        if (("scheduled_start" in update_data and update_data["scheduled_start"] != match.scheduled_start) or
            ("scheduled_end" in update_data and update_data["scheduled_end"] != match.scheduled_end)):
            
            # If we're updating scheduling, make sure there are no conflicts with other matches
            court_id = update_data.get("court_id", match.court_id)
            if court_id:
                start_time = update_data.get("scheduled_start", match.scheduled_start)
                end_time = update_data.get("scheduled_end", match.scheduled_end)
                
                # If start_time is set but end_time isn't, calculate it from time_limit if available
                if start_time and not end_time and "time_limit_minutes" in update_data:
                    end_time = start_time + timedelta(minutes=update_data["time_limit_minutes"])
                elif start_time and not end_time and match.time_limit_minutes:
                    end_time = start_time + timedelta(minutes=match.time_limit_minutes)
                
                # Check for conflicts only if we have both start and end times
                if start_time and end_time:
                    conflicting_matches = self.db.query(Match).filter(
                        Match.court_id == court_id,
                        Match.id != match_id,
                        Match.scheduled_start.isnot(None),
                        Match.scheduled_end.isnot(None),
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
                    
                    if conflicting_matches:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Court is already booked during this time (conflicts with match ID: {conflicting_matches[0].id})"
                        )
        
        # Handle match result updates
        if "match_result_status" in update_data or "games" in update_data or "winner_couple_id" in update_data:
            new_status = update_data.get("match_result_status", match.match_result_status)
            games = update_data.get("games", match.games)
            winner_id = update_data.get("winner_couple_id", match.winner_couple_id)
            
            # Validate the result status
            if new_status == MatchResultStatus.COMPLETED and not winner_id:
                # Calculate winner from games if not provided
                if games:
                    couple1_wins = sum(1 for game in games if game.get("winner_id") == match.couple1_id)
                    couple2_wins = sum(1 for game in games if game.get("winner_id") == match.couple2_id)
                    
                    if couple1_wins > couple2_wins:
                        update_data["winner_couple_id"] = match.couple1_id
                    elif couple2_wins > couple1_wins:
                        update_data["winner_couple_id"] = match.couple2_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Completed match must have games data or winner_couple_id"
                    )
            
            # If match is marked as completed, validate it has proper data
            if new_status == MatchResultStatus.COMPLETED:
                if not games:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Completed match must have games data"
                    )
        
        # Update the match with the new data
        for key, value in update_data.items():
            setattr(match, key, value)
        
        match.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(match)
        
        return match

    def get_match_by_id(self, match_id: int, company_id: int) -> Match:
        """Get a match by ID with ownership validation"""
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        
        if match.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this match")
            
        return match
    
    def get_tournament_matches(self, tournament_id: int, company_id: int) -> List[Match]:
        """Get all matches for a tournament"""
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
            
        matches = (
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
        
        return matches
    
    def get_stage_matches(self, stage_id: int, company_id: int) -> List[Match]:
        """Get all matches for a stage"""
        stage = (
            self.db.query(TournamentStage)
            .options(joinedload(TournamentStage.tournament))
            .filter(TournamentStage.id == stage_id)
            .first()
        )
        
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
        
        if stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this stage")
            
        matches = (
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
        
        return matches
    
    def get_group_matches(self, group_id: int, company_id: int) -> List[Match]:
        """Get all matches for a group"""
        group = (
            self.db.query(TournamentGroup)
            .options(
                joinedload(TournamentGroup.stage).joinedload(TournamentStage.tournament)
            )
            .filter(TournamentGroup.id == group_id)
            .first()
        )
        
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
        if group.stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this group")
            
        matches = (
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
        
        return matches
    
    def get_bracket_matches(self, bracket_id: int, company_id: int) -> List[Match]:
        """Get all matches for a bracket"""
        bracket = (
            self.db.query(TournamentBracket)
            .options(
                joinedload(TournamentBracket.stage).joinedload(TournamentStage.tournament)
            )
            .filter(TournamentBracket.id == bracket_id)
            .first()
        )
        
        if not bracket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bracket not found")
        
        if bracket.stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this bracket")
            
        matches = (
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
        
        return matches
    
    def validate_and_assign_court(
        self, 
        match_id: int, 
        tournament_id: int, 
        company_id: int, 
        court_id: int
    ) -> Match:
        """Validate court belongs to tournament/company and assign it to match"""
        # First validate the court exists and belongs to this tournament
        court = (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.court_id == court_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .first()
        )
        
        if not court:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Court ID {court_id} not found or not associated with this tournament"
            )
        
        # Get the match
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Match not found"
            )
        
        # Assign the court to the match
        match.court_id = court_id
        match.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(match)
        
        return match 