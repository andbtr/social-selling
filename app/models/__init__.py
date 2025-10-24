"""Database models."""
from app.models.comment import Comment, PlatformType
from app.models.lead_score import LeadScore
from app.models.lead_threshold import LeadThreshold

__all__ = ["Comment", "PlatformType", "LeadScore", "LeadThreshold"]
