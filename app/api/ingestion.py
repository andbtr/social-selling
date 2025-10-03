from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ingestion_service import (
    MetaIngestionService,
    XIngestionService,
    TripAdvisorIngestionService
)
from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate, CommentResponse
from typing import List

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


@router.post("/meta/{post_id}", response_model=List[CommentResponse])
async def ingest_meta_comments(
    post_id: str,
    db: Session = Depends(get_db)
):
    """Ingest comments from a Meta (Facebook/Instagram) post."""
    try:
        # Fetch comments from Meta API
        comments_data = await MetaIngestionService.fetch_comments(post_id)
        
        created_comments = []
        for comment_data in comments_data:
            # Transform to internal format
            comment_dict = MetaIngestionService.transform_to_comment(comment_data)
            
            # Check if already exists
            existing = CommentService.get_comment_by_platform_id(
                db, comment_dict["platform_id"]
            )
            if not existing:
                # Create comment
                comment = CommentCreate(**comment_dict)
                db_comment = CommentService.create_comment(db, comment)
                created_comments.append(db_comment)
        
        return created_comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Meta comments: {str(e)}")


@router.post("/x/{tweet_id}", response_model=List[CommentResponse])
async def ingest_x_replies(
    tweet_id: str,
    db: Session = Depends(get_db)
):
    """Ingest replies from an X (Twitter) tweet."""
    try:
        # Fetch replies from X API
        replies_data = await XIngestionService.fetch_replies(tweet_id)
        
        created_comments = []
        for reply_data in replies_data:
            # Transform to internal format
            comment_dict = XIngestionService.transform_to_comment(reply_data)
            
            # Check if already exists
            existing = CommentService.get_comment_by_platform_id(
                db, comment_dict["platform_id"]
            )
            if not existing:
                # Create comment
                comment = CommentCreate(**comment_dict)
                db_comment = CommentService.create_comment(db, comment)
                created_comments.append(db_comment)
        
        return created_comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting X replies: {str(e)}")


@router.post("/tripadvisor/{location_id}", response_model=List[CommentResponse])
async def ingest_tripadvisor_reviews(
    location_id: str,
    language: str = Query("en", pattern="^(en|es)$", description="Idioma de reviews: en|es"),
    db: Session = Depends(get_db),
):
    """Ingest reviews from a TripAdvisor location."""
    try:
        reviews_data = await TripAdvisorIngestionService.fetch_reviews(location_id, language=language)

        created_comments = []
        for review_data in reviews_data:
            comment_dict = TripAdvisorIngestionService.transform_to_comment(review_data)

            # si no hay ID, no podemos deduplicar
            if not comment_dict.get("platform_id"):
                continue

            existing = CommentService.get_comment_by_platform_id(
                db, comment_dict["platform_id"]
            )
            if not existing:
                comment = CommentCreate(**comment_dict)
                db_comment = CommentService.create_comment(db, comment)
                created_comments.append(db_comment)

        return created_comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting TripAdvisor reviews: {str(e)}")