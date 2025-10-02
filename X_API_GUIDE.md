# X (Twitter) API Service Documentation

This service provides access to X API v2 with support for the **Free Tier** (100 reads/month).

## Table of Contents

- [Setup](#setup)
- [Free Tier Limitations](#free-tier-limitations)
- [Available Endpoints](#available-endpoints)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Setup

### 1. Create X Developer Account

1. Go to [developer.x.com](https://developer.x.com/)
2. Sign up or log in with your X account
3. Apply for a developer account (free tier)

### 2. Create an App and Get Bearer Token

1. In the Developer Portal, create a new **Project**
2. Create an **App** within that project
3. Go to your App's "Keys and Tokens" section
4. Generate a **Bearer Token** (for read operations)
5. Generate **API Key & Secret** and **Access Token & Secret** (for write operations)
6. Copy all tokens (you won't be able to see them again)

### 3. Configure Environment Variables

Add all tokens to your `.env` file:

```bash
# For read operations (required)
X_BEARER_TOKEN=your_bearer_token_here

# For write operations (optional - only if you want to post tweets)
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### 4. Verify Configuration

Test that the service is configured correctly:

```bash
curl http://localhost:8000/x/health
```

## Free Tier Limitations

The X API Free Tier provides:

- ✅ **100 reads per month** (app level)
- ✅ 1,500 posts per month (write operations)
- ✅ Access to tweet lookup endpoints
- ✅ Access to user lookup endpoints
- ✅ Access to user timeline (limited)
- ❌ No search API access
- ❌ No filtered stream API
- ❌ No full-archive search

### What Counts as a "Read"?

Each API request counts as **1 read**, regardless of:

- How many items you fetch in a batch request (e.g., 100 tweets in one request = 1 read)
- What fields you request
- Whether you use expansions

**Pro Tip**: Use batch endpoints to maximize efficiency!

## Available Endpoints

### Tweet Endpoints

#### Get Single Tweet

```http
GET /x/tweets/{tweet_id}
```

**Parameters:**

- `tweet_id` (path): The tweet ID
- `include_author` (query, optional): Include author info (default: true)
- `include_metrics` (query, optional): Include engagement metrics (default: true)

**Response:**

```json
{
  "success": true,
  "data": {
    "data": {
      "id": "1234567890",
      "text": "Hello, world!",
      "created_at": "2024-01-01T12:00:00.000Z",
      "author_id": "987654321",
      "public_metrics": {
        "like_count": 42,
        "retweet_count": 10,
        "reply_count": 5,
        "quote_count": 2
      }
    },
    "includes": {
      "users": [
        {
          "id": "987654321",
          "username": "example_user",
          "name": "Example User",
          "verified": false
        }
      ]
    }
  }
}
```

#### Get Multiple Tweets

```http
POST /x/tweets/batch
```

**Request Body:**

```json
{
  "tweet_ids": ["1234567890", "0987654321"],
  "include_author": true,
  "include_metrics": true
}
```

**Benefits:** Fetch up to 100 tweets with just **1 read**!

#### Parse Tweet URL

```http
GET /x/tweets/parse-url?url={tweet_url}
```

Extracts tweet ID from various URL formats:

- `https://twitter.com/user/status/1234567890`
- `https://x.com/user/status/1234567890`

#### Create Tweet (NEW!)

```http
POST /x/tweets
```

**Request Body:**

```json
{
  "text": "¡Hola mundo! 👋",
  "reply_to_tweet_id": "1234567890",
  "quote_tweet_id": "9876543210",
  "poll_options": ["Option A", "Option B"],
  "poll_duration_minutes": 1440
}
```

**Free Tier Limit:** 1,500 posts/month

**Examples:**

Simple tweet:

```json
{
  "text": "¡Hola desde la API! 🚀"
}
```

Reply to tweet:

```json
{
  "text": "¡Gracias por compartir!",
  "reply_to_tweet_id": "1234567890"
}
```

Quote tweet:

```json
{
  "text": "¡Totalmente de acuerdo!",
  "quote_tweet_id": "1234567890"
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

#### Delete Tweet (NEW!)

```http
DELETE /x/tweets/{tweet_id}
```

**Note:** Only works for your own tweets. Doesn't count towards posting limit.

### User Endpoints

#### Get User by ID

```http
GET /x/users/{user_id}
```

#### Get User by Username

```http
GET /x/users/by-username/{username}
```

#### Get Multiple Users

```http
POST /x/users/batch
```

**Request Body (by usernames):**

```json
{
  "usernames": ["elonmusk", "jack"],
  "include_metrics": true
}
```

**Request Body (by IDs):**

```json
{
  "user_ids": ["44196397", "12"],
  "include_metrics": true
}
```

### Timeline Endpoints

#### Get User's Tweets

```http
GET /x/users/{user_id}/tweets
```

**Parameters:**

- `max_results`: Number of tweets (5-100)
- `exclude_retweets`: Filter out retweets
- `exclude_replies`: Filter out replies
- `pagination_token`: For pagination

**Note:** This endpoint may have limited availability on Free tier.

### Engagement Endpoints (NEW!)

#### Retweet

```http
POST /x/retweets
```

**Request Body:**

```json
{
  "user_id": "YOUR_USER_ID",
  "tweet_id": "1234567890"
}
```

**Counts towards:** 1,500 posts/month limit

#### Remove Retweet

```http
DELETE /x/retweets/{user_id}/{tweet_id}
```

**Doesn't count** towards posting limit.

#### Like Tweet

```http
POST /x/likes
```

**Request Body:**

```json
{
  "user_id": "YOUR_USER_ID",
  "tweet_id": "1234567890"
}
```

**Doesn't count** towards posting limit.

#### Unlike Tweet

```http
DELETE /x/likes/{user_id}/{tweet_id}
```

**Doesn't count** towards posting limit.

### Quota Endpoint (NEW!)

#### Check Posting Quota

```http
GET /x/quota
```

**Response:**

```json
{
  "success": true,
  "posts_used": 5,
  "posts_remaining": 1495,
  "max_posts_per_month": 1500,
  "can_post": true
}
```

## Usage Examples

### Python Example

```python
import httpx

# Get a tweet
async def get_tweet(tweet_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/x/tweets/{tweet_id}",
            params={
                "include_author": True,
                "include_metrics": True
            }
        )
        return response.json()

# Get multiple tweets efficiently
async def get_tweets_batch(tweet_ids: list):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/x/tweets/batch",
            json={
                "tweet_ids": tweet_ids,
                "include_author": True,
                "include_metrics": True
            }
        )
        return response.json()
```

### JavaScript Example

```javascript
// Get a user by username
async function getUserByUsername(username) {
  const response = await fetch(
    `http://localhost:8000/x/users/by-username/${username}?include_metrics=true`
  );
  return response.json();
}

// Get multiple users
async function getMultipleUsers(usernames) {
  const response = await fetch("http://localhost:8000/x/users/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      usernames: usernames,
      include_metrics: true,
    }),
  });
  return response.json();
}
```

### cURL Examples

```bash
# Get a tweet with full details
curl "http://localhost:8000/x/tweets/1234567890?include_author=true&include_metrics=true"

# Get 10 tweets in one request (1 read!)
curl -X POST http://localhost:8000/x/tweets/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tweet_ids": ["123", "456", "789", "012", "345", "678", "901", "234", "567", "890"],
    "include_author": true,
    "include_metrics": true
  }'

# Extract tweet ID from URL
curl "http://localhost:8000/x/tweets/parse-url?url=https://twitter.com/user/status/1234567890"

# Get user by username
curl "http://localhost:8000/x/users/by-username/elonmusk?include_metrics=true"

# Get user's tweets
curl "http://localhost:8000/x/users/44196397/tweets?max_results=20&exclude_retweets=true"
```

## Best Practices

### 1. Use Batch Endpoints

✅ **Do:** Fetch 100 tweets in one request (1 read)

```python
get_tweets_batch(["id1", "id2", ..., "id100"])  # 1 read
```

❌ **Don't:** Fetch tweets one at a time

```python
for tweet_id in tweet_ids:  # 100 reads!
    get_tweet(tweet_id)
```

### 2. Cache Results

Store results in your database to avoid re-fetching:

```python
# Check database first
tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
if not tweet:
    # Only fetch if not cached
    tweet_data = await get_tweet(tweet_id)
    tweet = save_to_db(tweet_data)
```

### 3. Track API Usage

Keep a counter of your API calls to stay within the 100 reads/month limit:

```python
class APIUsageTracker:
    def __init__(self):
        self.reads_this_month = 0
        self.max_reads = 100

    def can_make_request(self):
        return self.reads_this_month < self.max_reads

    def increment(self):
        self.reads_this_month += 1
```

### 4. Use Local Operations When Possible

Some endpoints don't count against your limit:

- ✅ `/x/health` - Health check
- ✅ `/x/tweets/parse-url` - URL parsing (local operation)

### 5. Handle Rate Limits Gracefully

```python
try:
    result = await get_tweet(tweet_id)
except XAPIException as e:
    if "rate limit" in str(e).lower():
        # Wait until next month or upgrade plan
        print("Rate limit reached. Try again next month.")
    else:
        raise
```

## Troubleshooting

### Error: "X_BEARER_TOKEN is required"

**Solution:** Add your Bearer Token to the `.env` file:

```bash
X_BEARER_TOKEN=your_actual_bearer_token_here
```

### Error: "401 Unauthorized"

**Possible causes:**

1. Invalid Bearer Token
2. Token has been revoked
3. App doesn't have the required permissions

**Solution:**

- Regenerate your Bearer Token in the Developer Portal
- Ensure you copied the entire token
- Check that your app has the correct access level

### Error: "429 Too Many Requests"

**Cause:** You've exceeded the 100 reads/month limit.

**Solutions:**

1. Wait until the next month (limits reset monthly)
2. Upgrade to Basic ($200/month) for 10,000 reads
3. Use cached data from previous requests

### Error: "403 Forbidden"

**Possible causes:**

1. Trying to access an endpoint not available on Free tier
2. Requesting a tweet that doesn't exist or is private
3. User account is suspended or deleted

**Solution:**

- Check X API documentation for endpoint availability
- Verify the tweet/user ID is correct and public

### No data returned

**Check:**

1. Is the tweet ID correct?
2. Is the tweet public?
3. Has the tweet been deleted?
4. Try accessing the tweet directly on X.com to verify it exists

## API Response Structure

### Standard Success Response

```json
{
  "success": true,
  "data": {
    /* X API response */
  }
}
```

### Standard Error Response

```json
{
  "detail": "Error message here"
}
```

## Additional Resources

- [X API Documentation](https://developer.x.com/en/docs/twitter-api)
- [X API v2 Data Dictionary](https://developer.x.com/en/docs/twitter-api/data-dictionary)
- [X API Rate Limits](https://developer.x.com/en/docs/twitter-api/rate-limits)
- [X Developer Portal](https://developer.x.com/en/portal/dashboard)

## Support

For issues with:

- **This implementation**: Check the main project README or create an issue
- **X API itself**: Visit [X Developer Community](https://twittercommunity.com/)
- **X Developer Portal**: Contact X Developer Support

## Upgrade Options

If you need more than 100 reads/month, consider upgrading:

| Tier  | Price  | Reads/Month |
| ----- | ------ | ----------- |
| Free  | $0     | 100         |
| Basic | $200   | 10,000      |
| Pro   | $5,000 | 1,000,000   |

Visit [X API Pricing](https://developer.x.com/en/products/twitter-api) for details.
