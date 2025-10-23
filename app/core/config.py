from pydantic_settings import BaseSettings
from pydantic import Field
import json
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = Field(default="sqlite:///./social_listening.db", env="DATABASE_URL")

    # Meta API
    meta_api_key: str = Field(default="", env="META_API_KEY")
    meta_api_secret: str = Field(default="", env="META_API_SECRET")
    meta_app_id: str = Field(default="", env="META_APP_ID")
    meta_app_secret: str = Field(default="", env="META_APP_SECRET")
    meta_redirect_uri: str = Field(default="http://localhost:8000/auth/meta/callback", env="META_REDIRECT_URI")
    fb_page_id: str = Field(default="", env="FB_PAGE_ID")
    meta_fb_access_token: str = Field(default="", env="META_FB_ACCESS_TOKEN")
    meta_ig_access_token: str = Field(default="", env="META_IG_ACCESS_TOKEN")
    instagram_business_account_id: str = Field(default="", env="INSTAGRAM_BUSINESS_ACCOUNT_ID")
    fb_access_token: str = Field(default="", env="META_FB_ACCESS_TOKEN")

    # X (Twitter) API
    x_api_key: str = Field(default="", env="X_API_KEY")
    x_api_secret: str = Field(default="", env="X_API_SECRET")
    x_bearer_token: str = Field(default="", env="X_BEARER_TOKEN")
    x_access_token: str = Field(default="", env="X_ACCESS_TOKEN")
    x_access_token_secret: str = Field(default="", env="X_ACCESS_TOKEN_SECRET")

    # TripAdvisor API
    tripadvisor_api_key: str = Field(default="", env="TRIPADVISOR_API_KEY")

    # App Settings
    app_name: str = Field(default="Social Listening Platform", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def load_meta_credentials_from_storage() -> Optional[dict]:
    """
    Loads Meta credentials from storage.json if it exists.
    This is used to override environment variables with OAuth-generated credentials.
    """
    storage_path = Path(__file__).parent.parent.parent / "storage.json"
    if storage_path.exists():
        try:
            with open(storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading credentials from storage.json: {e}")
            return None
    return None


# Load credentials from storage.json if available (OAuth-generated)
_storage_credentials = load_meta_credentials_from_storage()
if _storage_credentials:
    # Override settings with OAuth-generated credentials
    if "user_access_token" in _storage_credentials:
        settings.meta_fb_access_token = _storage_credentials["user_access_token"]
    if "fb_page_id" in _storage_credentials:
        settings.fb_page_id = _storage_credentials["fb_page_id"]
    if "ig_business_account_id" in _storage_credentials:
        settings.instagram_business_account_id = _storage_credentials["ig_business_account_id"]
