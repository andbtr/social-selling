from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PlatformType(str, enum.Enum):
    """Enum for social media platforms."""
    META = "meta"
    X = "x"
    TRIPADVISOR = "tripadvisor"


class Comment(Base):
    """Model for storing comments from social media platforms."""
    
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(PlatformType), nullable=False, index=True)
    platform_id = Column(String(255), unique=True, index=True, nullable=False)
    author = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    post_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    platform_created_at = Column(DateTime(timezone=True), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional platform-specific data
    
    def __repr__(self):
        return f"<Comment(id={self.id}, platform={self.platform}, author={self.author})>"
