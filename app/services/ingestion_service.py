import httpx
from typing import List, Dict, Any

from fastapi import requests

from app.core.database import SessionLocal
from app.services.post_service import PostService
from app.core.config import settings
from datetime import datetime
import json


class InstagramIngestionService:
    BASE_URL = "https://graph.facebook.com/v23.0"

    @staticmethod
    async def fetch_instagram_posts():
        async with httpx.AsyncClient() as client:
            url = f"{InstagramIngestionService.BASE_URL}/{settings.instagram_business_account_id}/media"
            params = {
                "access_token": settings.meta_ig_access_token,
                "fields": "id,caption,media_type,media_url,timestamp"
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get("data", [])

    @staticmethod
    def ingest_instagram_posts():
        posts_data = fetch_instagram_posts()
        db = SessionLocal()
        for post in posts_data:
            db_post = Post(
                platform="instagram",
                platform_id=post["id"],
                text=post.get("caption", ""),
                media_type=post.get("media_type"),
                media_url=post.get("media_url"),
                platform_created_at=post.get("timestamp")
            )
            db.add(db_post)
        db.commit()
        db.close()

    @staticmethod
    def transform_to_post(post_data: dict) -> dict:
        """Transform Instagram post data to internal format."""
        return {
            "platform": "instagram",
            "platform_id": post_data.get("id"),
            "text": post_data.get("caption", ""),
            "media_type": post_data.get("media_type"),
            "media_url": post_data.get("media_url"),
            "platform_created_at": post_data.get("timestamp"),
            "extra_data": json.dumps(post_data)
        }

    @staticmethod
    async def fetch_all_instagram_comments(access_token: str):
        posts = await InstagramIngestionService.fetch_instagram_posts()
        comments = []
        for post in posts:
            post_id = post["id"]
            post_comments = await InstagramIngestionService.fetch_comments(post_id)
        comments.extend(post_comments)
        return comments

    @staticmethod
    async def fetch_comments(post_id: str):
        async with httpx.AsyncClient() as client:
            url = f"{InstagramIngestionService.BASE_URL}/{post_id}/comments"
            params = {
                "access_token": settings.meta_ig_access_token,
                "fields": "id,text,username,timestamp"
            }
            r = await client.get(url, params=params)
            return r.json().get("data", [])

    @staticmethod
    def transform_to_comment(comment_data: dict) -> dict:
        """Transform Instagram comment data to internal format."""
        return {
            "platform": "instagram",
            "platform_id": comment_data.get("id"),
            "author": comment_data.get("username"),
            "content": comment_data.get("text", ""),
            "post_url": None,
            "platform_created_at": comment_data.get("timestamp"),
            "extra_data": json.dumps(comment_data)
        }


class MetaIngestionService:
    """Service for ingesting data from Meta (Facebook/Instagram) API."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    @staticmethod
    async def fetch_comments(post_id: str) -> List[Dict[str, Any]]:
        """
        Fetch comments from a Meta post.
        
        Note: This is a mock implementation. Replace with actual Meta API calls.
        """
        # Mock implementation - replace with actual API call
        # Example:
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{MetaIngestionService.BASE_URL}/{post_id}/comments",
        #         params={"access_token": settings.meta_api_key}
        #     )
        #     data = response.json()
        #     return data.get("data", [])
        
        return [
            {
                "id": f"meta_{post_id}_1",
                "from": {"name": "Example User", "id": "123456"},
                "message": "This is a sample comment from Meta",
                "created_time": datetime.now().isoformat(),
                "permalink_url": f"https://facebook.com/{post_id}"
            }
        ]
    
    @staticmethod
    def transform_to_comment(comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Meta comment data to internal format."""
        return {
            "platform": "meta",
            "platform_id": comment_data.get("id"),
            "author": comment_data.get("from", {}).get("name"),
            "content": comment_data.get("message", ""),
            "post_url": comment_data.get("permalink_url"),
            "platform_created_at": comment_data.get("created_time"),
            "extra_data": json.dumps(comment_data)
        }


class XIngestionService:
    """Service for ingesting data from X (Twitter) API."""
    
    BASE_URL = "https://api.twitter.com/2"
    
    @staticmethod
    async def fetch_replies(tweet_id: str) -> List[Dict[str, Any]]:
        """
        Fetch replies to a tweet.
        
        Note: This is a mock implementation. Replace with actual X API calls.
        """
        # Mock implementation - replace with actual API call
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{XIngestionService.BASE_URL}/tweets/search/recent",
        #         headers={"Authorization": f"Bearer {settings.x_bearer_token}"},
        #         params={"query": f"conversation_id:{tweet_id}"}
        #     )
        #     data = response.json()
        #     return data.get("data", [])
        
        return [
            {
                "id": f"x_{tweet_id}_1",
                "author_id": "987654",
                "text": "This is a sample reply from X",
                "created_at": datetime.now().isoformat(),
            }
        ]
    
    @staticmethod
    def transform_to_comment(reply_data: Dict[str, Any], author_username: str = None) -> Dict[str, Any]:
        """Transform X reply data to internal format."""
        tweet_id = reply_data.get("id")
        return {
            "platform": "x",
            "platform_id": tweet_id,
            "author": author_username or reply_data.get("author_id"),
            "content": reply_data.get("text", ""),
            "post_url": f"https://twitter.com/i/status/{tweet_id}" if tweet_id else None,
            "platform_created_at": reply_data.get("created_at"),
            "extra_data": json.dumps(reply_data)
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
        platform_id = f"tripadvisor_{raw_id}"
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
            "platform": "tripadvisor",
            "platform_id": platform_id,
            "id_comment_platform": id_comment_platform,
            "author": author,
            "content": content,
            "rating": rating,
            "post_url": post_url,
            "platform_created_at": platform_created_at or raw_dt,
        }


class FacebookIngestionService:
    # (opcional) usa la misma versión que tu Explorer
    BASE_URL = "https://graph.facebook.com/v23.0"

    @staticmethod
    def _page_token() -> str:
        """
        Lee el token desde settings o variables de entorno.
        Evita el caso donde settings.fb_access_token venga vacío.
        """
        import os
        token = (
            getattr(settings, "fb_access_token", "")               # alias que agregamos en Settings
            or getattr(settings, "meta_fb_access_token", "")       # nombre original en Settings
            or os.environ.get("META_FB_ACCESS_TOKEN", "")          # por si el sistema tiene la var
        )
        if not token:
            # Deja este error claro para no seguir llamando al Graph sin token
            raise RuntimeError("Facebook access token is empty. Check .env (META_FB_ACCESS_TOKEN).")
        return token

    @staticmethod
    def _get(url: str, params: dict):
        resp = httpx.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def fetch_posts(page_id: str | None = None, limit: int = 50):
        access_token = FacebookIngestionService._page_token()
        page_id = page_id or settings.fb_page_id
        url = f"{FacebookIngestionService.BASE_URL}/{page_id}/posts"
        params = {
            "fields": "id,message,created_time,permalink_url",
            "limit": limit,
            "access_token": access_token,
        }
        data = FacebookIngestionService._get(url, params)
        return data.get("data", [])

    @staticmethod
    def fetch_comments(post_platform_id: str, limit: int = 100):
        access_token = FacebookIngestionService._page_token()
        url = f"{FacebookIngestionService.BASE_URL}/{post_platform_id}/comments"
        params = {
            "fields": "id,from,message,created_time",
            "limit": limit,
            "access_token": access_token,
        }
        data = FacebookIngestionService._get(url, params)
        return data.get("data", [])

