from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, case, extract, desc, Float
from collections import defaultdict

from app.models.tournament import (
    Tournament, Match, TournamentPlayer, TournamentCouple, 
    CoupleStats, TournamentCourt, TournamentStage
)
from app.models.player import Player
from app.models.court import Court
from app.models.company import Company


class DashboardService:
    """Service for generating dashboard analytics and metrics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_data(self, company_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a company"""
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        start_of_last_month = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc) if now.month > 1 else datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        
        return {
            "tournament_management": self._get_tournament_management_overview(company_id, now, start_of_month, start_of_last_month),
            "real_time_progress": self._get_real_time_tournament_progress(company_id, now),
            "match_court_analytics": self._get_match_court_analytics(company_id, now, start_of_day, thirty_days_ago),
            "player_performance": self._get_player_couple_performance(company_id, start_of_month, start_of_last_month),
            "operational_dashboard": self._get_operational_dashboard(company_id, now),
            "generated_at": now.isoformat()
        }
    
    def _get_tournament_management_overview(self, company_id: int, now: datetime, start_of_month: datetime, start_of_last_month: datetime) -> Dict[str, Any]:
        """Get tournament management overview metrics"""
        
        # Tournament status counts
        active_tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date <= now,
            Tournament.end_date >= now
        ).count()
        
        upcoming_tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date > now
        ).count()
        
        completed_this_month = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.end_date >= start_of_month,
            Tournament.end_date < now
        ).count()
        
        # Total registered players (all time) and current month vs last month
        total_registered_players = self.db.query(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id
        ).count()
        
        current_month_players = self.db.query(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.created_at >= start_of_month
        ).count()
        
        last_month_players = self.db.query(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.created_at >= start_of_last_month,
            Tournament.created_at < start_of_month
        ).count()
        
        player_change = current_month_players - last_month_players
        player_change_percentage = round((player_change / last_month_players * 100) if last_month_players > 0 else 0, 2)
        
        # Matches played this month and pending
        matches_this_month = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.winner_couple_id.isnot(None),  # Only completed matches
            Tournament.created_at >= start_of_month
        ).count()
        
        pending_matches = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.winner_couple_id.is_(None),
            Match.scheduled_start.isnot(None)
        ).count()
        
        # Tournament capacity utilization (more useful than court utilization)
        active_tournaments_data = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date <= now,
            Tournament.end_date >= now
        ).all()
        
        total_tournament_capacity = sum([t.players_number for t in active_tournaments_data])
        actual_active_players = self.db.query(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date <= now,
            Tournament.end_date >= now
        ).count()
        
        tournament_capacity_utilization = round((actual_active_players / total_tournament_capacity * 100) if total_tournament_capacity > 0 else 0, 2)
        
        # Monthly tournament timeline
        monthly_tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            or_(
                and_(Tournament.start_date >= start_of_month, Tournament.start_date <= now),
                and_(Tournament.end_date >= start_of_month, Tournament.end_date <= now)
            )
        ).all()
        
        tournament_timeline = [
            {
                "id": t.id,
                "name": t.name,
                "start_date": t.start_date.isoformat(),
                "end_date": t.end_date.isoformat(),
                "players_number": t.players_number,
                "status": "active" if t.start_date <= now <= t.end_date else "upcoming" if t.start_date > now else "completed"
            }
            for t in monthly_tournaments
        ]
        
        # Next tournament, live tournament, tournaments ending soon
        next_tournament = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date > now
        ).order_by(Tournament.start_date).first()
        
        live_tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date <= now,
            Tournament.end_date >= now
        ).all()
        
        # Tournaments ending in next 3 days
        three_days_from_now = now + timedelta(days=3)
        tournaments_ending_soon = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.end_date >= now,
            Tournament.end_date <= three_days_from_now
        ).all()
        
        tournament_details = {
            "next_tournament": {
                "id": next_tournament.id,
                "name": next_tournament.name,
                "start_date": next_tournament.start_date.isoformat(),
                "days_until_start": (next_tournament.start_date - now).days
            } if next_tournament else None,
            "live_tournaments": [
                {
                    "id": t.id,
                    "name": t.name,
                    "start_date": t.start_date.isoformat(),
                    "end_date": t.end_date.isoformat(),
                    "days_running": (now - t.start_date).days
                }
                for t in live_tournaments
            ],
            "tournaments_ending_soon": [
                {
                    "id": t.id,
                    "name": t.name,
                    "end_date": t.end_date.isoformat(),
                    "days_remaining": (t.end_date - now).days
                }
                for t in tournaments_ending_soon
            ]
        }
        
        return {
            "active_tournaments": active_tournaments,
            "upcoming_tournaments": upcoming_tournaments,
            "completed_this_month": completed_this_month,
            "total_registered_players": total_registered_players,
            "current_month_players": current_month_players,
            "player_change": player_change,
            "player_change_percentage": player_change_percentage,
            "matches_played_this_month": matches_this_month,
            "pending_matches": pending_matches,
            "tournament_capacity_utilization": tournament_capacity_utilization,
            "tournament_timeline": tournament_timeline,
            "tournament_details": tournament_details
        }
    
    def _get_real_time_tournament_progress(self, company_id: int, now: datetime) -> Dict[str, Any]:
        """Get real-time tournament progress data"""
        
        # Get active tournaments with detailed progress
        active_tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date <= now,
            Tournament.end_date >= now
        ).options(joinedload(Tournament.matches), joinedload(Tournament.stages)).all()
        
        tournament_progress = []
        for tournament in active_tournaments:
            total_matches = len(tournament.matches)
            completed_matches = len([m for m in tournament.matches if m.winner_couple_id is not None])
            completion_percentage = round((completed_matches / total_matches * 100) if total_matches > 0 else 0, 2)
            
            # Stage progress
            stages_progress = []
            for stage in tournament.stages:
                stage_matches = [m for m in tournament.matches if m.stage_id == stage.id]
                stage_completed = len([m for m in stage_matches if m.winner_couple_id is not None])
                stage_total = len(stage_matches)
                stage_completion = round((stage_completed / stage_total * 100) if stage_total > 0 else 0, 2)
                
                stages_progress.append({
                    "stage_id": stage.id,
                    "stage_name": stage.name,
                    "stage_type": stage.stage_type,
                    "completion_percentage": stage_completion,
                    "order": stage.order
                })
            
            tournament_progress.append({
                "tournament_id": tournament.id,
                "tournament_name": tournament.name,
                "completion_percentage": completion_percentage,
                "total_matches": total_matches,
                "completed_matches": completed_matches,
                "stages_progress": sorted(stages_progress, key=lambda x: x["order"])
            })
        
        # Overall match status distribution
        all_matches = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.start_date <= now,
            Tournament.end_date >= now
        ).all()
        
        match_status = {
            "scheduled": len([m for m in all_matches if m.scheduled_start and not m.winner_couple_id]),
            "in_progress": len([m for m in all_matches if m.scheduled_start and m.scheduled_start <= now and not m.winner_couple_id]),
            "completed": len([m for m in all_matches if m.winner_couple_id]),
            "pending": len([m for m in all_matches if not m.scheduled_start])
        }
        
        # Top performing couples
        top_couples = self.db.query(CoupleStats).join(TournamentCouple).join(Tournament).filter(
            Tournament.company_id == company_id,
            CoupleStats.matches_played > 0
        ).order_by(
            desc(CoupleStats.total_points),
            desc(func.cast(CoupleStats.matches_won, Float) / func.cast(CoupleStats.matches_played, Float))
        ).limit(10).all()
        
        top_couples_data = []
        for stats in top_couples:
            win_rate = round((stats.matches_won / stats.matches_played * 100) if stats.matches_played > 0 else 0, 2)
            top_couples_data.append({
                "couple_id": stats.couple_id,
                "couple_name": stats.couple.name,
                "tournament_name": stats.tournament.name,
                "matches_played": stats.matches_played,
                "matches_won": stats.matches_won,
                "win_rate": win_rate,
                "total_points": stats.total_points
            })
        
        return {
            "tournament_progress": tournament_progress,
            "match_status_distribution": match_status,
            "top_performing_couples": top_couples_data
        }
    
    def _get_match_court_analytics(self, company_id: int, now: datetime, start_of_day: datetime, thirty_days_ago: datetime) -> Dict[str, Any]:
        """Get match and court analytics"""
        
        # Removed matches_per_day metric as requested
        
        # Average match duration (calculated from scheduled times)
        matches_with_duration = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.scheduled_start.isnot(None),
            Match.scheduled_end.isnot(None)
        ).all()
        
        total_duration = sum([
            (match.scheduled_end - match.scheduled_start).total_seconds() / 60
            for match in matches_with_duration
        ])
        avg_duration = round(total_duration / len(matches_with_duration)) if matches_with_duration else 0
        
        # Court efficiency (matches per court per day)
        total_courts = self.db.query(Court).filter(Court.company_id == company_id).count()
        total_matches_30_days = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.scheduled_start >= thirty_days_ago
        ).count()
        
        court_efficiency = round(total_matches_30_days / (total_courts * 30)) if total_courts > 0 else 0
        
        # Peak playing hours
        hourly_matches = self.db.query(
            extract('hour', Match.scheduled_start).label('hour'),
            func.count(Match.id).label('match_count')
        ).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.scheduled_start >= thirty_days_ago,
            Match.scheduled_start.isnot(None)
        ).group_by(extract('hour', Match.scheduled_start)).all()
        
        peak_hours = {str(int(hour)): count for hour, count in hourly_matches}
        
        # Match results distribution
        match_results = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.winner_couple_id.isnot(None)
        ).all()
        
        results_distribution = {
            "wins": len([m for m in match_results if m.winner_couple_id]),
            "draws": len([m for m in match_results if not m.winner_couple_id and m.games]),
            "time_expired": len([m for m in match_results if m.match_result_status == 'time_expired']),
            "forfeited": len([m for m in match_results if m.match_result_status == 'forfeited'])
        }
        
        return {
            "average_match_duration_minutes": avg_duration,
            "court_efficiency_matches_per_court_per_day": court_efficiency,
            "peak_playing_hours": peak_hours,
            "match_results_distribution": results_distribution
        }
    
    def _get_player_couple_performance(self, company_id: int, start_of_month: datetime, start_of_last_month: datetime) -> Dict[str, Any]:
        """Get player and couple performance analytics"""
        
        # Most active players by tournament participation
        active_players = self.db.query(
            Player.id,
            Player.name,
            Player.surname,
            Player.nickname,
            func.count(TournamentPlayer.tournament_id).label('tournament_count')
        ).join(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id
        ).group_by(Player.id, Player.name, Player.surname, Player.nickname).order_by(
            desc(func.count(TournamentPlayer.tournament_id))
        ).limit(10).all()
        
        most_active_players = [
            {
                "player_id": p.id,
                "name": f"{p.name} {p.surname}" if p.name and p.surname else p.nickname,
                "tournament_count": p.tournament_count
            }
            for p in active_players
        ]
        
        # Best performing couples by win percentage
        best_couples = self.db.query(CoupleStats).join(TournamentCouple).join(Tournament).filter(
            Tournament.company_id == company_id,
            CoupleStats.matches_played >= 3  # Minimum 3 matches for relevance
        ).all()
        
        couples_with_win_rate = []
        for stats in best_couples:
            win_rate = round((stats.matches_won / stats.matches_played * 100) if stats.matches_played > 0 else 0, 2)
            couples_with_win_rate.append({
                "couple_id": stats.couple_id,
                "couple_name": stats.couple.name,
                "tournament_name": stats.tournament.name,
                "matches_played": stats.matches_played,
                "win_rate": win_rate,
                "total_points": stats.total_points
            })
        
        best_performing_couples = sorted(couples_with_win_rate, key=lambda x: x["win_rate"], reverse=True)[:10]
        
        # Player level distribution
        level_distribution = self.db.query(
            Player.level,
            func.count(Player.id).label('player_count')
        ).join(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id,
            Player.level.isnot(None)
        ).group_by(Player.level).all()
        
        player_levels = {str(level): count for level, count in level_distribution}
        
        # Player registration trends
        current_month_registrations = self.db.query(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.created_at >= start_of_month
        ).count()
        
        last_month_registrations = self.db.query(TournamentPlayer).join(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.created_at >= start_of_last_month,
            Tournament.created_at < start_of_month
        ).count()
        
        registration_change = current_month_registrations - last_month_registrations
        
        return {
            "most_active_players": most_active_players,
            "best_performing_couples": best_performing_couples,
            "player_level_distribution": player_levels,
            "player_registration_trends": {
                "current_month": current_month_registrations,
                "last_month": last_month_registrations,
                "change": registration_change
            }
        }
    
    def _get_operational_dashboard(self, company_id: int, now: datetime) -> Dict[str, Any]:
        """Get operational dashboard data"""
        
        # Upcoming matches - ALL unplayed matches (scheduled and unscheduled)
        tomorrow = now + timedelta(hours=24)
        
        # Get matches in two categories:
        # 1. Scheduled matches in next 24 hours
        # 2. Unscheduled matches from active tournaments
        upcoming_matches = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.winner_couple_id.is_(None),  # Not yet played
            or_(
                # Scheduled matches in next 24 hours
                and_(
                    Match.scheduled_start.isnot(None),
                    Match.scheduled_start >= now,
                    Match.scheduled_start <= tomorrow
                ),
                # Unscheduled matches from active/upcoming tournaments
                and_(
                    Match.scheduled_start.is_(None),
                    Tournament.end_date >= now  # Tournament not finished
                )
            )
        ).order_by(
            # Order by scheduled_start if exists, otherwise by tournament start_date
            case(
                (Match.scheduled_start.isnot(None), Match.scheduled_start),
                else_=Tournament.start_date
            )
        ).all()
        
        upcoming_matches_data = [
            {
                "match_id": match.id,
                "tournament_id": match.tournament_id,
                "tournament_name": match.tournament.name,
                "couple1_name": match.couple1.name,
                "couple2_name": match.couple2.name,
                "scheduled_start": match.scheduled_start.isoformat() if match.scheduled_start else None,
                "court_name": match.court.name if match.court else None,
                "is_scheduled": match.scheduled_start is not None,  # Indicate if match is scheduled
                "tournament_start": match.tournament.start_date.isoformat(),
                "status": "scheduled" if match.scheduled_start else "unscheduled"
            }
            for match in upcoming_matches[:30]  # Increased limit to show more matches
        ]
        
        # Court conflicts (double-booked courts)
        court_conflicts = []
        courts = self.db.query(Court).filter(Court.company_id == company_id).all()
        
        for court in courts:
            matches = self.db.query(Match).join(Tournament).filter(
                Tournament.company_id == company_id,
                Match.court_id == court.id,
                Match.scheduled_start >= now,
                Match.scheduled_start.isnot(None),
                Match.scheduled_end.isnot(None)
            ).order_by(Match.scheduled_start).all()
            
            for i in range(len(matches) - 1):
                current_match = matches[i]
                next_match = matches[i + 1]
                
                if current_match.scheduled_end > next_match.scheduled_start:
                    court_conflicts.append({
                        "court_name": court.name,
                        "conflict_matches": [
                            {
                                "match_id": current_match.id,
                                "tournament": current_match.tournament.name,
                                "start_time": current_match.scheduled_start.isoformat(),
                                "end_time": current_match.scheduled_end.isoformat()
                            },
                            {
                                "match_id": next_match.id,
                                "tournament": next_match.tournament.name,
                                "start_time": next_match.scheduled_start.isoformat(),
                                "end_time": next_match.scheduled_end.isoformat()
                            }
                        ]
                    })
        
        # Incomplete match results (matches that should be completed but have no winner)
        incomplete_matches = self.db.query(Match).join(Tournament).filter(
            Tournament.company_id == company_id,
            Match.scheduled_end < now,
            Match.winner_couple_id.is_(None),
            Match.scheduled_start.isnot(None)
        ).count()
        
        # Tournament deadlines (tournaments ending in next 7 days)
        week_from_now = now + timedelta(days=7)
        ending_tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id,
            Tournament.end_date >= now,
            Tournament.end_date <= week_from_now
        ).all()
        
        tournament_deadlines = [
            {
                "tournament_id": t.id,
                "tournament_name": t.name,
                "end_date": t.end_date.isoformat(),
                "days_remaining": (t.end_date - now).days
            }
            for t in ending_tournaments
        ]
        
        # System alerts summary
        alerts_count = {
            "court_conflicts": len(court_conflicts),
            "incomplete_matches": incomplete_matches,
            "upcoming_deadlines": len(tournament_deadlines),
            "matches_next_24h": len(upcoming_matches_data)
        }
        
        return {
            "upcoming_matches_24h": upcoming_matches_data,
            "court_conflicts": court_conflicts,
            "incomplete_match_results": incomplete_matches,
            "tournament_deadlines": tournament_deadlines,
            "system_alerts": alerts_count
        }