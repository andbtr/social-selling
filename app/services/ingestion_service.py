import httpx
from typing import List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from datetime import datetime, timezone
import json
import asyncio


from app.services.meta_auth_service import MetaAuthService

def _get_meta_credentials(db: Session) -> Dict[str, Any]:
    """Helper to fetch Meta credentials from the database via MetaAuthService."""
    credentials = MetaAuthService.get_credentials_from_db(db)
    if not credentials or not credentials.get("user_access_token"):
        raise HTTPException(
            status_code=401,
            detail="Meta credentials not found or invalid. Please authenticate via /auth/meta/login.",
        )
    return credentials


class InstagramIngestionService:
    BASE_URL = "https://graph.facebook.com/v23.0"

    @staticmethod
    async def fetch_instagram_posts(db: Session):
        """Fetches posts from the configured Instagram Business Account."""
        credentials = _get_meta_credentials(db)
        ig_account_id = credentials.get("ig_business_account_id")
        access_token = credentials.get("user_access_token")

        if not ig_account_id:
            raise HTTPException(status_code=404, detail="Instagram Business Account ID not found in credentials.")

        async with httpx.AsyncClient() as client:
            url = f"{InstagramIngestionService.BASE_URL}/{ig_account_id}/media"
            params = {
                "access_token": access_token,
                "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink"
            }
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json().get("data", []) or []

    @staticmethod
    async def fetch_likes(db: Session, media_id: str) -> Dict[str, int]:
        """Devuelve el número de likes (like_count) de un media de Instagram."""
        credentials = _get_meta_credentials(db)
        access_token = credentials.get("user_access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing Meta access token")

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=10.0)) as client:
            r = await client.get(
                f"{InstagramIngestionService.BASE_URL}/{media_id}",
                params={"access_token": access_token, "fields": "like_count"},
            )
            r.raise_for_status()
            data = r.json()
            return {"likes": int(data.get("like_count", 0))}

    @staticmethod
    def _parse_iso(ts: str | None):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None

    @staticmethod
    def transform_to_post(post_data: dict) -> dict:
        """Transform Instagram post data to internal format."""
        return {
            "platform": "INSTAGRAM",
            "id_comment_platform": post_data.get("id"),
            "text": post_data.get("caption", ""),
            "media_type": post_data.get("media_type"),
            "media_url": post_data.get("media_url"),
            "platform_created_at": post_data.get("timestamp"),
            "post_url": post_data.get("permalink"),
            "extra_data": json.dumps(post_data)
        }

    @staticmethod
    async def fetch_comments(db: Session, post_id: str, post_permalink: str = None):
        """Fetches comments for a specific Instagram media ID."""
        credentials = _get_meta_credentials(db)
        access_token = credentials.get("user_access_token")

        async with httpx.AsyncClient() as client:
            url = f"{InstagramIngestionService.BASE_URL}/{post_id}/comments"
            params = {
                "access_token": access_token,
                "fields": "id,text,username,timestamp,permalink"
            }
            r = await client.get(url, params=params)
            comments = r.json().get("data", [])

            # Add post_permalink to each comment for reference
            for comment in comments:
                comment["_post_permalink"] = post_permalink

            return comments

    @staticmethod
    def transform_to_comment(comment_data: dict) -> dict:
        """Transform Instagram comment data to internal format."""
        # Use comment's permalink if available, otherwise use post permalink
        post_url = comment_data.get("permalink") or comment_data.get("_post_permalink")

        return {
            "platform": "INSTAGRAM",
            "id_comment_platform": comment_data.get("id"),
            "author": comment_data.get("username"),
            "content": comment_data.get("text", ""),
            "post_url": post_url,
            "platform_created_at": comment_data.get("timestamp"),
            "extra_data": json.dumps({k: v for k, v in comment_data.items() if not k.startswith("_")})
        }

class TripAdvisorIngestionService:
    """Service for ingesting data from TripAdvisor API (Content API v1)."""

    # Content API base
    BASE_URL = "https://api.content.tripadvisor.com/api/v1"

    @staticmethod
    async def fetch_reviews(location_id: str, language: str = "en") -> List[Dict[str, Any]]:

        api_key = settings.tripadvisor_api_key
        if not api_key:
            raise RuntimeError("TRIPADVISOR_API_KEY is not set")

        url = f"{TripAdvisorIngestionService.BASE_URL}/location/{location_id}/reviews"
        params = {
            "key": api_key,
            "language": language or "en",
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "social-listening/1.0",
        }

        timeout = httpx.Timeout(15.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, params=params, headers=headers)

            # 404: location no existe → retorna vacío en lugar de romper
            if resp.status_code == 404:
                return []

            if resp.is_error:
                raise RuntimeError(f"TripAdvisor API error {resp.status_code}: {resp.text}")

            data = resp.json()
            # La Content API suele devolver {"data": [ ...reviews... ]}
            reviews = data.get("data") or data.get("reviews") or []
            if not isinstance(reviews, list):
                reviews = []
            return reviews

    @staticmethod
    def transform_to_comment(review_data: Dict[str, Any]) -> Dict[str, Any]:
        # id TA: numérico (lo guardamos también como string namespaced en platform_id)
        raw_id = review_data.get("id")
        id_comment_platform = int(raw_id) if isinstance(raw_id, int) or str(raw_id).isdigit() else None
        # autor viene en user.username
        user = review_data.get("user") or {}
        author = user.get("username") or "Unknown"

        # texto/título
        content = (review_data.get("text") or review_data.get("title") or "").strip()

        # rating (puede no venir)
        rating = review_data.get("rating")

        # url pública
        post_url = review_data.get("url") or ""

        # fecha publicada
        raw_dt = review_data.get("published_date") or review_data.get("created_time") or review_data.get("created_at")
        platform_created_at = None
        if isinstance(raw_dt, str):
            try:
                platform_created_at = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
            except Exception:
                platform_created_at = None

        return {
            "platform": "TRIPADVISOR",
            "id_comment_platform": id_comment_platform,
            "author": author,
            "content": content,
            "rating": rating,
            "post_url": post_url,
            "platform_created_at": platform_created_at or raw_dt,
        }


class FacebookIngestionService:
    BASE_URL = "https://graph.facebook.com/v23.0"
    REACTION_TYPES = ["LIKE", "LOVE", "HAHA", "WOW", "SAD", "ANGRY"]

    @staticmethod
    async def fetch_posts(db: Session, limit: int = 50):
        """Fetches posts from the configured Facebook Page."""
        credentials = _get_meta_credentials(db)
        page_id = credentials.get("fb_page_id")
        # Prefer page_access_token, fallback to user_access_token
        access_token = (
            credentials.get("page_access_token") or credentials.get("user_access_token")
        )

        if not page_id:
            raise HTTPException(status_code=404, detail="Facebook Page ID not found in credentials.")

        url = f"{FacebookIngestionService.BASE_URL}/{page_id}/posts"
        params = {
            "fields": "id,message,created_time,permalink_url",
            "limit": limit,
            "access_token": access_token,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json().get("data", [])
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error fetching Facebook posts: {e.response.status_code} - {e.response.text}"
                )

    @staticmethod
    async def fetch_comments(db: Session, post_platform_id: str, limit: int = 100):
        """Fetches comments for a specific Facebook post ID."""
        credentials = _get_meta_credentials(db)
        # Prefer page_access_token, fallback to user_access_token
        access_token = (
            credentials.get("page_access_token") or credentials.get("user_access_token")
        )

        url = f"{FacebookIngestionService.BASE_URL}/{post_platform_id}/comments"
        params = {
            "fields": "id,from,message,created_time",
            "limit": limit,
            "access_token": access_token,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json().get("data", [])
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error fetching Facebook comments: {e.response.status_code} - {e.response.text}"
                )

    @staticmethod
    async def fetch_reactions(db: Session, post_platform_id: str) -> Dict[str, int]:
        """
        Devuelve los conteos de reacciones para un post de Facebook.
        - 1 request total
        - 1 por tipo (LIKE, LOVE, HAHA, WOW, SAD, ANGRY)
        Siempre retorna un diccionario con ceros si algo falla.
        """
        credentials = _get_meta_credentials(db)
        access_token = credentials.get("page_access_token")  # mejor que user_access_token
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing page_access_token for reactions")

        counts: Dict[str, int] = {t.lower(): 0 for t in FacebookIngestionService.REACTION_TYPES}
        counts["total"] = 0

        timeout = httpx.Timeout(15.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                # total
                r_total = await client.get(
                    f"{FacebookIngestionService.BASE_URL}/{post_platform_id}/reactions",
                    params={"access_token": access_token, "summary": "true", "limit": 0},
                )
                if not r_total.is_error:
                    j0 = r_total.json()
                    counts["total"] = int((j0.get("summary") or {}).get("total_count", 0))

                # por tipo
                tasks = [
                    client.get(
                        f"{FacebookIngestionService.BASE_URL}/{post_platform_id}/reactions",
                        params={
                            "access_token": access_token,
                            "type": t,
                            "summary": "true",
                            "limit": 0,
                        },
                    )
                    for t in FacebookIngestionService.REACTION_TYPES
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for t, resp in zip(FacebookIngestionService.REACTION_TYPES, responses):
                    if isinstance(resp, httpx.Response) and not resp.is_error:
                        jj = resp.json()
                        counts[t.lower()] = int((jj.get("summary") or {}).get("total_count", 0))
                    else:
                        counts[t.lower()] = 0

            except Exception:
                # dejar counts en ceros
                pass

        return counts

async def send_auto_reply_to_comment(db: Session, db_comment, platform: str) -> bool:
    """
    Send automatic reply to a comment via Meta API based on its lead score.

    Args:
        db: Database session
        db_comment: Comment object (with lead_score relationship populated)
        platform: Platform name ("INSTAGRAM" or "FACEBOOK")

    Returns:
        True if reply sent successfully, False otherwise
    """
    from app.services.response_service import CRMResponseService

    try:
        # Get lead score (created automatically by CommentService)
        lead_score = db_comment.lead_score
        if not lead_score:
            print(f"[send_auto_reply] No lead score for comment {db_comment.id}")
            return False

        # Generate message based on priority level
        message = CRMResponseService.generate_response_message(lead_score, platform, db_comment.id)

        # Get credentials from DB
        credentials = _get_meta_credentials(db)

        # Send reply via Meta API
        base_url = "https://graph.facebook.com/v23.0"

        if platform == "INSTAGRAM":
            access_token = credentials.get("user_access_token")
            url = f"{base_url}/{db_comment.id_comment_platform}/replies"
            # Instagram accepts params in URL
            params = {
                "message": message,
                "access_token": access_token,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params)
                response.raise_for_status()
                result = response.json()
                print(f"[send_auto_reply] {platform} reply sent to comment {db_comment.id_comment_platform}")
                return True

        elif platform == "FACEBOOK":
            access_token = credentials.get("page_access_token")
            if not access_token:
                print("[send_auto_reply] Missing page_access_token. Cannot send Facebook reply.")
                return False

            url = f"{base_url}/{db_comment.id_comment_platform}/comments"
            # Facebook uses /comments endpoint with access_token in URL params and message in body
            params = {
                "access_token": access_token,
            }
            data = {
                "message": message,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params, json=data)

                if response.status_code == 403:
                    # Log detailed error for 403
                    error_body = response.json()
                    print(f"[send_auto_reply] 403 Forbidden - Facebook error: {error_body}")
                    print(f"[send_auto_reply] Token used: {access_token[:20]}... (truncated)")
                    print(f"[send_auto_reply] Comment ID: {db_comment.id_comment_platform}")
                    return False

                response.raise_for_status()
                result = response.json()
                print(f"[send_auto_reply] {platform} reply sent to comment {db_comment.id_comment_platform}")
                return True
        else:
            print(f"[send_auto_reply] Unsupported platform: {platform}")
            return False

    except Exception as e:
        print(f"[send_auto_reply] Error sending {platform} reply: {str(e)}")
        return False


