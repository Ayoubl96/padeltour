from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any

from app.models.email_verification import EmailVerification
from app.models.company import Company
from app.services.email_service import LoopsEmailService
from app.services.company_service import CompanyService


class RegistrationService:
    """Service for handling company registration with email verification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = LoopsEmailService()
        self.company_service = CompanyService(db)
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists in companies table"""
        existing_company = self.db.query(Company).filter(Company.email == email).first()
        return existing_company is not None
    
    async def initiate_registration(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Store registration data and send verification code"""
        email = registration_data["email"]
        
        # Check if Loops is configured
        if not self.email_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please contact support."
            )
        
        # Check if email already exists in companies
        if self.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate verification code
        code = self.email_service.generate_verification_code()
        
        # Remove existing verification record if exists
        existing_verification = self.db.query(EmailVerification).filter(
            EmailVerification.email == email
        ).first()
        
        if existing_verification:
            self.db.delete(existing_verification)
            self.db.commit()
        
        # Create new verification record
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        verification = EmailVerification(
            email=email,
            code=code,
            registration_data=registration_data,
            expires_at=expires_at
        )
        
        self.db.add(verification)
        self.db.commit()
        
        # Send verification email
        email_sent = await self.email_service.send_verification_email(
            email=email,
            code=code,
            company_name=registration_data["name"]
        )
        
        if not email_sent:
            # Clean up verification record if email failed
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again."
            )
        
        return {
            "message": "Verification code sent to your email",
            "email": email,
            "expires_in_minutes": 10
        }
    
    def verify_and_complete_registration(self, email: str, code: str) -> Company:
        """Step 2: Verify code and create company account"""
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.email == email
        ).first()
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification record not found. Please start registration again."
            )
        
        # Check if expired
        if verification.is_expired():
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired. Please start registration again."
            )
        
        # Check attempts limit
        if verification.attempts >= 3:
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many failed attempts. Please start registration again."
            )
        
        # Verify code
        if verification.code != code:
            verification.increment_attempts()
            self.db.commit()
            remaining_attempts = 3 - verification.attempts
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {remaining_attempts} attempts remaining."
            )
        
        # Double-check email doesn't exist (race condition protection)
        if self.email_exists(email):
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create company account using existing service
        registration_data = verification.registration_data
        try:
            company = self.company_service.create_company(
                email=registration_data["email"],
                password=registration_data["password"],
                name=registration_data["name"],
                address=registration_data["address"],
                phone_number=registration_data["phone_number"]
            )
            
            # Clean up verification record
            self.db.delete(verification)
            self.db.commit()
            
            return company
            
        except Exception as e:
            # If company creation fails, keep verification record for retry
            raise e
    
    async def resend_verification_code(self, email: str) -> Dict[str, Any]:
        """Resend verification code"""
        # Check if Loops is configured
        if not self.email_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please contact support."
            )
            
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.email == email
        ).first()
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending verification for this email"
            )
        
        # Generate new code and extend expiry
        new_code = self.email_service.generate_verification_code()
        verification.code = new_code
        verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        verification.attempts = 0  # Reset attempts
        
        self.db.commit()
        
        # Send new verification email
        email_sent = await self.email_service.send_verification_email(
            email=email,
            code=new_code,
            company_name=verification.registration_data["name"]
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again."
            )
        
        return {
            "message": "New verification code sent",
            "expires_in_minutes": 10
        } 