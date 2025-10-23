from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.comment import PlatformType


class CommentBase(BaseModel):
    """Base schema for Comment."""
    platform: PlatformType
    platform_id: str = Field(..., description="Unique identifier from the platform")
    author: Optional[str] = None
    content: str = Field(..., min_length=1, description="Comment content")
    post_url: Optional[str] = None
    platform_created_at: Optional[datetime] = None
    sentiment_analized: bool = False
    sentiment_analized_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None

class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    sentiment_analized: Optional[bool] = None  # Exclude or make optional if not set during creation
    sentiment_analized_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None


class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentList(BaseModel):
    """Schema for list of comments."""
    comments: list[CommentResponse]
    total: int