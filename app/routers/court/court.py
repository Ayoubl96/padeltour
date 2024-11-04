import fastapi
from fastapi import Response, status, HTTPException, Depends, APIRouter, File, UploadFile, status
from sqlalchemy.orm import Session
from typing import Optional, List
from ... import models, schemas, tools, oauth2
from ...config import settings
from ...db import get_db
from sqlalchemy.sql import or_
from sqlalchemy import func
from supabase import create_client, Client
import uuid

router = APIRouter(
    prefix="/court",
    tags=['Companies']
)

@router.post("/upload_image/", status_code=status.HTTP_201_CREATED)
async def upload_image(
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    company = db.query(models.Company).filter(models.Company.id == current_company.id).first()
    folder_name = f"{company.login}/courts/"
    image_urls = []

    for file in files:
        # Genera un nome unico per l'immagine
        file_extension = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"{folder_name}{file_name}"

        # Leggi il contenuto del file come bytes
        file_content = await file.read()

        # Carica l'immagine su Supabase Storage
        response = supabase.storage.from_('padelcourt_dev').upload(file_path, file_content)

        # Controlla se ci sono errori durante il caricamento
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Errore durante il caricamento dell'immagine")

        # Ottieni l'URL pubblico dell'immagine
        public_url = supabase.storage.from_(settings.supabase_bucket).get_public_url(file_path)
        image_urls.append(public_url)

    return {"image_urls":image_urls}


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CourtBase)
def create_court(
        court: schemas.CourtBase, db: Session = Depends(get_db),
        current_company: int = Depends(oauth2.get_current_user)
):
    images_as_str = [str(url) for url in court.images]
    new_court = models.Court(
        name=court.name,
        images=images_as_str,
        company_id=current_company.id
    )
    db.add(new_court)
    db.commit()
    db.refresh(new_court)
    return new_court
