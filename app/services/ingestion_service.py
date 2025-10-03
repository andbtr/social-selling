import httpx
from typing import List, Dict, Any
from app.core.config import settings
from datetime import datetime
import json


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