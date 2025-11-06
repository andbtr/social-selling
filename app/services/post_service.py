from typing import Any, Dict, Union
from sqlalchemy.orm import Session
from sqlalchemy import inspect
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
    def create_post(db, payload: dict):
        # asegurar compatibilidad con tu tabla (usa id_post_platform)
        db_post = Post(
            platform=payload.get("platform"),
            id_post_platform=payload.get("platform_id"),
            text=payload.get("text", ""),
            media_type=payload.get("media_type"),
            media_url=payload.get("media_url"),
            created_at=payload.get("created_at"),
            platform_created_at=payload.get("platform_created_at"),
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
