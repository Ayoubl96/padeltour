from pydantic import BaseModel, EmailStr, conint
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    email: str
    password: str
    phone_number: str


