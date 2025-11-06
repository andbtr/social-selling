from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl
import json
from pathlib import Path
from typing import Optional, Literal


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
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    debug: bool = Field(default=True, env="DEBUG")

    encryption_key: str = Field(..., env="ENCRYPTION_KEY")

    # API Key para endpoints del dashboard (opcional - si está vacío, no se valida)
    api_key: str = Field(default="", env="API_KEY")

    # ---------- NUEVO: Publicación / Graph API ----------
    # Modo de publicación (META = Graph API; LOCAL = guarda archivo y devuelve /static/uploads/...)
    publish_mode: Literal["META", "LOCAL"] = Field(default="META", env="PUBLISH_MODE")

    # Requerido por Instagram si sirves imágenes tú mismo (URL pública accesible)
    public_base_url: Optional[AnyUrl] = Field(default=None, env="PUBLIC_BASE_URL")

    # Versión de Graph API
    meta_graph_version: str = Field(default="v20.0", env="META_GRAPH_VERSION")

    # --- helper para tomar siempre el mejor token ---
    @property
    def fb_page_token(self) -> Optional[str]:
        # Prefiere token de PÁGINA; si no hay, usa el que ya tienes
        return self.meta_fb_page_access_token or self.meta_fb_access_token or None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()