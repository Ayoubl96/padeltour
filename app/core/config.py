from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    db_password: str
    db_user: str
    db_name: str
    db_host: str
    secret_key: str
    algorithm: str
    access_token_exp_minutes: int
    refresh_token_exp_days: int = 7
    supabase_url: str
    supabase_key: str
    supabase_bucket: str
    playtomic_api_url: str
    playtomic_email: str
    playtomic_password: str
    
    # Loops Email Configuration (Optional for now)
    loops_api_key: Optional[str] = None
    loops_verification_template_id: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings() 