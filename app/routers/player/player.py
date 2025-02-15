from fastapi import Depends, APIRouter, status, HTTPException
from sqlalchemy.orm import Session

from ... import models
from ... import schemas, oauth2
from ...db import get_db
from ...function.player import create_new_player, get_user_from_playtomic, get_user_level_from_playtomic, \
    get_user_by_id_from_playtomic, create_new_player_from_playtomic, create_relation_with_company_and_player
from ...tools import extract_tournament_id_from_url

router = APIRouter(
    prefix="/player",
    tags=['Players']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PlayerOut)
def create_player(
        player: schemas.PlayersBase, db:Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    new_player = create_new_player(
        nickname=player.nickname,
        gender=player.gender
    )

    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    player_company = create_relation_with_company_and_player(
        player_id=new_player.id,
        company_id=current_company.id
    )

    db.add(player_company)
    db.commit()
    db.refresh(player_company)

    return new_player



from fastapi.responses import JSONResponse

@router.post("/from-playtomic/", status_code=status.HTTP_201_CREATED, response_model=schemas.PlayerOut)
def create_player_from_playtomic(
        player: schemas.PlayerPlaytomic, db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    playtomic_player = get_user_by_id_from_playtomic(player.user_id)
    additional_data = get_user_level_from_playtomic(player.user_id)

    if len(playtomic_player) == 1:
        playtomic_player = playtomic_player[0]
    else:
        raise ValueError("playtomic_player non contiene un solo elemento")

    playtomic_player['additional_data'] = additional_data
    level = playtomic_player['additional_data'][0]['level_value'] * 100

    # Check if player already exists in the DB
    existing_player = db.query(models.Player).filter_by(playtomic_id=playtomic_player['user_id']).first()

    if existing_player:
        # Check if relation with the company already exists
        existing_relation = db.query(models.PlayerCompany).filter_by(
            player_id=existing_player.id,
            company_id=current_company.id
        ).first()

        if existing_relation:
            # Player and relation already exist, return 200 OK with player_id
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Player and relation already exist.", "player_id": existing_player.id}
            )

        # If player exists but relation does not, create the relation
        player_company = create_relation_with_company_and_player(
            player_id=existing_player.id,
            company_id=current_company.id
        )
        db.add(player_company)
        db.commit()
        db.refresh(player_company)

        # Return 200 OK with message and player_id
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Relation with company created.", "player_id": existing_player.id}
        )

    # Create new player if not found
    new_player = create_new_player_from_playtomic(
        nickname=playtomic_player['full_name'],
        picture=playtomic_player['picture'],
        level=level,
        playtomic_id=playtomic_player['user_id'],
        gender=player.gender
    )

    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    # Create relation with company
    player_company = create_relation_with_company_and_player(
        player_id=new_player.id,
        company_id=current_company.id
    )

    db.add(player_company)
    db.commit()
    db.refresh(player_company)

    return new_player  # Default response 201 Created

@router.get("/playtomic-player/")
async def get_playtomic_play(name: str = None ):
    players = get_user_from_playtomic(name)

    for p in players:
        id = p['user_id']
        additional_data = get_user_level_from_playtomic(id)
        p['additional_data'] = additional_data

    return players

@router.get("/", response_model=list[schemas.PlayerOutFull])
def get_all_company_players(
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    # 1. Retrieve all player IDs associated with the current company
    player_ids = db.query(models.PlayerCompany.player_id).filter_by(company_id=current_company.id).all()

    # If there are no associated players, return an empty list
    if not player_ids:
        return []

    # 2. Retrieve player information using the found player IDs
    players = db.query(models.Player).filter(models.Player.id.in_([pid[0] for pid in player_ids])).all()

    return players


@router.get("/{player_id}", response_model=schemas.PlayerOutFull)
def get_player_by_id(
        player_id: int,
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    # 1. Check if the player exists
    player = db.query(models.Player).filter_by(id=player_id).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 2. Check if the player is associated with the current company
    player_company = db.query(models.PlayerCompany).filter_by(player_id=player_id,
                                                              company_id=current_company.id).first()

    if not player_company:
        raise HTTPException(status_code=403, detail="Player not associated with this company")

    return player

@router.get("/tournament-id/")
async def get_tournament_id(url: str = None ):
    id = extract_tournament_id_from_url(url)
    return {"id": id}