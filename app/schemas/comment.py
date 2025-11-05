from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.comment import PlatformType


class CommentBase(BaseModel):
    """Base schema for Comment."""
    platform: PlatformType
    id_comment_platform: str = Field(..., description="Unique identifier from the platform")
    author: Optional[str] = None
    content: str = Field(..., min_length=1, description="Comment content")
    post_url: Optional[str] = None
    platform_created_at: Optional[datetime] = None
    sentiment_analized: bool = False
    sentiment_analized_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    intention_analized: bool = False
    intention_analized_at: Optional[datetime] = None
    intention: Optional[str] = None
    intention_confidence: Optional[float] = None

class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    sentiment_analized: Optional[bool] = None  # Exclude or make optional if not set during creation
    sentiment_analized_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    intention_analized: bool = False
    intention_analized_at: Optional[datetime] = None
    intention: Optional[str] = None
    intention_confidence: Optional[float] = None


class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CommentList(BaseModel):
    """Schema for list of comments."""
    comments: list[CommentResponse]
    total: int