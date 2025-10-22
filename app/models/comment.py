from datetime import datetime
from tokenize import Double

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PlatformType(str, enum.Enum):
    """Enum for social media platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TRIPADVISOR = "tripadvisor"


class Comment(Base):
    """Model for storing comments from social media platforms."""
    
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(PlatformType), nullable=False, index=True)
    platform_id = Column(String(255), unique=True, index=True, nullable=False)
    id_comment_platform = Column(Integer, nullable=True)
    author = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    post_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    platform_created_at = Column(DateTime(timezone=True), nullable=True)
    sentiment_analized = Column(Boolean, default=False)
    sentiment_analized_at = Column(DateTime(timezone=True), nullable=True)
    sentiment = Column(String(5), nullable=True)
    sentiment_confidence = Column(Float, nullable=True)
    intention_analized = Column(Boolean, default=False)
    intention_analized_at = Column(DateTime(timezone=True), nullable=True)
    intention = Column(String(5), nullable=True)
    intention_confidence = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Comment(id={self.id}, platform={self.platform}, author={self.author})>"

