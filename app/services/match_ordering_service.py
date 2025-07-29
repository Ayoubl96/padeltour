from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict, Counter
import math
import random

from app.models.tournament import (
    Tournament, TournamentStage, TournamentGroup, TournamentBracket, 
    Match, TournamentCouple, TournamentCourt
)
from app.core.constants import StageType, MatchResultStatus


class MatchOrderingService:
    """
    Service for intelligent match ordering and sequencing in tournament stages.
    
    This service implements algorithms to optimally order matches considering:
    - Group balance (couples from same group don't play consecutively)  
    - Court utilization and availability
    - Rest time between matches for same couples
    - Stage dependencies and progression
    - Time constraints and scheduling preferences
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_optimal_match_order(
        self, 
        tournament_id: int, 
        company_id: int,
        stage_id: Optional[int] = None,
        optimization_strategy: str = "balanced_load"
    ) -> List[Match]:
        """
        Calculate the optimal ordering for all matches in a tournament or specific stage.
        
        Args:
            tournament_id: The tournament ID
            company_id: Company ID for security validation
            stage_id: Optional stage ID to limit ordering to specific stage
            optimization_strategy: Strategy for optimization:
                - "balanced_load": Balance groups and minimize couple rest conflicts
                - "court_efficient": Maximize court utilization 
                - "time_sequential": Optimize for sequential time scheduling
                - "group_clustered": Keep same-group matches together
        
        Returns:
            List of matches with updated ordering fields
        """
        # Validate tournament ownership
        tournament = self._validate_tournament_access(tournament_id, company_id)
        
        # Get matches to order
        if stage_id:
            matches = self._get_stage_matches(stage_id, company_id)
            stages = [self._get_stage(stage_id, company_id)]
        else:
            matches = self._get_tournament_matches(tournament_id, company_id)
            stages = self._get_tournament_stages(tournament_id, company_id)
        
        if not matches:
            return []
        
        # Get tournament context
        courts = self._get_tournament_courts(tournament_id)
        couples = self._get_tournament_couples(tournament_id)
        
        # Apply ordering algorithm based on strategy
        if optimization_strategy == "balanced_load":
            ordered_matches = self._apply_balanced_load_strategy(matches, stages, courts, couples)
        elif optimization_strategy == "court_efficient":
            ordered_matches = self._apply_court_efficient_strategy(matches, stages, courts, couples)
        elif optimization_strategy == "time_sequential":
            ordered_matches = self._apply_time_sequential_strategy(matches, stages, courts, couples)
        elif optimization_strategy == "group_clustered":
            ordered_matches = self._apply_group_clustered_strategy(matches, stages, courts, couples)
        else:
            # Default to balanced load
            ordered_matches = self._apply_balanced_load_strategy(matches, stages, courts, couples)
        
        # Update database with new ordering
        self._persist_match_ordering(ordered_matches)
        
        return ordered_matches
    
    def _apply_balanced_load_strategy(
        self, 
        matches: List[Match], 
        stages: List[TournamentStage],
        courts: List[TournamentCourt],
        couples: List[TournamentCouple]
    ) -> List[Match]:
        """
        Apply balanced load strategy that optimizes for:
        1. Even distribution of groups across time slots
        2. Minimum rest time between matches for same couples
        3. Efficient court utilization
        4. Stage progression logic
        """
        ordered_matches = []
        num_courts = len(courts)
        
        if num_courts == 0:
            return matches
        
        # Group matches by stage and type
        matches_by_stage = defaultdict(list)
        for match in matches:
            matches_by_stage[match.stage_id].append(match)
        
        global_order = 1
        
        # Process stages in order
        for stage in sorted(stages, key=lambda s: s.order):
            stage_matches = matches_by_stage.get(stage.id, [])
            if not stage_matches:
                continue
            
            if stage.stage_type == StageType.GROUP:
                ordered_stage_matches = self._order_group_stage_matches(
                    stage_matches, stage, num_courts, global_order
                )
            else:  # Elimination stage
                ordered_stage_matches = self._order_elimination_stage_matches(
                    stage_matches, stage, num_courts, global_order
                )
            
            ordered_matches.extend(ordered_stage_matches)
            global_order += len(ordered_stage_matches)
        
        return ordered_matches
    
    def _order_group_stage_matches(
        self, 
        matches: List[Match], 
        stage: TournamentStage, 
        num_courts: int,
        start_order: int
    ) -> List[Match]:
        """
        Order matches for group stages using improved court allocation algorithm.
        
        New Algorithm Logic:
        - If num_groups == num_courts: Dedicate each court to a specific group
        - If num_groups != num_courts: Use alternating distribution across courts
        
        This provides better organization and easier tournament management.
        """
        # Group matches by group_id
        matches_by_group = defaultdict(list)
        for match in matches:
            group_key = match.group_id or 0
            matches_by_group[group_key].append(match)
        
        num_groups = len(matches_by_group)
        
        # Strategy 1: When groups == courts, dedicate each court to a group
        if num_groups == num_courts and num_groups > 1:
            return self._order_with_dedicated_courts(matches_by_group, num_courts, start_order)
        
        # Strategy 2: When groups != courts, use alternating distribution
        else:
            return self._order_with_alternating_courts(matches_by_group, num_courts, start_order)
    
    def _order_with_dedicated_courts(
        self, 
        matches_by_group: Dict[int, List[Match]], 
        num_courts: int, 
        start_order: int
    ) -> List[Match]:
        """
        Dedicate each court to a specific group with couple-aware scheduling.
        
        NEW: Prevents same couple from playing consecutive matches.
        Ensures fair distribution and proper rest time between matches.
        """
        ordered_matches = []
        
        # Get tournament courts for court assignment
        first_match = next(iter(next(iter(matches_by_group.values()))))
        courts_list = self._get_tournament_courts(first_match.tournament_id)
        
        # Convert to list for consistent ordering
        group_items = list(matches_by_group.items())
        
        # Create separate queues for each court/group with couple-aware scheduling
        court_queues = []
        for court_index, (group_id, group_matches) in enumerate(group_items):
            # Apply couple-aware ordering within each group
            ordered_group_matches = self._apply_couple_aware_ordering(group_matches)
            court_queues.append(ordered_group_matches)
        
        # Interleave matches from different courts ensuring proper distribution
        current_order = start_order
        max_matches = max(len(queue) for queue in court_queues)
        
        for match_index in range(max_matches):
            for court_index, match_queue in enumerate(court_queues):
                if match_index < len(match_queue):
                    match = match_queue[match_index]
                    
                    # Assign ordering fields
                    match.display_order = current_order
                    match.order_in_stage = current_order - start_order + 1
                    match.order_in_group = match_index + 1
                    match.round_number = match_index + 1
                    match.priority_score = self._calculate_priority_score(match, match_index + 1, court_index)
                    
                    # Assign the dedicated court for this group
                    if not match.court_id and courts_list:
                        match.court_id = courts_list[court_index % len(courts_list)].court_id
                    
                    ordered_matches.append(match)
                    current_order += 1
        
        return ordered_matches
    
    def _order_with_alternating_courts(
        self, 
        matches_by_group: Dict[int, List[Match]], 
        num_courts: int, 
        start_order: int
    ) -> List[Match]:
        """
        Use alternating distribution across courts with couple-aware scheduling.
        
        NEW: Prevents same couple from playing consecutive matches across all courts.
        Ensures fair distribution and proper rest time between matches.
        """
        ordered_matches = []
        current_order = start_order
        
        # Get tournament courts
        first_match = next(iter(next(iter(matches_by_group.values()))))
        courts_list = self._get_tournament_courts(first_match.tournament_id)
        
        # Flatten all matches and apply global couple-aware scheduling
        all_matches = []
        for group_id, matches in matches_by_group.items():
            all_matches.extend(matches)
        
        # Apply couple-aware ordering to ALL matches globally
        globally_ordered_matches = self._apply_couple_aware_ordering(all_matches)
        
        # Now distribute the couple-aware ordered matches across courts
        court_assignments = [[] for _ in range(num_courts)]
        
        # Round-robin assignment to courts
        for i, match in enumerate(globally_ordered_matches):
            court_index = i % num_courts
            court_assignments[court_index].append(match)
        
        # Create final ordering by interleaving court assignments
        max_matches_per_court = max(len(court_matches) for court_matches in court_assignments)
        
        for round_index in range(max_matches_per_court):
            for court_index in range(num_courts):
                if round_index < len(court_assignments[court_index]):
                    match = court_assignments[court_index][round_index]
                    
                    # Find original group info for this match
                    original_group_id = match.group_id
                    group_matches = matches_by_group.get(original_group_id, [])
                    group_match_index = group_matches.index(match) if match in group_matches else 0
                    
                    # Assign ordering fields
                    match.display_order = current_order
                    match.order_in_stage = current_order - start_order + 1
                    match.order_in_group = group_match_index + 1
                    match.round_number = round_index + 1
                    match.priority_score = self._calculate_priority_score(match, round_index, court_index)
                    
                    # Assign court
                    if not match.court_id and courts_list:
                        match.court_id = courts_list[court_index].court_id
                    
                    ordered_matches.append(match)
                    current_order += 1
        
        return ordered_matches
    
    def _order_elimination_stage_matches(
        self, 
        matches: List[Match], 
        stage: TournamentStage, 
        num_courts: int,
        start_order: int
    ) -> List[Match]:
        """
        Order matches for elimination stages using bracket progression logic.
        """
        # Group matches by bracket and round
        matches_by_bracket = defaultdict(lambda: defaultdict(list))
        
        for match in matches:
            bracket_id = match.bracket_id or 0
            round_num = match.round_number or 1
            matches_by_bracket[bracket_id][round_num].append(match)
        
        ordered_matches = []
        current_order = start_order
        court_index = 0
        
        # Process rounds in order (round 1, then round 2, etc.)
        max_rounds = max(
            max(rounds.keys()) if rounds else 0 
            for rounds in matches_by_bracket.values()
        )
        
        for round_num in range(1, max_rounds + 1):
            round_matches = []
            
            # Collect all matches for this round across all brackets
            for bracket_id, bracket_rounds in matches_by_bracket.items():
                if round_num in bracket_rounds:
                    round_matches.extend(bracket_rounds[round_num])
            
            # Sort matches within round by bracket position
            round_matches.sort(key=lambda m: (m.bracket_id or 0, m.bracket_position or 0))
            
            # Assign ordering
            for match in round_matches:
                match.display_order = current_order
                match.order_in_stage = current_order - start_order + 1
                match.round_number = round_num
                match.priority_score = self._calculate_priority_score(match, round_num, court_index)
                
                # Assign court in rotation
                if not match.court_id and len(self._get_tournament_courts(match.tournament_id)) > 0:
                    courts_list = self._get_tournament_courts(match.tournament_id)
                    match.court_id = courts_list[court_index % len(courts_list)].court_id
                    court_index += 1
                
                ordered_matches.append(match)
                current_order += 1
        
        return ordered_matches
    
    def _calculate_group_order(self, match: Match, group_matches: List[Match]) -> int:
        """Calculate the order of this match within its group."""
        # Sort group matches by some criteria (e.g., couple IDs for consistency)
        sorted_matches = sorted(group_matches, key=lambda m: (m.couple1_id, m.couple2_id))
        try:
            return sorted_matches.index(match) + 1
        except ValueError:
            return len(sorted_matches)
    
    def _calculate_priority_score(self, match: Match, round_num: int, court_index: int) -> float:
        """
        Calculate a priority score for the match used for fine-tuning order.
        
        Lower scores = higher priority (earlier in the sequence)
        
        Factors:
        - Round number (earlier rounds have priority)
        - Court assignment (to balance load)
        - Group/bracket importance
        """
        base_score = round_num * 100  # Base score by round
        
        # Add court balancing factor
        court_factor = court_index * 0.1
        
        # Add group/bracket factors
        group_factor = (match.group_id or 0) * 0.01
        bracket_factor = (match.bracket_id or 0) * 0.01
        
        return base_score + court_factor + group_factor + bracket_factor
    
    def _apply_court_efficient_strategy(
        self, 
        matches: List[Match], 
        stages: List[TournamentStage],
        courts: List[TournamentCourt],
        couples: List[TournamentCouple]
    ) -> List[Match]:
        """Apply court-efficient ordering strategy (maximize court utilization)."""
        # Implementation for court-efficient strategy
        # This would prioritize keeping all courts busy at all times
        return self._apply_balanced_load_strategy(matches, stages, courts, couples)
    
    def _apply_time_sequential_strategy(
        self, 
        matches: List[Match], 
        stages: List[TournamentStage],
        courts: List[TournamentCourt],
        couples: List[TournamentCouple]
    ) -> List[Match]:
        """Apply time-sequential ordering strategy (optimize for time scheduling)."""
        # Implementation for time-based optimization
        # This would consider scheduled times and optimize transitions
        return self._apply_balanced_load_strategy(matches, stages, courts, couples)
    
    def _apply_group_clustered_strategy(
        self, 
        matches: List[Match], 
        stages: List[TournamentStage],
        courts: List[TournamentCourt],
        couples: List[TournamentCouple]
    ) -> List[Match]:
        """Apply group-clustered ordering strategy (keep same-group matches together)."""
        # Implementation for group clustering
        # This would group all matches from the same group together
        return self._apply_balanced_load_strategy(matches, stages, courts, couples)
    
    def _apply_couple_aware_ordering(self, matches: List[Match]) -> List[Match]:
        """
        Apply couple-aware ordering to prevent same couple from playing consecutive matches.
        
        Algorithm:
        1. Track couples and their last played match position
        2. Prioritize matches with couples who haven't played recently
        3. Ensure fair distribution of playing time
        4. Minimize consecutive matches for same couple
        
        This ensures better rest time and fairer tournament flow.
        """
        if len(matches) <= 1:
            return matches
        
        # Create a copy to avoid modifying original list
        remaining_matches = matches.copy()
        ordered_matches = []
        
        # Track when each couple last played (match position)
        couple_last_played = {}
        
        # Start with any match (preferably involving couples who haven't played)
        current_match = remaining_matches.pop(0)
        ordered_matches.append(current_match)
        
        # Update couple tracking
        couple_last_played[current_match.couple1_id] = 0
        couple_last_played[current_match.couple2_id] = 0
        
        # Order remaining matches with couple-aware logic
        while remaining_matches:
            best_match = None
            best_score = -1
            best_index = -1
            
            current_position = len(ordered_matches)
            
            # Find the best next match considering couple rest time
            for i, match in enumerate(remaining_matches):
                score = self._calculate_couple_rest_score(
                    match, couple_last_played, current_position
                )
                
                if score > best_score:
                    best_score = score
                    best_match = match
                    best_index = i
            
            # Add the best match to ordered list
            if best_match:
                ordered_matches.append(best_match)
                remaining_matches.pop(best_index)
                
                # Update couple tracking
                couple_last_played[best_match.couple1_id] = current_position
                couple_last_played[best_match.couple2_id] = current_position
        
        return ordered_matches
    
    def _calculate_couple_rest_score(
        self, 
        match: Match, 
        couple_last_played: Dict[int, int], 
        current_position: int
    ) -> float:
        """
        Calculate a score for how suitable this match is based on couple rest time.
        
        Higher score = better choice (couples have had more rest)
        Lower score = worse choice (couples played recently)
        
        Factors:
        - How long since couple1 last played
        - How long since couple2 last played  
        - Prefer matches where both couples have had rest
        - Heavily penalize consecutive matches for same couple
        """
        couple1_rest = current_position - couple_last_played.get(match.couple1_id, -10)
        couple2_rest = current_position - couple_last_played.get(match.couple2_id, -10)
        
        # Base score: sum of rest periods
        base_score = couple1_rest + couple2_rest
        
        # Bonus for couples who haven't played yet
        if match.couple1_id not in couple_last_played:
            base_score += 10
        if match.couple2_id not in couple_last_played:
            base_score += 10
        
        # Heavy penalty for consecutive matches (rest = 0)
        if couple1_rest == 0:
            base_score -= 50
        if couple2_rest == 0:
            base_score -= 50
        
        # Small penalty for recent play (rest = 1)
        if couple1_rest == 1:
            base_score -= 10
        if couple2_rest == 1:
            base_score -= 10
        
        # Bonus for well-rested couples (rest >= 3)
        if couple1_rest >= 3:
            base_score += 5
        if couple2_rest >= 3:
            base_score += 5
        
        # Add small random factor to break ties
        import random
        base_score += random.random() * 0.1
        
        return base_score
    
    def _persist_match_ordering(self, matches: List[Match]) -> None:
        """Persist the match ordering to the database."""
        for match in matches:
            self.db.merge(match)
        
        self.db.commit()
    
    # Helper methods for data retrieval
    def _validate_tournament_access(self, tournament_id: int, company_id: int) -> Tournament:
        """Validate tournament exists and company has access."""
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        if tournament.company_id != company_id:
            raise ValueError(f"Unauthorized access to tournament {tournament_id}")
        return tournament
    
    def _get_stage(self, stage_id: int, company_id: int) -> TournamentStage:
        """Get a specific stage with validation."""
        stage = (
            self.db.query(TournamentStage)
            .join(Tournament)
            .filter(
                TournamentStage.id == stage_id,
                Tournament.company_id == company_id,
                TournamentStage.deleted_at.is_(None)
            )
            .first()
        )
        if not stage:
            raise ValueError(f"Stage {stage_id} not found")
        return stage
    
    def _get_stage_matches(self, stage_id: int, company_id: int) -> List[Match]:
        """Get all matches for a specific stage."""
        return (
            self.db.query(Match)
            .join(Tournament)
            .filter(
                Match.stage_id == stage_id,
                Tournament.company_id == company_id,
                Match.match_result_status == MatchResultStatus.PENDING
            )
            .options(joinedload(Match.stage))
            .all()
        )
    
    def _get_tournament_matches(self, tournament_id: int, company_id: int) -> List[Match]:
        """Get all matches for a tournament."""
        return (
            self.db.query(Match)
            .join(Tournament)
            .filter(
                Match.tournament_id == tournament_id,
                Tournament.company_id == company_id,
                Match.match_result_status == MatchResultStatus.PENDING
            )
            .options(joinedload(Match.stage))
            .all()
        )
    
    def _get_tournament_stages(self, tournament_id: int, company_id: int) -> List[TournamentStage]:
        """Get all stages for a tournament."""
        return (
            self.db.query(TournamentStage)
            .join(Tournament)
            .filter(
                TournamentStage.tournament_id == tournament_id,
                Tournament.company_id == company_id,
                TournamentStage.deleted_at.is_(None)
            )
            .order_by(TournamentStage.order)
            .all()
        )
    
    def _get_tournament_courts(self, tournament_id: int) -> List[TournamentCourt]:
        """Get all courts for a tournament."""
        return (
            self.db.query(TournamentCourt)
            .filter(
                TournamentCourt.tournament_id == tournament_id,
                TournamentCourt.deleted_at.is_(None)
            )
            .all()
        )
    
    def _get_tournament_couples(self, tournament_id: int) -> List[TournamentCouple]:
        """Get all couples for a tournament."""
        return (
            self.db.query(TournamentCouple)
            .filter(
                TournamentCouple.tournament_id == tournament_id,
                TournamentCouple.deleted_at.is_(None)
            )
            .all()
        ) 