from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.password_reset_service import PasswordResetService
from app.services.email_service import LoopsEmailService
from app.schemas.password_reset import (
    PasswordResetInitiateRequest,
    PasswordResetInitiateResponse,
    PasswordResetVerifyRequest,
    PasswordResetVerifyResponse,
    PasswordResetCompleteRequest,
    PasswordResetCompleteResponse,
    PasswordResetStatusResponse,
    ErrorResponse
)

router = APIRouter()


def get_password_reset_service(db: Session = Depends(get_db)) -> PasswordResetService:
    """Dependency to get password reset service with email service"""
    email_service = LoopsEmailService()
    return PasswordResetService(db=db, email_service=email_service)


@router.post(
    "/initiate",
    response_model=PasswordResetInitiateResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate password reset",
    description="Send a password reset verification code to the user's email address",
    responses={
        200: {"model": PasswordResetInitiateResponse, "description": "Password reset initiated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid email or user not found"},
        429: {"model": ErrorResponse, "description": "Too many requests"},
        503: {"model": ErrorResponse, "description": "Email service unavailable"}
    }
)
async def initiate_password_reset(
    request_data: PasswordResetInitiateRequest,
    request: Request,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service)
):
    """
    **Step 1: Initiate Password Reset**
    
    Sends a 6-digit verification code to the user's email address.
    
    **Security Features:**
    - Rate limiting: Max 3 attempts per hour per email/IP
    - Email enumeration protection: Always returns success
    - Secure token generation for reset links
    - IP and User-Agent tracking for audit
    
    **Process:**
    1. Validate email format
    2. Check rate limits
    3. Generate secure token and 6-digit code
    4. Send email with both code and reset link
    5. Return success message
    
    **Note:** For security, this endpoint will always return success even if the email doesn't exist.
    """
    return await password_reset_service.initiate_password_reset(
        email=request_data.email,
        request=request
    )


@router.post(
    "/verify",
    response_model=PasswordResetVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify reset code",
    description="Verify the 6-digit code and get a reset token",
    responses={
        200: {"model": PasswordResetVerifyResponse, "description": "Code verified successfully"},
        400: {"model": ErrorResponse, "description": "Invalid or expired code"}
    }
)
async def verify_reset_code(
    request_data: PasswordResetVerifyRequest,
    request: Request,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service)
):
    """
    **Step 2: Verify Reset Code**
    
    Verifies the 6-digit code sent to the user's email and returns a secure token for password reset.
    
    **Security Features:**
    - Code expires after 15 minutes
    - Max 3 verification attempts
    - Secure token returned for next step
    - Audit logging of attempts
    
    **Process:**
    1. Find reset request by email and code
    2. Validate code and check expiry
    3. Increment attempt counter
    4. Return secure token for password change
    
    **Important:** Save the returned `reset_token` for the final step.
    """
    return password_reset_service.verify_reset_code(
        email=request_data.email,
        code=request_data.code,
        request=request
    )


@router.post(
    "/complete",
    response_model=PasswordResetCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete password reset",
    description="Set new password using the reset token",
    responses={
        200: {"model": PasswordResetCompleteResponse, "description": "Password reset successfully"},
        400: {"model": ErrorResponse, "description": "Invalid token or weak password"}
    }
)
async def complete_password_reset(
    request_data: PasswordResetCompleteRequest,
    request: Request,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service)
):
    """
    **Step 3: Complete Password Reset**
    
    Sets the new password using the secure token from step 2.
    
    **Security Features:**
    - Token can only be used once
    - Password strength validation
    - Secure bcrypt hashing
    - All reset tokens for user are invalidated
    - Comprehensive audit logging
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one letter
    - At least one digit
    
    **Process:**
    1. Validate reset token
    2. Check password strength
    3. Hash and update password
    4. Invalidate all reset tokens
    5. Log successful reset
    
    **After completion:** User can login with their new password.
    """
    return password_reset_service.complete_password_reset(
        token=request_data.token,
        new_password=request_data.new_password,
        request=request
    )


@router.get(
    "/status/{token}",
    response_model=PasswordResetStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check reset token status",
    description="Check if a reset token is valid and get its status",
    responses={
        200: {"model": PasswordResetStatusResponse, "description": "Token status retrieved"}
    }
)
async def get_reset_status(
    token: str,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service)
):
    """
    **Check Reset Token Status**
    
    Check if a password reset token is still valid and get information about it.
    
    **Useful for:**
    - Frontend validation
    - Showing expiry time to user
    - Debugging reset issues
    
    **Returns:**
    - Token validity status
    - Expiry time
    - Remaining attempts
    - Associated email (if valid)
    
    **Token becomes invalid if:**
    - Expired (after 15 minutes)
    - Already used
    - Too many failed attempts (3+)
    """
    return password_reset_service.get_reset_status(token)


# Alternative endpoint for URL-based reset (if using links in emails)
@router.get(
    "/reset/{token}",
    status_code=status.HTTP_200_OK,
    summary="Password reset page redirect",
    description="Redirect endpoint for password reset links in emails",
    include_in_schema=False  # Hide from docs as it's for frontend routing
)
async def password_reset_redirect(
    token: str,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service)
):
    """
    **Password Reset Link Handler**
    
    This endpoint handles password reset links clicked from emails.
    It validates the token and can redirect to your frontend reset form.
    
    **Implementation Notes:**
    - Validate token before showing reset form
    - Redirect to frontend with token as parameter
    - Handle expired/invalid tokens gracefully
    """
    status_result = password_reset_service.get_reset_status(token)
    
    if not status_result["valid"]:
        # You can customize this redirect to your frontend error page
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reset link: {status_result.get('reason', 'Unknown error')}"
        )
    
    # Here you would typically redirect to your frontend
    # For now, return the token status
    return {
        "message": "Valid reset token. Redirect user to password reset form.",
        "token": token,
        "status": status_result
    } 