from app.models.base import *
from datetime import datetime, timezone


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    code = Column(String(6), nullable=False)
    registration_data = Column(JSON, nullable=False)  # Store all form data
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    attempts = Column(Integer, default=0)
    
    def is_expired(self) -> bool:
        """Check if the verification code has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def increment_attempts(self):
        """Increment the number of verification attempts"""
        self.attempts += 1 