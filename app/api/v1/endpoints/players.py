from fastapi import APIRouter, Depends, status, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.player_service import PlayerService
from app.services.playtomic_service import PlaytomicService
from app.utils.string_utils import extract_tournament_id_from_url

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PlayerOutFull)
def create_player(
    player_data: schemas.PlayersBase,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    player_service = PlayerService(db)
    return player_service.create_player(
        nickname=player_data.nickname,
        gender=player_data.gender,
        company_id=current_company.id
    )


@router.post("/from-playtomic/", status_code=status.HTTP_201_CREATED, response_model=schemas.PlayerOutFull)
def create_player_from_playtomic(
    player: schemas.PlayerPlaytomic,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    player_service = PlayerService(db)
    
    try:
        # Get player data from Playtomic
        playtomic_data = player_service.get_playtomic_player_data(player.playtomic_id)
        
        # Create or update player
        result = player_service.create_player_from_playtomic(
            playtomic_data=playtomic_data,
            gender=player.gender,
            company_id=current_company.id
        )
        
        # Handle different result statuses
        if result["status"] == "existing":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Player and relation already exist.", "player_id": result["player"].id}
            )
        elif result["status"] == "related":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Relation with company created.", "player_id": result["player"].id}
            )
        else:
            return result["player"]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/playtomic-player/")
def get_playtomic_players(
    name: str = None
):
    # Direct call to the PlaytomicService
    players = PlaytomicService.get_user_from_playtomic(name)
    
    # Add additional data to each player
    for p in players:
        try:
            player_id = p['user_id']
            additional_data = PlaytomicService.get_user_level_from_playtomic(player_id)
            p['additional_data'] = additional_data
        except Exception:
            # If there's any error getting additional data, provide an empty list
            p['additional_data'] = []
    
    return players


@router.get("/tournament-id/")
def get_tournament_id(url: str = None):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    try:
        tournament_id = extract_tournament_id_from_url(url)
        return {"id": tournament_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}", response_model=schemas.PlayerOutFull)
def get_player_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    player_service = PlayerService(db)
    return player_service.get_player_by_id(id, current_company.id)


@router.put("/{id}", response_model=schemas.PlayerOutFull)
def update_player(
    id: int,
    player_data: schemas.PlayerOutFull,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    player_service = PlayerService(db)
    update_data = player_data.dict(exclude={"id"}, exclude_unset=True)
    
    # Process picture if it's a URL or list of URLs
    if "picture" in update_data and update_data["picture"] is not None:
        if isinstance(update_data["picture"], list):
            update_data["picture"] = [str(url) for url in update_data["picture"]]
        else:
            update_data["picture"] = str(update_data["picture"])
    
    return player_service.update_player(
        player_id=id,
        company_id=current_company.id,
        **update_data
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_association(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    player_service = PlayerService(db)
    player_service.delete_player_company_association(id, current_company.id)
    return None


@router.get("/", response_model=List[schemas.PlayerOutFull])
def get_players(
    search: Optional[str] = Query(None, description="Search term for player name/nickname"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    player_service = PlayerService(db)
    
    if search:
        return player_service.search_players(current_company.id, search)
    else:
        return player_service.get_all_players(current_company.id) 