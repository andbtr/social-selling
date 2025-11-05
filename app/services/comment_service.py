from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.schemas.comment import CommentCreate
from typing import Optional, List

from app.services.lead_scoring_service import LeadScoringService
from app.services.post_service import PostService
from app.services.sentiment_service import analize_sentiment
from app.services.intention_service import analyze_intent
from datetime import datetime, timezone


class CommentService:
    """Service for managing comments."""
    
    @staticmethod
    def create_comment(db: Session, comment) -> Comment:
        # Solo columnas reales del modelo
        allowed = {c.name for c in Comment.__table__.columns}
        data = comment.model_dump() if hasattr(comment, "model_dump") else dict(comment)
        filtered = {k: v for k, v in data.items() if k in allowed}

        db_comment = Comment(**filtered)
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)

        sentiment_label, sentiment_score = analize_sentiment(db_comment.content)
        intention_label, intention_score = analyze_intent(db_comment.content)
        db_comment.sentiment = sentiment_label
        db_comment.sentiment_confidence = round(sentiment_score, 3)
        db_comment.sentiment_analized = True
        db_comment.sentiment_analized_at = datetime.now(timezone.utc)
        db_comment.intention = intention_label
        db_comment.intention_confidence = round(intention_score, 3)
        db_comment.intention_analized = True
        db_comment.intention_analized_at = datetime.now(timezone.utc)
        print(db_comment.sentiment, db_comment.sentiment_confidence, db_comment.intention, db_comment.intention_confidence)
        db.commit()
        db.refresh(db_comment)

        # calcular y guardar lead score automáticamente
        try:
            LeadScoringService.compute_and_upsert(db, db_comment.id)
        except Exception as e:
            # loggear; no romper creación del comment
            print(f"[lead-scoring] error: {e}")

        return db_comment
    
    @staticmethod
    def get_comment(db: Session, comment_id: int) -> Optional[Comment]:
        """Get a comment by ID."""
        return db.query(Comment).filter(Comment.id == comment_id).first()
    
    @staticmethod
    def get_comment_by_id_comment_platform(db: Session, id_comment_platform: str) -> Optional[Comment]:
        """Get a comment by platform ID."""
        return db.query(Comment).filter(Comment.id_comment_platform == id_comment_platform).first()
    
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