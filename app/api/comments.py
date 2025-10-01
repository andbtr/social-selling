from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.comment import CommentCreate, CommentResponse, CommentList
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentResponse, status_code=201)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db)
):
    """Create a new comment."""
    # Check if comment with same platform_id already exists
    existing = CommentService.get_comment_by_platform_id(db, comment.platform_id)
    if existing:
        raise HTTPException(status_code=400, detail="Comment with this platform_id already exists")
    
    return CommentService.create_comment(db, comment)


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Get a comment by ID."""
    comment = CommentService.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get("/", response_model=CommentList)
def list_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List comments with optional filtering."""
    comments = CommentService.get_comments(db, skip=skip, limit=limit, platform=platform)
    total = CommentService.count_comments(db, platform=platform)
    return CommentList(comments=comments, total=total)
