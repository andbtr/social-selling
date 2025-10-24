"""API routes."""
from app.api.comments import router as comments_router
from app.api.ingestion import router as ingestion_router
from app.api.lead_scoring import router as lead_scoring_router

__all__ = ["comments_router", "ingestion_router", "lead_scoring_router"]
