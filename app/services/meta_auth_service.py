
import httpx
import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.config import settings

# Define the path for our persistent storage file
STORAGE_PATH = Path(__file__).parent.parent.parent / "storage.json"

class MetaAuthService:
    """
    Handles Meta (Facebook/Instagram) OAuth2 flow and token management.
    """
    BASE_URL = "https://graph.facebook.com/v23.0"

    @staticmethod
    def get_auth_url() -> str:
        """
        Generates the Meta authorization URL for the user to visit.
        """
        scopes = [
            "public_profile",
            "email",
            "pages_show_list",
            "instagram_basic",
            "instagram_manage_comments",
            "pages_read_engagement"
        ]
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.meta_redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
        }
        auth_url = f"https://www.facebook.com/v23.0/dialog/oauth?{httpx.URL(params).query.decode('utf-8')}"
        return auth_url

    @staticmethod
    def _save_credentials(credentials: Dict[str, Any]):
        """Saves credentials to the storage file."""
        with open(STORAGE_PATH, "w") as f:
            json.dump(credentials, f, indent=4)

    @staticmethod
    def get_credentials() -> Optional[Dict[str, Any]]:
        """Loads credentials from the storage file."""
        if not STORAGE_PATH.exists():
            return None
        with open(STORAGE_PATH, "r") as f:
            return json.load(f)

    @staticmethod
    def exchange_code_for_token(code: str) -> Optional[str]:
        """
        Exchanges an authorization code for a long-lived access token and stores it.
        """
        url = f"{MetaAuthService.BASE_URL}/oauth/access_token"
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.meta_redirect_uri,
            "client_secret": settings.meta_app_secret,
            "code": code,
        }
        
        try:
            with httpx.Client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                long_lived_token = data.get("access_token")
                if not long_lived_token:
                    return None

                # Discover and save assets
                MetaAuthService.discover_and_store_assets(long_lived_token)
                
                return long_lived_token
        except httpx.HTTPStatusError as e:
            print(f"Error exchanging code for token: {e.response.text}")
            return None

    @staticmethod
    def discover_and_store_assets(user_access_token: str):
        """
        Discovers Facebook Pages and linked Instagram accounts, then stores them.
        """
        url = f"{MetaAuthService.BASE_URL}/me/accounts"
        params = {"access_token": user_access_token}

        try:
            with httpx.Client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                pages = response.json().get("data", [])

                for page in pages:
                    page_id = page["id"]
                    # Check for linked Instagram account
                    ig_url = f"{MetaAuthService.BASE_URL}/{page_id}"
                    ig_params = {
                        "fields": "instagram_business_account",
                        "access_token": user_access_token,
                    }
                    ig_response = client.get(ig_url, params=ig_params)
                    
                    if ig_response.status_code == 200:
                        ig_data = ig_response.json()
                        if "instagram_business_account" in ig_data:
                            ig_account_id = ig_data["instagram_business_account"]["id"]
                            
                            # Found the first valid page, save credentials and exit
                            credentials = {
                                "user_access_token": user_access_token,
                                "fb_page_id": page_id,
                                "ig_business_account_id": ig_account_id,
                            }
                            MetaAuthService._save_credentials(credentials)
                            print(f"Successfully found and stored credentials for page {page_id} and IG account {ig_account_id}")
                            return

                print("Could not find any Facebook Page with a linked Instagram Business Account.")

        except httpx.HTTPStatusError as e:
            print(f"Error discovering assets: {e.response.text}")

