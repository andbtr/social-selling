from sqlalchemy import Column, Integer, Boolean, Numeric, Text, DateTime
from datetime import datetime
from app.core.database import Base

class LeadThreshold(Base):
    __tablename__ = "lead_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    scoring_version = Column(Text, nullable=False, default="v1")
    alpha = Column(Numeric(3,2), nullable=False, default=0.70)         # peso intención
    beta  = Column(Numeric(3,2), nullable=False, default=0.30)         # peso sentimiento
    fkw_min = Column(Numeric(3,2), nullable=False, default=0.60)       # piso F_kw
    fkw_max = Column(Numeric(3,2), nullable=False, default=1.60)       # techo F_kw
    hot_min = Column(Numeric(5,2), nullable=False, default=80.00)
    warm_min = Column(Numeric(5,2), nullable=False, default=60.00)
    min_intent_for_hot = Column(Numeric(3,2), nullable=False, default=0.50)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
