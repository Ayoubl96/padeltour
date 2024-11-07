from .. import models

def get_all_court(db, id):
    courts = db.query(models.Court).filter(models.Company.id == id)
    return courts

def create_new_court(name: str, images: str, company_id: int):
    new_court = models.Court(
        name=name,
        images=images,
        company_id=company_id
    )
    return new_court