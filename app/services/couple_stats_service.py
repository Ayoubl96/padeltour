from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.tournament import Match, CoupleStats, TournamentStage, TournamentCouple
from app.core.constants import DEFAULT_SCORING_SYSTEM, ScoringType
from app.repositories.couple_stats_repository import CoupleStatsRepository


class CoupleStatsService:
    """Service for managing couple statistics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = CoupleStatsRepository(db)
    
    def update_couple_stats_from_match(self, match: Match) -> None:
        """Update couple stats based on match result"""
        if not match.winner_couple_id or not match.games:
            # Match not completed yet, nothing to update
            return
        
        # Get stage configuration for scoring system
        scoring_system = self._get_scoring_system(match)
        
        # Calculate match statistics
        match_stats = self._calculate_match_stats(match, scoring_system)
        
        # Update stats for both couples
        self._update_couple_stats(match.couple1_id, match_stats['couple1'], match)
        self._update_couple_stats(match.couple2_id, match_stats['couple2'], match)
        
        self.db.commit()
    
    def recalculate_couple_stats(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> None:
        """Recalculate all stats for a couple in a tournament/group"""
        # Get all completed matches for this couple
        matches_query = self.db.query(Match).filter(
            Match.tournament_id == tournament_id,
            ((Match.couple1_id == couple_id) | (Match.couple2_id == couple_id)),
            Match.winner_couple_id.isnot(None),
            Match.games.isnot(None)
        )
        
        if group_id:
            matches_query = matches_query.filter(Match.group_id == group_id)
        
        matches = matches_query.all()
        
        # Reset stats using repository
        stats = self.repository.create_or_update_stats(
            couple_id=couple_id,
            tournament_id=tournament_id,
            group_id=group_id,
            matches_played=0,
            matches_won=0,
            matches_lost=0,
            matches_drawn=0,
            games_won=0,
            games_lost=0,
            total_points=0
        )
        
        # Recalculate from all matches
        for match in matches:
            scoring_system = self._get_scoring_system(match)
            match_stats = self._calculate_match_stats(match, scoring_system)
            
            if match.couple1_id == couple_id:
                self._add_stats_to_entity(stats, match_stats['couple1'])
            else:
                self._add_stats_to_entity(stats, match_stats['couple2'])
        
        self.db.commit()
    
    def _get_scoring_system(self, match: Match) -> Dict[str, Any]:
        """Get scoring system configuration from stage or use default"""
        if match.stage_id:
            stage = self.db.query(TournamentStage).filter(TournamentStage.id == match.stage_id).first()
            if stage and stage.config:
                return stage.config.get("scoring_system", DEFAULT_SCORING_SYSTEM)
        
        return DEFAULT_SCORING_SYSTEM
    
    def _calculate_match_stats(self, match: Match, scoring_system: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics for both couples from a match"""
        couple1_stats = {
            "matches_played": 1,
            "matches_won": 0,
            "matches_lost": 0,
            "matches_drawn": 0,
            "games_won": 0,
            "games_lost": 0,
            "total_points": 0
        }
        
        couple2_stats = couple1_stats.copy()
        
        # Count individual games won/lost from each set
        for game in match.games:
            if isinstance(game, dict):
                couple1_score = game.get("couple1_score", 0)
                couple2_score = game.get("couple2_score", 0)
                
                # Add the actual game scores, not just count the set winner
                couple1_stats["games_won"] += couple1_score
                couple1_stats["games_lost"] += couple2_score
                couple2_stats["games_won"] += couple2_score
                couple2_stats["games_lost"] += couple1_score
        
        # Determine match winner and assign points
        if match.winner_couple_id == match.couple1_id:
            couple1_stats["matches_won"] = 1
            couple2_stats["matches_lost"] = 1
            couple1_stats["total_points"] = scoring_system.get("win", 3)
            couple2_stats["total_points"] = scoring_system.get("loss", 0)
        elif match.winner_couple_id == match.couple2_id:
            couple2_stats["matches_won"] = 1
            couple1_stats["matches_lost"] = 1
            couple2_stats["total_points"] = scoring_system.get("win", 3)
            couple1_stats["total_points"] = scoring_system.get("loss", 0)
        else:
            # Draw (though unlikely in padel)
            couple1_stats["matches_drawn"] = 1
            couple2_stats["matches_drawn"] = 1
            couple1_stats["total_points"] = scoring_system.get("draw", 1)
            couple2_stats["total_points"] = scoring_system.get("draw", 1)
        
        # Add bonus points for games won/lost if configured
        if scoring_system.get("game_win", 0) > 0:
            couple1_stats["total_points"] += couple1_stats["games_won"] * scoring_system.get("game_win", 0)
            couple2_stats["total_points"] += couple2_stats["games_won"] * scoring_system.get("game_win", 0)
        
        if scoring_system.get("game_loss", 0) > 0:
            couple1_stats["total_points"] += couple1_stats["games_lost"] * scoring_system.get("game_loss", 0)
            couple2_stats["total_points"] += couple2_stats["games_lost"] * scoring_system.get("game_loss", 0)
        
        return {
            "couple1": couple1_stats,
            "couple2": couple2_stats
        }
    
    def _update_couple_stats(self, couple_id: int, stats_delta: Dict[str, Any], match: Match) -> None:
        """Update couple stats with the delta from a match"""
        stats = self.repository.get_couple_stats(couple_id, match.tournament_id, match.group_id)
        if not stats:
            stats = self.repository.create_or_update_stats(
                couple_id=couple_id,
                tournament_id=match.tournament_id,
                group_id=match.group_id
            )
        
        self._add_stats_to_entity(stats, stats_delta)
    
    def _add_stats_to_entity(self, stats: CoupleStats, stats_delta: Dict[str, Any]) -> None:
        """Add delta stats to existing stats entity"""
        stats.matches_played += stats_delta.get("matches_played", 0)
        stats.matches_won += stats_delta.get("matches_won", 0)
        stats.matches_lost += stats_delta.get("matches_lost", 0)
        stats.matches_drawn += stats_delta.get("matches_drawn", 0)
        stats.games_won += stats_delta.get("games_won", 0)
        stats.games_lost += stats_delta.get("games_lost", 0)
        stats.total_points += stats_delta.get("total_points", 0)
    
    def remove_match_from_stats(self, match: Match) -> None:
        """Remove a match's contribution from couple stats (used when deleting/updating matches)"""
        if not match.winner_couple_id or not match.games:
            return
        
        scoring_system = self._get_scoring_system(match)
        match_stats = self._calculate_match_stats(match, scoring_system)
        
        # Subtract stats for both couples
        self._subtract_couple_stats(match.couple1_id, match_stats['couple1'], match)
        self._subtract_couple_stats(match.couple2_id, match_stats['couple2'], match)
        
        self.db.commit()
    
    def _subtract_couple_stats(self, couple_id: int, stats_delta: Dict[str, Any], match: Match) -> None:
        """Subtract couple stats with the delta from a match"""
        stats = self.repository.get_couple_stats(couple_id, match.tournament_id, match.group_id)
        if not stats:
            return
        
        stats.matches_played = max(0, stats.matches_played - stats_delta.get("matches_played", 0))
        stats.matches_won = max(0, stats.matches_won - stats_delta.get("matches_won", 0))
        stats.matches_lost = max(0, stats.matches_lost - stats_delta.get("matches_lost", 0))
        stats.matches_drawn = max(0, stats.matches_drawn - stats_delta.get("matches_drawn", 0))
        stats.games_won = max(0, stats.games_won - stats_delta.get("games_won", 0))
        stats.games_lost = max(0, stats.games_lost - stats_delta.get("games_lost", 0))
        stats.total_points = max(0, stats.total_points - stats_delta.get("total_points", 0))
    
    def get_couple_stats(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> Optional[CoupleStats]:
        """Get couple stats for a specific tournament/group"""
        return self.repository.get_couple_stats(couple_id, tournament_id, group_id)
    
    def get_tournament_stats(self, tournament_id: int, group_id: Optional[int] = None) -> List[CoupleStats]:
        """Get all couple stats for a tournament/group ordered by ranking"""
        if group_id is not None:
            return self.repository.get_group_standings(group_id)
        else:
            return self.repository.get_top_couples(tournament_id, group_id, limit=100)
    
    def get_couple_ranking(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> Optional[int]:
        """Get the ranking position of a couple"""
        return self.repository.get_couple_ranking(couple_id, tournament_id, group_id)
    
    def reset_tournament_stats(self, tournament_id: int, group_id: Optional[int] = None) -> int:
        """Reset all stats for a tournament/group"""
        return self.repository.reset_tournament_stats(tournament_id, group_id)
    
    def initialize_couple_stats_for_match(self, match: Match) -> None:
        """Initialize couple stats records when a match is created (even without results)"""
        # Initialize stats for couple1
        self._ensure_couple_stats_exist(
            couple_id=match.couple1_id,
            tournament_id=match.tournament_id,
            group_id=match.group_id
        )
        
        # Initialize stats for couple2
        self._ensure_couple_stats_exist(
            couple_id=match.couple2_id,
            tournament_id=match.tournament_id,
            group_id=match.group_id
        )
        
        self.db.commit()
    
    def initialize_couple_stats_for_matches(self, matches: List[Match]) -> None:
        """Initialize couple stats records for multiple matches"""
        couples_to_initialize = set()
        
        for match in matches:
            # Add both couples from each match to the set (eliminates duplicates)
            couples_to_initialize.add((match.couple1_id, match.tournament_id, match.group_id))
            couples_to_initialize.add((match.couple2_id, match.tournament_id, match.group_id))
        
        # Initialize stats for all unique couples
        for couple_id, tournament_id, group_id in couples_to_initialize:
            self._ensure_couple_stats_exist(couple_id, tournament_id, group_id)
        
        self.db.commit()
    
    def _ensure_couple_stats_exist(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> CoupleStats:
        """Ensure couple stats record exists, create if not found"""
        stats = self.repository.get_couple_stats(couple_id, tournament_id, group_id)
        
        if not stats:
            # Create new stats record with zero values
            stats = self.repository.create_or_update_stats(
                couple_id=couple_id,
                tournament_id=tournament_id,
                group_id=group_id,
                matches_played=0,
                matches_won=0,
                matches_lost=0,
                matches_drawn=0,
                games_won=0,
                games_lost=0,
                total_points=0
            )
        
        return stats 