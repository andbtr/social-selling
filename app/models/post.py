from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

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
