from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session
from ... import schemas, oauth2
from ...db import get_db
from ...function.tournament import create_new_tournament
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
        players_number=tournament.players_number
    )
    db.add(new_tournament)
    db.commit()
    db.refresh(new_tournament)
    return new_tournament

