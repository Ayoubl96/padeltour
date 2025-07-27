from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.company_service import CompanyService

router = APIRouter()

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


@router.patch("/me", response_model=schemas.CompanyOut)
def update_current_company(
    company_update: schemas.CompanyUpdate,
    current_company: Company = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current company information.
    Only provided fields will be updated (partial update).
    """
    company_service = CompanyService(db)
    
    # Convert to dict and filter out None values
    update_data = {k: v for k, v in company_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    return company_service.update_company(current_company.id, **update_data)


@router.post("/me/change-password", response_model=schemas.PasswordChangeResponse)
def change_password(
    password_data: schemas.PasswordChange,
    current_company: Company = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current company password.
    Requires current password verification.
    """
    # Validate password confirmation
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )
    
    # Basic password validation
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    company_service = CompanyService(db)
    company_service.change_password(
        company_id=current_company.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    return schemas.PasswordChangeResponse(
        success=True,
        message="Password changed successfully"
    )


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