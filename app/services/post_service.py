from typing import Any, Dict, Union, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, String, func

from app.models.post import Post
from app.schemas.post import PostCreate

def _to_dict(data: Union[Dict[str, Any], PostCreate]) -> Dict[str, Any]:
    if hasattr(data, "model_dump"):   # Pydantic v2
        return data.model_dump()
    if hasattr(data, "dict"):         # Pydantic v1
        return data.dict()
    return dict(data)

class PostService:
    @staticmethod
    def create_post(db: Session, payload: Union[dict, PostCreate]) -> Post:
        data = _to_dict(payload)

        db_post = Post(
            platform=(data.get("platform") or "").strip().upper(),  # normaliza
            id_post_platform=data.get("platform_id"),
            text=data.get("text", "") or "",
            media_type=data.get("media_type"),
            media_url=data.get("media_url"),
            created_at=data.get("created_at"),
            platform_created_at=data.get("platform_created_at"),
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def get_post_by_platform_id(db: Session, platform_id: str) -> Optional[Post]:
        """
        Devuelve el Post por su id en la plataforma externa (columna id_post_platform).
        """
        return (
            db.query(Post)
            .filter(Post.id_post_platform == str(platform_id))
            .first()
        )

    @staticmethod
    def list_posts(
        db: Session,
        platform: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Post]:
        q = db.query(Post).order_by(Post.created_at.desc())
        if platform:
            # Si platform es ENUM en DB, evita ILIKE; usa igualdad normalizando
            q = q.filter(Post.platform == platform.upper()) 
        return q.offset(offset).limit(limit).all()

    @staticmethod
    def to_dict(p: Post) -> dict:
        return {
            "id": p.id,
            "platform": (p.platform or "").lower(),
            "platform_id": getattr(p, "id_post_platform", None),
            "text": p.text,
            "media_type": p.media_type,
            "media_url": p.media_url,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "platform_created_at": p.platform_created_at.isoformat() if p.platform_created_at else None,
        }
