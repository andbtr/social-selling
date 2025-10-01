# API Quick Reference

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
