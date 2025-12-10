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

### Meta Authentication (OAuth)
```bash
# Start authentication flow
http://127.0.0.1:8000/auth/meta/login

# Check if authenticated
curl http://127.0.0.1:8000/auth/meta/status
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


