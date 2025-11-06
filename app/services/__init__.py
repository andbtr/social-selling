"""Services for data ingestion and processing."""
from app.services.comment_service import CommentService
from app.services.ingestion_service import (
    InstagramIngestionService,
    FacebookIngestionService,
    TripAdvisorIngestionService
)

from importlib import import_module
from typing import TYPE_CHECKING

__all__ = [
    "CommentService",
    "InstagramIngestionService",
    "FacebookIngestionService",
    "TripAdvisorIngestionService"
]

# Durante type checking sí importamos, para que el IDE/autocompletado funcione.
if TYPE_CHECKING:
    from .post_service import PostService as _PostService
    from .comment_service import CommentService as _CommentService

def __getattr__(name: str):
    # Se ejecuta SOLO cuando alguien accede a ese atributo.
    if name == "PostService":
        return import_module(".post_service", __name__).PostService
    if name == "CommentService":
        return import_module(".comment_service", __name__).CommentService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")