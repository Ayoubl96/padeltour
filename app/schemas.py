from pydantic import BaseModel, EmailStr, conint
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    email: str
    password: str
    phone_number: str
    name: str
    address: str


class CompanyOut(BaseModel):
    id: int
    login: str
    name: str
    address: str
    email: str
    phone_number: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
