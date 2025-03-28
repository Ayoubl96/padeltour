from .. import models

def get_all_court(db, id):
    courts = db.query(models.Court).filter(models.Court.company_id == id).all()
    return courts

def get_court_by_id(db, court_id, company_id):
    court = db.query(models.Court).filter(
        models.Court.id == court_id,
        models.Court.company_id == company_id
    ).first()
    return court

def create_new_court(name: str, images: str, company_id: int):
    new_court = models.Court(
        name=name,
        images=images,
        company_id=company_id
    )
    return new_court

def update_court_details(db, court_id, company_id, update_data):
    court_query = db.query(models.Court).filter(
        models.Court.id == court_id,
        models.Court.company_id == company_id
    )
    
    court_query.update(update_data, synchronize_session=False)
    return court_query.first()

def is_court_in_use(db, court_id):
    match = db.query(models.Match).filter(
        models.Match.court_id == court_id
    ).first()
    return match is not None

def delete_court_by_id(db, court_id, company_id):
    court_query = db.query(models.Court).filter(
        models.Court.id == court_id,
        models.Court.company_id == company_id
    )
    
    if court_query.first():
        court_query.delete(synchronize_session=False)
        return True
    return False