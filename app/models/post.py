from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
from .comment import PlatformType


class Post(Base):
    """Model for storing posts from social media platforms."""

    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(PlatformType, name="platformtype", create_type=False),
                      nullable=False, index=True)
    id_post_platform = Column(String(255), unique=True, index=True, nullable=False)
    text = Column(Text, nullable=False)
    media_type = Column(String)
    media_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    platform_created_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Post(id={self.id}, platform={self.platform}, platform_id={self.platform_id})>"
