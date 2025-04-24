from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status

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
            
        return matches
        
    def auto_schedule_matches(
        self, 
        tournament_id: int, 
        company_id: int,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> List[Match]:
        """Automatically schedule unscheduled matches within a date range"""
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
            
            # Set court availability for the requested period
            court_start = max(start_date, court.availability_start) if court.availability_start else start_date
            court_end = min(end_date, court.availability_end) if court.availability_end else end_date
            
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
            
        # Define a default match duration if not specified
        default_match_duration = timedelta(minutes=90)
        
        # Try to schedule each match
        scheduled = []
        
        for match in unscheduled_matches:
            # Determine match duration
            if match.time_limit_minutes:
                match_duration = timedelta(minutes=match.time_limit_minutes)
            else:
                match_duration = default_match_duration
                
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
                match.updated_at = datetime.now()
                
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