from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.models.tournament import Tournament, TournamentPlayer, TournamentCouple
from app.services.tournament_service import TournamentService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.TournamentOut)
def create_tournament(
        tournament: schemas.TournamentBase, 
        db: Session = Depends(get_db),
        current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    images_as_str = [str(url) for url in tournament.images] if tournament.images else []
    
    return tournament_service.create_tournament(
        name=tournament.name,
        description=tournament.description,
        images=images_as_str,
        company_id=current_company.id,
        start_date=tournament.start_date,
        end_date=tournament.end_date,
        players_number=tournament.players_number,
        full_description=tournament.full_description
    )


@router.get("/{id}", response_model=schemas.TournamentOut)
def get_tournament_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    return tournament_service.get_tournament_by_id(id, current_company.id)


@router.put("/{id}", response_model=schemas.TournamentOut)
def update_tournament(
    id: int,
    tournament_update: schemas.TournamentUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    update_data = tournament_update.dict(exclude_unset=True)
    return tournament_service.update_tournament(id, current_company.id, update_data)


@router.get("/", response_model=List[schemas.TournamentOut])
def get_all_tournaments(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    return tournament_service.get_all_tournaments(current_company.id)


@router.post("/{id}/player", response_model=schemas.TournamentPlayerOut)
def add_player_to_tournament(
    id: int,
    player_data: schemas.TournamentPlayerCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    return tournament_service.add_player_to_tournament(
        tournament_id=id,
        player_id=player_data.player_id,
        company_id=current_company.id
    )


@router.get("/{id}/player", response_model=List[schemas.TournamentPlayerOut])
def get_tournament_players(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    return tournament_service.get_tournament_players(id, current_company.id)


@router.delete("/{tournament_id}/player/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_from_tournament(
    tournament_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    tournament_service.remove_player_from_tournament(tournament_id, player_id, current_company.id)
    return None


# Tournament couple endpoints
@router.post("/{id}/couple", response_model=schemas.TournamentCoupleOut, status_code=status.HTTP_201_CREATED)
def create_tournament_couple(
    id: int,
    couple: schemas.TournamentCoupleCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(Tournament).filter(id == Tournament.id).first()
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

    # Check if the couple has the same player for first and second
    if couple.first_player_id == couple.second_player_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A player cannot be paired with themselves"
        )

    # Check if both players are in the tournament_player table for this tournament
    players_in_tournament = db.query(TournamentPlayer).filter(
        id == TournamentPlayer.tournament_id,
        TournamentPlayer.player_id.in_([couple.first_player_id, couple.second_player_id]),
        TournamentPlayer.deleted_at.is_(None)
    ).all()

    if len(players_in_tournament) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or both players are not in this tournament"
        )

    # Check if the couple already exists (regardless of player order)
    existing_couple = db.query(TournamentCouple).filter(
        id == TournamentCouple.tournament_id,
        TournamentCouple.deleted_at.is_(None),
        (
            (couple.first_player_id == TournamentCouple.first_player_id) &
            (TournamentCouple.second_player_id == couple.second_player_id)
        ) | (
            (TournamentCouple.first_player_id == couple.second_player_id) &
            (TournamentCouple.second_player_id == couple.first_player_id)
        )
    ).first()

    if existing_couple:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This couple already exists in the tournament (including reverse order)"
        )

    # Create the new couple
    new_couple = TournamentCouple(
        tournament_id=id,
        first_player_id=couple.first_player_id,
        second_player_id=couple.second_player_id,
        name=couple.name
    )
    
    db.add(new_couple)
    db.commit()
    db.refresh(new_couple)

    return new_couple


@router.get("/{id}/couple", response_model=List[schemas.TournamentCoupleOut])
def get_tournament_couples(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(Tournament).filter(id == Tournament.id).first()
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

    # Fetch all couples in the tournament
    couples = (
        db.query(TournamentCouple)
        .options(
            joinedload(TournamentCouple.first_player),
            joinedload(TournamentCouple.second_player)
        )
        .filter(id == TournamentCouple.tournament_id)
        .filter(TournamentCouple.deleted_at.is_(None))
        .all()
    )

    return couples


@router.put("/{tournament_id}/couple/{couple_id}", response_model=schemas.TournamentCoupleOut)
def update_tournament_couple(
    tournament_id: int,
    couple_id: int,
    couple_update: schemas.TournamentCoupleUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(Tournament).filter(tournament_id == Tournament.id).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    # Find the couple
    couple = db.query(TournamentCouple).filter(
        TournamentCouple.id == couple_id,
        TournamentCouple.tournament_id == tournament_id,
        TournamentCouple.deleted_at.is_(None)
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
        players_in_tournament = db.query(TournamentPlayer).filter(
            tournament_id == TournamentPlayer.tournament_id,
            TournamentPlayer.player_id.in_([first_player_id, second_player_id]),
            TournamentPlayer.deleted_at.is_(None)
        ).all()
        
        if len(players_in_tournament) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both players are not in this tournament"
            )
            
        # Check if the couple already exists (regardless of player order)
        existing_couple = db.query(TournamentCouple).filter(
            tournament_id == TournamentCouple.tournament_id,
            TournamentCouple.id != couple_id,  # Exclude the current couple
            TournamentCouple.deleted_at.is_(None),
            (
                (first_player_id == TournamentCouple.first_player_id) &
                (TournamentCouple.second_player_id == second_player_id)
            ) | (
                (TournamentCouple.first_player_id == second_player_id) &
                (TournamentCouple.second_player_id == first_player_id)
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
    current_company: Company = Depends(get_current_user)
):
    # Check if the tournament exists and is owned by the current company
    tournament = db.query(Tournament).filter(tournament_id == Tournament.id).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.company_id != current_company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this tournament")
    
    # Find the couple
    couple = db.query(TournamentCouple).filter(
        TournamentCouple.id == couple_id,
        TournamentCouple.tournament_id == tournament_id,
        TournamentCouple.deleted_at.is_(None)
    ).first()
    
    if not couple:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Couple not found in this tournament")
    
    # Soft delete by setting deleted_at timestamp
    couple.deleted_at = datetime.now()
    db.commit()
    
    return None 


# Tournament court endpoints
@router.post("/{id}/court", response_model=schemas.TournamentCourtOut, status_code=status.HTTP_201_CREATED)
def add_court_to_tournament(
    id: int,
    court_data: schemas.TournamentCourtCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    return tournament_service.add_court_to_tournament(
        tournament_id=id,
        court_id=court_data.court_id,
        company_id=current_company.id,
        availability_start=court_data.availability_start,
        availability_end=court_data.availability_end
    )


@router.get("/{id}/court", response_model=List[schemas.TournamentCourtOut])
def get_tournament_courts(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    return tournament_service.get_tournament_courts(id, current_company.id)


@router.put("/{tournament_id}/court/{court_id}", response_model=schemas.TournamentCourtOut)
def update_tournament_court(
    tournament_id: int,
    court_id: int,
    court_update: schemas.TournamentCourtUpdate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    update_data = court_update.dict(exclude_unset=True)
    return tournament_service.update_tournament_court(
        tournament_id=tournament_id,
        court_id=court_id,
        company_id=current_company.id,
        update_data=update_data
    )


@router.delete("/{tournament_id}/court/{court_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_court_from_tournament(
    tournament_id: int,
    court_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    tournament_service = TournamentService(db)
    tournament_service.remove_court_from_tournament(
        tournament_id=tournament_id,
        court_id=court_id,
        company_id=current_company.id
    )
    return None 