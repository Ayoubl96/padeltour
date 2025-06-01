from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.tournament import CoupleStats, TournamentCouple
from app.schemas.tournament import GroupStandingsEntry


class CoupleStatsRepository:
    """Repository for couple statistics operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = CoupleStats
    
    def get_couple_stats(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> Optional[CoupleStats]:
        """Get couple stats for a specific tournament/group"""
        query = self.db.query(CoupleStats).filter(
            CoupleStats.couple_id == couple_id,
            CoupleStats.tournament_id == tournament_id
        )
        
        if group_id is not None:
            query = query.filter(CoupleStats.group_id == group_id)
        else:
            query = query.filter(CoupleStats.group_id.is_(None))
        
        return query.first()
    
    def get_tournament_stats(self, tournament_id: int, group_id: Optional[int] = None) -> List[CoupleStats]:
        """Get all couple stats for a tournament/group"""
        query = self.db.query(CoupleStats).filter(
            CoupleStats.tournament_id == tournament_id
        ).options(joinedload(CoupleStats.couple))
        
        if group_id is not None:
            query = query.filter(CoupleStats.group_id == group_id)
        else:
            query = query.filter(CoupleStats.group_id.is_(None))
        
        return query.all()
    
    def get_group_standings(self, group_id: int) -> List[CoupleStats]:
        """Get couple stats for a specific group ordered by ranking"""
        return (
            self.db.query(CoupleStats)
            .options(joinedload(CoupleStats.couple))
            .filter(CoupleStats.group_id == group_id)
            .order_by(
                CoupleStats.total_points.desc(),
                (CoupleStats.games_won - CoupleStats.games_lost).desc(),
                CoupleStats.games_won.desc(),
                CoupleStats.matches_won.desc()
            )
            .all()
        )
    
    def create_or_update_stats(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None, **kwargs) -> CoupleStats:
        """Create or update couple stats"""
        stats = self.get_couple_stats(couple_id, tournament_id, group_id)
        
        if not stats:
            stats = CoupleStats(
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
            self.db.add(stats)
        
        # Update with provided values
        for key, value in kwargs.items():
            if hasattr(stats, key):
                setattr(stats, key, value)
        
        self.db.flush()
        return stats
    
    def delete_stats(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> bool:
        """Delete couple stats"""
        stats = self.get_couple_stats(couple_id, tournament_id, group_id)
        if stats:
            self.db.delete(stats)
            self.db.flush()
            return True
        return False
    
    def reset_tournament_stats(self, tournament_id: int, group_id: Optional[int] = None) -> int:
        """Reset all stats for a tournament/group to zero"""
        query = self.db.query(CoupleStats).filter(
            CoupleStats.tournament_id == tournament_id
        )
        
        if group_id is not None:
            query = query.filter(CoupleStats.group_id == group_id)
        else:
            query = query.filter(CoupleStats.group_id.is_(None))
        
        stats_list = query.all()
        count = 0
        
        for stats in stats_list:
            stats.matches_played = 0
            stats.matches_won = 0
            stats.matches_lost = 0
            stats.matches_drawn = 0
            stats.games_won = 0
            stats.games_lost = 0
            stats.total_points = 0
            count += 1
        
        self.db.flush()
        return count
    
    def get_couple_ranking(self, couple_id: int, tournament_id: int, group_id: Optional[int] = None) -> Optional[int]:
        """Get the ranking position of a couple in tournament/group"""
        stats = self.get_tournament_stats(tournament_id, group_id)
        
        # Sort by the same criteria as get_group_standings
        sorted_stats = sorted(
            stats,
            key=lambda s: (
                s.total_points,
                s.games_won - s.games_lost,
                s.games_won,
                s.matches_won
            ),
            reverse=True
        )
        
        for i, stat in enumerate(sorted_stats, 1):
            if stat.couple_id == couple_id:
                return i
        
        return None
    
    def get_top_couples(self, tournament_id: int, group_id: Optional[int] = None, limit: int = 10) -> List[CoupleStats]:
        """Get top performing couples in tournament/group"""
        query = self.db.query(CoupleStats).filter(
            CoupleStats.tournament_id == tournament_id
        ).options(joinedload(CoupleStats.couple))
        
        if group_id is not None:
            query = query.filter(CoupleStats.group_id == group_id)
        else:
            query = query.filter(CoupleStats.group_id.is_(None))
        
        return (
            query.order_by(
                CoupleStats.total_points.desc(),
                (CoupleStats.games_won - CoupleStats.games_lost).desc(),
                CoupleStats.games_won.desc(),
                CoupleStats.matches_won.desc()
            )
            .limit(limit)
            .all()
        ) 