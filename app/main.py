import fastapi
from fastapi import FastAPI, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from . import models, schemas
from . db import get_db
from typing import List
from sqlalchemy.sql import or_
from sqlalchemy import func
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/submit-registration/", status_code=status.HTTP_201_CREATED, response_model=schemas.CompanyBase)
def create_company(
            company: schemas.CompanyBase, db: Session = Depends(get_db),
):
    email = company.email
    password = company.password
    phone_number = company.phone_number
    new_company = models.Company(
        email=email,
        password=password,
        phone_number=phone_number
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


@app.get("/companies/", response_model=List[schemas.CompanyOut])
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(models.Company).all()
    return companies