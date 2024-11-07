from .. import models


# This function take in input all attribute for the Company model and return a model object
def new_company(email, password, phone_number, name, address):
    company = models.Company(
        email=email,
        password=password,
        phone_number=phone_number,
        name=name,
        address=address
    )
    return company


# from db session give back the all company of a company
def get_all_companies(db):
    companies = db.query(models.Company).all()
    return companies


def get_single_company(db, login=None, company_id=None):
    query = db.query(models.Company)

    if login:
        company = query.filter(models.Company.login == login).first()
    elif company_id:
        company = query.filter(models.Company.id == company_id).first()
    else:
        company = None  # Nessun parametro valido è stato passato

    return company
