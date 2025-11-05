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
    meta_app_id: str = Field(default="", env="META_APP_ID")
    meta_app_secret: str = Field(default="", env="META_APP_SECRET")
    meta_redirect_uri: str = Field(default="http://localhost:8000/auth/meta/callback", env="META_REDIRECT_URI")

    # TripAdvisor API
    tripadvisor_api_key: str = Field(default="", env="TRIPADVISOR_API_KEY")

    # CRM Integration
    crm_api_url: str = Field(default="", env="CRM_API_URL")

    # App Settings
    app_name: str = Field(default="Social Listening Platform", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")

    encryption_key: str = Field(..., env="ENCRYPTION_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()