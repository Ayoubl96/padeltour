import fastapi
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import Optional, List
from ... import schemas, tools, oauth2
from ...db import get_db
from ...function.compnay import new_company, get_all_companies, get_single_company
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
    company = new_company(
        email=company.email,
        password=tools.has_psw(company.password),
        phone_number=company.phone_number,
        name=company.name,
        address=company.address
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=List[schemas.CompanyOut])
def get_companies(db: Session = Depends(get_db)):
    companies = get_all_companies(db)
    return companies


@router.get("/{login}", response_model=schemas.CompanyOut)
def get_company(
        login: str,
        db: Session = Depends(get_db)
):
    company = get_single_company(db, login=login)

    if not company:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND,
                                    detail=f"Company with login: {id} not found")
    return company


@router.get("/me/", response_model=schemas.CompanyOut)
def get_company(db: Session = Depends(get_db),
                current_company: int = Depends(oauth2.get_current_user)):
    company_id = current_company.id
    company = get_single_company(db, company_id=company_id)
    return company
