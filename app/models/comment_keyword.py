from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CommentKeyword(Base):
    __tablename__ = "comment_keywords"

    id = Column(Integer, primary_key=True, index=True)
    
    comment_id = Column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # palabra clave extraída por el LLM
    keyword = Column(String(128), nullable=False, index=True)

    # cuántas veces aparece la palabra en ese comentario (opcional pero útil)
    frequency = Column(Integer, nullable=False, default=1)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    comment = relationship("Comment", back_populates="keywords")