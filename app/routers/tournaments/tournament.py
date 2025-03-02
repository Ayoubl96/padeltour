from fastapi import Depends, APIRouter, status, HTTPException
from sqlalchemy.orm import Session, joinedload
from ... import schemas, oauth2
from ...db import get_db
from ...function.tournament import create_new_tournament
from ... import models
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

    # Check if the player is already in the tournament
    existing_entry = db.query(models.TournamentPlayer).filter(
        payload.tournament_id == models.TournamentPlayer.tournament_id,
        payload.player_id == models.TournamentPlayer.player_id
    ).first()
    if existing_entry:
        raise HTTPException(status_code=400, detail="Player is already in the tournament")

    #. Check if the player is associated with the current company
    player_company = db.query(models.PlayerCompany).filter_by(player_id=payload.player_id,
                                                              company_id=current_company.id).first()

    if not player_company:
        raise HTTPException(status_code=403, detail="Player not associated with this company")

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
        .all()
    )

    return tournament_players

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

@router.get("/", response_model=list[schemas.TournamentOut])
def get_all_tournaments(
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    tournaments = db.query(models.Tournament).filter(
        models.Tournament.company_id == current_company.id
    ).all()
    return tournaments