from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from collections import defaultdict

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.match_scheduling_service import MatchSchedulingService
from app.core.constants import MatchResultStatus
from app.models.tournament import Match, Tournament, TournamentStage, TournamentGroup
from sqlalchemy.orm import joinedload

router = APIRouter()

# Match ordering endpoints
@router.post("/tournament/{tournament_id}/calculate-match-order", response_model=List[schemas.MatchOut])
def calculate_tournament_match_order(
    tournament_id: int,
    strategy: Optional[str] = Query("balanced_load", description="Ordering strategy: balanced_load, court_efficient, time_sequential, group_clustered"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Calculate and apply optimal match ordering for an entire tournament.
    
    Strategies:
    - balanced_load: Balance groups and minimize couple rest conflicts (recommended)
    - court_efficient: Maximize court utilization
    - time_sequential: Optimize for sequential time scheduling  
    - group_clustered: Keep same-group matches together
    """
    from app.services.match_ordering_service import MatchOrderingService
    
    ordering_service = MatchOrderingService(db)
    ordered_matches = ordering_service.calculate_optimal_match_order(
        tournament_id=tournament_id,
        company_id=current_company.id,
        optimization_strategy=strategy
    )
    
    return ordered_matches

@router.post("/stage/{stage_id}/calculate-match-order", response_model=List[schemas.MatchOut])
def calculate_stage_match_order(
    stage_id: int,
    strategy: Optional[str] = Query("balanced_load", description="Ordering strategy: balanced_load, court_efficient, time_sequential, group_clustered"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Calculate and apply optimal match ordering for a specific stage.
    
    Strategies:
    - balanced_load: Balance groups and minimize couple rest conflicts (recommended)
    - court_efficient: Maximize court utilization
    - time_sequential: Optimize for sequential time scheduling  
    - group_clustered: Keep same-group matches together
    """
    from app.services.match_ordering_service import MatchOrderingService
    
    # First, get the stage and its tournament_id
    stage = (
        db.query(TournamentStage)
        .join(Tournament)
        .filter(
            TournamentStage.id == stage_id,
            Tournament.company_id == current_company.id,
            TournamentStage.deleted_at.is_(None)
        )
        .first()
    )
    
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage not found or unauthorized access"
        )
    
    ordering_service = MatchOrderingService(db)
    ordered_matches = ordering_service.calculate_optimal_match_order(
        tournament_id=stage.tournament_id,  # Now we have the actual tournament_id
        company_id=current_company.id,
        stage_id=stage_id,
        optimization_strategy=strategy
    )
    
    return ordered_matches

# Match order info endpoints
@router.get("/tournament/{tournament_id}/match-order-info")
def get_tournament_match_order_info(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Get comprehensive information about the current match ordering for a tournament.
    
    Returns detailed tournament state including:
    - Live matches (currently being played)
    - Next matches (ready to start) 
    - All pending matches (not yet started)
    - Completed matches (finished games)
    - Tournament progress and court information
    
    This information updates dynamically as match statuses change.
    """
    from app.services.match_ordering_service import MatchOrderingService
    
    ordering_service = MatchOrderingService(db)
    
    try:
        # Get tournament info
        tournament = ordering_service._validate_tournament_access(tournament_id, current_company.id)
        stages = ordering_service._get_tournament_stages(tournament_id, current_company.id)
        courts = ordering_service._get_tournament_courts(tournament_id)
        
        # Get ALL matches for this tournament (not just pending)
        all_matches = (
            db.query(Match)
            .join(Tournament)
            .filter(
                Match.tournament_id == tournament_id,
                Tournament.company_id == current_company.id
            )
            .options(joinedload(Match.stage), joinedload(Match.group), joinedload(Match.bracket))
            .order_by(Match.display_order.asc().nullslast(), Match.id)
            .all()
        )
        
        # Categorize matches by status
        pending_matches = [m for m in all_matches if m.match_result_status == MatchResultStatus.PENDING]
        completed_matches = [m for m in all_matches if m.match_result_status == MatchResultStatus.COMPLETED]
        
        # Determine live matches and next matches based on current state
        num_courts = len(courts)
        
        # Live matches: First N pending matches where N = number of courts
        # These are the matches that should be currently playing
        live_matches = pending_matches[:num_courts] if num_courts > 0 else []
        
        # Next matches: Next batch after live matches  
        next_batch_size = min(num_courts, len(pending_matches) - len(live_matches))
        next_matches = pending_matches[len(live_matches):len(live_matches) + next_batch_size] if next_batch_size > 0 else []
        
        # Calculate tournament progress
        total_matches = len(all_matches)
        completed_count = len(completed_matches)
        progress_percentage = round((completed_count / total_matches * 100), 1) if total_matches > 0 else 0
        
        # Helper function to format match info
        def format_match_info(match: Match) -> Dict[str, Any]:
            return {
                "id": match.id,
                "display_order": match.display_order,
                "couple1_id": match.couple1_id,
                "couple2_id": match.couple2_id,
                "winner_couple_id": match.winner_couple_id,
                "court_id": match.court_id,
                "stage_id": match.stage_id,
                "stage_name": match.stage.name if match.stage else None,
                "stage_type": match.stage.stage_type if match.stage else None,
                "group_id": match.group_id,
                "group_name": match.group.name if match.group else None,
                "bracket_id": match.bracket_id,
                "bracket_type": match.bracket.bracket_type if match.bracket else None,
                "round_number": match.round_number,
                "order_in_group": match.order_in_group,
                "order_in_stage": match.order_in_stage,
                "scheduled_start": match.scheduled_start.isoformat() if match.scheduled_start else None,
                "scheduled_end": match.scheduled_end.isoformat() if match.scheduled_end else None,
                "match_result_status": match.match_result_status,
                "games": match.games,
                "created_at": match.created_at.isoformat(),
                "updated_at": match.updated_at.isoformat()
            }
        
        # Group completed matches by stage for better organization
        completed_by_stage = defaultdict(list)
        for match in completed_matches:
            stage_key = f"{match.stage.name}" if match.stage else "Unknown Stage"
            completed_by_stage[stage_key].append(format_match_info(match))
        
        return {
            "tournament_id": tournament_id,
            "tournament_name": tournament.name,
            "tournament_start_date": tournament.start_date.isoformat(),
            "tournament_end_date": tournament.end_date.isoformat(),
            
            # Tournament structure
            "total_stages": len(stages),
            "total_courts": num_courts,
            "total_matches": total_matches,
            
            # Progress tracking
            "completed_matches_count": completed_count,
            "pending_matches_count": len(pending_matches),
            "progress_percentage": progress_percentage,
            
            # Current state (updates dynamically as matches complete)
            "live_matches": [format_match_info(m) for m in live_matches],
            "next_matches": [format_match_info(m) for m in next_matches],
            
            # All match lists for comprehensive view
            "all_pending_matches": [format_match_info(m) for m in pending_matches],
            "completed_matches_by_stage": dict(completed_by_stage),
            
            # Court and stage information
            "courts": [
                {
                    "id": c.court_id,
                    "tournament_court_id": c.id,
                    "availability_start": c.availability_start.isoformat() if c.availability_start else None,
                    "availability_end": c.availability_end.isoformat() if c.availability_end else None,
                    "court_name": c.court.name if hasattr(c, 'court') and c.court else f"Court {c.court_id}"
                } for c in courts
            ],
            "stages": [
                {
                    "id": s.id,
                    "name": s.name,
                    "stage_type": s.stage_type,
                    "order": s.order,
                    "config": s.config
                } for s in stages
            ],
            
            # Algorithm insights
            "ordering_strategy_used": "balanced_load",  # Could be made dynamic
            "last_updated": datetime.now().isoformat(),
            
            # Quick stats for frontend display
            "quick_stats": {
                "matches_in_progress": len(live_matches),
                "matches_waiting": len(next_matches),
                "matches_remaining": len(pending_matches),
                "matches_completed": completed_count,
                "estimated_completion": f"{progress_percentage}% complete"
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tournament match information: {str(e)}"
        )

@router.get("/tournament/{tournament_id}/stage/{stage_id}/match-order-info")
def get_stage_match_order_info(
    tournament_id: int,
    stage_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Get comprehensive information about the current match ordering for a specific tournament stage.
    
    Returns detailed stage state including:
    - Live matches in this stage (currently being played)
    - Next matches in this stage (ready to start) 
    - All pending matches in this stage (not yet started)
    - Completed matches in this stage (finished games)
    - Stage progress and court information
    
    This information updates dynamically as match statuses change.
    """
    from app.services.match_ordering_service import MatchOrderingService
    
    ordering_service = MatchOrderingService(db)
    
    try:
        # Get tournament info
        tournament = ordering_service._validate_tournament_access(tournament_id, current_company.id)
        stages = ordering_service._get_tournament_stages(tournament_id, current_company.id)
        courts = ordering_service._get_tournament_courts(tournament_id)
        
        # Validate that the stage exists and belongs to this tournament
        stage = db.query(TournamentStage).filter(
            TournamentStage.id == stage_id,
            TournamentStage.tournament_id == tournament_id,
            TournamentStage.deleted_at.is_(None)
        ).first()
        
        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stage {stage_id} not found in tournament {tournament_id}"
            )
        
        # Get ALL matches for this specific stage
        all_stage_matches = (
            db.query(Match)
            .join(Tournament)
            .filter(
                Match.tournament_id == tournament_id,
                Match.stage_id == stage_id,
                Tournament.company_id == current_company.id
            )
            .options(joinedload(Match.stage), joinedload(Match.group), joinedload(Match.bracket))
            .order_by(Match.display_order.asc().nullslast(), Match.order_in_stage.asc().nullslast(), Match.id)
            .all()
        )
        
        # Categorize matches by status
        pending_matches = [m for m in all_stage_matches if m.match_result_status == MatchResultStatus.PENDING]
        completed_matches = [m for m in all_stage_matches if m.match_result_status == MatchResultStatus.COMPLETED]
        
        # Determine live matches and next matches based on current state
        num_courts = len(courts)
        
        # Live matches: First N pending matches where N = number of courts
        # These are the matches that should be currently playing
        live_matches = pending_matches[:num_courts] if num_courts > 0 else []
        
        # Next matches: Next batch after live matches  
        next_batch_size = min(num_courts, len(pending_matches) - len(live_matches))
        next_matches = pending_matches[len(live_matches):len(live_matches) + next_batch_size] if next_batch_size > 0 else []
        
        # Calculate stage progress
        total_stage_matches = len(all_stage_matches)
        completed_count = len(completed_matches)
        progress_percentage = round((completed_count / total_stage_matches * 100), 1) if total_stage_matches > 0 else 0
        
        # Helper function to format match info
        def format_match_info(match: Match) -> Dict[str, Any]:
            return {
                "id": match.id,
                "display_order": match.display_order,
                "couple1_id": match.couple1_id,
                "couple2_id": match.couple2_id,
                "winner_couple_id": match.winner_couple_id,
                "court_id": match.court_id,
                "stage_id": match.stage_id,
                "stage_name": match.stage.name if match.stage else None,
                "stage_type": match.stage.stage_type if match.stage else None,
                "group_id": match.group_id,
                "group_name": match.group.name if match.group else None,
                "bracket_id": match.bracket_id,
                "bracket_type": match.bracket.bracket_type if match.bracket else None,
                "round_number": match.round_number,
                "order_in_group": match.order_in_group,
                "order_in_stage": match.order_in_stage,
                "scheduled_start": match.scheduled_start.isoformat() if match.scheduled_start else None,
                "scheduled_end": match.scheduled_end.isoformat() if match.scheduled_end else None,
                "match_result_status": match.match_result_status,
                "games": match.games,
                "created_at": match.created_at.isoformat(),
                "updated_at": match.updated_at.isoformat()
            }
        
        # Get groups in this stage for better organization
        stage_groups = db.query(TournamentGroup).filter(
            TournamentGroup.stage_id == stage_id,
            TournamentGroup.deleted_at.is_(None)
        ).all()
        
        # Group completed matches by group for better organization within the stage
        completed_by_group = defaultdict(list)
        for match in completed_matches:
            group_key = f"{match.group.name}" if match.group else "No Group"
            completed_by_group[group_key].append(format_match_info(match))
        
        return {
            "tournament_id": tournament_id,
            "tournament_name": tournament.name,
            "tournament_start_date": tournament.start_date.isoformat(),
            "tournament_end_date": tournament.end_date.isoformat(),
            
            # Stage information
            "stage_id": stage_id,
            "stage_name": stage.name,
            "stage_type": stage.stage_type,
            "stage_order": stage.order,
            "stage_config": stage.config,
            
            # Stage structure
            "total_courts": num_courts,
            "total_matches_in_stage": total_stage_matches,
            "total_groups_in_stage": len(stage_groups),
            
            # Progress tracking (stage-specific)
            "completed_matches_count": completed_count,
            "pending_matches_count": len(pending_matches),
            "progress_percentage": progress_percentage,
            
            # Current state (updates dynamically as matches complete)
            "live_matches": [format_match_info(m) for m in live_matches],
            "next_matches": [format_match_info(m) for m in next_matches],
            
            # All match lists for comprehensive view
            "all_pending_matches": [format_match_info(m) for m in pending_matches],
            "completed_matches_by_group": dict(completed_by_group),
            
            # Court information
            "courts": [
                {
                    "id": c.court_id,
                    "tournament_court_id": c.id,
                    "availability_start": c.availability_start.isoformat() if c.availability_start else None,
                    "availability_end": c.availability_end.isoformat() if c.availability_end else None,
                    "court_name": c.court.name if hasattr(c, 'court') and c.court else f"Court {c.court_id}"
                } for c in courts
            ],
            
            # Groups in this stage
            "groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "stage_id": g.stage_id
                } for g in stage_groups
            ],
            
            # Algorithm insights
            "ordering_strategy_used": "balanced_load",  # Could be made dynamic
            "last_updated": datetime.now().isoformat(),
            
            # Quick stats for frontend display
            "quick_stats": {
                "matches_in_progress": len(live_matches),
                "matches_waiting": len(next_matches),
                "matches_remaining": len(pending_matches),
                "matches_completed": completed_count,
                "estimated_completion": f"{progress_percentage}% complete"
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving stage match information: {str(e)}"
        )

# Court and time scheduling endpoints
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
    """Schedule a specific match to a court and time"""
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
    """Remove scheduling from a match"""
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.unschedule_match(match_id, current_company.id)

@router.get("/tournament/{tournament_id}/court-availability", response_model=List[dict])
def get_court_availability(
    tournament_id: int,
    date: date,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """Get court availability for a specific date"""
    # Convert date to datetime
    date_as_datetime = datetime.combine(date, datetime.min.time())
    
    scheduling_service = MatchSchedulingService(db)
    return scheduling_service.get_court_availability(tournament_id, current_company.id, date_as_datetime)

@router.post("/tournament/{tournament_id}/auto-schedule", response_model=List[schemas.MatchOut])
def auto_schedule_matches(
    tournament_id: int,
    start_date: Optional[str] = None,  # Make it optional for order-only mode
    end_date: Optional[str] = None,
    order_only: bool = False,  # Add order-only parameter
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Auto-schedule matches for a tournament.
    
    - order_only: If True, only assign courts and sequence order without specific times.
    - start_date: Required if order_only=False. Date in YYYY-MM-DD format or ISO datetime.
    - end_date: Optional end date in YYYY-MM-DD format or ISO datetime.
    """
    scheduling_service = MatchSchedulingService(db)
    
    # If order_only mode is requested, don't need date parameters
    if order_only:
        return scheduling_service.auto_order_matches(tournament_id, current_company.id)
        
    # For timed scheduling, we need at least a start date
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date is required for timed scheduling. Use order_only=True for order-only scheduling."
        )
        
    try:
        # Parse dates as naive datetime objects (no timezone)
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        # Strip timezone info to make it naive
        start_datetime = start_datetime.replace(tzinfo=None)
        
        end_datetime = None
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Strip timezone info to make it naive
            end_datetime = end_datetime.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
        )
        
    return scheduling_service.auto_schedule_matches(
        tournament_id=tournament_id,
        company_id=current_company.id,
        start_date=start_datetime,
        end_date=end_datetime,
        order_only=order_only
    )