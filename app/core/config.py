from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = Field(default="sqlite:///./social_listening.db", env="DATABASE_URL")
    
    # Meta API
    meta_api_key: str = Field(default="", env="META_API_KEY")
    meta_api_secret: str = Field(default="", env="META_API_SECRET")
    fb_page_id: str = Field(default="", env="FB_PAGE_ID")
    meta_fb_access_token: str = Field(default="", env="META_FB_ACCESS_TOKEN")
    meta_ig_access_token: str = Field(default="", env="META_IG_ACCESS_TOKEN")
    instagram_business_account_id: str = Field(default="", env="INSTAGRAM_BUSINESS_ACCOUNT_ID")
    fb_access_token: str = Field(default="", env="META_FB_ACCESS_TOKEN")

    # X (Twitter) API
    x_api_key: str = Field(default="", env="X_API_KEY")
    x_api_secret: str = Field(default="", env="X_API_SECRET")
    x_bearer_token: str = Field(default="", env="X_BEARER_TOKEN")
    
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
