from fastapi import APIRouter, Depends, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.services.court_service import CourtService
from app.services.storage_service import StorageService
from app.services.company_service import CompanyService

router = APIRouter()


@router.post("/upload_image/", status_code=status.HTTP_201_CREATED)
async def upload_image(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    company_service = CompanyService(db)
    company = company_service.get_company_by_id(current_company.id)
    
    # Use the supabase integration from the old code
    return await StorageService.upload_image_on_supabase(
        login=company.login, 
        folder="courts", 
        files=files
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CourtBase)
def create_court(
    court_data: schemas.CourtBase,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    court_service = CourtService(db)
    images_as_str = [str(url) for url in court_data.images] if court_data.images else []
    
    return court_service.create_court(
        name=court_data.name,
        images=images_as_str,
        company_id=current_company.id
    )


@router.get("/{id}", response_model=schemas.CourtBase)
def get_court_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    court_service = CourtService(db)
    return court_service.get_court_by_id(id, current_company.id)


@router.put("/{id}", response_model=schemas.CourtBase)
def update_court(
    id: int,
    court_data: schemas.CourtBase,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    court_service = CourtService(db)
    images_as_str = [str(url) for url in court_data.images] if court_data.images else []
    
    return court_service.update_court(
        court_id=id,
        company_id=current_company.id,
        name=court_data.name,
        images=images_as_str
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_court(
    id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    court_service = CourtService(db)
    court_service.delete_court(id, current_company.id)
    return None


@router.get("/", response_model=List[schemas.CourtBase])
def get_all_courts(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    court_service = CourtService(db)
    return court_service.get_all_courts(current_company.id) 