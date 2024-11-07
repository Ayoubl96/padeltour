from supabase import create_client, Client
from ..config import settings
from fastapi import HTTPException, UploadFile
import uuid
from typing import List


def connection_supabase():
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    return supabase


async def upload_image_on_supabase(login: str, folder: str, files: List[UploadFile]):
    supabase = connection_supabase()
    folder_name = f"{login}/{folder}/"
    image_urls = []

    for file in files:
        # Genera un nome unico per l'immagine
        file_extension = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"{folder_name}{file_name}"

        # Leggi il contenuto del file come bytes (asincrono)
        file_content = await file.read()  # Correzione: usa await per leggere il contenuto del file

        # Carica l'immagine su Supabase Storage
        response = supabase.storage.from_('padelcourt_dev').upload(file_path, file_content)

        # Controlla se ci sono errori durante il caricamento
        if not response:  # l'upload di supabase restituisce None in caso di successo
            raise HTTPException(status_code=500, detail="Errore durante il caricamento dell'immagine")

        # Ottieni l'URL pubblico dell'immagine
        public_url = supabase.storage.from_(settings.supabase_bucket).get_public_url(file_path)

        # Aggiungi l'URL pubblico direttamente alla lista
        image_urls.append(public_url)  # Ora public_url è una stringa, non un dizionario

    return {"image_urls":image_urls}