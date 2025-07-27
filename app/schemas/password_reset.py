from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re


class PasswordResetInitiateRequest(BaseModel):
    """Request to initiate password reset"""
    email: EmailStr = Field(..., description="Email address of the account to reset")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "company@example.com"
            }
        }


class PasswordResetInitiateResponse(BaseModel):
    """Response for password reset initiation"""
    success: bool
    message: str
    expires_in_minutes: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Password reset code sent to your email.",
                "expires_in_minutes": 15
            }
        }


class PasswordResetVerifyRequest(BaseModel):
    """Request to verify reset code"""
    email: EmailStr = Field(..., description="Email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('Code must contain only digits')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "company@example.com",
                "code": "123456"
            }
        }


class PasswordResetVerifyResponse(BaseModel):
    """Response for code verification"""
    success: bool
    message: str
    reset_token: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Code verified successfully.",
                "reset_token": "secure_token_here"
            }
        }


class PasswordResetCompleteRequest(BaseModel):
    """Request to complete password reset"""
    token: str = Field(..., description="Reset token from verification step")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="New password (minimum 8 characters)"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one letter
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "secure_token_here",
                "new_password": "newsecurepassword123"
            }
        }


class PasswordResetCompleteResponse(BaseModel):
    """Response for password reset completion"""
    success: bool
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Password reset successfully. You can now login with your new password."
            }
        }


class PasswordResetStatusResponse(BaseModel):
    """Response for reset token status check"""
    valid: bool
    reason: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[str] = None
    attempts_remaining: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "email": "company@example.com",
                "expires_at": "2024-01-01T12:00:00Z",
                "attempts_remaining": 2
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid verification code."
            }
        } 