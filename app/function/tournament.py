import datetime
from .. import models

def create_new_tournament(name: str,
                          description: str,
                          images: list,
                          company_id: int,
                          type: int,
                          start_date: datetime,
                          end_date: datetime,
                          player_type: int,
                          participants: int,
                          is_couple: int ):
    new_tournament = models.Tournament(
        name=name,
        description=description,
        images=images,
        company_id=company_id,
        type=type,
        start_date=start_date,
        end_date=end_date,
        player_type=player_type,
        participants=participants,
        is_couple=is_couple
    )
    return new_tournament