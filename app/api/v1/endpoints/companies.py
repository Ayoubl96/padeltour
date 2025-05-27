from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.company_service import CompanyService

router = APIRouter()


@router.post("/", status_code=status.HTTP_410_GONE)
def create_company_deprecated():
    """
    DEPRECATED: Direct company creation is no longer supported.
    Please use the registration flow instead.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={
            "message": "Direct company creation is deprecated. Please use the registration flow with email verification.",
            "registration_endpoints": {
                "step_1": "POST /api/v1/register/initiate - Send verification code",
                "step_2": "POST /api/v1/register/verify - Complete registration",
                "resend": "POST /api/v1/register/resend - Resend verification code"
            },
            "documentation": "/docs#/Registration"
        }
    )


@router.post("/admin/create", status_code=status.HTTP_201_CREATED, response_model=schemas.CompanyOut)
def create_company_admin(
    company_data: schemas.CompanyBase,
    db: Session = Depends(get_db)
    # TODO: Add admin authentication here
    # current_admin: Admin = Depends(get_current_admin)
):
    """
    ADMIN ONLY: Create company without email verification.
    This endpoint is for internal use only.
    
    TODO: Implement admin authentication before using in production.
    """
    company_service = CompanyService(db)
    return company_service.create_company(
        email=company_data.email,
        password=company_data.password,
        name=company_data.name,
        address=company_data.address,
        phone_number=company_data.phone_number
    )


@router.get("/me", response_model=schemas.CompanyOut)
def get_current_company(
    current_company: Company = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_service = CompanyService(db)
    return company_service.get_company_by_id(current_company.id)


@router.get("", response_model=List[schemas.CompanyOut])
def get_all_companies(
    db: Session = Depends(get_db)
):
    company_service = CompanyService(db)
    # You may want to add admin access check here
    return db.query(Company).all()


@router.get("/{login}", response_model=schemas.CompanyOut)
def get_company_by_login(
    login: str,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.login == login).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with login: {login} not found"
        )
        
    return company 