import httpx
import json
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import urllib.parse
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.meta_credentials import MetaCredentials
from app.core.database import get_db # Necesitamos el generador de sesiones

class MetaAuthService:
    """
    Handles Meta (Facebook/Instagram) OAuth2 flow and token management.
    """
    BASE_URL = "https://graph.facebook.com/v23.0"
    _fernet: Fernet = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            cls._fernet = Fernet(settings.encryption_key.encode('utf-8'))
        return cls._fernet

    @classmethod
    def _encrypt(cls, data: str) -> str:
        return cls._get_fernet().encrypt(data.encode('utf-8')).decode('utf-8')

    @classmethod
    def _decrypt(cls, data: str) -> str:
        return cls._get_fernet().decrypt(data.encode('utf-8')).decode('utf-8')

    @staticmethod
    def get_auth_url() -> str:
        """
        Generates the Meta authorization URL for the user to visit.
        """
        scopes = [
            "public_profile",
            "pages_show_list",
            "pages_manage_metadata",
            "pages_manage_posts",
            "pages_read_engagement",
            "instagram_basic",
            "instagram_manage_comments"
        ]
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.meta_redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
        }
        query_string = urllib.parse.urlencode(params)
        auth_url = f"https://www.facebook.com/v23.0/dialog/oauth?{query_string}"
        return auth_url

    @staticmethod
    def _save_credentials_to_db(db: Session, credentials: Dict[str, Any]):
        """Saves or updates credentials in the database."""
        encrypted_access_token = MetaAuthService._encrypt(credentials["user_access_token"])
        encrypted_page_token = MetaAuthService._encrypt(credentials["page_access_token"])

        db_credentials = db.query(MetaCredentials).first()
        if db_credentials:
            db_credentials.encrypted_access_token = encrypted_access_token
            db_credentials.encrypted_page_token = encrypted_page_token
            db_credentials.fb_page_id = credentials.get("fb_page_id")
            db_credentials.ig_business_account_id = credentials.get("ig_business_account_id")
        else:
            db_credentials = MetaCredentials(
                encrypted_access_token=encrypted_access_token,
                encrypted_page_token=encrypted_page_token,
                fb_page_id=credentials.get("fb_page_id"),
                ig_business_account_id=credentials.get("ig_business_account_id"),
            )
            db.add(db_credentials)

        db.commit()
        db.refresh(db_credentials)

    @staticmethod
    def get_credentials_from_db(db: Session) -> Optional[Dict[str, Any]]:
        """Loads credentials from the database."""
        db_credentials = db.query(MetaCredentials).first()
        if db_credentials == None:
            return None
        decrypted_user_token = MetaAuthService._decrypt(db_credentials.encrypted_access_token)
        decrypted_page_token = (
            MetaAuthService._decrypt(db_credentials.encrypted_page_token)
            if db_credentials.encrypted_page_token else None
        )

        return {
            "user_access_token": decrypted_user_token,
            "page_access_token": decrypted_page_token,
            "fb_page_id": db_credentials.fb_page_id,
            "ig_business_account_id": db_credentials.ig_business_account_id,
        }

    @staticmethod
    def _get_long_lived_token(short_lived_token: str) -> Optional[str]:
        """Exchanges a short-lived token for a long-lived one."""
        url = f"{MetaAuthService.BASE_URL}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "fb_exchange_token": short_lived_token,
        }
        try:
            with httpx.Client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                long_lived_token = data.get("access_token")
                if not long_lived_token:
                    print("Error: Long-lived token not found in response.")
                    return None
                print("Successfully obtained a long-lived access token.")
                return long_lived_token
        except httpx.HTTPStatusError as e:
            print(f"Error exchanging short-lived token for long-lived token: {e.response.text}")
            return None


    @staticmethod
    def exchange_code_for_token(db: Session, code: str) -> Optional[str]:
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

                short_lived_token = data.get("access_token")
                if not short_lived_token:
                    print("Error: Short-lived token not found in initial exchange.")
                    return None

                # Exchange the short-lived token for a long-lived one
                long_lived_token = MetaAuthService._get_long_lived_token(short_lived_token)
                if not long_lived_token:
                    return None # Error already printed in the helper function

                # Discover and save assets
                MetaAuthService.discover_and_store_assets(db, long_lived_token)
                
                return long_lived_token
        except httpx.HTTPStatusError as e:
            print(f"Error exchanging code for short-lived token: {e.response.text}")
            return None

    @staticmethod
    def discover_and_store_assets(db: Session, user_access_token: str):
        """
        Discovers Facebook Pages and linked Instagram accounts, then stores them.
        Ensures a valid PAGE access_token is retrieved and saved.
        """
        me_accounts_url = f"{MetaAuthService.BASE_URL}/me/accounts"
        params = {"access_token": user_access_token}

        try:
            with httpx.Client() as client:
                # Get all Facebook pages linked to the user
                response = client.get(me_accounts_url, params=params)
                response.raise_for_status()
                pages = response.json().get("data", [])

                if not pages:
                    print("No Facebook Pages found for this user.")
                    return

                for page in pages:
                    page_id = page["id"]

                    # Always re-fetch page access_token directly from Graph API
                    token_url = f"{MetaAuthService.BASE_URL}/{page_id}"
                    token_params = {"fields": "access_token", "access_token": user_access_token}
                    token_resp = client.get(token_url, params=token_params)
                    token_resp.raise_for_status()

                    page_access_token = token_resp.json().get("access_token")
                    if not page_access_token:
                        print(f"Skipping page {page_id}: could not retrieve a valid page access_token.")
                        continue

                    # Now check for linked Instagram Business Account
                    ig_url = f"{MetaAuthService.BASE_URL}/{page_id}"
                    ig_params = {
                        "fields": "instagram_business_account",
                        "access_token": page_access_token,
                    }
                    ig_response = client.get(ig_url, params=ig_params)

                    if ig_response.status_code == 200:
                        ig_data = ig_response.json()
                        if "instagram_business_account" in ig_data:
                            ig_account_id = ig_data["instagram_business_account"]["id"]

                            # Save both tokens
                            credentials = {
                                "user_access_token": user_access_token,
                                "page_access_token": page_access_token,
                                "fb_page_id": page_id,
                                "ig_business_account_id": ig_account_id,
                            }

                            MetaAuthService._save_credentials_to_db(db, credentials)
                            print(
                                f"Stored credentials for Page {page_id} and IG account {ig_account_id}"
                            )
                            return

                print("Could not find any Facebook Page linked to an Instagram Business Account.")

        except httpx.HTTPStatusError as e:
            print(f"Error discovering assets: {e.response.text}")

