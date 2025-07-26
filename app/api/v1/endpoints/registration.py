from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.db.database import get_db
from app.services.registration_service import RegistrationService
from app.services.email_service import LoopsEmailService
from app.schemas.registration import (
    CompanyRegistration, 
    EmailVerification, 
    ResendVerification,
    RegistrationInitiateResponse
)

router = APIRouter()


@router.get(
    "/test-loops",
    status_code=status.HTTP_200_OK,
    summary="Test Loops API connection",
    description="Test the Loops API connection and configuration"
)
def test_loops_connection():
    """
    Test endpoint to verify Loops API integration
    
    - Tests API key validity
    - Returns connection status
    """
    try:
        email_service = LoopsEmailService()
        
        if not email_service.is_configured:
            return {
                "status": "not_configured",
                "message": "Loops API is not configured. Please set LOOPS_API_KEY and LOOPS_VERIFICATION_TEMPLATE_ID environment variables.",
                "api_configured": False,
                "missing_config": [
                    key for key in ["LOOPS_API_KEY", "LOOPS_VERIFICATION_TEMPLATE_ID"] 
                    if not getattr(email_service, key.lower().replace("loops_", ""), None)
                ]
            }
        
        is_connected = email_service.test_api_connection()
        
        if is_connected:
            return {
                "status": "success",
                "message": "Loops API connection successful",
                "api_configured": True
            }
        else:
            return {
                "status": "error", 
                "message": "Loops API connection failed. Please check your API key and template ID.",
                "api_configured": True
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing Loops connection: {str(e)}"
        )


@router.post(
    "/initiate", 
    status_code=status.HTTP_200_OK,
    response_model=RegistrationInitiateResponse,
    summary="Initiate company registration",
    description="Send verification code to email and store registration data temporarily"
)
async def initiate_registration(
    registration_data: CompanyRegistration,
    db: Session = Depends(get_db)
):
    """
    Step 1 of registration: Send verification code to email
    
    - Validates that email is not already registered
    - Generates a 6-digit verification code
    - Sends email with verification code
    - Stores registration data temporarily (expires in 10 minutes)
    """
    registration_service = RegistrationService(db)
    return await registration_service.initiate_registration(registration_data.dict())


@router.post(
    "/verify", 
    status_code=status.HTTP_201_CREATED, 
    response_model=schemas.CompanyOut,
    summary="Verify email and complete registration",
    description="Verify the email code and create the company account"
)
async def verify_and_complete(
    verification_data: EmailVerification,
    db: Session = Depends(get_db)
):
    """
    Step 2 of registration: Verify code and create company account
    
    - Validates the 6-digit verification code
    - Creates the company account if code is valid
    - Returns the created company data
    - Cleans up temporary verification data
    """
    registration_service = RegistrationService(db)
    return await registration_service.verify_and_complete_registration(
        email=verification_data.email,
        code=verification_data.code
    )


@router.post(
    "/resend", 
    status_code=status.HTTP_200_OK,
    response_model=RegistrationInitiateResponse,
    summary="Resend verification code",
    description="Resend verification code to email"
)
async def resend_verification(
    resend_data: ResendVerification,
    db: Session = Depends(get_db)
):
    """
    Resend verification code for pending registration
    
    - Generates a new 6-digit verification code
    - Extends expiration time by 10 minutes
    - Resets failed attempt counter
    - Sends new verification email
    """
    registration_service = RegistrationService(db)
    return await registration_service.resend_verification_code(resend_data.email) 