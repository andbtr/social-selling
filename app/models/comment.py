from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class PlatformType(str, enum.Enum):
    """Enum for social media platforms."""
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    TRIPADVISOR = "TRIPADVISOR"

class Comment(Base):
    """Model for storing comments from social media platforms."""
    
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(
        SQLEnum(PlatformType, name="platformtype", create_type=False), 
        nullable=False, 
        index=True
    )
    id_comment_platform = Column(String(255), unique=True, index=True, nullable=False)
    author = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    post_url = Column(String(2048), nullable=True)
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

    lead_score = relationship("LeadScore", back_populates="comment", uselist=False, cascade="all, delete-orphan")

    keywords = relationship(
        "CommentKeyword",
        back_populates="comment",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, platform={self.platform}, author={self.author})>"
