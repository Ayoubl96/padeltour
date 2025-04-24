from supabase import create_client, Client
from fastapi import HTTPException, UploadFile
import uuid
from typing import List
from app.core.config import settings


class StorageService:
    @staticmethod
    def connection_supabase():
        supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
        return supabase

    @staticmethod
    async def upload_image_on_supabase(login: str, folder: str, files: List[UploadFile]):
        supabase = StorageService.connection_supabase()
        folder_name = f"{login}/{folder}/"
        image_urls = []

        for file in files:
            # Generate a unique name for the image
            file_extension = file.filename.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"{folder_name}{file_name}"

            # Read the file content as bytes (async)
            file_content = await file.read()

            # Upload the image to Supabase Storage
            response = supabase.storage.from_(settings.supabase_bucket).upload(file_path, file_content)

            # Check for errors during upload
            if not response:  # supabase upload returns None on success
                raise HTTPException(status_code=500, detail="Error uploading image")

            # Get the public URL of the image
            public_url = supabase.storage.from_(settings.supabase_bucket).get_public_url(file_path)

            # Add the public URL directly to the list
            image_urls.append(public_url)

        return {"image_urls": image_urls} 