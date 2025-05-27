from pydantic import BaseModel, EmailStr
from typing import Optional


class CompanyRegistration(BaseModel):
    """Schema for initial company registration data"""
    email: EmailStr
    password: str
    name: str
    address: str
    phone_number: str

    class Config:
        schema_extra = {
            "example": {
                "email": "company@example.com",
                "password": "securepassword123",
                "name": "Padel Club Barcelona",
                "address": "Carrer de la Marina, 123, Barcelona",
                "phone_number": "+34 123 456 789"
            }
        }


class EmailVerification(BaseModel):
    """Schema for email verification"""
    email: EmailStr
    code: str

    class Config:
        schema_extra = {
            "example": {
                "email": "company@example.com",
                "code": "123456"
            }
        }


class ResendVerification(BaseModel):
    """Schema for resending verification code"""
    email: EmailStr

    class Config:
        schema_extra = {
            "example": {
                "email": "company@example.com"
            }
        }


class RegistrationInitiateResponse(BaseModel):
    """Response schema for registration initiation"""
    message: str
    email: str
    expires_in_minutes: int

    class Config:
        schema_extra = {
            "example": {
                "message": "Verification code sent to your email",
                "email": "company@example.com",
                "expires_in_minutes": 10
            }
        } 