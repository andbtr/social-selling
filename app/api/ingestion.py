from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import PostCreate
from app.services.ingestion_service import (
    InstagramIngestionService,
    MetaIngestionService,
    XIngestionService,
    TripAdvisorIngestionService
)
from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate, CommentResponse
from typing import List

from app.services.post_service import PostService

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


@router.post("/instagram/posts")
async def ingest_instagram_posts(db: Session = Depends(get_db)):
    try:
        # Fetch posts from Meta IG API
        posts_data = await InstagramIngestionService.fetch_instagram_posts()

        created_posts = []
        for post_data in posts_data:
            # Transform to internal format
            post_dict = InstagramIngestionService.transform_to_post(post_data)

            # Check if already exists
            existing = PostService.get_post_by_platform_id(
                db, post_dict["platform_id"]
            )
            if not existing:
                # Create post
                post = PostCreate(**post_dict)
                db_post = PostService.create_post(db, post)
                created_posts.append(db_post)

        return created_posts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Meta posts: {str(e)}")

@router.post("/instagram/comments", response_model=List[CommentResponse])
async def ingest_instagram_comments(db: Session = Depends(get_db)):
    try:
        # Fetch all posts
        posts = await InstagramIngestionService.fetch_instagram_posts()
        created_comments = []

        for post in posts:
            post_id = post["id"]
            # Fetch comments for each post
            comments_data = await InstagramIngestionService.fetch_comments(post_id)
            for comment_data in comments_data:
                # Transform to internal format
                comment_dict = InstagramIngestionService.transform_to_comment(comment_data)
                # Check if already exists
                existing = CommentService.get_comment_by_platform_id(
                    db, comment_dict["platform_id"]
                )
                if not existing:
                    comment = CommentCreate(**comment_dict)
                    db_comment = CommentService.create_comment(db, comment)
                    created_comments.append(db_comment)

        return created_comments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Instagram comments: {str(e)}")


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
    db: Session = Depends(get_db)
):
    """Ingest reviews from a TripAdvisor location."""
    try:
        # Fetch reviews from TripAdvisor API
        reviews_data = await TripAdvisorIngestionService.fetch_reviews(location_id)
        
        created_comments = []
        for review_data in reviews_data:
            # Transform to internal format
            comment_dict = TripAdvisorIngestionService.transform_to_comment(review_data)
            
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
        raise HTTPException(status_code=500, detail=f"Error ingesting TripAdvisor reviews: {str(e)}")
