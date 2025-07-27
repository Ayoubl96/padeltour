from app.schemas.base import *
from typing import Optional


class CompanyBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None  # Fixed: changed from 'phone' to match model
    address: Optional[str] = None

    class Config:
        from_attributes = True


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    players_count: Optional[int] = None
    courts_count: Optional[int] = None
    tournaments_count: Optional[int] = None
    vat_number: Optional[str] = None
    login: str

    class Config:
        from_attributes = True


class CompanyUpdate(BaseModel):
    """Schema for partial company updates - all fields optional"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    vat_number: Optional[str] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for password change requests"""
    current_password: str
    new_password: str
    confirm_password: str

    class Config:
        from_attributes = True


class PasswordChangeResponse(BaseModel):
    """Response schema for password change"""
    success: bool
    message: str

    class Config:
        from_attributes = True 