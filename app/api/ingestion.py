
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import PostCreate
from app.services.ingestion_service import (
    InstagramIngestionService,
    TripAdvisorIngestionService,
    FacebookIngestionService,
    send_auto_reply_to_comment
)
from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate, CommentResponse
from typing import List
from app.services.crm_service import CrmService
from app.core.config import settings
from app.services.post_service import PostService
from datetime import datetime

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])

@router.post("/instagram/posts")
async def ingest_instagram_posts(db: Session = Depends(get_db)):
    try:
        # Fetch posts from Meta IG API
        posts_data = await InstagramIngestionService.fetch_instagram_posts(db)

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
        posts = PostService.get_posts_by_platform(db, "instagram")
        created_comments = []

        for post in posts:
            post_id = post.id_post_platform
            post_permalink = post.media_url
            # Fetch comments for each post
            comments_data = await InstagramIngestionService.fetch_comments(db, post_id, post_permalink)
            for comment_data in comments_data:
                # Transform to internal format
                comment_dict = InstagramIngestionService.transform_to_comment(comment_data)
                # Check if already exists
                existing = CommentService.get_comment_by_id_comment_platform(
                    db, comment_dict["id_comment_platform"]
                )
                if not existing:
                    # 1. Create comment (sentiment, intention, lead_score calculated automatically)
                    comment = CommentCreate(**comment_dict)
                    db_comment = CommentService.create_comment(db, comment)

                    priority = db_comment.lead_score.priority_level
                    if priority == "HOT" or priority == "WARM":
                        crm_service = CrmService(crm_api_base_url=settings.crm_api_url)
                        crm_lead = crm_service.create_crm_lead_from_comment(db, db_comment, "INSTAGRAM")

                    # 3. Send automatic reply based on lead score
                    await send_auto_reply_to_comment(db, db_comment, "INSTAGRAM")

                    created_comments.append(db_comment)

        return created_comments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Instagram comments: {str(e)}")


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

            raw_id = comment_dict.get("id_comment_platform")
            # si no hay ID, no podemos deduplicar
            if not raw_id:
                continue

            comment_id = str(raw_id)
            comment_dict["id_comment_platform"] = comment_id

            existing = CommentService.get_comment_by_id_comment_platform(db, comment_id)

            if not existing:
                # Create comment
                comment = CommentCreate(**comment_dict)
                db_comment = CommentService.create_comment(db, comment)
                created_comments.append(db_comment)

        return created_comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting TripAdvisor reviews: {str(e)}")

@router.post("/facebook/posts")
async def ingest_facebook_posts(db: Session = Depends(get_db)):
    """
    Trae posts de la página de Facebook (config en .env) y los guarda.
    """
    try:
        # 1) Traer posts desde Graph API (servicio FB)
        posts_data = await FacebookIngestionService.fetch_posts(db)

        created_posts = []
        for p in posts_data:
            post_dict = {
                "platform": "facebook",
                "platform_id": p["id"],
                "text": p.get("message", "") or "",
                "media_type": "post",
                "media_url": p.get("permalink_url"),
                "platform_created_at": p.get("created_time"),
                "created_at": datetime.utcnow()
            }

            # 2) Evitar duplicados por platform_id (igual que haces en IG)
            existing = PostService.get_post_by_platform_id(db, post_dict["platform_id"])
            if not existing:
                post = PostCreate(**post_dict)
                db_post = PostService.create_post(db, post)
                created_posts.append(db_post)

        return created_posts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Facebook posts: {str(e)}")


@router.post("/facebook/comments", response_model=List[CommentResponse])
async def ingest_facebook_comments(db: Session = Depends(get_db)):
    """
    Trae comentarios de todos los posts recientes de la página y los guarda.
    FB solo permite comentarios post-por-post.
    """
    try:
        created_comments = []

        # Get posts from DB
        posts_data = PostService.get_posts_by_platform(db, "facebook")

        for p in posts_data:
            post_id = p.id_post_platform
            comments_data = await FacebookIngestionService.fetch_comments(db, post_id)

            for c in comments_data:
                comment_dict = {
                    "platform": "FACEBOOK",
                    "id_comment_platform": c["id"],
                    "author": (c.get("from") or {}).get("name"),
                    "content": c.get("message", "") or "",
                    "post_url": p.media_url,
                    "platform_created_at": c.get("created_time"),
                }

                existing = CommentService.get_comment_by_id_comment_platform(
                    db, comment_dict["id_comment_platform"]
                )
                if not existing:
                    # 1. Create comment (sentiment, intention, lead_score calculated automatically)
                    comment = CommentCreate(**comment_dict)
                    db_comment = CommentService.create_comment(db, comment)

                    priority = db_comment.lead_score.priority_level
                    if priority == "HOT" or priority == "WARM":
                        crm_service = CrmService(crm_api_base_url=settings.crm_api_url)
                        crm_lead = crm_service.create_crm_lead_from_comment(db, db_comment, "FACEBOOK")

                    # 3. Send automatic reply based on lead score
                    await send_auto_reply_to_comment(db, db_comment, "FACEBOOK")

                    created_comments.append(db_comment)

        return created_comments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Facebook comments: {str(e)}")


@router.post("/facebook/comments/{post_platform_id}", response_model=List[CommentResponse])
async def ingest_facebook_comments_for_post(
    post_platform_id: str,
    db: Session = Depends(get_db)
):
    """
    Trae y guarda comentarios de un post específico (por su ID de plataforma).
    """
    try:
        created_comments = []

        comments_data = await FacebookIngestionService.fetch_comments(db, post_platform_id)
        # Si quieres, intenta obtener el permalink del post llamando a /{id}?fields=permalink_url
        post_permalink = None

        for c in comments_data:
            comment_dict = {
                "platform": "FACEBOOK",
                "id_comment_platform": c["id"],
                "author": (c.get("from") or {}).get("name"),
                "content": c.get("message", "") or "",
                "post_url": post_permalink,
                "platform_created_at": c.get("created_time"),
            }

            existing = CommentService.get_comment_by_id_comment_platform(
                db, comment_dict["id_comment_platform"]
            )
            if not existing:
                # Create comment (sentiment, intention, lead_score calculated automatically)
                comment = CommentCreate(**comment_dict)
                db_comment = CommentService.create_comment(db, comment)

                # Send automatic reply based on lead score
                await send_auto_reply_to_comment(db, db_comment, "FACEBOOK")

                created_comments.append(db_comment)

        return created_comments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Facebook comments for post: {str(e)}")
