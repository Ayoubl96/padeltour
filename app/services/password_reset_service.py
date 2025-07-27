from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from datetime import datetime, timezone, timedelta

from app.models.password_reset import PasswordReset
from app.models.company import Company
from app.services.email_service import LoopsEmailService
from app.utils.security import hash_password
from app.utils.logging_utils import log_user_action, log_error


class PasswordResetService:
    def __init__(self, db: Session, email_service: LoopsEmailService):
        self.db = db
        self.email_service = email_service
    
    def _get_client_info(self, request: Request) -> Dict[str, str]:
        """Extract client information for security audit"""
        return {
            "ip_address": request.client.host if request and request.client else None,
            "user_agent": request.headers.get("user-agent") if request else None
        }
    
    def _cleanup_old_requests(self, email: str):
        """Clean up old/expired password reset requests for the email"""
        old_requests = self.db.query(PasswordReset).filter(
            PasswordReset.email == email
        ).all()
        
        for req in old_requests:
            self.db.delete(req)
        self.db.commit()
    
    def _check_rate_limit(self, email: str, ip_address: str) -> bool:
        """Check if rate limit is exceeded (max 3 requests per hour per email/IP)"""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Check email-based rate limit
        email_count = self.db.query(PasswordReset).filter(
            PasswordReset.email == email,
            PasswordReset.created_at > one_hour_ago
        ).count()
        
        # Check IP-based rate limit
        ip_count = self.db.query(PasswordReset).filter(
            PasswordReset.ip_address == ip_address,
            PasswordReset.created_at > one_hour_ago
        ).count() if ip_address else 0
        
        return email_count >= 3 or ip_count >= 3
    
    async def initiate_password_reset(self, email: str, request: Request = None) -> Dict[str, Any]:
        """Step 1: Initiate password reset by sending verification code"""
        
        # Get client information for security
        client_info = self._get_client_info(request)
        
        # Check if email service is configured
        if not self.email_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please contact support."
            )
        
        # Check if user exists
        user = self.db.query(Company).filter(Company.email == email).first()
        if not user:
            # Security: Don't reveal if email exists, but log the attempt
            log_error(
                "padeltour.password_reset",
                f"Password reset attempt for non-existent email: {email}",
                error_type="security_warning",
                request=request
            )
            # Return success to prevent email enumeration
            return {
                "success": True,
                "message": "If the email exists, a password reset code has been sent."
            }
        
        # Check rate limiting
        if self._check_rate_limit(email, client_info["ip_address"]):
            log_error(
                "padeltour.password_reset",
                f"Password reset rate limit exceeded for email: {email}, IP: {client_info['ip_address']}",
                error_type="rate_limit_exceeded",
                request=request,
                user_id=user.id
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later."
            )
        
        # Clean up old requests
        self._cleanup_old_requests(email)
        
        # Generate secure token and code
        reset_token = PasswordReset.generate_secure_token()
        verification_code = PasswordReset.generate_verification_code()
        expires_at = PasswordReset.create_expiry_time(15)  # 15 minutes
        
        # Create password reset record
        password_reset = PasswordReset(
            email=email,
            token=reset_token,
            code=verification_code,
            expires_at=expires_at,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        self.db.add(password_reset)
        self.db.commit()
        
        # Send password reset email
        email_sent = await self.email_service.send_password_reset_email(
            email=email,
            code=verification_code,
            company_name=user.name,
            reset_token=reset_token
        )
        
        if not email_sent:
            # Clean up if email failed
            self.db.delete(password_reset)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email. Please try again."
            )
        
        # Log successful initiation
        log_user_action(
            "padeltour.password_reset",
            "reset_initiated",
            user_id=user.id,
            request=request,
            extra_data={"email": email}
        )
        
        return {
            "success": True,
            "message": "Password reset code sent to your email.",
            "expires_in_minutes": 15
        }
    
    def verify_reset_code(self, email: str, code: str, request: Request = None) -> Dict[str, Any]:
        """Step 2: Verify the reset code and return token for password change"""
        
        # Find the reset request
        reset_request = self.db.query(PasswordReset).filter(
            PasswordReset.email == email,
            PasswordReset.code == code
        ).first()
        
        if not reset_request:
            log_error(
                "padeltour.password_reset",
                f"Invalid reset code attempt for email: {email}",
                error_type="security_warning",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code."
            )
        
        if not reset_request.is_valid():
            log_error(
                "padeltour.password_reset",
                f"Expired or invalid reset request for email: {email}",
                error_type="security_warning",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired or is no longer valid."
            )
        
        # Increment attempts
        reset_request.increment_attempts()
        self.db.commit()
        
        # Log successful verification
        user = self.db.query(Company).filter(Company.email == email).first()
        log_user_action(
            "padeltour.password_reset",
            "code_verified",
            user_id=user.id if user else None,
            request=request,
            extra_data={"email": email}
        )
        
        return {
            "success": True,
            "message": "Code verified successfully.",
            "reset_token": reset_request.token
        }
    
    def complete_password_reset(self, token: str, new_password: str, request: Request = None) -> Dict[str, Any]:
        """Step 3: Complete password reset with new password"""
        
        # Find the reset request by token
        reset_request = self.db.query(PasswordReset).filter(
            PasswordReset.token == token
        ).first()
        
        if not reset_request or not reset_request.is_valid():
            log_error(
                "padeltour.password_reset",
                f"Invalid or expired reset token used",
                error_type="security_warning",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token."
            )
        
        # Find the user
        user = self.db.query(Company).filter(Company.email == reset_request.email).first()
        if not user:
            log_error(
                "padeltour.password_reset",
                f"Password reset attempted for non-existent user: {reset_request.email}",
                error_type="security_error",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found."
            )
        
        # Hash and update password
        hashed_password = hash_password(new_password)
        user.password = hashed_password
        
        # Mark reset request as used
        reset_request.used = True
        
        self.db.commit()
        
        # Clean up all reset requests for this email
        self._cleanup_old_requests(reset_request.email)
        
        # Log successful password reset
        log_user_action(
            "padeltour.password_reset",
            "password_reset_completed",
            user_id=user.id,
            request=request,
            extra_data={"email": user.email}
        )
        
        return {
            "success": True,
            "message": "Password reset successfully. You can now login with your new password."
        }
    
    def get_reset_status(self, token: str) -> Dict[str, Any]:
        """Get the status of a password reset token"""
        reset_request = self.db.query(PasswordReset).filter(
            PasswordReset.token == token
        ).first()
        
        if not reset_request:
            return {"valid": False, "reason": "Token not found"}
        
        if reset_request.used:
            return {"valid": False, "reason": "Token already used"}
        
        if reset_request.is_expired():
            return {"valid": False, "reason": "Token expired"}
        
        if reset_request.attempts >= 3:
            return {"valid": False, "reason": "Too many attempts"}
        
        return {
            "valid": True,
            "email": reset_request.email,
            "expires_at": reset_request.expires_at.isoformat(),
            "attempts_remaining": 3 - reset_request.attempts
        } 