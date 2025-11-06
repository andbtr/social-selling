from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, Numeric
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base
import enum

class CRMLeadStatus(str, enum.Enum):
    """Enum for CRM lead sync status."""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    UPDATED = "UPDATED"


class CRMLead(Base):
    """Model for tracking leads sent to external CRM."""
    
    __tablename__ = "crm_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    # Reference to LeadScore (optional - only for auto-response flow)
    lead_score_id = Column(Integer, ForeignKey("lead_scores.id", ondelete="CASCADE"), nullable=True, index=True)
    # Reference to Comment (optional - only for auto-response flow)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)

    # CRM tracking
    crm_lead_id = Column(String(255), nullable=True, index=True)  # ID returned by CRM
    crm_status = Column(SQLEnum(CRMLeadStatus), nullable=False, default=CRMLeadStatus.PENDING)
    
    # Lead details
    priority_level = Column(String(10), nullable=True)  # HOT | WARM | COLD
    lead_score = Column(Numeric(5,2), nullable=True)
    author = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False)  # facebook | instagram | tripadvisor
    post_url = Column(String(512), nullable=True)
    
    # Enriched lead data
    fullname = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    segment = Column(String(100), nullable=True)
    interest = Column(Text, nullable=True)
    instagram_id = Column(Integer, nullable=True)
    facebook_id = Column(Integer, nullable=True)
    tripadvisor_id = Column(Integer, nullable=True)

    # Sync tracking
    synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_error = Column(Text, nullable=True)
    last_sync_attempt = Column(DateTime(timezone=True), nullable=True)
    sync_attempts = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CRMLead(id={self.id}, priority_level={self.priority_level}, crm_status={self.crm_status})>"

