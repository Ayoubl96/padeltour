from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.player import Player, PlayerCompany
from app.services.playtomic_service import PlaytomicService


class PlayerService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_player(self, nickname: str, gender: str, company_id: int, **kwargs):
        """Create a new player and a player-company association."""
        # Create player
        player = Player(
            nickname=nickname,
            gender=gender,
            **kwargs
        )
        self.db.add(player)
        self.db.flush()  # Flush to get the player ID

        # Create player-company association
        player_company = PlayerCompany(
            player_id=player.id,
            company_id=company_id
        )
        self.db.add(player_company)
        self.db.commit()
        self.db.refresh(player)

        return player
    
    def get_player_by_id(self, player_id: int, company_id: int):
        """Get a player by ID and verify company association."""
        # Check if player exists and is associated with the company
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Check if player is associated with the company
        association = self.db.query(PlayerCompany).filter(
            PlayerCompany.player_id == player_id,
            PlayerCompany.company_id == company_id
        ).first()
        
        if not association:
            raise HTTPException(status_code=403, detail="Player not associated with this company")
        
        return player
    
    def update_player(self, player_id: int, company_id: int, **kwargs):
        """Update player details."""
        player = self.get_player_by_id(player_id, company_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(player, key):
                setattr(player, key, value)
        
        self.db.commit()
        self.db.refresh(player)
        return player
    
    def delete_player_company_association(self, player_id: int, company_id: int):
        """Remove the association between a player and company."""
        # Verify player exists
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Delete association
        association = self.db.query(PlayerCompany).filter(
            PlayerCompany.player_id == player_id,
            PlayerCompany.company_id == company_id
        ).first()
        
        if not association:
            raise HTTPException(status_code=404, detail="Player not associated with this company")
        
        self.db.delete(association)
        self.db.commit()
    
    def get_all_players(self, company_id: int) -> List[Player]:
        """Get all players associated with a company."""
        return self.db.query(Player).join(
            PlayerCompany, Player.id == PlayerCompany.player_id
        ).filter(
            PlayerCompany.company_id == company_id
        ).all()
    
    def search_players(self, company_id: int, search_term: str) -> List[Player]:
        """Search for players by nickname."""
        return self.db.query(Player).join(
            PlayerCompany, Player.id == PlayerCompany.player_id
        ).filter(
            PlayerCompany.company_id == company_id,
            Player.nickname.ilike(f"%{search_term}%")
        ).all()
    
    def get_player_by_playtomic_id(self, playtomic_id: str):
        """Get a player by Playtomic ID."""
        return self.db.query(Player).filter_by(playtomic_id=playtomic_id).first()
    
    def check_player_company_relation(self, player_id: int, company_id: int):
        """Check if a relation between player and company exists."""
        return self.db.query(PlayerCompany).filter_by(
            player_id=player_id,
            company_id=company_id
        ).first()
    
    def create_player_company_relation(self, player_id: int, company_id: int):
        """Create a relation between player and company."""
        player_company = PlayerCompany(
            player_id=player_id,
            company_id=company_id
        )
        self.db.add(player_company)
        self.db.commit()
        
    def create_player_from_playtomic(self, playtomic_data: dict, gender: str, company_id: int):
        """Create a player from Playtomic data."""
        # Extract playtomic data
        playtomic_id = playtomic_data.get('user_id')
        
        # Check for existing player
        existing_player = self.get_player_by_playtomic_id(playtomic_id)
        
        if existing_player:
            # Check for existing relation
            existing_relation = self.check_player_company_relation(existing_player.id, company_id)
            
            if existing_relation:
                return {"status": "existing", "player": existing_player}
            
            # Create relation
            self.create_player_company_relation(existing_player.id, company_id)
            return {"status": "related", "player": existing_player}
        
        # Calculate level
        level = 0  # Default level
        try:
            additional_data = playtomic_data.get('additional_data', [])
            if additional_data and len(additional_data) > 0 and 'level_value' in additional_data[0]:
                level = additional_data[0]['level_value'] * 100
        except (IndexError, KeyError, TypeError):
            pass
            
        # Create new player
        player = self.create_player(
            nickname=playtomic_data.get('full_name', ''),
            gender=gender,
            company_id=company_id,
            picture=playtomic_data.get('picture'),
            level=level,
            playtomic_id=playtomic_id
        )
        
        return {"status": "created", "player": player}
        
    def get_playtomic_player_data(self, user_id: str):
        """Get player data from Playtomic with additional information."""
        playtomic_player = PlaytomicService.get_user_by_id_from_playtomic(user_id)
        additional_data = PlaytomicService.get_user_level_from_playtomic(user_id)
        
        if len(playtomic_player) == 1:
            player_data = playtomic_player[0]
            player_data['additional_data'] = additional_data
            return player_data
        else:
            raise ValueError("Playtomic returned unexpected data format") 