from app.schemas.base import *


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str 