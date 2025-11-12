# app/schemas/post.py
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel
from pydantic import ConfigDict  # Pydantic v2

# -------- Input (crear/ingestar) --------
class PostCreate(BaseModel):
    platform: Literal["facebook", "instagram"]              # usa minúsculas
    platform_id: str                                        # id en la plataforma (IG media id / FB post id)
    text: str = ""                                          # no None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    created_at: Optional[datetime] = None
    platform_created_at: Optional[datetime] = None

    # Ignora silenciosamente cualquier campo extra (p.ej., si el transform trae algo más)
    model_config = ConfigDict(extra="ignore")

# -------- Output (para el front) --------
class PostResponse(BaseModel):
    id: int
    platform: Literal["facebook", "instagram"]              # minúsculas para ser consistente con el front
    platform_id: Optional[str] = None
    text: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    created_at: Optional[datetime] = None
    platform_created_at: Optional[datetime] = None

    # Permite mapear desde ORM y usar valores crudos (si en el modelo es Enum)
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
