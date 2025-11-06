from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from app.core.database import Base

Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    id_post_platform = Column(String(255), nullable=True)  # <- nombre real en BD
    text = Column(Text, nullable=False, default="")
    media_type = Column(String(50), nullable=True)
    media_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True))
    platform_created_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Post(id={self.id}, platform={self.platform}, platform_id={self.platform_id})>"
