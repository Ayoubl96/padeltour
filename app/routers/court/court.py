from fastapi import Response, status, HTTPException, Depends, APIRouter, File, UploadFile, status
from sqlalchemy.orm import Session
from typing import List
from ... import models, schemas, tools, oauth2
from ...db import get_db
from sqlalchemy.sql import or_
from sqlalchemy import func
from ...function.compnay import get_single_company
from ...function.court import *
from ...function.supabase import *

router = APIRouter(
    prefix="/court",
    tags=['Courts']
)


@router.post("/upload_image/", status_code=status.HTTP_201_CREATED)
async def upload_image(
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    company = get_single_company(db, company_id=current_company.id)
    upload_file = await upload_image_on_supabase(login=company.login, folder="courts", files=files)
    return upload_file


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CourtBase)
def create_court(
        court: schemas.CourtBase, db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    images_as_str = [str(url) for url in court.images]
    new_court = create_new_court(
        name=court.name,
        images=images_as_str,
        company_id=current_company.id
    )
    db.add(new_court)
    db.commit()
    db.refresh(new_court)
    return new_court


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[schemas.Court])
def get_court(
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    courts = get_all_court(db, id=current_company.id)
    return courts


@router.get("/{court_id}", response_model=schemas.Court)
def get_court_by_id(
        court_id: int,
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    """Get a specific court by ID"""
    court = get_court_by_id(db, court_id=court_id, company_id=current_company.id)
    
    if not court:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Court not found")
    
    return court


@router.put("/{court_id}", response_model=schemas.Court)
def update_court(
        court_id: int,
        court_data: schemas.CourtUpdate,
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    """Update an existing court"""
    # Check if court exists
    court = get_court_by_id(db, court_id=court_id, company_id=current_company.id)
    
    if not court:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Court not found")
    
    # Handle images if provided
    update_data = court_data.dict(exclude_unset=True)
    if "images" in update_data and update_data["images"]:
        update_data["images"] = [str(url) for url in update_data["images"]]
    
    # Update court
    updated_court = update_court_details(
        db, court_id=court_id, company_id=current_company.id, update_data=update_data
    )
    db.commit()
    
    return updated_court


@router.delete("/{court_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_court(
        court_id: int,
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    """Delete a court"""
    # Check if court exists
    court = get_court_by_id(db, court_id=court_id, company_id=current_company.id)
    
    if not court:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Court not found")
    
    # Check if court is being used in any matches
    if is_court_in_use(db, court_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Cannot delete court that is being used in matches")
    
    # Delete the court
    delete_court_by_id(db, court_id=court_id, company_id=current_company.id)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
