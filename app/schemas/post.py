from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # v2

class PostCreate(BaseModel):
    platform: Literal["facebook", "instagram"]
    text: Optional[str] = ""  # <- que nunca vaya None

class PostResponse(BaseModel):
    id: int
    # Opción A: usa el mismo casing que tu enum en BD
    platform: Literal["FACEBOOK", "INSTAGRAM"]  # <-- mayúsculas para que haga match
    platform_id: Optional[str] = None
    text: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    created_at: Optional[datetime] = None
    platform_created_at: Optional[datetime] = None

    # Muy importante para enums SQLAlchemy: devolver el valor, no el objeto Enum
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
