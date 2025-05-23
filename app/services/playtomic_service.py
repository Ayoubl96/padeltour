from typing import Optional, List, Dict, Any
import requests
from app.core.config import settings


class PlaytomicService:
    """Service class for Playtomic API interactions"""
    
    class PlaytomicAPIClient:
        def __init__(self):
            self.api_url = settings.playtomic_api_url
            self.email = settings.playtomic_email
            self.password = settings.playtomic_password
            self.access_token = None
            self.refresh_token = None

        def login(self):
            """Authenticate the user and retrieve tokens."""
            url = f"{self.api_url}/v3/auth/login"
            payload = {
                "email": self.email,
                "password": self.password
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Raise an error if the request fails
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")

        def refresh_access_token(self):
            """Refresh the access token using the refresh token."""
            url = f"{self.api_url}/auth/refresh"
            headers = {
                "Authorization": f"Bearer {self.refresh_token}"
            }
            response = requests.post(url, headers=headers)
            if response.status_code == 401:
                # If refresh token is invalid, retry login
                self.login()
            else:
                response.raise_for_status()
                data = response.json()
                self.access_token = data.get("access_token")

        def _get_headers(self) -> dict:
            """Return the headers for API requests."""
            if not self.access_token:
                self.login()
            return {
                "Authorization": f"Bearer {self.access_token}"
            }

        def make_request(self, endpoint: str, method: str = "GET", data: Optional[dict] = None, params: Optional[dict] = None):
            """
            Make an API request with automatic token refresh handling.

            Args:
                endpoint (str): The API endpoint (relative to the base URL).
                method (str): HTTP method (GET, POST, etc.).
                data (dict, optional): Request payload for POST/PUT requests.
                params (dict, optional): Query parameters for GET requests.

            Returns:
                dict: The JSON response from the API.
            """
            url = f"{self.api_url}/{endpoint.lstrip('/')}"
            headers = self._get_headers()

            # Choose the appropriate request method
            method = method.upper()
            request_func = getattr(requests, method.lower(), None)
            if not request_func:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Make the request with optional params and data
            if method == "GET":
                response = request_func(url, headers=headers, params=params)
            else:
                response = request_func(url, headers=headers, json=data)

            # Handle token expiration
            if response.status_code == 401 and "token expired" in response.text.lower():
                self.refresh_access_token()
                headers = self._get_headers()  # Update headers with new token
                # Retry the request with the new token
                if method == "GET":
                    response = request_func(url, headers=headers, params=params)
                else:
                    response = request_func(url, headers=headers, json=data)

            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def get_client():
        """Get a client instance for making API calls"""
        return PlaytomicService.PlaytomicAPIClient()
    
    @staticmethod
    def get_user_from_playtomic(name: str):
        """Search for users by name"""
        client = PlaytomicService.get_client()
        try:
            data = client.make_request(
                "/v1/social/users",
                method="GET",
                params={
                    "name": name,
                    "requester_user_id": "me",
                    "size": "50",
                }
            )
            return data
        except requests.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
    
    @staticmethod
    def get_user_by_id_from_playtomic(user_id: int):
        """Get user details by ID"""
        client = PlaytomicService.get_client()
        try:
            data = client.make_request(
                "/v2/users",
                method="GET",
                params={
                    "user_id": user_id,
                }
            )
            return data
        except requests.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
    
    @staticmethod
    def get_user_level_from_playtomic(user_id: int):
        """Get user's padel level"""
        client = PlaytomicService.get_client()
        try:
            data = client.make_request(
                "/v1/levels",
                method="GET",
                params={
                    "size": 1000,
                    "sport_id": "PADEL",
                    "status": "CONFIRMED",
                    "user_id": user_id,
                    "with_history": "false",
                    "with_history_size": 0
                }
            )
            return data
        except requests.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise 