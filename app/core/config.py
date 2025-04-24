from pydantic_settings import BaseSettings


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

    class Config:
        env_file = ".env"


settings = Settings() 