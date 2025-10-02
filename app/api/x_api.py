"""
X (Twitter) API Routes

FastAPI endpoints for accessing X (Twitter) API v2 functionality.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.x_api_service import get_x_api_service, XAPIException


router = APIRouter(prefix="/x", tags=["X (Twitter) API"])


# ==================== REQUEST/RESPONSE MODELS ====================


class TweetLookupRequest(BaseModel):
    """Request model for looking up a single tweet."""

    tweet_id: str = Field(..., description="The ID of the tweet to retrieve")
    include_author: bool = Field(default=True, description="Include author information")
    include_metrics: bool = Field(default=True, description="Include public metrics")


class TweetBatchLookupRequest(BaseModel):
    """Request model for looking up multiple tweets."""

    tweet_ids: List[str] = Field(..., description="List of tweet IDs (max 100)", max_length=100)
    include_author: bool = Field(default=True, description="Include author information")
    include_metrics: bool = Field(default=True, description="Include public metrics")


class UserLookupRequest(BaseModel):
    """Request model for looking up a user."""

    user_id: Optional[str] = Field(None, description="The ID of the user")
    username: Optional[str] = Field(None, description="The username (without @)")
    include_metrics: bool = Field(default=True, description="Include public metrics")


class UserTweetsRequest(BaseModel):
    """Request model for getting user tweets."""

    user_id: str = Field(..., description="The ID of the user")
    max_results: int = Field(default=10, ge=5, le=100, description="Number of results (5-100)")
    exclude_retweets: bool = Field(default=False, description="Exclude retweets")
    exclude_replies: bool = Field(default=False, description="Exclude replies")


class CreateTweetRequest(BaseModel):
    """Request model for creating a tweet."""

    text: str = Field(..., max_length=280, description="Tweet text (max 280 characters)")
    reply_to_tweet_id: Optional[str] = Field(None, description="Tweet ID to reply to")
    quote_tweet_id: Optional[str] = Field(None, description="Tweet ID to quote")
    poll_options: Optional[List[str]] = Field(None, description="Poll options (2-4 options)")
    poll_duration_minutes: Optional[int] = Field(
        None, ge=5, le=10080, description="Poll duration in minutes"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"text": "¡Hola desde la API! 👋"},
                {"text": "Gracias por tu comentario!", "reply_to_tweet_id": "1234567890"},
                {"text": "Totalmente de acuerdo!", "quote_tweet_id": "1234567890"},
                {
                    "text": "¿Cuál es tu favorito?",
                    "poll_options": ["Opción A", "Opción B", "Opción C"],
                    "poll_duration_minutes": 1440,
                },
            ]
        }


class RetweetRequest(BaseModel):
    """Request model for retweeting."""

    user_id: str = Field(..., description="Your user ID")
    tweet_id: str = Field(..., description="Tweet ID to retweet")


class LikeRequest(BaseModel):
    """Request model for liking a tweet."""

    user_id: str = Field(..., description="Your user ID")
    tweet_id: str = Field(..., description="Tweet ID to like")


# ==================== TWEET ENDPOINTS ====================


@router.get("/tweets/{tweet_id}")
async def get_tweet(
    tweet_id: str,
    include_author: bool = Query(default=True, description="Include author information"),
    include_metrics: bool = Query(default=True, description="Include public metrics"),
):
    """
    Retrieve a single tweet by its ID.

    This endpoint uses the X API v2 tweet lookup endpoint.

    **Free Tier Limitation**: Counts as 1 read towards your 100 reads/month limit.

    **Parameters**:
    - `tweet_id`: The unique identifier of the tweet
    - `include_author`: Whether to include author information in the response
    - `include_metrics`: Whether to include engagement metrics (likes, retweets, etc.)

    **Returns**: Tweet data with requested fields
    """
    try:
        service = get_x_api_service()

        # Build expansions and fields based on parameters
        expansions = []
        tweet_fields = ["created_at", "conversation_id", "lang"]
        user_fields = ["username", "name", "verified", "profile_image_url"]

        if include_author:
            expansions.append("author_id")

        if include_metrics:
            tweet_fields.append("public_metrics")
            user_fields.append("public_metrics")

        result = await service.get_tweet(
            tweet_id=tweet_id,
            expansions=expansions if expansions else None,
            tweet_fields=tweet_fields,
            user_fields=user_fields if include_author else None,
        )

        return {
            "success": True,
            "data": result,
            "formatted": service.format_tweet_for_display(result),
        }

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/tweets/batch")
async def get_tweets_batch(request: TweetBatchLookupRequest):
    """
    Retrieve multiple tweets by their IDs (up to 100 per request).

    This endpoint uses the X API v2 tweet lookup endpoint.

    **Free Tier Limitation**: Counts as 1 read per request (not per tweet) towards your 100 reads/month limit.

    **Request Body**:
    ```json
    {
        "tweet_ids": ["1234567890", "0987654321"],
        "include_author": true,
        "include_metrics": true
    }
    ```

    **Returns**: List of tweet data
    """
    try:
        service = get_x_api_service()

        # Build expansions and fields
        expansions = []
        tweet_fields = ["created_at", "conversation_id", "lang"]
        user_fields = ["username", "name", "verified", "profile_image_url"]

        if request.include_author:
            expansions.append("author_id")

        if request.include_metrics:
            tweet_fields.append("public_metrics")
            user_fields.append("public_metrics")

        result = await service.get_tweets(
            tweet_ids=request.tweet_ids,
            expansions=expansions if expansions else None,
            tweet_fields=tweet_fields,
            user_fields=user_fields if request.include_author else None,
        )

        return {"success": True, "data": result, "count": len(result.get("data", []))}

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/tweets/parse-url")
async def parse_tweet_url(url: str = Query(..., description="Tweet URL to parse")):
    """
    Extract tweet ID from a tweet URL.

    **Free Tier**: This endpoint does not count towards your API limits as it's a local operation.

    **Parameters**:
    - `url`: Full tweet URL (e.g., https://twitter.com/username/status/1234567890)

    **Returns**: Extracted tweet ID
    """
    try:
        service = get_x_api_service()
        tweet_id = service.parse_tweet_url(url)

        if not tweet_id:
            raise HTTPException(status_code=400, detail="Could not extract tweet ID from URL")

        return {"success": True, "url": url, "tweet_id": tweet_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== USER ENDPOINTS ====================


@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: str, include_metrics: bool = Query(default=True, description="Include public metrics")
):
    """
    Retrieve a user by their ID.

    **Free Tier Limitation**: Counts as 1 read towards your 100 reads/month limit.

    **Parameters**:
    - `user_id`: The unique identifier of the user
    - `include_metrics`: Whether to include follower counts and other metrics

    **Returns**: User data with requested fields
    """
    try:
        service = get_x_api_service()

        user_fields = [
            "username",
            "name",
            "description",
            "created_at",
            "verified",
            "profile_image_url",
        ]

        if include_metrics:
            user_fields.append("public_metrics")

        result = await service.get_user(user_id=user_id, user_fields=user_fields)

        return {"success": True, "data": result}

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/users/by-username/{username}")
async def get_user_by_username(
    username: str, include_metrics: bool = Query(default=True, description="Include public metrics")
):
    """
    Retrieve a user by their username.

    **Free Tier Limitation**: Counts as 1 read towards your 100 reads/month limit.

    **Parameters**:
    - `username`: The username (without @) of the user
    - `include_metrics`: Whether to include follower counts and other metrics

    **Returns**: User data with requested fields
    """
    try:
        service = get_x_api_service()

        user_fields = [
            "username",
            "name",
            "description",
            "created_at",
            "verified",
            "profile_image_url",
        ]

        if include_metrics:
            user_fields.append("public_metrics")

        result = await service.get_user_by_username(username=username, user_fields=user_fields)

        return {"success": True, "data": result}

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/users/batch")
async def get_users_batch(
    user_ids: Optional[List[str]] = None,
    usernames: Optional[List[str]] = None,
    include_metrics: bool = True,
):
    """
    Retrieve multiple users by their IDs or usernames (up to 100 per request).

    **Free Tier Limitation**: Counts as 1 read per request towards your 100 reads/month limit.

    **Request Body**:
    ```json
    {
        "user_ids": ["123456", "789012"],  // OR
        "usernames": ["elonmusk", "jack"],
        "include_metrics": true
    }
    ```

    **Returns**: List of user data
    """
    if not user_ids and not usernames:
        raise HTTPException(status_code=400, detail="Either user_ids or usernames must be provided")

    if user_ids and usernames:
        raise HTTPException(
            status_code=400, detail="Provide either user_ids or usernames, not both"
        )

    try:
        service = get_x_api_service()

        user_fields = [
            "username",
            "name",
            "description",
            "created_at",
            "verified",
            "profile_image_url",
        ]

        if include_metrics:
            user_fields.append("public_metrics")

        if user_ids:
            result = await service.get_users(user_ids=user_ids, user_fields=user_fields)
        else:
            result = await service.get_users_by_usernames(
                usernames=usernames, user_fields=user_fields
            )

        return {"success": True, "data": result, "count": len(result.get("data", []))}

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== USER TIMELINE ENDPOINTS ====================


@router.get("/users/{user_id}/tweets")
async def get_user_tweets(
    user_id: str,
    max_results: int = Query(default=10, ge=5, le=100, description="Number of results (5-100)"),
    exclude_retweets: bool = Query(default=False, description="Exclude retweets"),
    exclude_replies: bool = Query(default=False, description="Exclude replies"),
    pagination_token: Optional[str] = Query(default=None, description="Token for pagination"),
):
    """
    Retrieve tweets posted by a specific user.

    **Important**: This endpoint may not be available on the Free tier.
    Please check the X API documentation for current access levels.

    **Free Tier Limitation**: If available, counts as 1 read towards your 100 reads/month limit.

    **Parameters**:
    - `user_id`: The ID of the user
    - `max_results`: Number of tweets to retrieve (5-100)
    - `exclude_retweets`: Filter out retweets
    - `exclude_replies`: Filter out replies
    - `pagination_token`: Token from previous response for pagination

    **Returns**: List of tweets with pagination metadata
    """
    try:
        service = get_x_api_service()

        exclude = []
        if exclude_retweets:
            exclude.append("retweets")
        if exclude_replies:
            exclude.append("replies")

        result = await service.get_user_tweets(
            user_id=user_id,
            max_results=max_results,
            pagination_token=pagination_token,
            exclude=exclude if exclude else None,
            expansions=["author_id"],
            tweet_fields=["created_at", "public_metrics", "conversation_id"],
            user_fields=["username", "name", "verified"],
        )

        return {
            "success": True,
            "data": result,
            "count": len(result.get("data", [])),
            "next_token": result.get("meta", {}).get("next_token"),
        }

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== UTILITY ENDPOINTS ====================


@router.get("/health")
async def health_check():
    """
    Check if the X API service is properly configured.

    **Free Tier**: This endpoint does not count towards your API limits.

    **Returns**: Service health status
    """
    try:
        service = get_x_api_service()
        return {
            "success": True,
            "message": "X API service is configured",
            "has_bearer_token": bool(service.bearer_token),
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


# ==================== TWEET CREATION ENDPOINTS ====================


@router.post("/tweets", summary="Create a tweet")
async def create_tweet(request: CreateTweetRequest):
    """
    Create a new tweet.

    **Free Tier Limit**: 1,500 posts per month

    This endpoint allows you to:
    - Create a simple tweet
    - Reply to an existing tweet
    - Quote tweet (retweet with comment)
    - Create a poll

    **Requirements**:
    - OAuth 1.0a User Context credentials must be configured
    - Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET in .env

    **Examples**:

    Simple tweet:
    ```json
    {
        "text": "¡Hola mundo! 👋"
    }
    ```

    Reply to a tweet:
    ```json
    {
        "text": "¡Gracias por tu comentario!",
        "reply_to_tweet_id": "1973729560794665200"
    }
    ```

    Quote tweet:
    ```json
    {
        "text": "¡Totalmente de acuerdo con esto!",
        "quote_tweet_id": "1973729560794665200"
    }
    ```

    Tweet with poll:
    ```json
    {
        "text": "¿Cuál prefieres?",
        "poll_options": ["Opción A", "Opción B", "Opción C"],
        "poll_duration_minutes": 1440
    }
    ```

    **Returns**: Created tweet data with ID, URL, and quota information
    """
    try:
        service = get_x_api_service()
        result = await service.create_tweet(
            text=request.text,
            reply_to_tweet_id=request.reply_to_tweet_id,
            quote_tweet_id=request.quote_tweet_id,
            poll_options=request.poll_options,
            poll_duration_minutes=request.poll_duration_minutes,
        )

        return {
            "success": True,
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/tweets/{tweet_id}", summary="Delete a tweet")
async def delete_tweet(tweet_id: str):
    """
    Delete a tweet.

    **Note**: You can only delete tweets that you posted.

    **Free Tier**: Deletions do not count towards the 1,500 posts/month limit.

    **Requirements**:
    - OAuth 1.0a User Context credentials must be configured

    **Parameters**:
    - **tweet_id**: The ID of the tweet to delete

    **Returns**: Deletion confirmation
    """
    try:
        service = get_x_api_service()
        result = await service.delete_tweet(tweet_id)

        return {
            "success": True,
            "data": result,
        }

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/retweets", summary="Retweet a tweet")
async def retweet(request: RetweetRequest):
    """
    Retweet a tweet.

    **Free Tier Limit**: Counts towards the 1,500 posts/month limit

    **Requirements**:
    - OAuth 1.0a User Context credentials must be configured

    **Example**:
    ```json
    {
        "user_id": "1973607890520084480",
        "tweet_id": "1973729560794665200"
    }
    ```

    **Returns**: Retweet confirmation with quota information
    """
    try:
        service = get_x_api_service()
        result = await service.retweet(user_id=request.user_id, tweet_id=request.tweet_id)

        return {
            "success": True,
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/retweets/{user_id}/{tweet_id}", summary="Remove a retweet")
async def unretweet(user_id: str, tweet_id: str):
    """
    Remove a retweet (undo retweet).

    **Free Tier**: Does not count towards the 1,500 posts/month limit

    **Parameters**:
    - **user_id**: Your user ID
    - **tweet_id**: ID of the tweet to unretweet

    **Returns**: Unretweet confirmation
    """
    try:
        service = get_x_api_service()
        result = await service.unretweet(user_id=user_id, tweet_id=tweet_id)

        return {
            "success": True,
            "data": result,
        }

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/likes", summary="Like a tweet")
async def like_tweet(request: LikeRequest):
    """
    Like a tweet.

    **Free Tier**: Does not count towards the 1,500 posts/month limit

    **Requirements**:
    - OAuth 1.0a User Context credentials must be configured

    **Example**:
    ```json
    {
        "user_id": "1973607890520084480",
        "tweet_id": "1973729560794665200"
    }
    ```

    **Returns**: Like confirmation
    """
    try:
        service = get_x_api_service()
        result = await service.like_tweet(user_id=request.user_id, tweet_id=request.tweet_id)

        return {
            "success": True,
            "data": result,
        }

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/likes/{user_id}/{tweet_id}", summary="Unlike a tweet")
async def unlike_tweet(user_id: str, tweet_id: str):
    """
    Remove a like from a tweet (unlike).

    **Free Tier**: Does not count towards the 1,500 posts/month limit

    **Parameters**:
    - **user_id**: Your user ID
    - **tweet_id**: ID of the tweet to unlike

    **Returns**: Unlike confirmation
    """
    try:
        service = get_x_api_service()
        result = await service.unlike_tweet(user_id=user_id, tweet_id=tweet_id)

        return {
            "success": True,
            "data": result,
        }

    except XAPIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/quota", summary="Check posting quota")
async def get_posting_quota():
    """
    Check your posting quota status.

    **Free Tier**: 1,500 posts per month

    This includes:
    - Creating tweets
    - Replying to tweets
    - Quote tweets
    - Retweets

    This does NOT include:
    - Deleting tweets
    - Liking/unliking tweets
    - Unretweeting

    **Note**: The counter is per service instance. For production, implement
    persistent quota tracking using a database.

    **Returns**: Current quota usage and remaining posts
    """
    try:
        service = get_x_api_service()
        return {
            "success": True,
            "posts_used": service.posts_created,
            "posts_remaining": service.max_posts_per_month - service.posts_created,
            "max_posts_per_month": service.max_posts_per_month,
            "can_post": service.can_post(),
            "note": "Counter is per service instance. Implement persistent tracking for production.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
