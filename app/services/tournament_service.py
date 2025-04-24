from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.tournament import Tournament, TournamentPlayer, TournamentCouple, Match, CoupleStats, TournamentCourt
from app.models.player import Player
from app.models.court import Court


class TournamentService:
    def __init__(self, db: Session):
        self.db = db

    def create_tournament(self, 
                          name: str,
                          description: str,
                          images: list,
                          company_id: int,
                          start_date: datetime,
                          end_date: datetime,
                          players_number: int,
                          full_description: Optional[Dict[str, Any]] = None) -> Tournament:
        """Create a new tournament"""
        new_tournament = Tournament(
            name=name,
            description=description,
            images=images,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            players_number=players_number,
            full_description=full_description
        )
        self.db.add(new_tournament)
        self.db.commit()
        self.db.refresh(new_tournament)
        return new_tournament

    def get_tournament_by_id(self, tournament_id: int, company_id: int) -> Tournament:
        """Get tournament by ID with company validation"""
        tournament = self.db.query(Tournament).filter(Tournament.id == tournament_id).first()
        
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        return tournament

    def update_tournament(self, tournament_id: int, company_id: int, update_data: Dict[str, Any]) -> Tournament:
        """Update tournament details"""
        tournament_query = self.db.query(Tournament).filter(Tournament.id == tournament_id)
        tournament = tournament_query.first()
        
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Process image URLs if provided
        if "images" in update_data and update_data["images"] is not None:
            update_data["images"] = [str(url) for url in update_data["images"]]
        
        # Apply the updates
        tournament_query.update(update_data, synchronize_session=False)
        
        # Update the updated_at timestamp
        tournament.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(tournament)
        
        return tournament

    def get_all_tournaments(self, company_id: int) -> List[Tournament]:
        """Get all tournaments for a company"""
        tournaments = self.db.query(Tournament).filter(
            Tournament.company_id == company_id
        ).all()
        return tournaments

    def add_player_to_tournament(self, tournament_id: int, player_id: int, company_id: int) -> TournamentPlayer:
        """Add a player to a tournament"""
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(
            tournament_id == Tournament.id
        ).first()

        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

        if not tournament.company_id == company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this tournament")

        # Check if the player exists
        player = self.db.query(Player).filter(player_id == Player.id).first()
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

        # Check if the player is already active in the tournament
        active_entry = self.db.query(TournamentPlayer).filter(
            tournament_id == TournamentPlayer.tournament_id,
            player_id == TournamentPlayer.player_id,
            TournamentPlayer.deleted_at.is_(None)
        ).first()
        
        if active_entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Player is already in the tournament")

        # Check if the player is associated with the current company
        from app.models.player import PlayerCompany
        player_company = self.db.query(PlayerCompany).filter_by(player_id=player_id,
                                                            company_id=company_id).first()

        if not player_company:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Player not associated with this company")

        # Check if there's a soft-deleted entry for this player in this tournament
        deleted_entry = self.db.query(TournamentPlayer).filter(
            tournament_id == TournamentPlayer.tournament_id,
            player_id == TournamentPlayer.player_id,
            TournamentPlayer.deleted_at.is_not(None)
        ).first()
        
        if deleted_entry:
            # Reactivate the player by clearing the deleted_at field
            deleted_entry.deleted_at = None
            deleted_entry.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(deleted_entry)
            return deleted_entry
        else:
            # Create a new tournament player entry
            new_tournament_player = TournamentPlayer(
                tournament_id=tournament_id,
                player_id=player_id
            )
            self.db.add(new_tournament_player)
            self.db.commit()
            self.db.refresh(new_tournament_player)
            return new_tournament_player

    def get_tournament_players(self, tournament_id: int, company_id: int) -> List[TournamentPlayer]:
        """Get all players in a tournament"""
        # Fetch tournament with ownership check
        tournament = self.db.query(Tournament).filter(tournament_id == Tournament.id).first()

        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")

        # Get players with eager loading
        tournament_players = (
            self.db.query(TournamentPlayer)
            .options(joinedload(TournamentPlayer.player))
            .filter(tournament_id == TournamentPlayer.tournament_id)
            .filter(TournamentPlayer.deleted_at.is_(None))
            .all()
        )

        return tournament_players

    def remove_player_from_tournament(self, tournament_id: int, player_id: int, company_id: int) -> None:
        """Remove a player from a tournament (soft delete)"""
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(tournament_id == Tournament.id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Find the tournament player
        tournament_player = self.db.query(TournamentPlayer).filter(
            TournamentPlayer.tournament_id == tournament_id,
            TournamentPlayer.player_id == player_id
        ).first()
        
        if not tournament_player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found in this tournament")
        
        # First find any couples that include this player
        couples_to_delete = self.db.query(TournamentCouple).filter(
            TournamentCouple.tournament_id == tournament_id,
            (TournamentCouple.first_player_id == player_id) | 
            (TournamentCouple.second_player_id == player_id)
        ).all()
        
        # Delete the couples that include this player
        for couple in couples_to_delete:
            self.db.delete(couple)
        
        # Soft delete the player from the tournament
        tournament_player.deleted_at = datetime.now()
        
        self.db.commit()
        
        return None
        
    def add_court_to_tournament(self, tournament_id: int, court_id: int, company_id: int, 
                               availability_start: Optional[datetime] = None,
                               availability_end: Optional[datetime] = None) -> TournamentCourt:
        """Add a court to a tournament with optional time restrictions"""
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(tournament_id == Tournament.id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Check if the court exists and is owned by the company
        court = self.db.query(Court).filter(court_id == Court.id).first()
        if not court:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
        if court.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only add courts owned by your company")
        
        # Validate availability time ranges if provided
        if availability_start and availability_end and availability_start >= availability_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Availability start time must be before end time"
            )
        
        # If time ranges are provided, ensure they are within tournament dates
        if availability_start and availability_start < tournament.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Court availability cannot start before tournament start date"
            )
        
        if availability_end and availability_end > tournament.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Court availability cannot end after tournament end date"
            )
        
        # Check if the court is already active in the tournament
        active_entry = self.db.query(TournamentCourt).filter(
            tournament_id == TournamentCourt.tournament_id,
            court_id == TournamentCourt.court_id,
            TournamentCourt.deleted_at.is_(None)
        ).first()
        
        if active_entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Court is already assigned to this tournament")
        
        # Check if there's a soft-deleted entry for this court in this tournament
        deleted_entry = self.db.query(TournamentCourt).filter(
            tournament_id == TournamentCourt.tournament_id,
            court_id == TournamentCourt.court_id,
            TournamentCourt.deleted_at.is_not(None)
        ).first()
        
        if deleted_entry:
            # Reactivate the court by clearing the deleted_at field and updating availability
            deleted_entry.deleted_at = None
            deleted_entry.availability_start = availability_start
            deleted_entry.availability_end = availability_end
            deleted_entry.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(deleted_entry)
            return deleted_entry
        else:
            # Create a new tournament court entry
            new_tournament_court = TournamentCourt(
                tournament_id=tournament_id,
                court_id=court_id,
                availability_start=availability_start,
                availability_end=availability_end
            )
            self.db.add(new_tournament_court)
            self.db.commit()
            self.db.refresh(new_tournament_court)
            return new_tournament_court
    
    def update_tournament_court(self, tournament_id: int, court_id: int, company_id: int, 
                               update_data: Dict[str, Any]) -> TournamentCourt:
        """Update tournament court details, particularly availability times"""
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(tournament_id == Tournament.id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Find the tournament court
        tournament_court = self.db.query(TournamentCourt).filter(
            TournamentCourt.tournament_id == tournament_id,
            TournamentCourt.court_id == court_id,
            TournamentCourt.deleted_at.is_(None)
        ).first()
        
        if not tournament_court:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found in this tournament")
        
        # Validate availability times if provided
        availability_start = update_data.get("availability_start", tournament_court.availability_start)
        availability_end = update_data.get("availability_end", tournament_court.availability_end)
        
        if availability_start and availability_end and availability_start >= availability_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Availability start time must be before end time"
            )
        
        # Ensure availability is within tournament dates
        if availability_start and availability_start < tournament.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Court availability cannot start before tournament start date"
            )
        
        if availability_end and availability_end > tournament.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Court availability cannot end after tournament end date"
            )
        
        # Update the tournament court
        tournament_court.availability_start = availability_start
        tournament_court.availability_end = availability_end
        tournament_court.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(tournament_court)
        
        return tournament_court
    
    def get_tournament_courts(self, tournament_id: int, company_id: int) -> List[TournamentCourt]:
        """Get all courts in a tournament"""
        # Fetch tournament with ownership check
        tournament = self.db.query(Tournament).filter(tournament_id == Tournament.id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")
        
        # Get courts with eager loading
        tournament_courts = (
            self.db.query(TournamentCourt)
            .options(joinedload(TournamentCourt.court))
            .filter(tournament_id == TournamentCourt.tournament_id)
            .filter(TournamentCourt.deleted_at.is_(None))
            .all()
        )
        
        return tournament_courts
    
    def remove_court_from_tournament(self, tournament_id: int, court_id: int, company_id: int) -> None:
        """Remove a court from a tournament (soft delete)"""
        # Check if the tournament exists and is owned by the company
        tournament = self.db.query(Tournament).filter(tournament_id == Tournament.id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if tournament.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
        
        # Find the tournament court
        tournament_court = self.db.query(TournamentCourt).filter(
            TournamentCourt.tournament_id == tournament_id,
            TournamentCourt.court_id == court_id,
            TournamentCourt.deleted_at.is_(None)
        ).first()
        
        if not tournament_court:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found in this tournament")
        
        # Soft delete the court from the tournament
        tournament_court.deleted_at = datetime.now()
        self.db.commit()
        
        return None 