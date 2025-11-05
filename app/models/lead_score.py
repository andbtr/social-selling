from sqlalchemy import Column, Integer, BigInteger, Numeric, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class LeadScore(Base):
    __tablename__ = "lead_scores"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    score = Column(Numeric(5,2), nullable=False)
    priority_level = Column(String(10), nullable=False)   # HOT | WARM | COLD
    scoring_version = Column(Text, nullable=False, default="v1")
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)


    comment = relationship("Comment", back_populates="lead_score")

Index("idx_lead_scores_priority", LeadScore.priority_level, LeadScore.score.desc())
Index("idx_lead_scores_time", LeadScore.computed_at.desc())
