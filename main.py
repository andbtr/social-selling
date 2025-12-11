from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api import (
    comments_router,
    ingestion_router,
    auth_router,
    lead_scoring_router,
    intention_router,
)
from app.api.social_selling import router as social_router
from app.api.crm import router as crm_router
from app.api.social_posts import router as posts_router

from app.services.intention_service import initialize_ensemble
import logging

logger = logging.getLogger(__name__)


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Social Listening Platform for ingesting and analyzing comments from Meta and TripAdvisor",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(comments_router)
app.include_router(ingestion_router)
app.include_router(lead_scoring_router)
app.include_router(auth_router)
app.include_router(social_router)
app.include_router(crm_router)
app.include_router(posts_router)
# app.include_router(intention_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
