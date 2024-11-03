import fastapi
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import Optional, List
from ... import models, schemas, tools, oauth2
from ...db import get_db
from sqlalchemy.sql import or_
from sqlalchemy import func

router = APIRouter(
    prefix="/companies",
    tags=['Companies']
)


@router.post("/submit-registration/", status_code=status.HTTP_201_CREATED, response_model=schemas.CompanyOut)
def create_company(
        company: schemas.CompanyBase, db: Session = Depends(get_db),
):
    hashed_password = tools.has_psw(company.password)
    password = hashed_password
    email = company.email
    phone_number = company.phone_number
    name = company.name
    address = company.address
    new_company = models.Company(
        email=email,
        password=password,
        phone_number=phone_number,
        name=name,
        address=address
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


@router.get("", response_model=List[schemas.CompanyOut])
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(models.Company).all()
    return companies


@router.get("/{id}", response_model=schemas.CompanyOut)
def get_company(
        id: str, db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)):
    company = db.query(models.Company).filter(models.Company.login == id).first()

    if not company:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND,
                                    detail=f"Company with login: {id} not found")
    return company


@router.get("/me/", response_model=schemas.CompanyOut)
def get_company(db: Session = Depends(get_db),
                current_company: int = Depends(oauth2.get_current_user)):
    company = db.query(models.Company).filter(models.Company.id == current_company.id).first()
    return company
