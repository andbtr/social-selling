"""
Test script for X API Service

This script demonstrates how to use the X API service endpoints.
Run the API server first: uvicorn main:app --reload
"""

import httpx
import asyncio
from typing import List, Dict, Any


BASE_URL = "http://localhost:8000"


async def test_health():
    """Test the X API health endpoint."""
    print("\n=== Testing X API Health ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/x/health")
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
        return result


async def test_parse_tweet_url():
    """Test parsing a tweet URL."""
    print("\n=== Testing Tweet URL Parser ===")
    test_url = "https://twitter.com/elonmusk/status/1234567890"

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/x/tweets/parse-url", params={"url": test_url})
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"URL: {test_url}")
        print(f"Extracted ID: {result.get('tweet_id')}")
        return result


async def test_get_tweet(tweet_id: str):
    """Test getting a single tweet."""
    print(f"\n=== Testing Get Tweet: {tweet_id} ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/x/tweets/{tweet_id}",
            params={"include_author": True, "include_metrics": True},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            # Display formatted tweet
            formatted = result.get("formatted", {})
            print(f"\nTweet Details:")
            print(f"  ID: {formatted.get('id')}")
            print(f"  Author: {formatted.get('author_name')} (@{formatted.get('author_username')})")
            print(f"  Text: {formatted.get('text')}")
            print(f"  Created: {formatted.get('created_at')}")
            print(f"  Metrics: {formatted.get('public_metrics')}")
            print(f"  URL: {formatted.get('url')}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")

        return response


async def test_get_tweets_batch(tweet_ids: List[str]):
    """Test getting multiple tweets in one request."""
    print(f"\n=== Testing Get Tweets Batch ({len(tweet_ids)} tweets) ===")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/tweets/batch",
            json={"tweet_ids": tweet_ids, "include_author": True, "include_metrics": True},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"Count: {result.get('count')} tweets retrieved")

            # Display brief info about each tweet
            tweets = result.get("data", {}).get("data", [])
            for tweet in tweets[:3]:  # Show first 3
                print(f"\n  Tweet {tweet.get('id')}:")
                print(f"    Text: {tweet.get('text', '')[:60]}...")
                print(f"    Author ID: {tweet.get('author_id')}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")

        return response


async def test_get_user_by_username(username: str):
    """Test getting a user by username."""
    print(f"\n=== Testing Get User by Username: @{username} ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/x/users/by-username/{username}", params={"include_metrics": True}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            user = result.get("data", {}).get("data", {})
            print(f"\nUser Details:")
            print(f"  ID: {user.get('id')}")
            print(f"  Name: {user.get('name')}")
            print(f"  Username: @{user.get('username')}")
            print(f"  Verified: {user.get('verified')}")
            print(f"  Description: {user.get('description', '')[:100]}...")
            print(f"  Created: {user.get('created_at')}")
            print(f"  Metrics: {user.get('public_metrics')}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")

        return response


async def test_get_user_by_id(user_id: str):
    """Test getting a user by ID."""
    print(f"\n=== Testing Get User by ID: {user_id} ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/x/users/{user_id}", params={"include_metrics": True}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            user = result.get("data", {}).get("data", {})
            print(f"\nUser Details:")
            print(f"  ID: {user.get('id')}")
            print(f"  Name: {user.get('name')}")
            print(f"  Username: @{user.get('username')}")
            print(f"  Verified: {user.get('verified')}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")

        return response


async def test_get_users_batch(usernames: List[str]):
    """Test getting multiple users by username."""
    print(f"\n=== Testing Get Users Batch ({len(usernames)} users) ===")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/users/batch", json={"usernames": usernames, "include_metrics": True}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"Count: {result.get('count')} users retrieved")

            users = result.get("data", {}).get("data", [])
            for user in users:
                print(f"\n  @{user.get('username')}:")
                print(f"    Name: {user.get('name')}")
                print(f"    ID: {user.get('id')}")
                print(f"    Verified: {user.get('verified')}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")

        return response


async def test_get_user_tweets(user_id: str, max_results: int = 10):
    """Test getting a user's tweets."""
    print(f"\n=== Testing Get User Tweets: {user_id} ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/x/users/{user_id}/tweets",
            params={
                "max_results": max_results,
                "exclude_retweets": False,
                "exclude_replies": False,
            },
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"Count: {result.get('count')} tweets retrieved")

            tweets = result.get("data", {}).get("data", [])
            for tweet in tweets[:3]:  # Show first 3
                print(f"\n  Tweet {tweet.get('id')}:")
                print(f"    Text: {tweet.get('text', '')[:60]}...")
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")

        return response


async def test_create_tweet(text: str):
    """Test creating a simple tweet."""
    print(f"\n=== Testing Create Tweet ===")
    print(f"Text: {text}")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/x/tweets", json={"text": text})

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            data = result.get("data", {}).get("data", {})
            print(f"\nTweet Created:")
            print(f"  ID: {data.get('id')}")
            print(f"  Text: {data.get('text')}")
            print(f"  URL: {result.get('data', {}).get('tweet_url')}")
            print(f"  Posts used: {result.get('data', {}).get('posts_used')}")
            print(f"  Posts remaining: {result.get('data', {}).get('posts_remaining')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_reply_to_tweet(tweet_id: str, reply_text: str):
    """Test replying to a tweet."""
    print(f"\n=== Testing Reply to Tweet ===")
    print(f"Reply to: {tweet_id}")
    print(f"Text: {reply_text}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/tweets", json={"text": reply_text, "reply_to_tweet_id": tweet_id}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            data = result.get("data", {}).get("data", {})
            print(f"\nReply Created:")
            print(f"  ID: {data.get('id')}")
            print(f"  URL: {result.get('data', {}).get('tweet_url')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_quote_tweet(tweet_id: str, quote_text: str):
    """Test quote tweeting."""
    print(f"\n=== Testing Quote Tweet ===")
    print(f"Quote: {tweet_id}")
    print(f"Text: {quote_text}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/tweets", json={"text": quote_text, "quote_tweet_id": tweet_id}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            data = result.get("data", {}).get("data", {})
            print(f"\nQuote Tweet Created:")
            print(f"  ID: {data.get('id')}")
            print(f"  URL: {result.get('data', {}).get('tweet_url')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_create_poll(text: str, options: List[str], duration: int = 1440):
    """Test creating a tweet with a poll."""
    print(f"\n=== Testing Create Poll ===")
    print(f"Text: {text}")
    print(f"Options: {options}")
    print(f"Duration: {duration} minutes")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/tweets",
            json={"text": text, "poll_options": options, "poll_duration_minutes": duration},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")

            data = result.get("data", {}).get("data", {})
            print(f"\nPoll Created:")
            print(f"  ID: {data.get('id')}")
            print(f"  URL: {result.get('data', {}).get('tweet_url')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_delete_tweet(tweet_id: str):
    """Test deleting a tweet."""
    print(f"\n=== Testing Delete Tweet ===")
    print(f"Tweet ID: {tweet_id}")

    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{BASE_URL}/x/tweets/{tweet_id}")

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"Deleted: {result.get('data', {}).get('data', {}).get('deleted')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_retweet(user_id: str, tweet_id: str):
    """Test retweeting."""
    print(f"\n=== Testing Retweet ===")
    print(f"User ID: {user_id}")
    print(f"Tweet ID: {tweet_id}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/retweets", json={"user_id": user_id, "tweet_id": tweet_id}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"Retweeted: {result.get('data', {}).get('data', {}).get('retweeted')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_like_tweet(user_id: str, tweet_id: str):
    """Test liking a tweet."""
    print(f"\n=== Testing Like Tweet ===")
    print(f"User ID: {user_id}")
    print(f"Tweet ID: {tweet_id}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/x/likes", json={"user_id": user_id, "tweet_id": tweet_id}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"Liked: {result.get('data', {}).get('data', {}).get('liked')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def test_get_quota():
    """Test getting the posting quota."""
    print(f"\n=== Testing Get Posting Quota ===")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/x/quota")

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Success: {result.get('success')}")
            print(f"\nQuota Status:")
            print(f"  Posts used: {result.get('posts_used')}")
            print(f"  Posts remaining: {result.get('posts_remaining')}")
            print(f"  Max per month: {result.get('max_posts_per_month')}")
            print(f"  Can post: {result.get('can_post')}")

            return result
        else:
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
            return None


async def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("X API Service Test Suite")
    print("=" * 60)
    print("\nNOTE: These tests use the X API and count towards your")
    print("100 reads/month limit. Adjust the test data as needed.")
    print("=" * 60)

    try:
        # Test health check (doesn't count as a read)
        await test_health()

        # Test URL parser (doesn't count as a read)
        await test_parse_tweet_url()

        # ===== IMPORTANT =====
        # The tests below will use your API quota!
        # Comment them out or use test data that exists

        print("\n" + "=" * 60)
        print("LIVE API TESTS (Uses API quota)")
        print("=" * 60)
        print("\nTo run live tests, replace the IDs below with real")
        print("tweet IDs and user IDs/usernames, then uncomment the tests.")
        print("\nExample real IDs you could use:")
        print("  - Tweet ID: Any public tweet ID from X.com")
        print("  - Username: elonmusk, jack, X, etc.")
        print("  - User ID: 44196397 (Elon Musk), 12 (Jack), etc.")

        # Uncomment and modify these tests with real data:

        # # Test getting a single tweet (1 read)
        # await test_get_tweet("1234567890123456789")

        # # Test getting multiple tweets (1 read for all)
        # await test_get_tweets_batch([
        #     "1234567890123456789",
        #     "9876543210987654321"
        # ])

        # # Test getting user by username (1 read)
        # await test_get_user_by_username("elonmusk")

        # # Test getting user by ID (1 read)
        # await test_get_user_by_id("44196397")

        # # Test getting multiple users (1 read)
        # await test_get_users_batch(["elonmusk", "jack"])

        # # Test getting user tweets (1 read)
        # await test_get_user_tweets("44196397", max_results=10)

        print("\n" + "=" * 60)
        print("POSTING TESTS (Uses posting quota - 1,500/month)")
        print("=" * 60)
        print("\nTo run posting tests, you need OAuth 1.0a credentials:")
        print("  - X_API_KEY")
        print("  - X_API_SECRET")
        print("  - X_ACCESS_TOKEN")
        print("  - X_ACCESS_TOKEN_SECRET")
        print("\nUncomment the tests below to try them:")

        # # Check posting quota first
        # await test_get_quota()

        # # Test creating a simple tweet (1 post)
        # tweet_result = await test_create_tweet("¡Hola desde la API! 🚀 #Testing")
        # if tweet_result:
        #     tweet_id = tweet_result.get("data", {}).get("data", {}).get("id")
        #
        #     # Test replying to your own tweet (1 post)
        #     await test_reply_to_tweet(tweet_id, "Y esta es una respuesta automática! 💬")
        #
        #     # Test deleting the tweet (doesn't count as post)
        #     await test_delete_tweet(tweet_id)

        # # Test quote tweet (1 post)
        # await test_quote_tweet("1973729560794665200", "¡Interesante contenido! 👍")

        # # Test creating a poll (1 post)
        # await test_create_poll(
        #     "¿Cuál es tu favorito?",
        #     ["Opción A", "Opción B", "Opción C"],
        #     duration=1440
        # )

        # # Test retweet (1 post)
        # await test_retweet("YOUR_USER_ID", "1973729560794665200")

        # # Test like (doesn't count as post)
        # await test_like_tweet("YOUR_USER_ID", "1973729560794665200")

        # # Check quota again
        # await test_get_quota()

        print("\n" + "=" * 60)
        print("Tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main entry point."""
    print("\nMake sure the API server is running:")
    print("  uvicorn main:app --reload\n")

    asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
