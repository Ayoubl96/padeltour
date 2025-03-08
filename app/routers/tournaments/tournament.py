from fastapi import Depends, APIRouter, status, HTTPException
from sqlalchemy.orm import Session, joinedload
from ... import schemas, oauth2
from ...db import get_db
from ...function.tournament import create_new_tournament
from ... import models
from datetime import datetime

router = APIRouter(
    prefix="/tournament",
    tags=['Tournaments']
)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.TournamentOut)
def create_tournament(
        tournament: schemas.TournamentBase, db:Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    images_as_str = [str(url) for url in tournament.images]
    new_tournament = create_new_tournament(
        name=tournament.name,
        description=tournament.description,
        images=images_as_str,
        company_id=current_company.id,
        start_date=tournament.start_date,
        end_date=tournament.end_date,
        players_number=tournament.players_number,
        full_description=tournament.full_description
    )
    db.add(new_tournament)
    db.commit()
    db.refresh(new_tournament)
    return new_tournament


@router.get("/{id}", response_model=schemas.TournamentOut)
def get_tournament_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(models.Tournament.id == id).first()
    
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    return tournament


@router.put("/{id}", response_model=schemas.TournamentOut)
def update_tournament(
    id: int,
    tournament_update: schemas.TournamentUpdate,
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament_query = db.query(models.Tournament).filter(models.Tournament.id == id)
    tournament = tournament_query.first()
    
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    # Process image URLs if provided
    update_data = tournament_update.dict(exclude_unset=True)
    if "images" in update_data and update_data["images"] is not None:
        update_data["images"] = [str(url) for url in update_data["images"]]
    
    # Apply the updates
    tournament_query.update(update_data, synchronize_session=False)
    
    # Update the updated_at timestamp
    tournament.updated_at = datetime.now()
    
    db.commit()
    db.refresh(tournament)
    
    return tournament


@router.post("/player/", response_model=schemas.TournamentPlayerOut)
def add_player_to_tournament(
    payload: schemas.TournamentPlayerCreate,
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(
        payload.tournament_id == models.Tournament.id
    ).first()
    print(tournament)

    if not tournament:
        raise HTTPException(status_code=403, detail="Tournament not found")

    if not tournament.company_id == current_company.id:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this tournament")

    # Check if the player exists
    player = db.query(models.Player).filter(payload.player_id == models.Player.id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if the player is already active in the tournament
    active_entry = db.query(models.TournamentPlayer).filter(
        payload.tournament_id == models.TournamentPlayer.tournament_id,
        payload.player_id == models.TournamentPlayer.player_id,
        models.TournamentPlayer.deleted_at.is_(None)
    ).first()
    
    if active_entry:
        raise HTTPException(status_code=400, detail="Player is already in the tournament")

    #. Check if the player is associated with the current company
    player_company = db.query(models.PlayerCompany).filter_by(player_id=payload.player_id,
                                                              company_id=current_company.id).first()

    if not player_company:
        raise HTTPException(status_code=403, detail="Player not associated with this company")

    # Check if there's a soft-deleted entry for this player in this tournament
    deleted_entry = db.query(models.TournamentPlayer).filter(
        payload.tournament_id == models.TournamentPlayer.tournament_id,
        payload.player_id == models.TournamentPlayer.player_id,
        models.TournamentPlayer.deleted_at.is_not(None)
    ).first()
    
    if deleted_entry:
        # Reactivate the player by clearing the deleted_at field
        deleted_entry.deleted_at = None
        deleted_entry.updated_at = datetime.now()
        db.commit()
        db.refresh(deleted_entry)
        return deleted_entry
    else:
        # Create a new tournament player entry
        new_tournament_player = models.TournamentPlayer(
            tournament_id=payload.tournament_id,
            player_id=payload.player_id
        )
        db.add(new_tournament_player)
        db.commit()
        db.refresh(new_tournament_player)
        return new_tournament_player


@router.get("/{id}/player", response_model=list[schemas.TournamentPlayerOut])
def get_tournament_players(
        id: int,
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    # Fetch tournament with ownership check
    tournament = db.query(models.Tournament).filter(id == models.Tournament.id).first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Get players with eager loading
    tournament_players = (
        db.query(models.TournamentPlayer)
        .options(joinedload(models.TournamentPlayer.player))
        .filter(id == models.TournamentPlayer.tournament_id)
        .filter(models.TournamentPlayer.deleted_at.is_(None))
        .all()
    )

    return tournament_players

@router.delete("/{tournament_id}/player/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_from_tournament(
    tournament_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(tournament_id == models.Tournament.id).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    # Find the tournament player
    tournament_player = db.query(models.TournamentPlayer).filter(
        models.TournamentPlayer.tournament_id == tournament_id,
        models.TournamentPlayer.player_id == player_id
    ).first()
    
    if not tournament_player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found in this tournament")
    
    # First find any couples that include this player
    couples_to_delete = db.query(models.TournamentCouple).filter(
        models.TournamentCouple.tournament_id == tournament_id,
        (models.TournamentCouple.first_player_id == player_id) | 
        (models.TournamentCouple.second_player_id == player_id)
    ).all()
    
    # Delete the couples that include this player
    for couple in couples_to_delete:
        db.delete(couple)
    
    # Soft delete the player from the tournament
    tournament_player.deleted_at = datetime.now()
    
    db.commit()
    
    return None

@router.post("/{id}/couple", response_model=schemas.TournamentCoupleOut, status_code=status.HTTP_201_CREATED)
def create_tournament_couple(
    id: int,  # Tournament ID from the path
    couple: schemas.TournamentCoupleCreate,  # Payload with first_player_id, second_player_id, and name
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # 1. Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(id == models.Tournament.id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    if tournament.company_id != current_company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a couple for this tournament"
        )


    # 2. Check if the couple has the same player for first and second
    if couple.first_player_id == couple.second_player_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A player cannot be paired with themselves"
        )


    # 3. Check if both players are in the tournament_player table for this tournament
    players_in_tournament = db.query(models.TournamentPlayer).filter(
        id == models.TournamentPlayer.tournament_id,
        models.TournamentPlayer.player_id.in_([couple.first_player_id, couple.second_player_id])
    ).all()

    if len(players_in_tournament) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or both players are not in this tournament"
        )

    # 4. Check if the couple already exists (regardless of player order)
    existing_couple = db.query(models.TournamentCouple).filter(
        id == models.TournamentCouple.tournament_id,
        (
                (couple.first_player_id == models.TournamentCouple.first_player_id) &
                (models.TournamentCouple.second_player_id == couple.second_player_id)
        ) | (
            (models.TournamentCouple.first_player_id == couple.second_player_id) &
            (models.TournamentCouple.second_player_id == couple.first_player_id)
        )
    ).first()

    if existing_couple:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This couple already exists in the tournament (including reverse order)"
        )

    # 5. Create the new couple
    new_couple = models.TournamentCouple(
        tournament_id=id,
        first_player_id=couple.first_player_id,
        second_player_id=couple.second_player_id,
        name=couple.name
    )
    db.add(new_couple)
    db.commit()
    db.refresh(new_couple)

    return new_couple

@router.get("/{id}/couple", response_model=list[schemas.TournamentCoupleOut])
def get_tournament_couples(
    id: int,  # Tournament ID from the path
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # 1. Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(id == models.Tournament.id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    if tournament.company_id != current_company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view couples for this tournament"
        )

    # 2. Fetch all couples in the tournament
    couples = (
        db.query(models.TournamentCouple)
        .options(
            joinedload(models.TournamentCouple.first_player),
            joinedload(models.TournamentCouple.second_player)
        )
        .filter(id == models.TournamentCouple.tournament_id)
        .filter(models.TournamentCouple.deleted_at.is_(None))
        .all()
    )

    return couples

@router.put("/{tournament_id}/couple/{couple_id}", response_model=schemas.TournamentCoupleOut)
def update_tournament_couple(
    tournament_id: int,
    couple_id: int,
    couple_update: schemas.TournamentCoupleUpdate,
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(tournament_id == models.Tournament.id).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    # Find the couple
    couple = db.query(models.TournamentCouple).filter(
        models.TournamentCouple.id == couple_id,
        models.TournamentCouple.tournament_id == tournament_id,
        models.TournamentCouple.deleted_at.is_(None)
    ).first()
    
    if not couple:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Couple not found in this tournament")
    
    # Check if we're updating player IDs
    if couple_update.first_player_id or couple_update.second_player_id:
        first_player_id = couple_update.first_player_id or couple.first_player_id
        second_player_id = couple_update.second_player_id or couple.second_player_id
        
        # Check if the couple has the same player for first and second
        if first_player_id == second_player_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A player cannot be paired with themselves"
            )
        
        # Check if both players are in the tournament_player table for this tournament
        players_in_tournament = db.query(models.TournamentPlayer).filter(
            tournament_id == models.TournamentPlayer.tournament_id,
            models.TournamentPlayer.player_id.in_([first_player_id, second_player_id]),
            models.TournamentPlayer.deleted_at.is_(None)
        ).all()
        
        if len(players_in_tournament) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both players are not in this tournament"
            )
            
        # Check if the couple already exists (regardless of player order)
        existing_couple = db.query(models.TournamentCouple).filter(
            tournament_id == models.TournamentCouple.tournament_id,
            models.TournamentCouple.id != couple_id,  # Exclude the current couple
            models.TournamentCouple.deleted_at.is_(None),
            (
                (first_player_id == models.TournamentCouple.first_player_id) &
                (models.TournamentCouple.second_player_id == second_player_id)
            ) | (
                (models.TournamentCouple.first_player_id == second_player_id) &
                (models.TournamentCouple.second_player_id == first_player_id)
            )
        ).first()
        
        if existing_couple:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This couple already exists in the tournament (including reverse order)"
            )
    
    # Update couple attributes that were provided
    if couple_update.first_player_id is not None:
        couple.first_player_id = couple_update.first_player_id
    if couple_update.second_player_id is not None:
        couple.second_player_id = couple_update.second_player_id
    if couple_update.name is not None:
        couple.name = couple_update.name
    
    couple.updated_at = datetime.now()
    db.commit()
    db.refresh(couple)
    
    return couple


@router.delete("/{tournament_id}/couple/{couple_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament_couple(
    tournament_id: int,
    couple_id: int,
    db: Session = Depends(get_db),
    current_company: int = Depends(oauth2.get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(models.Tournament).filter(tournament_id == models.Tournament.id).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    # Find the couple
    couple = db.query(models.TournamentCouple).filter(
        models.TournamentCouple.id == couple_id,
        models.TournamentCouple.tournament_id == tournament_id,
        models.TournamentCouple.deleted_at.is_(None)
    ).first()
    
    if not couple:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Couple not found in this tournament")
    
    # Soft delete by setting deleted_at timestamp
    couple.deleted_at = datetime.now()
    db.commit()
    
    return None

@router.get("/", response_model=list[schemas.TournamentOut])
def get_all_tournaments(
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    tournaments = db.query(models.Tournament).filter(
        models.Tournament.company_id == current_company.id
    ).all()
    return tournaments