# app/services/post_publisher.py
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import httpx
from fastapi import UploadFile

from app.core.config import settings

Graph = lambda path: f"https://graph.facebook.com/{settings.meta_graph_version}/{path}"

# ---------------------------
# Utilidades
# ---------------------------
def utcnow():
    return datetime.now(timezone.utc)

def ensure_public_url(local_path: str) -> str:
    """
    Convierte un path relativo (p.ej. /static/uploads/x.jpg) a URL pública usando PUBLIC_BASE_URL.
    """
    base = (settings.public_base_url or "").rstrip("/")
    rel = local_path if local_path.startswith("/") else f"/{local_path}"
    return f"{base}{rel}"

# ---------------------------
# Guardar imagen local (dev)
# ---------------------------
async def save_local_and_get_urls(image: UploadFile) -> Tuple[str, str]:
    uploads = Path("static/uploads")
    uploads.mkdir(parents=True, exist_ok=True)

    ext = Path(image.filename or "").suffix.lower() or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    dest = uploads / name

    with dest.open("wb") as f:
        f.write(await image.read())

    local_path = f"/static/uploads/{name}"
    public_url = ensure_public_url(local_path)
    return local_path, public_url

# ---------------------------
# Facebook Page
# ---------------------------
async def publish_facebook(text: str | None, image: UploadFile | None):
    """
    Publica en una Página de Facebook.
    - Solo texto -> POST /{page-id}/feed
    - Con imagen  -> 1) POST /{page-id}/photos?published=false
                      2) POST /{page-id}/feed con attached_media
    Devuelve: (platform_id, media_type, media_url, platform_created_at)
    """
    page_id = settings.fb_page_id
    page_token = settings.fb_page_token
    if not page_id or not page_token:
        raise RuntimeError("Falta FB_PAGE_ID o PAGE ACCESS TOKEN.")

    async with httpx.AsyncClient(timeout=60) as client:
        # Solo texto
        if not image:
            r = await client.post(
                Graph(f"{page_id}/feed"),
                data={"message": text or "", "access_token": page_token},
            )
            r.raise_for_status()
            post_id = r.json().get("id")
            # permalink
            p = await client.get(Graph(f"{post_id}"), params={"fields": "permalink_url", "access_token": page_token})
            media_url = p.json().get("permalink_url")
            return post_id, None, media_url, utcnow()

        # Con imagen: subir foto sin publicar
        # Puedes subir binario directo o por url pública; aquí usamos binario.
        files = {"source": (image.filename or "image.jpg", await image.read())}
        data = {"published": "false", "access_token": page_token}
        r = await client.post(Graph(f"{page_id}/photos"), data=data, files=files)
        r.raise_for_status()
        media_fbid = r.json().get("id")
        if not media_fbid:
            raise RuntimeError("No se obtuvo media_fbid de Facebook.")

        # Publicar el post adjuntando la media
        attached_media = [{"media_fbid": media_fbid}]
        r2 = await client.post(
            Graph(f"{page_id}/feed"),
            data={
                "message": text or "",
                "attached_media[0]": str(attached_media[0]).replace("'", '"'),
                "access_token": page_token,
            },
        )
        r2.raise_for_status()
        post_id = r2.json().get("id")

        p = await client.get(Graph(f"{post_id}"), params={"fields": "permalink_url", "access_token": page_token})
        media_url = p.json().get("permalink_url")

        return post_id, "image", media_url, utcnow()

# ---------------------------
# Instagram Business
# ---------------------------
async def publish_instagram(text: str | None, image: UploadFile | None):
    """
    Publica en Instagram Business.
    Requiere URL pública de la imagen.
      1) POST /{ig-user-id}/media (image_url, caption) -> id (creation_id)
      2) POST /{ig-user-id}/media_publish (creation_id) -> id (post_id)
      3) GET  /{post_id}?fields=permalink -> permalink
    Devuelve: (platform_id, media_type, media_url, platform_created_at)
    """
    ig_user_id = settings.instagram_business_account_id
    ig_token = settings.meta_ig_access_token
    if not ig_user_id or not ig_token:
        raise RuntimeError("Falta INSTAGRAM_BUSINESS_ACCOUNT_ID o META_IG_ACCESS_TOKEN.")

    # Si recibimos archivo, guardamos local y usamos PUBLIC_BASE_URL + /static/uploads/...
    image_url: Optional[str] = None
    if image:
        if not settings.public_base_url:
            raise RuntimeError("PUBLIC_BASE_URL es obligatorio para publicar una imagen en Instagram.")
        _, public_url = await save_local_and_get_urls(image)
        image_url = public_url

    async with httpx.AsyncClient(timeout=60) as client:
        # Crear media
        media_params = {"access_token": ig_token}
        if image_url:
            media_params["image_url"] = image_url
        if text:
            media_params["caption"] = text

        r = await client.post(Graph(f"{ig_user_id}/media"), data=media_params)
        r.raise_for_status()
        creation_id = r.json().get("id")
        if not creation_id:
            raise RuntimeError("No se obtuvo creation_id de Instagram.")

        # Publicar media
        r2 = await client.post(
            Graph(f"{ig_user_id}/media_publish"),
            data={"creation_id": creation_id, "access_token": ig_token},
        )
        r2.raise_for_status()
        post_id = r2.json().get("id")

        # Obtener permalink
        r3 = await client.get(Graph(f"{post_id}"), params={"fields": "permalink", "access_token": ig_token})
        permalink = r3.json().get("permalink")

        return post_id, ("image" if image_url else None), permalink, utcnow()

# ---------------------------
# Orquestador público
# ---------------------------
async def publish_to_meta(platform: str, text: str | None, image: UploadFile | None):
    platform = (platform or "").lower()
    if platform == "facebook":
        return await publish_facebook(text, image)
    if platform == "instagram":
        return await publish_instagram(text, image)
    raise RuntimeError("Plataforma no soportada: usa facebook | instagram")

# ---------------------------
# Entry para el router
# ---------------------------
async def publish_post(platform: str, text: str | None, image: UploadFile | None):
    """
    Decide según PUBLISH_MODE:
      - META  -> usa Graph API (facebook/instagram)
      - LOCAL -> guarda imagen y devuelve URL local (sin publicar en redes)
    """
    mode = (settings.publish_mode or "META").upper()
    if mode == "LOCAL":
        if image:
            _, public_url = await save_local_and_get_urls(image)
            return None, "image", public_url, utcnow()
        return None, None, None, utcnow()
    # META
    return await publish_to_meta(platform, text, image)
