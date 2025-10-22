from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.post import PostCreate
from typing import Optional, List

class PostService:
    """Service for managing posts."""

    @staticmethod
    def create_post(db: Session, post: PostCreate) -> Post:
        """Create a new post."""
        db_post = Post(**post.model_dump())
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def get_post(db: Session, post_id: int) -> Optional[Post]:
        """Get a post by ID."""
        return db.query(Post).filter(Post.id == post_id).first()

    @staticmethod
    def get_post_by_platform_id(db: Session, platform_id: str) -> Optional[Post]:
        """Get a post by platform ID."""
        return db.query(Post).filter(Post.platform_id == platform_id).first()

    @staticmethod
    def get_posts(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        platform: Optional[str] = None
    ) -> List[Post]:
        """Get list of posts with optional filtering."""
        query = db.query(Post)
        if platform:
            query = query.filter(Post.platform == platform)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def count_posts(db: Session, platform: Optional[str] = None) -> int:
        """Count total posts."""
        query = db.query(Post)
        if platform:
            query = query.filter(Post.platform == platform)
        return query.count()