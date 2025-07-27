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
        self.login_info_template_id = settings.loops_login_info_template_id
        self.password_reset_template_id = getattr(settings, 'loops_password_reset_template_id', None)
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

    async def send_login_info_email(self, email: str, company_name: str, login: str) -> bool:
        """Send login information email using Loops transactional email"""
        if not self.api_key or not self.login_info_template_id:
            print("Loops login info template is not configured. Please set LOOPS_API_KEY and LOOPS_LOGIN_INFO_TEMPLATE_ID")
            return False
            
        try:
            payload = {
                "email": email,
                "transactionalId": self.login_info_template_id,
                "dataVariables": {
                    "companyName": company_name,
                    "login": login,
                    "email": email
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
                print(f"Loops API error sending login info: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending login info email: {e}")
            return False
    
    async def send_password_reset_email(self, email: str, code: str, company_name: str, reset_token: str) -> bool:
        """Send password reset email using Loops transactional email"""
        if not self.api_key or not self.password_reset_template_id:
            print("Loops password reset template is not configured. Please set LOOPS_API_KEY and LOOPS_PASSWORD_RESET_TEMPLATE_ID")
            return False
            
        try:
            # Create secure reset link (you'll need to define your frontend reset URL)
            reset_link = f"https://{settings.frontend_url}/reset-password?token={reset_token}"
            
            payload = {
                "email": email,
                "transactionalId": self.password_reset_template_id,
                "dataVariables": {
                    "verificationCode": code,
                    "companyName": company_name,
                    "resetLink": reset_link,
                    "expiryMinutes": "15"
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
                print(f"Loops API error sending password reset: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending password reset email: {e}")
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