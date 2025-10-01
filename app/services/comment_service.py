from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.schemas.comment import CommentCreate
from typing import Optional, List


class CommentService:
    """Service for managing comments."""
    
    @staticmethod
    def create_comment(db: Session, comment: CommentCreate) -> Comment:
        """Create a new comment."""
        db_comment = Comment(**comment.model_dump())
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment
    
    @staticmethod
    def get_comment(db: Session, comment_id: int) -> Optional[Comment]:
        """Get a comment by ID."""
        return db.query(Comment).filter(Comment.id == comment_id).first()
    
    @staticmethod
    def get_comment_by_platform_id(db: Session, platform_id: str) -> Optional[Comment]:
        """Get a comment by platform ID."""
        return db.query(Comment).filter(Comment.platform_id == platform_id).first()
    
    @staticmethod
    def get_comments(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        platform: Optional[str] = None
    ) -> List[Comment]:
        """Get list of comments with optional filtering."""
        query = db.query(Comment)
        if platform:
            query = query.filter(Comment.platform == platform)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def count_comments(db: Session, platform: Optional[str] = None) -> int:
        """Count total comments."""
        query = db.query(Comment)
        if platform:
            query = query.filter(Comment.platform == platform)
        return query.count()
