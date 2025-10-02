"""
X (Twitter) API Service

This service provides access to X API v2 with Free Tier support.
Free tier limitations:
- 100 reads per month (app level)
- 1,500 posts per month (posting limit)
- Access to basic v2 endpoints

Documentation: https://developer.x.com/en/docs/twitter-api
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from requests_oauthlib import OAuth1Session
from app.core.config import settings


class XAPIException(Exception):
    """Custom exception for X API errors."""

    pass


class XAPIService:
    """
    Service for interacting with X (Twitter) API v2.

    Supports free tier endpoints:
    - Tweet lookup (by ID)
    - User lookup (by ID or username)
    - User tweets timeline
    """

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self):
        """Initialize the X API service with bearer token authentication."""
        self.bearer_token = settings.x_bearer_token
        if not self.bearer_token:
            raise ValueError("X_BEARER_TOKEN is required for X API access")

        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

        # OAuth 1.0a credentials for posting (optional)
        self.api_key = settings.x_api_key
        self.api_secret = settings.x_api_secret
        self.access_token = settings.x_access_token
        self.access_token_secret = settings.x_access_token_secret

        # Track posting quota
        self.posts_created = 0
        self.max_posts_per_month = 1500

    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the X API.

        Args:
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            method: HTTP method (GET, POST, etc.)

        Returns:
            JSON response from the API

        Raises:
            XAPIException: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=self.headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=self.headers, json=params)
                elif method == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get("detail", error_json.get("errors", error_detail))
                except:
                    pass
                raise XAPIException(f"X API error ({e.response.status_code}): {error_detail}")
            except httpx.RequestError as e:
                raise XAPIException(f"Request error: {str(e)}")

    # ==================== TWEET LOOKUP ENDPOINTS ====================

    async def get_tweet(
        self,
        tweet_id: str,
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
        user_fields: Optional[List[str]] = None,
        media_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a single tweet by ID.

        Args:
            tweet_id: The ID of the tweet to retrieve
            expansions: List of expansions (author_id, referenced_tweets.id, etc.)
            tweet_fields: Additional tweet fields to include
            user_fields: Additional user fields when expanding users
            media_fields: Additional media fields when expanding media

        Returns:
            Tweet data with requested fields and expansions

        Example:
            tweet = await service.get_tweet(
                "1234567890",
                expansions=["author_id"],
                tweet_fields=["created_at", "public_metrics"],
                user_fields=["username", "verified"]
            )
        """
        params = {}

        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if media_fields:
            params["media.fields"] = ",".join(media_fields)

        return await self._make_request(f"tweets/{tweet_id}", params)

    async def get_tweets(
        self,
        tweet_ids: List[str],
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
        user_fields: Optional[List[str]] = None,
        media_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve multiple tweets by their IDs (up to 100 per request).

        Args:
            tweet_ids: List of tweet IDs (max 100)
            expansions: List of expansions
            tweet_fields: Additional tweet fields to include
            user_fields: Additional user fields when expanding users
            media_fields: Additional media fields when expanding media

        Returns:
            Dictionary with 'data' containing list of tweets
        """
        if len(tweet_ids) > 100:
            raise ValueError("Maximum 100 tweet IDs per request")

        params = {"ids": ",".join(tweet_ids)}

        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if media_fields:
            params["media.fields"] = ",".join(media_fields)

        return await self._make_request("tweets", params)

    # ==================== USER LOOKUP ENDPOINTS ====================

    async def get_user(
        self,
        user_id: str,
        user_fields: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a single user by ID.

        Args:
            user_id: The ID of the user to retrieve
            user_fields: Additional user fields to include
            expansions: List of expansions
            tweet_fields: Additional tweet fields when expanding tweets

        Returns:
            User data with requested fields
        """
        params = {}

        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        return await self._make_request(f"users/{user_id}", params)

    async def get_user_by_username(
        self,
        username: str,
        user_fields: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a single user by username.

        Args:
            username: The username (without @) of the user to retrieve
            user_fields: Additional user fields to include
            expansions: List of expansions
            tweet_fields: Additional tweet fields when expanding tweets

        Returns:
            User data with requested fields
        """
        params = {}

        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        return await self._make_request(f"users/by/username/{username}", params)

    async def get_users(
        self,
        user_ids: List[str],
        user_fields: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve multiple users by their IDs (up to 100 per request).

        Args:
            user_ids: List of user IDs (max 100)
            user_fields: Additional user fields to include
            expansions: List of expansions
            tweet_fields: Additional tweet fields when expanding tweets

        Returns:
            Dictionary with 'data' containing list of users
        """
        if len(user_ids) > 100:
            raise ValueError("Maximum 100 user IDs per request")

        params = {"ids": ",".join(user_ids)}

        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        return await self._make_request("users", params)

    async def get_users_by_usernames(
        self,
        usernames: List[str],
        user_fields: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve multiple users by their usernames (up to 100 per request).

        Args:
            usernames: List of usernames (max 100)
            user_fields: Additional user fields to include
            expansions: List of expansions
            tweet_fields: Additional tweet fields when expanding tweets

        Returns:
            Dictionary with 'data' containing list of users
        """
        if len(usernames) > 100:
            raise ValueError("Maximum 100 usernames per request")

        params = {"usernames": ",".join(usernames)}

        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        return await self._make_request("users/by", params)

    # ==================== USER TIMELINE ENDPOINTS ====================

    async def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 10,
        pagination_token: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
        tweet_fields: Optional[List[str]] = None,
        user_fields: Optional[List[str]] = None,
        media_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve tweets posted by a specific user.

        Note: This endpoint may not be available on Free tier. Check X API docs.

        Args:
            user_id: The ID of the user
            max_results: Number of results per page (5-100, default 10)
            pagination_token: Token for pagination
            exclude: Types to exclude (retweets, replies)
            expansions: List of expansions
            tweet_fields: Additional tweet fields to include
            user_fields: Additional user fields when expanding users
            media_fields: Additional media fields when expanding media

        Returns:
            Dictionary with tweets and pagination info
        """
        if max_results < 5 or max_results > 100:
            raise ValueError("max_results must be between 5 and 100")

        params = {"max_results": max_results}

        if pagination_token:
            params["pagination_token"] = pagination_token
        if exclude:
            params["exclude"] = ",".join(exclude)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if media_fields:
            params["media.fields"] = ",".join(media_fields)

        return await self._make_request(f"users/{user_id}/tweets", params)

    # ==================== TWEET CREATION ENDPOINTS ====================

    def _get_oauth_session(self) -> OAuth1Session:
        """
        Create an OAuth1Session for authenticated requests.
        Required for write operations (creating tweets, etc.)

        Returns:
            OAuth1Session configured with user credentials

        Raises:
            ValueError: If OAuth credentials are not configured
        """
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError(
                "OAuth 1.0a credentials are required for posting. "
                "Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET in your .env file."
            )

        return OAuth1Session(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

    def can_post(self) -> bool:
        """
        Check if we can still post within the monthly limit.
        Free tier: 1,500 posts per month.

        Returns:
            True if we haven't reached the limit
        """
        return self.posts_created < self.max_posts_per_month

    async def create_tweet(
        self,
        text: str,
        reply_to_tweet_id: Optional[str] = None,
        quote_tweet_id: Optional[str] = None,
        poll_options: Optional[List[str]] = None,
        poll_duration_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new tweet.

        Free tier: 1,500 posts per month

        Args:
            text: Tweet text (max 280 characters)
            reply_to_tweet_id: ID of tweet to reply to (optional)
            quote_tweet_id: ID of tweet to quote (optional)
            poll_options: List of poll options (2-4 options, optional)
            poll_duration_minutes: Poll duration in minutes (5-10080, optional)

        Returns:
            Created tweet data with ID and metadata

        Raises:
            ValueError: If credentials missing or quota exceeded
            XAPIException: If API request fails

        Example:
            # Simple tweet
            tweet = await service.create_tweet("Hello, world!")

            # Reply to a tweet
            reply = await service.create_tweet(
                "Thanks for sharing!",
                reply_to_tweet_id="1234567890"
            )

            # Quote tweet
            quote = await service.create_tweet(
                "This is interesting!",
                quote_tweet_id="1234567890"
            )
        """
        if not self.can_post():
            raise ValueError(
                f"Monthly post limit reached ({self.posts_created}/{self.max_posts_per_month}). "
                "Limit resets at the start of each month."
            )

        if len(text) > 280:
            raise ValueError("Tweet text cannot exceed 280 characters")

        # Build request payload
        payload = {"text": text}

        # Add reply settings
        if reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_tweet_id}

        # Add quote tweet
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id

        # Add poll (if provided)
        if poll_options:
            if len(poll_options) < 2 or len(poll_options) > 4:
                raise ValueError("Poll must have 2-4 options")
            if not poll_duration_minutes:
                poll_duration_minutes = 1440  # Default 24 hours

            payload["poll"] = {"options": poll_options, "duration_minutes": poll_duration_minutes}

        # Make OAuth request
        url = f"{self.BASE_URL}/tweets"
        oauth = self._get_oauth_session()

        try:
            response = oauth.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            self.posts_created += 1

            # Add helpful metadata
            tweet_id = result.get("data", {}).get("id")
            result["posts_used"] = self.posts_created
            result["posts_remaining"] = self.max_posts_per_month - self.posts_created
            if tweet_id:
                result["tweet_url"] = f"https://x.com/i/status/{tweet_id}"

            return result

        except Exception as e:
            raise XAPIException(f"Failed to create tweet: {str(e)}")

    async def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """
        Delete a tweet.

        Note: You can only delete tweets posted by the authenticated user.

        Args:
            tweet_id: ID of the tweet to delete

        Returns:
            Deletion confirmation

        Raises:
            ValueError: If OAuth credentials are missing
            XAPIException: If API request fails
        """
        url = f"{self.BASE_URL}/tweets/{tweet_id}"
        oauth = self._get_oauth_session()

        try:
            response = oauth.delete(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise XAPIException(f"Failed to delete tweet: {str(e)}")

    async def retweet(self, user_id: str, tweet_id: str) -> Dict[str, Any]:
        """
        Retweet a tweet.

        Args:
            user_id: Your user ID (the authenticated user)
            tweet_id: ID of the tweet to retweet

        Returns:
            Retweet confirmation

        Raises:
            ValueError: If OAuth credentials are missing
            XAPIException: If API request fails
        """
        if not self.can_post():
            raise ValueError(
                f"Monthly post limit reached ({self.posts_created}/{self.max_posts_per_month})"
            )

        url = f"{self.BASE_URL}/users/{user_id}/retweets"
        oauth = self._get_oauth_session()
        payload = {"tweet_id": tweet_id}

        try:
            response = oauth.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            self.posts_created += 1
            result["posts_used"] = self.posts_created
            result["posts_remaining"] = self.max_posts_per_month - self.posts_created

            return result
        except Exception as e:
            raise XAPIException(f"Failed to retweet: {str(e)}")

    async def unretweet(self, user_id: str, tweet_id: str) -> Dict[str, Any]:
        """
        Remove a retweet.

        Args:
            user_id: Your user ID (the authenticated user)
            tweet_id: ID of the tweet to unretweet

        Returns:
            Unretweet confirmation
        """
        url = f"{self.BASE_URL}/users/{user_id}/retweets/{tweet_id}"
        oauth = self._get_oauth_session()

        try:
            response = oauth.delete(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise XAPIException(f"Failed to unretweet: {str(e)}")

    async def like_tweet(self, user_id: str, tweet_id: str) -> Dict[str, Any]:
        """
        Like a tweet.

        Args:
            user_id: Your user ID (the authenticated user)
            tweet_id: ID of the tweet to like

        Returns:
            Like confirmation
        """
        url = f"{self.BASE_URL}/users/{user_id}/likes"
        oauth = self._get_oauth_session()
        payload = {"tweet_id": tweet_id}

        try:
            response = oauth.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise XAPIException(f"Failed to like tweet: {str(e)}")

    async def unlike_tweet(self, user_id: str, tweet_id: str) -> Dict[str, Any]:
        """
        Remove a like from a tweet.

        Args:
            user_id: Your user ID (the authenticated user)
            tweet_id: ID of the tweet to unlike

        Returns:
            Unlike confirmation
        """
        url = f"{self.BASE_URL}/users/{user_id}/likes/{tweet_id}"
        oauth = self._get_oauth_session()

        try:
            response = oauth.delete(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise XAPIException(f"Failed to unlike tweet: {str(e)}")

    # ==================== HELPER METHODS ====================

    def parse_tweet_url(self, url: str) -> Optional[str]:
        """
        Extract tweet ID from a tweet URL.

        Args:
            url: Tweet URL (e.g., https://twitter.com/username/status/1234567890)

        Returns:
            Tweet ID or None if not found
        """
        import re

        patterns = [
            r"twitter\.com/[^/]+/status/(\d+)",
            r"x\.com/[^/]+/status/(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def format_tweet_for_display(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format tweet data for easy display/storage.

        Args:
            tweet_data: Raw tweet data from API

        Returns:
            Formatted tweet data
        """
        tweet = tweet_data.get("data", {})
        includes = tweet_data.get("includes", {})

        # Get author info if available
        author_info = None
        if includes.get("users"):
            author_info = includes["users"][0]

        formatted = {
            "id": tweet.get("id"),
            "text": tweet.get("text"),
            "created_at": tweet.get("created_at"),
            "author_id": tweet.get("author_id"),
            "author_username": author_info.get("username") if author_info else None,
            "author_name": author_info.get("name") if author_info else None,
            "url": f"https://twitter.com/i/status/{tweet.get('id')}" if tweet.get("id") else None,
            "public_metrics": tweet.get("public_metrics", {}),
            "raw_data": tweet,
        }

        return formatted


# Singleton instance
_x_api_service: Optional[XAPIService] = None


def get_x_api_service() -> XAPIService:
    """Get or create the X API service instance."""
    global _x_api_service
    if _x_api_service is None:
        _x_api_service = XAPIService()
    return _x_api_service
