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
    """Service for ingesting data from TripAdvisor API."""
    
    BASE_URL = "https://api.tripadvisor.com/api/partner/2.0"
    
    @staticmethod
    async def fetch_reviews(location_id: str) -> List[Dict[str, Any]]:
        """
        Fetch reviews for a TripAdvisor location.
        
        Note: This is a mock implementation. Replace with actual TripAdvisor API calls.
        """
        # Mock implementation - replace with actual API call
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{TripAdvisorIngestionService.BASE_URL}/location/{location_id}/reviews",
        #         headers={"X-TripAdvisor-API-Key": settings.tripadvisor_api_key}
        #     )
        #     data = response.json()
        #     return data.get("data", [])
        
        return [
            {
                "id": f"tripadvisor_{location_id}_1",
                "author": "Traveler123",
                "text": "This is a sample review from TripAdvisor",
                "published_date": datetime.now().isoformat(),
                "url": f"https://tripadvisor.com/review/{location_id}_1"
            }
        ]
    
    @staticmethod
    def transform_to_comment(review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform TripAdvisor review data to internal format."""
        return {
            "platform": "tripadvisor",
            "platform_id": review_data.get("id"),
            "author": review_data.get("author"),
            "content": review_data.get("text", ""),
            "post_url": review_data.get("url"),
            "platform_created_at": review_data.get("published_date"),
            "extra_data": json.dumps(review_data)
        }
