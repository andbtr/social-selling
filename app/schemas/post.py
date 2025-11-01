from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.comment import PlatformType

class PostBase(BaseModel):
    platform: PlatformType
    platform_id: str
    text: str
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    platform_created_at: Optional[datetime] = None

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
