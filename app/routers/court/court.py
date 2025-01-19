from fastapi import Response, status, HTTPException, Depends, APIRouter, File, UploadFile, status
from sqlalchemy.orm import Session
from ... import models, schemas, tools, oauth2
from ...db import get_db
from sqlalchemy.sql import or_
from sqlalchemy import func
from app.function.compnay import get_single_company
from app.function.court import *
from app.function.supabase import *

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
    new_court = court.create_new_court(
        name=court.name,
        images=images_as_str,
        company_id=current_company.id
    )
    db.add(new_court)
    db.commit()
    db.refresh(new_court)
    return new_court


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[schemas.CourtBase])
def get_court(
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    courts = get_all_court(db, id=current_company.id)
    return courts
