import datetime
from .. import models
from typing import Optional

def create_new_tournament(name: str,
                          description: str,
                          company_id: int,
                          start_date: datetime,
                          end_date: datetime,
                          players_number: int,
                          images: Optional[list] = None,
                          full_description: Optional[dict] = None
                          ):
    new_tournament = models.Tournament(
        name=name,
        description=description,
        images=images,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        players_number=players_number,
        full_description=full_description
    )
    return new_tournament