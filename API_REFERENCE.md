# API Quick Reference

## 🔐 Authentication Endpoints (NEW)

### OAuth Meta

- `GET /auth/meta/login` - Initiate Meta OAuth flow (redirect to Facebook)
- `GET /auth/meta/callback` - Meta callback (automatic) - receives authorization code
- `GET /auth/meta/status` - Check if Meta credentials are stored

**Quick Start**:
1. Open in browser: `http://localhost:8000/auth/meta/login`
2. Authorize in Meta/Facebook
3. Check status: `curl http://localhost:8000/auth/meta/status`

**For detailed guide see**: [META_OAUTH_SETUP.md](META_OAUTH_SETUP.md)

---

## Endpoints

### Health & Documentation

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

### Comment Management

- `POST /comments/` - Create new comment
- `GET /comments/` - List comments (supports filtering and pagination)
  - Query params: `skip`, `limit`, `platform`
- `GET /comments/{id}` - Get comment by ID

### Data Ingestion

- `POST /ingest/meta/{post_id}` - Ingest Meta comments
- `POST /ingest/x/{tweet_id}` - Ingest X replies
- `POST /ingest/tripadvisor/{location_id}` - Ingest TripAdvisor reviews

### X (Twitter) API v2 - Free Tier

#### Tweet Lookup

- `GET /x/tweets/{tweet_id}` - Get single tweet by ID
  - Query params: `include_author`, `include_metrics`
- `POST /x/tweets/batch` - Get multiple tweets (up to 100)
  - Body: `{"tweet_ids": [...], "include_author": true, "include_metrics": true}`
- `GET /x/tweets/parse-url` - Extract tweet ID from URL
  - Query param: `url`

#### User Lookup

- `GET /x/users/{user_id}` - Get user by ID
  - Query param: `include_metrics`
- `GET /x/users/by-username/{username}` - Get user by username
  - Query param: `include_metrics`
- `POST /x/users/batch` - Get multiple users (up to 100)
  - Body: `{"user_ids": [...]}` OR `{"usernames": [...]}`

#### User Timeline

- `GET /x/users/{user_id}/tweets` - Get user's tweets
  - Query params: `max_results`, `exclude_retweets`, `exclude_replies`, `pagination_token`

#### Utility

- `GET /x/health` - Check X API service configuration

## Quick Start

### Linux/Mac

```bash
./start.sh
```

### Windows

```cmd
start.bat
```

### Manual Start

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Example Requests

### Ingest Data

```bash
# Meta
curl -X POST http://localhost:8000/ingest/meta/post_123

# X (Twitter)
curl -X POST http://localhost:8000/ingest/x/tweet_456

# TripAdvisor
curl -X POST http://localhost:8000/ingest/tripadvisor/location_789
```

### X API Direct Access (Free Tier)

#### Get Single Tweet

```bash
curl "http://localhost:8000/x/tweets/1234567890?include_author=true&include_metrics=true"
```

#### Get Multiple Tweets

```bash
curl -X POST http://localhost:8000/x/tweets/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tweet_ids": ["1234567890", "0987654321"],
    "include_author": true,
    "include_metrics": true
  }'
```

#### Parse Tweet URL

```bash
curl "http://localhost:8000/x/tweets/parse-url?url=https://twitter.com/user/status/1234567890"
```

#### Get User by ID

```bash
curl "http://localhost:8000/x/users/12345678?include_metrics=true"
```

#### Get User by Username

```bash
curl "http://localhost:8000/x/users/by-username/elonmusk?include_metrics=true"
```

#### Get User's Tweets

```bash
curl "http://localhost:8000/x/users/12345678/tweets?max_results=10&exclude_retweets=true"
```

#### Get Multiple Users

```bash
curl -X POST http://localhost:8000/x/users/batch \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": ["elonmusk", "jack"],
    "include_metrics": true
  }'
```

### Query Comments

```bash
# All comments
curl http://localhost:8000/comments/

# Filtered by platform
curl http://localhost:8000/comments/?platform=meta

# With pagination
curl http://localhost:8000/comments/?skip=0&limit=10
```

### Create Comment

```bash
curl -X POST http://localhost:8000/comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "meta",
    "platform_id": "unique_123",
    "author": "John Doe",
    "content": "This is a test comment",
    "post_url": "https://example.com/post/123"
  }'
```

## Configuration

Edit `.env` file to configure:

- Database URL
- API credentials for Meta, X, and TripAdvisor
- App settings

### X API Configuration

To use the X API endpoints, you need to:

1. **Create a Developer Account**: Sign up at [developer.x.com](https://developer.x.com/)

2. **Create an App**:

   - Go to the Developer Portal
   - Create a new Project and App
   - Generate Bearer Token

3. **Add to `.env` file**:

   ```bash
   X_BEARER_TOKEN=your_bearer_token_here
   ```

4. **Free Tier Limitations**:

   - **100 reads per month** at the app level
   - 1,500 posts per month (if you want to create posts)
   - Access to basic v2 endpoints
   - No access to search or filtered stream APIs

5. **Recommended Usage**:

   - Use batch endpoints to fetch multiple items in one request
   - Track your API usage to stay within the 100 reads/month limit
   - Each API call counts as 1 read (regardless of how many items you fetch in batch)

6. **Available Fields**:
   - **Tweet Fields**: `id`, `text`, `created_at`, `author_id`, `conversation_id`, `public_metrics`, `lang`
   - **User Fields**: `id`, `name`, `username`, `description`, `verified`, `profile_image_url`, `public_metrics`, `created_at`
   - **Public Metrics**: `like_count`, `retweet_count`, `reply_count`, `quote_count` (for tweets)
   - **User Metrics**: `followers_count`, `following_count`, `tweet_count`, `listed_count`

## Testing

Run the automated test suite:

```bash
python test_api.py
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Next Steps

1. Configure real API credentials in `.env`
2. Implement actual API calls in `app/services/ingestion_service.py`
3. Add authentication/authorization if needed
4. Deploy to production (consider using PostgreSQL instead of SQLite)
