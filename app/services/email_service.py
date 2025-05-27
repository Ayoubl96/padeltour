import requests
import secrets
import string
from typing import Dict, Any
from app.core.config import settings


class LoopsEmailService:
    """Service for sending emails using Loops API"""
    
    BASE_URL = "https://app.loops.so/api/v1"
    
    def __init__(self):
        self.api_key = settings.loops_api_key
        self.verification_template_id = settings.loops_verification_template_id
        self.is_configured = bool(self.api_key and self.verification_template_id)
        
        if self.is_configured:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = {}
    
    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    async def send_verification_email(self, email: str, code: str, company_name: str) -> bool:
        """Send verification email using Loops transactional email"""
        if not self.is_configured:
            print("Loops is not configured. Please set LOOPS_API_KEY and LOOPS_VERIFICATION_TEMPLATE_ID")
            return False
            
        try:
            payload = {
                "email": email,
                "transactionalId": self.verification_template_id,
                "dataVariables": {
                    "verificationCode": code,
                    "companyName": company_name,
                    "expiryMinutes": "10"
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/transactional",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Loops API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False
    
    def test_api_connection(self) -> bool:
        """Test the Loops API connection"""
        if not self.is_configured:
            return False
            
        try:
            response = requests.get(
                f"{self.BASE_URL}/api-key",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200 and response.json().get("success", False)
        except Exception as e:
            print(f"Error testing Loops API: {e}")
            return False 