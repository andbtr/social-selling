# Social Listening Platform

A platform for ingesting, analyzing and monitoring comments from social media (Instagram, Facebook, Twitter, TripAdvisor) in real-time.

## 📋 What does it do?

- **Connects** with Meta (Instagram/Facebook) via OAuth2
- **Ingests** comments automatically
- **Analyzes** sentiment (positive/negative/neutral) with NLP
- **Detects** comment intention
- **Exposes** a REST API to query and filter

---

## 🚀 Quick Start: Run Locally

### Requirements

- Python 3.10+
- pip
- Git

### Installation (5 minutes)

```bash
# 1. Clone repo
git clone <your-repo>
cd social-selling

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: .\venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure .env
cp .env.example .env
# Edit .env with your credentials (Meta API, etc)

# 5. Database
alembic upgrade head

# 6. Ready! Start the server
uvicorn main:app --reload
```

**Server will be at**: `http://127.0.0.1:8000`

---

## 🔌 Main Endpoints

### Health Check
```bash
curl http://127.0.0.1:8000/health
# {"status": "healthy"}
```

### Meta Authentication (OAuth)
```bash
# Start authentication flow
http://127.0.0.1:8000/auth/meta/login

# Check if authenticated
curl http://127.0.0.1:8000/auth/meta/status
```

### Comments
```bash
# List comments
GET /comments?skip=0&limit=100&platform=instagram

# Get a comment
GET /comments/1

# Create comment (test)
POST /comments
Body: {"platform": "instagram", "platform_id": "123", "author": "user", "content": "text"}

# Update
PUT /comments/1

# Delete
DELETE /comments/1
```

### Ingest Data
```bash
# Fetch Instagram comments
POST /ingest/instagram/comments

# Fetch Facebook posts
POST /ingest/facebook/posts
```

### Interactive Documentation
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 🔐 Setup Meta OAuth (Required)

### In Meta Developer Console

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create an app → type "Consumer"
3. Add product: **Facebook Login**
4. Go to: Facebook Login → Settings
5. In **Valid OAuth Redirect URIs** add:
   ```
   http://localhost:8000/auth/meta/callback
   ```
6. Go to: Settings → Basic
7. Copy **App ID** and **App Secret**

### In your `.env`
```env
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_REDIRECT_URI=http://localhost:8000/auth/meta/callback
```

### Test OAuth
```bash
# 1. Open in browser
http://127.0.0.1:8000/auth/meta/login

# 2. Login with your Meta account
# 3. Approve permissions
# 4. Done, token encrypted and saved in DB
```

---

## 📁 Project Structure

```
app/
├── api/                 # HTTP routes
│   ├── auth.py         # OAuth2
│   ├── comments.py     # Comments CRUD
│   ├── ingestion.py    # Fetch data from APIs
│   └── ...
│
├── services/           # Business logic
│   ├── comment_service.py
│   ├── meta_auth_service.py
│   ├── sentiment_service.py  # NLP analysis
│   ├── ingestion_service.py
│   └── ...
│
├── models/             # DB models (SQLAlchemy)
│   ├── comment.py
│   ├── post.py
│   └── ...
│
├── schemas/            # Data validation (Pydantic)
│   ├── comment.py
│   └── ...
│
├── core/
│   ├── config.py       # Environment variables
│   └── database.py     # DB connection
│
└── seeders/            # Test data
```

---

## 🗄️ Database

**Default**: SQLite (`social_listening.db`)
**Production**: PostgreSQL (configure in `.env`)

### Useful Commands

```bash
# Apply migrations
alembic upgrade head

# Generate migration (after changing models)
alembic revision --autogenerate -m "Description"

# Rollback last migration
alembic downgrade -1

# Reset DB (⚠️ deletes everything)
python -m app.reset_db

# Fill with test data
python -m app.seed
```

---

## 🧪 Development

### Typical Workflow

```bash
# Activate environment
source venv/bin/activate

# Start server (with auto-reload)
uvicorn main:app --reload

# In another terminal, test endpoints
curl http://127.0.0.1:8000/health

# If you edited models, create migration
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Tests
```bash
pytest -v
pytest tests/api -v
pytest -k "oauth" -v
```

---

## 🐛 Common Issues

### "Address already in use" (port 8000)
```bash
# Change port
uvicorn main:app --reload --port 8001
```

### OAuth says "Invalid redirect URI"
- Make sure it's set in Meta Console as:
  ```
  http://localhost:8000/auth/meta/callback
  ```
- No trailing slash
- Exactly same as in `.env`

### "No Meta credentials found"
- You haven't authenticated yet
- Visit: `http://127.0.0.1:8000/auth/meta/login`
- Login and approve permissions

### "No module named 'app'"
```bash
# Make sure you're in the root folder
cd /home/ander/Projects/social-selling
source venv/bin/activate
```

---

## 📦 Main Dependencies

- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation
- **Transformers** - NLP models
- **httpx** - Async HTTP client
- **python-multipart** - Form handling

---

## 🚀 Next Steps

- [ ] Setup Meta OAuth
- [ ] Run server locally
- [ ] Ingest first comments
- [ ] Verify sentiment analysis
- [ ] Make code changes

---

## 📞 Help

- **Interactive Swagger**: http://127.0.0.1:8000/docs
- **Server logs**: Shown in terminal where `uvicorn` is running
- **SQLite database**: `sqlite3 social_listening.db` to inspect

