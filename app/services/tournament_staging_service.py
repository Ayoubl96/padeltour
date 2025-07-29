from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status
import random
import math

from app.models.tournament import (
    Tournament, TournamentStage, TournamentGroup, TournamentGroupCouple,
    TournamentBracket, Match, TournamentCouple, CoupleStats, TournamentCourt
)
from app.core.constants import (
    StageType, BracketType, ScoringType, WinCriteria, AssignmentMethod,
    SchedulingPriority, TiebreakerOption, MatchResultStatus, MatchFormat,
    DEFAULT_STAGE_CONFIG
)
from app.services.match_scheduling_service import MatchSchedulingService
from app.services.couple_stats_service import CoupleStatsService


class TournamentStagingService:
    def __init__(self, db: Session):
        self.db = db
        self.couple_stats_service = CoupleStatsService(db)

    # ==============================
    # Stage Management Methods
    # ==============================
    def create_stage(self, 
                    tournament_id: int,
                    company_id: int, 
                    name: str,
                    stage_type: str,
                    order: int,
                    config: Dict[str, Any] = None) -> TournamentStage:
        """Create a new tournament stage"""
        # Validate tournament ownership
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Use default config if not provided
        if config is None:
            config = DEFAULT_STAGE_CONFIG
            
        # Validate stage type
        if stage_type not in [StageType.GROUP, StageType.ELIMINATION]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage type. Must be one of {[t.value for t in StageType]}"
            )
            
        # Check if a stage with the same order already exists
        existing_stage = self.db.query(TournamentStage).filter(
            TournamentStage.tournament_id == tournament_id,
            TournamentStage.order == order,
            TournamentStage.deleted_at.is_(None)
        ).first()
        
        if existing_stage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A stage with order {order} already exists for this tournament"
            )
        
        # Check if there's a soft-deleted stage with the same order
        soft_deleted_stage = self.db.query(TournamentStage).filter(
            TournamentStage.tournament_id == tournament_id,
            TournamentStage.order == order,
            TournamentStage.deleted_at.isnot(None)
        ).first()
        
        if soft_deleted_stage:
            # Before deleting the stage, we need to delete its related brackets first
            # to avoid foreign key constraint violations
            brackets = self.db.query(TournamentBracket).filter(
                TournamentBracket.stage_id == soft_deleted_stage.id
            ).all()
            
            for bracket in brackets:
                self.db.delete(bracket)
            
            # Also delete related groups
            groups = self.db.query(TournamentGroup).filter(
                TournamentGroup.stage_id == soft_deleted_stage.id
            ).all()
            
            for group in groups:
                # Delete group-couple associations first
                group_couples = self.db.query(TournamentGroupCouple).filter(
                    TournamentGroupCouple.group_id == group.id
                ).all()
                
                for group_couple in group_couples:
                    self.db.delete(group_couple)
                
                # Delete the group
                self.db.delete(group)
            
            # Now we can safely delete the stage
            self.db.delete(soft_deleted_stage)
            self.db.commit()
        
        # Create the new stage
        new_stage = TournamentStage(
            tournament_id=tournament_id,
            name=name,
            stage_type=stage_type,
            order=order,
            config=config
        )
        
        self.db.add(new_stage)
        self.db.commit()
        self.db.refresh(new_stage)
        
        # For elimination stages, automatically create the main bracket
        if stage_type == StageType.ELIMINATION:
            main_bracket = TournamentBracket(
                stage_id=new_stage.id,
                bracket_type=BracketType.MAIN
            )
            self.db.add(main_bracket)
            self.db.commit()
        
        return new_stage
        
    def get_tournament_stages(self, tournament_id: int, company_id: int) -> List[TournamentStage]:
        """Get all stages for a tournament"""
        # Validate tournament ownership
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Get all active stages, ordered by their sequence
        stages = (
            self.db.query(TournamentStage)
            .filter(
                TournamentStage.tournament_id == tournament_id,
                TournamentStage.deleted_at.is_(None)
            )
            .order_by(TournamentStage.order)
            .all()
        )
        
        return stages
        
    def get_stage_by_id(self, stage_id: int, company_id: int) -> TournamentStage:
        """Get a tournament stage by ID with company validation"""
        stage = (
            self.db.query(TournamentStage)
            .options(joinedload(TournamentStage.tournament))
            .filter(TournamentStage.id == stage_id)
            .filter(TournamentStage.deleted_at.is_(None))
            .first()
        )
        
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
        
        if stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this stage")
        
        return stage
        
    def update_stage(self, stage_id: int, company_id: int, update_data: Dict[str, Any]) -> TournamentStage:
        """Update a tournament stage"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Check if we're updating the order
        if "order" in update_data and update_data["order"] != stage.order:
            new_order = update_data["order"]
            
            # Check if a stage with the new order already exists
            existing_stage = self.db.query(TournamentStage).filter(
                TournamentStage.tournament_id == stage.tournament_id,
                TournamentStage.order == new_order,
                TournamentStage.id != stage_id,
                TournamentStage.deleted_at.is_(None)
            ).first()
            
            if existing_stage:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A stage with order {new_order} already exists for this tournament"
                )
        
        # Apply the updates
        for key, value in update_data.items():
            setattr(stage, key, value)
        
        stage.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(stage)
        
        return stage
        
    def delete_stage(self, stage_id: int, company_id: int) -> None:
        """Delete a tournament stage (soft delete)"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Soft delete the stage
        stage.deleted_at = datetime.now()
        
        # Also delete associated groups, brackets, matches
        for group in stage.groups:
            group.deleted_at = datetime.now()
            
            # Delete group-couple associations
            group_couples = self.db.query(TournamentGroupCouple).filter(
                TournamentGroupCouple.group_id == group.id
            ).all()
            
            for group_couple in group_couples:
                group_couple.deleted_at = datetime.now()
        
        for bracket in stage.brackets:
            bracket.deleted_at = datetime.now()
        
        # Don't delete matches - just remove their association
        matches = self.db.query(Match).filter(Match.stage_id == stage_id).all()
        for match in matches:
            match.stage_id = None
            match.group_id = None
            match.bracket_id = None
        
        self.db.commit()
        
        return None
        
    # ==============================
    # Group Management Methods
    # ==============================
    def create_group(self, stage_id: int, company_id: int, name: str) -> TournamentGroup:
        """Create a new group in a tournament stage"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Verify this is a group stage
        if stage.stage_type != StageType.GROUP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Groups can only be created in a group stage"
            )
            
        # Create the new group
        new_group = TournamentGroup(
            stage_id=stage_id,
            name=name
        )
        
        self.db.add(new_group)
        self.db.commit()
        self.db.refresh(new_group)
        
        return new_group
        
    def get_stage_groups(self, stage_id: int, company_id: int) -> List[TournamentGroup]:
        """Get all groups in a tournament stage"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Get all active groups for this stage
        groups = (
            self.db.query(TournamentGroup)
            .filter(
                TournamentGroup.stage_id == stage_id,
                TournamentGroup.deleted_at.is_(None)
            )
            .all()
        )
        
        return groups
        
    def get_group_by_id(self, group_id: int, company_id: int) -> TournamentGroup:
        """Get a tournament group by ID with company validation"""
        group = (
            self.db.query(TournamentGroup)
            .options(joinedload(TournamentGroup.stage).joinedload(TournamentStage.tournament))
            .filter(TournamentGroup.id == group_id)
            .filter(TournamentGroup.deleted_at.is_(None))
            .first()
        )
        
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
        if group.stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this group")
        
        return group
        
    def update_group(self, group_id: int, company_id: int, name: str) -> TournamentGroup:
        """Update a tournament group"""
        # Get the group with ownership validation
        group = self.get_group_by_id(group_id, company_id)
        
        # Update the group name
        group.name = name
        group.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(group)
        
        return group
        
    def delete_group(self, group_id: int, company_id: int) -> None:
        """Delete a tournament group (soft delete)"""
        # Get the group with ownership validation
        group = self.get_group_by_id(group_id, company_id)
        
        # Soft delete the group
        group.deleted_at = datetime.now()
        
        # Also delete group-couple associations
        group_couples = self.db.query(TournamentGroupCouple).filter(
            TournamentGroupCouple.group_id == group_id
        ).all()
        
        for group_couple in group_couples:
            group_couple.deleted_at = datetime.now()
        
        # Don't delete matches - just remove their association with this group
        matches = self.db.query(Match).filter(Match.group_id == group_id).all()
        for match in matches:
            match.group_id = None
        
        self.db.commit()
        
        return None

    # ==============================
    # Group Couple Assignment Methods
    # ==============================
    def add_couple_to_group(self, group_id: int, couple_id: int, company_id: int) -> TournamentGroupCouple:
        """Add a couple to a tournament group"""
        # Get the group with ownership validation
        group = self.get_group_by_id(group_id, company_id)
        
        # Verify the couple exists and belongs to the same tournament
        couple = self.db.query(TournamentCouple).filter(
            TournamentCouple.id == couple_id,
            TournamentCouple.deleted_at.is_(None)
        ).first()
        
        if not couple:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Couple not found")
        
        # Verify the couple belongs to the same tournament as the group
        if couple.tournament_id != group.stage.tournament_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Couple belongs to a different tournament"
            )
        
        # Check if the couple is already in another group in this stage
        existing_assignment = (
            self.db.query(TournamentGroupCouple)
            .join(TournamentGroup)
            .filter(
                TournamentGroupCouple.couple_id == couple_id,
                TournamentGroup.stage_id == group.stage_id,
                TournamentGroupCouple.deleted_at.is_(None),
                TournamentGroup.deleted_at.is_(None)
            )
            .first()
        )
        
        if existing_assignment:
            if existing_assignment.group_id == group_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Couple is already in this group"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Couple is already assigned to another group in this stage"
                )
        
        # Check for soft-deleted records with the same group_id and couple_id
        soft_deleted_record = (
            self.db.query(TournamentGroupCouple)
            .filter(
                TournamentGroupCouple.group_id == group_id,
                TournamentGroupCouple.couple_id == couple_id,
                TournamentGroupCouple.deleted_at.is_not(None)
            )
            .first()
        )
        
        if soft_deleted_record:
            # Update the existing record instead of creating a new one
            soft_deleted_record.deleted_at = None
            self.db.commit()
            self.db.refresh(soft_deleted_record)
            
            # Initialize or update the couple stats for this group
            stats = self.db.query(CoupleStats).filter(
                CoupleStats.tournament_id == group.stage.tournament_id,
                CoupleStats.couple_id == couple_id,
                CoupleStats.group_id == group_id
            ).first()
            
            if not stats:
                stats = CoupleStats(
                    tournament_id=group.stage.tournament_id,
                    couple_id=couple_id,
                    group_id=group_id
                )
                self.db.add(stats)
                self.db.commit()
            
            return soft_deleted_record
        else:
            # Create a new group-couple association
            new_group_couple = TournamentGroupCouple(
                group_id=group_id,
                couple_id=couple_id
            )
            
            self.db.add(new_group_couple)
            
            # Initialize the couple stats for this group
            stats = CoupleStats(
                tournament_id=group.stage.tournament_id,
                couple_id=couple_id,
                group_id=group_id
            )
            
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(new_group_couple)
            
            return new_group_couple
        
    def remove_couple_from_group(self, group_id: int, couple_id: int, company_id: int) -> None:
        """Remove a couple from a tournament group"""
        # Get the group with ownership validation
        group = self.get_group_by_id(group_id, company_id)
        
        # Find the group-couple association
        group_couple = self.db.query(TournamentGroupCouple).filter(
            TournamentGroupCouple.group_id == group_id,
            TournamentGroupCouple.couple_id == couple_id,
            TournamentGroupCouple.deleted_at.is_(None)
        ).first()
        
        if not group_couple:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couple not found in this group"
            )
        
        # Soft delete the group-couple association
        group_couple.deleted_at = datetime.now()
        
        # Also delete the couple stats for this group
        stats = self.db.query(CoupleStats).filter(
            CoupleStats.couple_id == couple_id,
            CoupleStats.group_id == group_id
        ).first()
        
        if stats:
            self.db.delete(stats)
        
        self.db.commit()
        
        return None
        
    def get_group_couples(self, group_id: int, company_id: int) -> List[TournamentCouple]:
        """Get all couples in a tournament group"""
        # Get the group with ownership validation
        group = self.get_group_by_id(group_id, company_id)
        
        # Get all couples in this group
        couples = (
            self.db.query(TournamentCouple)
            .join(TournamentGroupCouple)
            .filter(
                TournamentGroupCouple.group_id == group_id,
                TournamentGroupCouple.deleted_at.is_(None),
                TournamentCouple.deleted_at.is_(None)
            )
            .all()
        )
        
        return couples
        
    def assign_couples_to_groups(
        self, 
        stage_id: int, 
        company_id: int, 
        method: str = AssignmentMethod.RANDOM
    ) -> List[TournamentGroupCouple]:
        """Auto-assign couples to groups in a stage based on specified method"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Verify this is a group stage
        if stage.stage_type != StageType.GROUP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Automatic assignment is only available for group stages"
            )
        
        # Get all groups in this stage
        groups = self.get_stage_groups(stage_id, company_id)
        if not groups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No groups found in this stage"
            )
        
        # Get all couples in the tournament that aren't already assigned to a group in this stage
        assigned_couples = (
            self.db.query(TournamentCouple.id)
            .join(TournamentGroupCouple)
            .join(TournamentGroup)
            .filter(
                TournamentCouple.tournament_id == stage.tournament_id,
                TournamentGroup.stage_id == stage_id,
                TournamentGroupCouple.deleted_at.is_(None),
                TournamentGroup.deleted_at.is_(None)
            )
        )
        
        available_couples = (
            self.db.query(TournamentCouple)
            .filter(
                TournamentCouple.tournament_id == stage.tournament_id,
                TournamentCouple.deleted_at.is_(None),
                ~TournamentCouple.id.in_(assigned_couples)
            )
            .all()
        )
        
        if not available_couples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No available couples to assign"
            )
        
        # Perform the assignment based on the specified method
        assignments = []
        
        if method == AssignmentMethod.RANDOM:
            # Randomly shuffle the couples
            random.shuffle(available_couples)
            
            # Assign couples evenly across groups
            group_index = 0
            for couple in available_couples:
                group = groups[group_index % len(groups)]
                
                # Check for soft-deleted records with the same group_id and couple_id
                soft_deleted_record = (
                    self.db.query(TournamentGroupCouple)
                    .filter(
                        TournamentGroupCouple.group_id == group.id,
                        TournamentGroupCouple.couple_id == couple.id,
                        TournamentGroupCouple.deleted_at.is_not(None)
                    )
                    .first()
                )
                
                if soft_deleted_record:
                    # Update the existing record instead of creating a new one
                    soft_deleted_record.deleted_at = None
                    assignments.append(soft_deleted_record)
                else:
                    # Create a new group-couple association
                    assignment = TournamentGroupCouple(
                        group_id=group.id,
                        couple_id=couple.id
                    )
                    self.db.add(assignment)
                    assignments.append(assignment)
                
                # Initialize the couple stats for this group
                stats = self.db.query(CoupleStats).filter(
                    CoupleStats.tournament_id == stage.tournament_id,
                    CoupleStats.couple_id == couple.id,
                    CoupleStats.group_id == group.id
                ).first()
                
                if not stats:
                    stats = CoupleStats(
                        tournament_id=stage.tournament_id,
                        couple_id=couple.id,
                        group_id=group.id
                    )
                    self.db.add(stats)
                
                group_index += 1
                
        elif method == AssignmentMethod.BALANCED:
            # TODO: Implement balanced assignment logic based on couple skill/ranking
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Balanced assignment method is not yet implemented"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid assignment method. Must be one of {[m.value for m in AssignmentMethod]}"
            )
        
        self.db.commit()
        
        # Refresh all assignments to get their IDs
        for assignment in assignments:
            self.db.refresh(assignment)
        
        return assignments
    
    # ==============================
    # Group Standings Methods
    # ==============================
    def calculate_group_standings(self, group_id: int, company_id: int) -> List[Dict[str, Any]]:
        """Calculate the standings for a tournament group"""
        # Get the group with ownership validation
        group = self.get_group_by_id(group_id, company_id)
        
        # Get the stage config for scoring and tiebreakers
        stage = group.stage
        scoring_system = stage.config.get("scoring_system", {})
        advancement_rules = stage.config.get("advancement_rules", {})
        tiebreakers = advancement_rules.get("tiebreaker", [])
        
        # Get all couples in this group with their stats
        stats = (
            self.db.query(CoupleStats)
            .options(joinedload(CoupleStats.couple))
            .filter(
                CoupleStats.group_id == group_id
            )
            .all()
        )
        
        if not stats:
            return []
        
        # Create standings list
        standings = []
        for stat in stats:
            entry = {
                "couple_id": stat.couple_id,
                "couple_name": stat.couple.name,
                "matches_played": stat.matches_played,
                "matches_won": stat.matches_won,
                "matches_lost": stat.matches_lost,
                "matches_drawn": stat.matches_drawn,
                "games_won": stat.games_won,
                "games_lost": stat.games_lost,
                "total_points": stat.total_points,
                "games_diff": stat.games_won - stat.games_lost
            }
            standings.append(entry)
        
        # Sort the standings based on tiebreakers
        def get_sort_key(entry, tiebreaker):
            if tiebreaker == TiebreakerOption.POINTS:
                return entry["total_points"]
            elif tiebreaker == TiebreakerOption.GAMES_DIFF:
                return entry["games_diff"]
            elif tiebreaker == TiebreakerOption.GAMES_WON:
                return entry["games_won"]
            elif tiebreaker == TiebreakerOption.MATCHES_WON:
                return entry["matches_won"]
            else:  # Head-to-head handled separately
                return 0
        
        # First sort by points (primary sort)
        standings.sort(key=lambda x: x["total_points"], reverse=True)
        
        # Then apply tiebreakers for tied positions
        i = 0
        while i < len(standings):
            j = i + 1
            # Find all entries tied with the current one
            while j < len(standings) and standings[j]["total_points"] == standings[i]["total_points"]:
                j += 1
                
            # If we have a tie, apply tiebreakers
            if j - i > 1:
                tied_entries = standings[i:j]
                
                # Apply each tiebreaker in sequence
                for tiebreaker in tiebreakers:
                    if tiebreaker == TiebreakerOption.HEAD_TO_HEAD:
                        # For head-to-head, need to examine matches between tied couples
                        if len(tied_entries) == 2:
                            # Only works for 2 tied teams
                            couple1_id = tied_entries[0]["couple_id"]
                            couple2_id = tied_entries[1]["couple_id"]
                            
                            # Find matches between these two couples
                            h2h_matches = self.db.query(Match).filter(
                                Match.group_id == group_id,
                                ((Match.couple1_id == couple1_id) & (Match.couple2_id == couple2_id)) |
                                ((Match.couple1_id == couple2_id) & (Match.couple2_id == couple1_id)),
                                Match.winner_couple_id.isnot(None)
                            ).all()
                            
                            # Count wins for each couple
                            couple1_wins = sum(1 for m in h2h_matches if m.winner_couple_id == couple1_id)
                            couple2_wins = sum(1 for m in h2h_matches if m.winner_couple_id == couple2_id)
                            
                            # If one couple won more h2h matches, sort accordingly
                            if couple1_wins > couple2_wins:
                                # No need to change order
                                pass
                            elif couple2_wins > couple1_wins:
                                # Swap positions
                                standings[i], standings[i+1] = standings[i+1], standings[i]
                            # If tied in h2h, continue to next tiebreaker
                    else:
                        # For non-head-to-head tiebreakers, sort the tied entries
                        tied_entries.sort(key=lambda x: get_sort_key(x, tiebreaker), reverse=True)
                        # Replace the tied section with the sorted entries
                        standings[i:j] = tied_entries
                            
            # Move to the next unprocessed position
            i = j
        
        # Add position to each entry
        for i, entry in enumerate(standings):
            entry["position"] = i + 1
        
        return standings

    # ==============================
    # Bracket Management Methods
    # ==============================
    def create_bracket(self, stage_id: int, company_id: int, bracket_type: str) -> TournamentBracket:
        """Create a new bracket in a tournament stage"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Verify this is an elimination stage
        if stage.stage_type != StageType.ELIMINATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brackets can only be created in an elimination stage"
            )
            
        # Validate bracket type
        if bracket_type not in [BracketType.MAIN, BracketType.SILVER, BracketType.BRONZE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bracket type. Must be one of {[t.value for t in BracketType]}"
            )
            
        # Check if a bracket of this type already exists in this stage
        existing_bracket = self.db.query(TournamentBracket).filter(
            TournamentBracket.stage_id == stage_id,
            TournamentBracket.bracket_type == bracket_type,
            TournamentBracket.deleted_at.is_(None)
        ).first()
        
        if existing_bracket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {bracket_type} bracket already exists for this stage"
            )
            
        # Create the new bracket
        new_bracket = TournamentBracket(
            stage_id=stage_id,
            bracket_type=bracket_type
        )
        
        self.db.add(new_bracket)
        self.db.commit()
        self.db.refresh(new_bracket)
        
        return new_bracket
        
    def get_stage_brackets(self, stage_id: int, company_id: int) -> List[TournamentBracket]:
        """Get all brackets in a tournament stage"""
        # Get the stage with ownership validation
        stage = self.get_stage_by_id(stage_id, company_id)
        
        # Get all active brackets for this stage
        brackets = (
            self.db.query(TournamentBracket)
            .filter(
                TournamentBracket.stage_id == stage_id,
                TournamentBracket.deleted_at.is_(None)
            )
            .all()
        )
        
        return brackets
        
    def get_bracket_by_id(self, bracket_id: int, company_id: int) -> TournamentBracket:
        """Get a tournament bracket by ID with company validation"""
        bracket = (
            self.db.query(TournamentBracket)
            .options(joinedload(TournamentBracket.stage).joinedload(TournamentStage.tournament))
            .filter(TournamentBracket.id == bracket_id)
            .filter(TournamentBracket.deleted_at.is_(None))
            .first()
        )
        
        if not bracket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bracket not found")
        
        if bracket.stage.tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this bracket")
        
        return bracket
        
    def update_bracket(self, bracket_id: int, company_id: int, bracket_type: str) -> TournamentBracket:
        """Update a tournament bracket"""
        # Get the bracket with ownership validation
        bracket = self.get_bracket_by_id(bracket_id, company_id)
        
        # Validate bracket type
        if bracket_type not in [BracketType.MAIN, BracketType.SILVER, BracketType.BRONZE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bracket type. Must be one of {[t.value for t in BracketType]}"
            )
            
        # Check if another bracket of this type already exists in this stage
        existing_bracket = self.db.query(TournamentBracket).filter(
            TournamentBracket.stage_id == bracket.stage_id,
            TournamentBracket.bracket_type == bracket_type,
            TournamentBracket.id != bracket_id,
            TournamentBracket.deleted_at.is_(None)
        ).first()
        
        if existing_bracket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {bracket_type} bracket already exists for this stage"
            )
            
        # Update the bracket type
        bracket.bracket_type = bracket_type
        bracket.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(bracket)
        
        return bracket
        
    def delete_bracket(self, bracket_id: int, company_id: int) -> None:
        """Delete a tournament bracket (soft delete)"""
        # Get the bracket with ownership validation
        bracket = self.get_bracket_by_id(bracket_id, company_id)
        
        # Don't allow deleting the main bracket
        if bracket.bracket_type == BracketType.MAIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the main bracket"
            )
            
        # Soft delete the bracket
        bracket.deleted_at = datetime.now()
        
        # Remove the bracket association from matches
        matches = self.db.query(Match).filter(Match.bracket_id == bracket_id).all()
        for match in matches:
            match.bracket_id = None
        
        self.db.commit()
        
        return None
        
    def generate_bracket_matches(self, bracket_id: int, company_id: int, couples: List[int] = None) -> List[Match]:
        """Generate matches for an elimination bracket"""
        # Get the bracket with ownership validation
        bracket = self.get_bracket_by_id(bracket_id, company_id)
        
        # If couples not provided, attempt to use results from previous stage
        if not couples:
            # Check if there's a previous stage with groups
            current_stage = bracket.stage
            prev_stage = self.db.query(TournamentStage).filter(
                TournamentStage.tournament_id == current_stage.tournament_id,
                TournamentStage.order < current_stage.order,
                TournamentStage.stage_type == StageType.GROUP,
                TournamentStage.deleted_at.is_(None)
            ).order_by(desc(TournamentStage.order)).first()
            
            if not prev_stage:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No previous group stage found to generate bracket from. Please provide couples manually."
                )
                
            # Get the advancement rules from the previous stage
            advancement_rules = prev_stage.config.get("advancement_rules", {})
            top_n = advancement_rules.get("top_n", 2)
            to_bracket = advancement_rules.get("to_bracket", BracketType.MAIN)
            
            # Only use these rules if they apply to the current bracket
            if to_bracket != bracket.bracket_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Previous stage advancement rules don't match this bracket type. Expected {bracket.bracket_type}, got {to_bracket}."
                )
                
            # Get all groups from the previous stage
            groups = self.db.query(TournamentGroup).filter(
                TournamentGroup.stage_id == prev_stage.id,
                TournamentGroup.deleted_at.is_(None)
            ).all()
            
            if not groups:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No groups found in previous stage"
                )
                
            # Get the standings for each group
            couples = []
            for group in groups:
                standings = self.calculate_group_standings(group.id, company_id)
                # Get the top N couples from each group
                top_couples = [entry["couple_id"] for entry in standings[:top_n]]
                couples.extend(top_couples)
                
        # Ensure we have couples to work with
        if not couples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No couples provided to generate bracket"
            )
                
        # If not power of 2, add byes to make it a power of 2
        bracket_size = 2 ** math.ceil(math.log2(len(couples)))
        while len(couples) < bracket_size:
            couples.append(None)  # None represents a bye
            
        # Seed the couples in the bracket
        # For now, just randomize
        random.shuffle(couples)
        
        # Create matches for the first round
        matches = []
        round_number = 1
        match_number = 1
        tournament_id = bracket.stage.tournament_id
        
        for i in range(0, len(couples), 2):
            couple1_id = couples[i]
            couple2_id = couples[i+1]
            
            # If either couple is None (bye), the other automatically advances
            if couple1_id is None and couple2_id is None:
                # Skip this match if both are byes
                continue
            elif couple1_id is None:
                winner_id = couple2_id
            elif couple2_id is None:
                winner_id = couple1_id
            else:
                winner_id = None
                
            # Create the match
            match = Match(
                tournament_id=tournament_id,
                stage_id=bracket.stage_id,
                bracket_id=bracket.id,
                couple1_id=couple1_id if couple1_id is not None else 0,  # Use 0 as placeholder for bye
                couple2_id=couple2_id if couple2_id is not None else 0,  # Use 0 as placeholder for bye
                winner_couple_id=winner_id,
                games=[],  # Empty games for now
                match_result_status=MatchResultStatus.PENDING if winner_id is None else MatchResultStatus.COMPLETED
            )
            
            matches.append(match)
            match_number += 1
            
        # Add all matches to the database
        for match in matches:
            self.db.add(match)
            
        self.db.commit()
        
        # Refresh all matches to get their IDs
        for match in matches:
            self.db.refresh(match)
        
        # Automatically assign courts to the matches
        scheduling_service = MatchSchedulingService(self.db)
        matches = scheduling_service.auto_assign_courts(matches, tournament_id)
        
        # Initialize couple stats for all matches
        self.couple_stats_service.initialize_couple_stats_for_matches(matches)
            
        return matches

    def generate_stage_matches(self, stage_id: int, company_id: int, couples: List[int] = None) -> List[Match]:
        """
        Generate matches for a stage. Works for both group stages and elimination stages.
        For group stages, it generates matches for all groups.
        For elimination stages, it generates matches in the bracket.
        
        NEW: Automatically applies intelligent match ordering after generation.
        """
        # Get stage and validate ownership
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
        
        # Create a scheduling service instance for court assignment
        scheduling_service = MatchSchedulingService(self.db)
        
        # Generate matches based on stage type
        if stage.stage_type == StageType.GROUP:
            # For group stages, get all groups and generate matches for each
            groups = self.get_stage_groups(stage_id, company_id)
            if not groups:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No groups found in this stage"
                )
            
            all_matches = []
            for group in groups:
                # Get couples in this group
                group_couples = self.get_group_couples(group.id, company_id)
                couple_ids = [c.id for c in group_couples]
                
                if len(couple_ids) < 2:
                    # Skip groups with insufficient couples
                    continue
                
                # Create matches
                stage_config = stage.config
                match_rules = stage_config.get("match_rules", {})
                match_format = match_rules.get("match_format", MatchFormat.ROUND_ROBIN)
                matches_per_opponent = match_rules.get("matches_per_opponent", 1)
                is_time_limited = match_rules.get("time_limited", False)
                time_limit_minutes = match_rules.get("time_limit_minutes", 90)
                
                # Create all pairings for this group based on match format
                group_matches = []
                
                if match_format == MatchFormat.ROUND_ROBIN:
                    # Round-robin: every couple plays every other couple
                    for i in range(len(couple_ids)):
                        for j in range(i + 1, len(couple_ids)):
                            for _ in range(matches_per_opponent):
                                match = Match(
                                    tournament_id=stage.tournament_id,
                                    stage_id=stage.id,
                                    group_id=group.id,
                                    couple1_id=couple_ids[i],
                                    couple2_id=couple_ids[j],
                                    games=[],
                                    is_time_limited=is_time_limited,
                                    time_limit_minutes=time_limit_minutes,
                                    match_result_status=MatchResultStatus.PENDING
                                )
                                group_matches.append(match)
                
                elif match_format == MatchFormat.SWISS_SYSTEM:
                    # Swiss system: complex pairing algorithm
                    # For now, implement as simplified round-robin
                    # TODO: Implement proper Swiss system algorithm
                    for i in range(len(couple_ids)):
                        for j in range(i + 1, len(couple_ids)):
                            for _ in range(matches_per_opponent):
                                match = Match(
                                    tournament_id=stage.tournament_id,
                                    stage_id=stage.id,
                                    group_id=group.id,
                                    couple1_id=couple_ids[i],
                                    couple2_id=couple_ids[j],
                                    games=[],
                                    is_time_limited=is_time_limited,
                                    time_limit_minutes=time_limit_minutes,
                                    match_result_status=MatchResultStatus.PENDING
                                )
                                group_matches.append(match)
                
                else:
                    # Default to round-robin for unknown formats
                    for i in range(len(couple_ids)):
                        for j in range(i + 1, len(couple_ids)):
                            for _ in range(matches_per_opponent):
                                match = Match(
                                    tournament_id=stage.tournament_id,
                                    stage_id=stage.id,
                                    group_id=group.id,
                                    couple1_id=couple_ids[i],
                                    couple2_id=couple_ids[j],
                                    games=[],
                                    is_time_limited=is_time_limited,
                                    time_limit_minutes=time_limit_minutes,
                                    match_result_status=MatchResultStatus.PENDING
                                )
                                group_matches.append(match)
                
                # Add all matches to database
                for match in group_matches:
                    self.db.add(match)
                
                all_matches.extend(group_matches)
            
            # Commit all matches
            self.db.commit()
            
            # Refresh matches to get their IDs
            for match in all_matches:
                self.db.refresh(match)
                
            # NEW: Apply intelligent match ordering
            try:
                from app.services.match_ordering_service import MatchOrderingService
                ordering_service = MatchOrderingService(self.db)
                all_matches = ordering_service.calculate_optimal_match_order(
                    tournament_id=stage.tournament_id,
                    company_id=company_id,
                    stage_id=stage_id,
                    optimization_strategy="balanced_load"
                )
            except Exception as e:
                # If ordering fails, continue with basic court assignment
                print(f"Warning: Match ordering failed: {e}")
                all_matches = scheduling_service.auto_assign_courts(all_matches, stage.tournament_id)
            
            # Initialize couple stats for all matches
            self.couple_stats_service.initialize_couple_stats_for_matches(all_matches)
            
            return all_matches
            
        elif stage.stage_type == StageType.ELIMINATION:
            # For elimination stages, create bracket matches
            return self.generate_bracket_matches(stage_id, company_id, couples)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported stage type: {stage.stage_type}"
            ) 