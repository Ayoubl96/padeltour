from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session
from ... import schemas
from ...db import get_db

from ...function.player import create_new_player, get_user_from_playtomic, get_user_level_from_playtomic, get_user_by_id_from_playtomic, create_new_player_from_playtomic
from ...tools import extract_tournament_id_from_url
router = APIRouter(
    prefix="/player",
    tags=['Players']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PlayerOut)
def create_player(
        player: schemas.PlayersBase, db:Session = Depends(get_db),
):
    new_player = create_new_player(
        nickname=player.nickname,
        gender=player.gender
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player



@router.post("/from-playtomic/", status_code=status.HTTP_201_CREATED, response_model=schemas.PlayerOut)
def create_player_from_playtomic(
        player: schemas.PlayerPlaytomic, db:Session = Depends(get_db),
):
    playtomic_player = get_user_by_id_from_playtomic(player.user_id)

    additional_data = get_user_level_from_playtomic(player.user_id)

    if len(playtomic_player) == 1:
        playtomic_player = playtomic_player[0]
    else:
        raise ValueError("playtomic_player non contiene un solo elemento")

    playtomic_player['additional_data'] = additional_data

    level = playtomic_player['additional_data'][0]['level_value']

    new_player = create_new_player_from_playtomic(
        nickname=playtomic_player['full_name'],
        picture=playtomic_player['picture'],
        level=level,
        playtomic_id=playtomic_player['user_id']
    )

    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    return new_player

@router.get("/playtomic-player/")
async def get_playtomic_play(name: str = None ):
    players = get_user_from_playtomic(name)

    for p in players:
        id = p['user_id']
        additional_data = get_user_level_from_playtomic(id)
        p['additional_data'] = additional_data

    return players

@router.get("/tournament-id/")
async def get_tournament_id(url: str = None ):
    id = extract_tournament_id_from_url(url)
    return {"id": id}

