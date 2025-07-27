from app.models.base import *
from sqlalchemy import Boolean
from datetime import datetime, timezone, timedelta
import secrets
import string


class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, index=True)  # Index for fast lookup
    token = Column(String, nullable=False, unique=True)  # Secure reset token
    code = Column(String(6), nullable=False)  # 6-digit code for UX
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    attempts = Column(Integer, default=0)
    used = Column(Boolean, default=False)  # Prevent token reuse
    user_agent = Column(String, nullable=True)  # Security audit trail
    ip_address = Column(String, nullable=True)  # Security audit trail
    
    def is_expired(self) -> bool:
        """Check if the reset request has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the reset request is valid (not expired, not used, not too many attempts)"""
        return not self.is_expired() and not self.used and self.attempts < 3
    
    def increment_attempts(self):
        """Increment the number of verification attempts"""
        self.attempts += 1
    
    @classmethod
    def generate_secure_token(cls) -> str:
        """Generate a cryptographically secure reset token"""
        return secrets.token_urlsafe(32)  # 32 bytes = 256 bits of entropy
    
    @classmethod
    def generate_verification_code(cls) -> str:
        """Generate a 6-digit verification code for better UX"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @classmethod
    def create_expiry_time(cls, minutes: int = 15) -> datetime:
        """Create expiry time (default 15 minutes for password reset)"""
        return datetime.now(timezone.utc) + timedelta(minutes=minutes) 