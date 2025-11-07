# app/api/social_posts.py
from datetime import datetime, timezone
from typing import Optional
import asyncio

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.post_publisher import publish_post
from app.services.post_service import PostService
from app.schemas.post import PostResponse

router = APIRouter(prefix="/api/social-selling", tags=["social-selling"])

@router.post("/posts", response_model=PostResponse)
async def create_post(
    platform: str = Form(...),          # "facebook" | "instagram"
    text: Optional[str] = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # ---- Normalización de entrada (minúsculas) ----
    platform_in = (platform or "").strip().lower()
    if platform_in not in ("facebook", "instagram"):
        raise HTTPException(status_code=400, detail="platform must be facebook | instagram")

    # ---- Publicación en Meta con timeout para evitar cuelgues ----
    try:
        platform_id, media_type, media_url, platform_created_at = await asyncio.wait_for(
            publish_post(db, platform_in, text, image),
            timeout=25.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Meta publish timed out")
    except Exception as e:
        # Propaga el error de Meta (para ver el detalle en el front)
        raise HTTPException(status_code=502, detail=str(e))

    # ---- Persistencia en BD (ENUM en MAYÚSCULAS) ----
    payload = {
        "platform": platform_in.upper(),          # tu enum en BD: FACEBOOK/INSTAGRAM
        "platform_id": platform_id,               # PostService debe mapear a id_post_platform
        "text": (text or ""),                     # NOT NULL en tu tabla
        "media_type": media_type,
        "media_url": media_url,
        "created_at": datetime.now(timezone.utc),
        "platform_created_at": platform_created_at,
    }

    db_post = PostService.create_post(db, payload)

    # ---- Mapeo explícito ORM -> Schema para evitar 500 ----
    # platform puede ser Enum('FACEBOOK') o string. Tomamos el valor.
    platform_value = getattr(db_post.platform, "value", db_post.platform)

    response = {
        "id": db_post.id,
        "platform": platform_value,               # "FACEBOOK" | "INSTAGRAM"
        "platform_id": getattr(db_post, "id_post_platform", None),
        "text": db_post.text,
        "media_type": db_post.media_type,
        "media_url": db_post.media_url,
        "created_at": db_post.created_at,
        "platform_created_at": db_post.platform_created_at,
    }

    return PostResponse.model_validate(response)
