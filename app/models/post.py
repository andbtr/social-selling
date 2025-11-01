from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from .comment import platform_type_enum


class Post(Base):
    """Model for storing posts from social media platforms."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(platform_type_enum, nullable=False, index=True)
    platform_id = Column(String(255), unique=True, index=True, nullable=False)
    text = Column(Text, nullable=False)
    media_type = Column(String)
    media_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    platform_created_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Post(id={self.id}, platform={self.platform}, platform_id={self.platform_id})>"
