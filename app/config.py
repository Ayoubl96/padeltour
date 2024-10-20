from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_password: str
    db_user: str
    db_name: str
    db_host: str
    secret_key: str
    algorithm: str
    access_token_exp_minutes: int

    class Config:
        env_file = ".env"


settings = Settings()
