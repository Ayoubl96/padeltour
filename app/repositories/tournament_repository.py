from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.repositories.base import BaseRepository, EntityNotFoundError, UnauthorizedAccessError
from app.models.tournament import (
    Tournament, TournamentStage, TournamentGroup, TournamentBracket,
    TournamentGroupCouple, TournamentCouple, TournamentCourt
)

class TournamentRepository(BaseRepository):
    """Repository for tournament-related entities"""
    
    def get_tournament_with_check(self, tournament_id: int, company_id: int) -> Tournament:
        """Get a tournament by ID with company ownership check"""
        return self.get_by_id_with_company_check(Tournament, tournament_id, company_id)
    
    def get_stage_with_check(self, stage_id: int, company_id: int) -> TournamentStage:
        """Get a tournament stage by ID with company ownership check"""
        return self.get_by_id_with_company_check(TournamentStage, stage_id, company_id)
    
    def get_group_with_check(self, group_id: int, company_id: int) -> TournamentGroup:
        """Get a tournament group by ID with company ownership check"""
        return self.get_by_id_with_company_check(TournamentGroup, group_id, company_id)
    
    def get_bracket_with_check(self, bracket_id: int, company_id: int) -> TournamentBracket:
        """Get a tournament bracket by ID with company ownership check"""
        return self.get_by_id_with_company_check(TournamentBracket, bracket_id, company_id)
    
    def get_stage_groups(self, stage_id: int) -> List[TournamentGroup]:
        """Get all groups for a stage"""
        return (
            self.db.query(TournamentGroup)
            .filter(
                TournamentGroup.stage_id == stage_id,
                TournamentGroup.deleted_at.is_(None)
            )
            .all()
        )
    
    def get_stage_brackets(self, stage_id: int) -> List[TournamentBracket]:
        """Get all brackets for a stage"""
        return (
            self.db.query(TournamentBracket)
            .filter(
                TournamentBracket.stage_id == stage_id,
                TournamentBracket.deleted_at.is_(None)
            )
            .all()
        )
    
    def get_tournament_courts(self, tournament_id: int) -> List[TournamentCourt]:
        """Get all courts for a tournament"""
        return (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .all()
        )
    
    def get_group_couples(self, group_id: int) -> List[TournamentCouple]:
        """Get all couples in a group"""
        return (
            self.db.query(TournamentCouple)
            .join(TournamentGroupCouple)
            .filter(
                TournamentGroupCouple.group_id == group_id,
                TournamentGroupCouple.deleted_at.is_(None),
                TournamentCouple.deleted_at.is_(None)
            )
            .all()
        )
    
    def get_previous_group_stage(self, stage_id: int) -> Optional[TournamentStage]:
        """Get the previous group stage before the given stage"""
        current_stage = self.get_by_id(TournamentStage, stage_id)
        if not current_stage:
            return None
            
        return (
            self.db.query(TournamentStage)
            .filter(
                TournamentStage.tournament_id == current_stage.tournament_id,
                TournamentStage.order < current_stage.order,
                TournamentStage.stage_type == "group",
                TournamentStage.deleted_at.is_(None)
            )
            .order_by(desc(TournamentStage.order))
            .first()
        )
    
    def create_stage(self, **kwargs) -> TournamentStage:
        """Create a new tournament stage"""
        return self.create(TournamentStage, **kwargs)
    
    def create_group(self, **kwargs) -> TournamentGroup:
        """Create a new tournament group"""
        return self.create(TournamentGroup, **kwargs)
    
    def create_bracket(self, **kwargs) -> TournamentBracket:
        """Create a new tournament bracket"""
        return self.create(TournamentBracket, **kwargs)
    
    def add_couple_to_group(self, group_id: int, couple_id: int) -> TournamentGroupCouple:
        """Add a couple to a group"""
        # Check for soft-deleted record with the same group_id and couple_id
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
            return soft_deleted_record
        else:
            # Create a new group-couple association
            return self.create(
                TournamentGroupCouple, 
                group_id=group_id,
                couple_id=couple_id
            ) 