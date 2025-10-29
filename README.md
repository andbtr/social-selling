# Social Listening Platform

A comprehensive platform for ingesting, analyzing, and monitoring comments from multiple social media platforms (Meta, X, TripAdvisor) in real-time. Built with FastAPI and powered by NLP models for sentiment and intention analysis.

## 🎯 What This Project Does

This platform helps businesses understand customer sentiment and engagement across social media by:

1. **Connecting to Social Platforms** → OAuth2 authentication with Meta (Facebook/Instagram), API keys for X (Twitter) and TripAdvisor
2. **Fetching Comments & Posts** → Automatically ingests comments from your business pages/accounts using their respective APIs
3. **Storing Data** → All comments stored in PostgreSQL/SQLite with full metadata (author, timestamp, platform, etc.)
4. **Analyzing with NLP** → Two-stage analysis:
   - **Sentiment Analysis**: Using `robertuito-sentiment-analysis` model → classifies as POS (positive), NEG (negative), or NEU (neutral)
   - **Intention Detection**: Identifies user intent (inquiry, complaint, praise, purchase interest, etc.)
5. **Exposing via REST API** → Query, filter, and export analyzed comments through FastAPI endpoints

**Use Case Example**: A restaurant chain monitors Instagram and Facebook comments, discovers trending sentiment about specific menu items, identifies support requests automatically, and tracks customer satisfaction over time.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (main.py)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routes (app/api/)                 │  │
│  │  ┌──────────┬──────────────┬──────────────────┐          │  │
│  │  │ /auth    │  /comments   │  /ingest         │          │  │
│  │  │ (OAuth2) │  (CRUD)      │  (Fetch data)    │          │  │
│  │  └──────────┴──────────────┴──────────────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Business Logic (app/services/)          │  │
│  │  ┌────────────────┬─────────────┬──────────────────┐    │  │
│  │  │ MetaAuthService│ Ingestion   │ CommentService  │    │  │
│  │  │ (OAuth flow)   │ Services    │ (CRUD ops)      │    │  │
│  │  └────────────────┴─────────────┴──────────────────┘    │  │
│  │  ┌────────────────┬──────────────────────────────┐      │  │
│  │  │ SentimentService (NLP Analysis)              │      │  │
│  │  │ IntentionService (Intent Detection)          │      │  │
│  │  └────────────────┬──────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Data Models (app/models/) with SQLAlchemy ORM   │  │
│  │  ┌──────────┬──────────┬────────────────────┐           │  │
│  │  │ Comment  │ Post     │ MetaCredentials    │           │  │
│  │  │ (Analyzed│ (From    │ (OAuth tokens)     │           │  │
│  │  │ comments)│ posts)   │ [encrypted]        │           │  │
│  │  └──────────┴──────────┴────────────────────┘           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           ↓
        ┌────────────────────────────────────┐
        │  PostgreSQL / SQLite Database      │
        │  ├── comments (analyzed)           │
        │  ├── posts                         │
        │  └── meta_credentials (encrypted)  │
        └────────────────────────────────────┘
                           ↓
        ┌────────────────────────────────────┐
        │  External APIs (when ingesting)   │
        │  ├── Meta Graph API                │
        │  ├── X (Twitter) API               │
        │  └── TripAdvisor API               │
        └────────────────────────────────────┘
```

---

## 📦 Project Structure

```
social-selling/
│
├── main.py                          # FastAPI app entry point
│                                    # - Creates app instance
│                                    # - Configures CORS
│                                    # - Registers routers
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/                         # 🌐 API Routes (HTTP endpoints)
│   │   ├── __init__.py
│   │   ├── auth.py                  # OAuth2 flow with Meta
│   │   │                            # - GET /auth/meta/login
│   │   │                            # - GET /auth/meta/callback
│   │   │                            # - GET /auth/meta/status
│   │   │
│   │   ├── comments.py              # Comment CRUD operations
│   │   │                            # - POST /comments (create)
│   │   │                            # - GET /comments (list, filter by platform/sentiment)
│   │   │                            # - GET /comments/{id} (retrieve one)
│   │   │                            # - PUT /comments/{id} (update)
│   │   │                            # - DELETE /comments/{id} (delete)
│   │   │
│   │   └── ingestion.py             # Data ingestion endpoints
│   │                                # - POST /ingest/instagram/posts
│   │                                # - POST /ingest/instagram/comments
│   │                                # - POST /ingest/facebook/posts
│   │                                # - POST /ingest/facebook/comments
│   │                                # - POST /ingest/twitter/...
│   │                                # - POST /ingest/tripadvisor/...
│   │
│   ├── core/                        # 🔧 Core configuration & setup
│   │   ├── __init__.py
│   │   ├── config.py                # Settings from .env
│   │   │                            # - Database URL
│   │   │                            # - API credentials (Meta, X, TripAdvisor)
│   │   │                            # - Encryption keys
│   │   │
│   │   └── database.py              # SQLAlchemy setup
│   │                                # - Engine creation
│   │                                # - Session management
│   │                                # - get_db() dependency
│   │
│   ├── models/                      # 🗄️ SQLAlchemy ORM Models
│   │   ├── __init__.py
│   │   ├── comment.py               # Comment model
│   │   │                            # Fields:
│   │   │                            # - id (primary key)
│   │   │                            # - platform (facebook/instagram/tripadvisor)
│   │   │                            # - platform_id (unique per platform)
│   │   │                            # - author, content, rating
│   │   │                            # - sentiment, sentiment_confidence
│   │   │                            # - intention, intention_confidence
│   │   │                            # - timestamps (created_at, platform_created_at)
│   │   │                            # - flags (sentiment_analized, intention_analized)
│   │   │
│   │   ├── post.py                  # Post model
│   │   │                            # Fields:
│   │   │                            # - id, platform, platform_id
│   │   │                            # - text, media_url
│   │   │                            # - engagement metrics
│   │   │                            # - timestamps
│   │   │
│   │   └── meta_credentials.py      # MetaCredentials model
│   │                                # Stores encrypted OAuth tokens
│   │                                # Fields:
│   │                                # - encrypted_access_token (Fernet encrypted)
│   │                                # - fb_page_id
│   │                                # - ig_business_account_id
│   │
│   ├── schemas/                     # 📋 Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── comment.py               # CommentCreate, CommentResponse, CommentList
│   │   │                            # Used for request/response validation
│   │   │
│   │   └── post.py                  # PostCreate, PostResponse
│   │
│   ├── services/                    # 💼 Business Logic Layer
│   │   ├── __init__.py
│   │   │
│   │   ├── meta_auth_service.py     # OAuth2 with Meta
│   │   │                            # Functions:
│   │   │                            # - get_auth_url() → generates Meta OAuth URL
│   │   │                            # - exchange_code_for_token() → auth code → long-lived token
│   │   │                            # - discover_and_store_assets() → finds Pages + IG accounts
│   │   │                            # - get_credentials_from_db() → fetch + decrypt token
│   │   │                            # - Token encryption/decryption with Fernet
│   │   │
│   │   ├── ingestion_service.py     # Data fetching from APIs
│   │   │                            # Classes:
│   │   │                            # - InstagramIngestionService
│   │   │                            # - FacebookIngestionService
│   │   │                            # - XIngestionService (Twitter)
│   │   │                            # - TripAdvisorIngestionService
│   │   │                            # Methods:
│   │   │                            # - fetch_posts() → get posts from API
│   │   │                            # - fetch_comments() → get comments per post
│   │   │                            # - transform_to_comment() → normalize API response
│   │   │
│   │   ├── comment_service.py       # Comment CRUD operations
│   │   │                            # Functions:
│   │   │                            # - create_comment()
│   │   │                            # - get_comment()
│   │   │                            # - get_comments() with filters
│   │   │                            # - update_comment()
│   │   │                            # - delete_comment()
│   │   │                            # - count_comments()
│   │   │
│   │   ├── post_service.py          # Post management
│   │   │                            # Similar CRUD operations for posts
│   │   │
│   │   ├── sentiment_service.py     # NLP Sentiment Analysis
│   │   │                            # Uses: robertuito-sentiment-analysis model
│   │   │                            # Function: analize_sentiment(text)
│   │   │                            # Returns: (label: "POS"/"NEG"/"NEU", confidence: 0-1)
│   │   │
│   │   ├── intention_service.py     # Intent Detection
│   │   │                            # Identifies user intentions from text
│   │   │                            # Returns: (intention_label, confidence)
│   │   │
│   │   └── __init__.py
│   │
│   ├── seeders/                     # 🌱 Database seeders (test data)
│   │   ├── __init__.py
│   │   └── comment_seeder.py        # Creates sample comments for testing
│   │
│   ├── reset_db.py                  # ⚠️ Utility: drops & recreates all tables
│   ├── seed.py                      # Utility: populates DB with sample data
│   └── __init__.py
│
├── alembic/                         # 📚 Database migrations (schema versioning)
│   ├── env.py                       # Alembic configuration
│   ├── script.py.mako               # Migration template
│   └── versions/                    # Individual migration files
│       └── 2025_10_23_*.py
│
├── .env.example                     # Template for environment variables
├── .env                             # ⚠️ NOT in git (local config only)
├── alembic.ini                      # Alembic config file
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🔄 Data Flow Example

### Scenario: Ingesting Instagram Comments

```
1. User calls: POST /ingest/instagram/comments
   ↓
2. API route (app/api/ingestion.py) receives request
   ↓
3. Calls InstagramIngestionService.fetch_instagram_posts(db)
   ├─ Calls MetaAuthService.get_credentials_from_db(db)
   ├─ Retrieves encrypted token → decrypts it
   ├─ Makes HTTP request to Meta Graph API v23.0
   │  GET /me/accounts → gets Instagram Business Account ID
   │  GET /{ig_account_id}/media → gets all posts
   └─ Returns: List of posts
   ↓
4. For each post, call InstagramIngestionService.fetch_comments(db, post_id)
   ├─ Makes HTTP request to Meta Graph API
   │  GET /{post_id}/comments → gets comments for that post
   └─ Returns: List of comments
   ↓
5. For each comment, transform to internal format
   ├─ platform_id → unique identifier (Meta ID)
   ├─ author → commenter username
   ├─ content → comment text
   ├─ platform_created_at → when comment was posted
   └─ extra_data → raw API response (JSON)
   ↓
6. Check if comment already exists (deduplicate by platform_id)
   ↓
7. Create Comment in database
   ├─ Set sentiment_analized = False (initially)
   ├─ Set intention_analized = False (initially)
   └─ Save to DB
   ↓
8. (Optional) Run NLP analysis
   ├─ Call SentimentService.analize_sentiment(comment.content)
   │  ├─ Feeds text to robertuito model
   │  ├─ Gets result: {"label": "POS", "score": 0.95}
   │  └─ Updates: sentiment="POS", sentiment_confidence=0.95, sentiment_analized=True
   │
   ├─ Call IntentionService.analyze_intent(comment.content)
   │  ├─ Feeds text to intent model
   │  ├─ Gets result: {"label": "praise", "score": 0.88}
   │  └─ Updates: intention="praise", intention_confidence=0.88, intention_analized=True
   └─ Save updated comment to DB
   ↓
9. Return results to API caller
   {
     "status": "success",
     "comments_fetched": 42,
     "comments_analyzed": 42,
     "summary": {"positive": 30, "neutral": 8, "negative": 4}
   }
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (tested on 3.11)
- **pip** package manager
- **Git**
- **PostgreSQL** (production) or **SQLite** (development - comes with Python)
- **Meta Developer Account** (for OAuth - free tier available)

### Step 1: Clone & Setup Environment

```bash
# Clone repository
git clone https://github.com/your-username/social-selling.git
cd social-selling

# Create virtual environment
python -m venv venv
source venv/bin/activate              # macOS/Linux
# or: .\venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your values (see section below)
nano .env  # or your preferred editor
```

### Step 3: Setup Database

```bash
# Apply all migrations
alembic upgrade head

# Optionally, seed with sample data
python -m app.seed
```

### Step 4: Configure Meta OAuth (Required for Instagram/Facebook)

**In Meta Developers Console:**

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create new app (or use existing) → type: "Consumer"
3. Add product: **Facebook Login**
4. Go to: Facebook Login → Settings
5. **Valid OAuth Redirect URIs**: Add `http://localhost:8000/auth/meta/callback`
6. **App Domains**: Add `localhost`
7. Go to: Settings → Basic
8. Copy **App ID** and **App Secret** → add to `.env`

### Step 5: Run Server

```bash
uvicorn main:app --reload
# Server at: http://127.0.0.1:8000

# In another terminal, test it:
curl http://127.0.0.1:8000/health
# Response: {"status": "healthy"}
```

---

## 🔐 Environment Configuration

Create `.env` file (copy from `.env.example`):

```env
# DATABASE
DATABASE_URL=sqlite:///./social_listening.db
# Production: postgresql://user:password@localhost:5432/social_listening

# META (Facebook/Instagram) - OAuth2
META_APP_ID=your_app_id_from_console
META_APP_SECRET=your_app_secret_keep_safe
META_REDIRECT_URI=http://localhost:8000/auth/meta/callback
# Note: META_ACCESS_TOKEN is auto-generated during OAuth flow
#       Do NOT manually set it here - gets encrypted and stored in database

# X / TWITTER (Optional)
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_BEARER_TOKEN=your_x_bearer_token
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret

# TRIPADVISOR (Optional)
TRIPADVISOR_API_KEY=your_tripadvisor_api_key

# ENCRYPTION
# Used to encrypt/decrypt OAuth tokens before storing in database
# Must be at least 32 characters, don't change after first setup
ENCRYPTION_KEY=your_32_char_encryption_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# APP SETTINGS
APP_NAME=Social Listening Platform
APP_VERSION=1.0.0
DEBUG=True                          # Set to False in production
```

**⚠️ Never commit `.env` to git** (already in `.gitignore`)

---

## 🔐 OAuth2 Flow with Meta

### How It Works

The platform uses Meta's **Server-Side (Authorization Code) Flow** for secure authentication:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: User Initiates Login                                           │
│                                                                          │
│  Your Dashboard                    Your App Server                      │
│  ┌──────────────────────┐         ┌──────────────────┐                │
│  │ Click "Connect Meta" │────────→ │ GET /auth/meta/  │                │
│  └──────────────────────┘         │ login            │                │
│                                    │                  │                │
│                                    │ Generates OAuth  │                │
│                                    │ URL with:        │                │
│                                    │ - client_id      │                │
│                                    │ - redirect_uri   │                │
│                                    │ - scopes         │                │
│                                    └────────┬─────────┘                │
│                                             │                          │
│                                             ↓                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: User Grants Permissions on Facebook                            │
│                                                                          │
│  Your App Server          Meta Facebook Servers                        │
│  ┌──────────────┐         ┌────────────────────────────────────┐      │
│  │ Redirect to: │────────→│ Facebook Login Screen              │      │
│  │ facebook.com │         │ ┌──────────────────────────────┐   │      │
│  │ /dialog/oauth│         │ │ Login with Meta Account      │   │      │
│  └──────────────┘         │ │                              │   │      │
│                           │ │ [Show permission dialog]     │   │      │
│                           │ │ - View Public Profile        │   │      │
│                           │ │ - List Your Pages            │   │      │
│                           │ │ - Instagram Basic Display    │   │      │
│                           │ │ - Manage Instagram Comments  │   │      │
│                           │ │ - Read Page Engagement       │   │      │
│                           │ │                              │   │      │
│                           │ │ [User Clicks APPROVE]        │   │      │
│                           │ └──────────────────────────────┘   │      │
│                           └───────────────┬────────────────────┘      │
│                                          │                            │
│                                          ↓                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Meta Redirects Back with Authorization Code                    │
│                                                                          │
│  Meta Facebook Servers         Your App Server                          │
│  ┌──────────────────────┐     ┌──────────────────────────────────┐    │
│  │ Redirect to:         │────→│ GET /auth/meta/callback          │    │
│  │ your-app/auth/meta/  │     │ ?code=AUTHORIZATION_CODE&state=X│    │
│  │ callback?code=...    │     │                                  │    │
│  └──────────────────────┘     │ Backend receives code (not token)│    │
│                               └──────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Backend Exchanges Code for Short-Lived Token (Server-to-      │
│ Server - User doesn't see this)                                         │
│                                                                          │
│  Your App Server           Meta Graph API v23.0                        │
│  ┌──────────────────────┐  ┌────────────────────────────────┐         │
│  │ POST /oauth/         │→ │ Parameters:                    │         │
│  │ access_token         │  │ - client_id                    │         │
│  │                      │  │ - client_secret (secret!)      │         │
│  │ With params:         │  │ - code                         │         │
│  │ - code               │  │ - redirect_uri                 │         │
│  │ - client_id          │  │                                │         │
│  │ - client_secret      │  │ Returns:                       │         │
│  │ - redirect_uri       │  │ - access_token (short-lived)   │         │
│  │                      │  │ - expires_in: 5184000 secs (~2h)         │
│  │                      │←─│ - token_type: "bearer"         │         │
│  │ Gets short-lived token               │                    │         │
│  └──────────────────────┘  └────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: Exchange Short-Lived for Long-Lived Token (Server-to-Server)   │
│                                                                          │
│  Your App Server           Meta Graph API v23.0                        │
│  ┌──────────────────────┐  ┌────────────────────────────────┐         │
│  │ POST /oauth/         │→ │ Parameters:                    │         │
│  │ access_token         │  │ - grant_type: "fb_exchange_   │         │
│  │                      │  │   token"                       │         │
│  │ With params:         │  │ - client_id                    │         │
│  │ - grant_type:        │  │ - client_secret                │         │
│  │   fb_exchange_token  │  │ - fb_exchange_token            │         │
│  │ - client_id          │  │   (the short-lived token)      │         │
│  │ - client_secret      │  │                                │         │
│  │ - fb_exchange_token  │  │ Returns:                       │         │
│  │   (short-lived)      │  │ - access_token (long-lived)    │         │
│  │                      │←─│ - expires_in: 5184000 secs     │         │
│  │ Gets long-lived token                (~60 days)          │         │
│  └──────────────────────┘  └────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: Discover & Store Assets (Pages & Instagram Accounts)           │
│                                                                          │
│  Your App Server           Meta Graph API v23.0                        │
│  ┌──────────────────────┐  ┌────────────────────────────────┐         │
│  │ GET /me/accounts     │→ │ With long-lived access_token   │         │
│  │                      │  │                                │         │
│  │                      │←─│ Returns:                       │         │
│  │ Gets list of:        │  │ - Facebook Pages list          │         │
│  │ - Pages              │  │ - Page IDs                     │         │
│  │ - Instagram Business │  │                                │         │
│  │   Accounts           │  │ For each page:                 │         │
│  │                      │  │ GET /{page_id}/               │         │
│  │                      │→ │ ?fields=instagram_business_    │         │
│  │                      │  │ account                        │         │
│  │                      │←─│ Returns Instagram Account ID   │         │
│  └──────────────────────┘  └────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: Encrypt & Store in Database                                    │
│                                                                          │
│  Your App Server           Database                                     │
│  ┌──────────────────────┐  ┌────────────────────────────────┐         │
│  │ Have:                │  │ Table: meta_credentials        │         │
│  │ - long_lived_token   │  │                                │         │
│  │ - fb_page_id         │→ │ INSERT:                        │         │
│  │ - ig_account_id      │  │ - encrypted_access_token      │         │
│  │                      │  │   (encrypted with ENCRYPTION_  │         │
│  │ Encrypt token with   │  │    KEY using Fernet)           │         │
│  │ Fernet + ENCRYPTION_ │  │ - fb_page_id                   │         │
│  │ KEY                  │  │ - ig_business_account_id       │         │
│  │                      │←─│                                │         │
│  │ Now token is safe    │  │ Token now at rest encrypted    │         │
│  │ in database          │  │                                │         │
│  └──────────────────────┘  └────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 8: Ongoing API Calls                                              │
│                                                                          │
│  Future Requests (ingestion, etc.)                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │ 1. Call: MetaAuthService.get_credentials_from_db(db)       │      │
│  │    └─ Fetch from DB, decrypt token                          │      │
│  │                                                             │      │
│  │ 2. Use decrypted token for Meta Graph API calls            │      │
│  │    └─ GET /me/accounts                                      │      │
│  │    └─ GET /{page_id}/posts                                  │      │
│  │    └─ GET /{post_id}/comments                               │      │
│  │                                                             │      │
│  │ 3. Token refresh (automatic, every ~55 days)               │      │
│  │    └─ If expired, repeat phases 4-7                        │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Testing OAuth Locally

```bash
# 1. Start server
uvicorn main:app --reload

# 2. Open browser and visit (this redirects to Meta)
http://127.0.0.1:8000/auth/meta/login

# 3. Log in with your Meta account, approve permissions

# 4. You'll be redirected to /auth/meta/status
# Should see:
{
  "status": "authenticated",
  "fb_page_id": "123456789",
  "ig_business_account_id": "987654321",
  "message": "Meta credentials found in database."
}

# 5. From terminal, verify token was stored encrypted:
curl http://127.0.0.1:8000/auth/meta/status
# Response should be same as step 4
```

---

## 💾 Database & Migrations

### Initial Setup

```bash
# Apply all pending migrations
alembic upgrade head

# Check current version
alembic current
```

### Adding New Fields to Comments Model

```bash
# 1. Edit app/models/comment.py (add new column)

# 2. Generate migration automatically
alembic revision --autogenerate -m "Add new field to comments"

# 3. Review generated file in alembic/versions/

# 4. Apply migration
alembic upgrade head
```

### Rollback / Undo

```bash
# Revert one migration
alembic downgrade -1

# Revert to specific version
alembic downgrade 2025_10_23_0103

# Revert all (back to start)
alembic downgrade base
```

---

## 🌐 API Endpoints

### Health Check

```bash
GET /health
# Response: {"status": "healthy"}
```

### Authentication (Meta OAuth2)

```bash
# Start OAuth flow (redirects to Meta)
GET /auth/meta/login

# Meta redirects here after user approves (automatic)
GET /auth/meta/callback?code=XXX&state=YYY

# Check if authenticated
GET /auth/meta/status
# Response:
# {
#   "status": "authenticated",
#   "fb_page_id": "123456789",
#   "ig_business_account_id": "987654321",
#   "message": "Meta credentials found in database."
# }
```

### Comments CRUD

```bash
# List comments (with filters)
GET /comments?skip=0&limit=100&platform=instagram

# Get one comment
GET /comments/1

# Create comment (usually done via ingestion, but can test manually)
POST /comments
Body: {
  "platform": "instagram",
  "platform_id": "unique_id",
  "author": "john_doe",
  "content": "Great product!"
}

# Update comment
PUT /comments/1
Body: { "sentiment": "POS" }

# Delete comment
DELETE /comments/1
```

### Data Ingestion

```bash
# Ingest all Instagram posts and their comments
POST /ingest/instagram/comments

# Ingest all Instagram posts only
POST /ingest/instagram/posts

# Ingest Facebook posts and comments
POST /ingest/facebook/comments

# Similar endpoints for Twitter (/ingest/twitter/) and TripAdvisor

# Response example:
# {
#   "status": "success",
#   "comments_fetched": 42,
#   "comments_analyzed": 42,
#   "summary": {
#     "positive": 30,
#     "neutral": 8,
#     "negative": 4
#   }
# }
```

### Interactive API Documentation

While server is running:

```
Swagger UI (interactive): http://127.0.0.1:8000/docs
ReDoc (read-only):       http://127.0.0.1:8000/redoc
```

---

## 🧪 Development Workflow

### Typical Day

```bash
# 1. Start day - activate environment
source venv/bin/activate
cd social-selling

# 2. Ensure DB is up-to-date
alembic upgrade head

# 3. Start server with hot reload
uvicorn main:app --reload

# 4. Test an endpoint (in another terminal)
curl http://127.0.0.1:8000/health

# 5. Make changes to code
# (server automatically reloads)

# 6. If you modified a model:
alembic revision --autogenerate -m "description"
alembic upgrade head

# 7. Commit changes
git add -A
git commit -m "Add feature X"
git push origin feature/feature-name
```

### Important Commands

```bash
# Reset everything and start fresh (development only!)
python -m app.reset_db    # ⚠️ Deletes all data
python -m app.seed        # Populate with sample data

# Run tests
pytest -v
pytest tests/api -v
pytest -k "oauth" -v

# Check if imports work
python -c "from app.services.sentiment_service import analize_sentiment; print('OK')"

# View DB contents (SQLite only)
sqlite3 social_listening.db ".tables"
sqlite3 social_listening.db "SELECT COUNT(*) FROM comments;"
```

---

## 🐛 Troubleshooting

### "Address already in use" (port 8000 occupied)

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn main:app --reload --port 8001
```

### OAuth says "Invalid redirect URI"

**Fix:**

1. Go to Meta Developers Console → Your App
2. Facebook Login → Settings
3. Add to "Valid OAuth Redirect URIs":
   ```
   http://localhost:8000/auth/meta/callback
   ```
   (Exact match, no trailing slash)
4. Ensure `.env` has same URI:
   ```
   META_REDIRECT_URI=http://localhost:8000/auth/meta/callback
   ```

### "No Meta credentials found"

You haven't authenticated yet:

1. Visit http://127.0.0.1:8000/auth/meta/login
2. Log in with Meta account that owns a Facebook Page
3. Approve permissions
4. Tokens will be encrypted and stored in DB

### Comments are missing sentiment/intention data

The NLP analysis might not have run:

```bash
# Check model is loading correctly
python -c "from app.services.sentiment_service import analize_sentiment; print(analize_sentiment('Great product!'))"

# Should output something like: ('POS', 0.95)
```

If fails, reinstall dependencies:

```bash
pip install --upgrade transformers torch
```

### Database "locked" error (SQLite only)

SQLite doesn't handle concurrent writes well. For production:

- Switch to PostgreSQL (see `.env` configuration)

---

## 📚 Key Services Explained

### MetaAuthService (`app/services/meta_auth_service.py`)

Handles entire OAuth2 flow with Meta:

| Function                               | Purpose                                                   |
| -------------------------------------- | --------------------------------------------------------- |
| `get_auth_url()`                       | Generates OAuth authorization URL                         |
| `exchange_code_for_token(db, code)`    | Exchange auth code → short-lived token → long-lived token |
| `discover_and_store_assets(db, token)` | Find user's Pages & Instagram accounts, store encrypted   |
| `get_credentials_from_db(db)`          | Retrieve & decrypt token from DB for API calls            |
| `_encrypt(data)`                       | Encrypt token with Fernet + ENCRYPTION_KEY                |
| `_decrypt(data)`                       | Decrypt token from DB                                     |

### SentimentService (`app/services/sentiment_service.py`)

NLP sentiment classification:

```python
from app.services.sentiment_service import analize_sentiment

label, confidence = analize_sentiment("Great product!")
# Returns: ("POS", 0.95)

# Labels: "POS" (positive), "NEG" (negative), "NEU" (neutral)
# Confidence: 0.0 to 1.0
```

Model: `robertuito-sentiment-analysis` (Spanish/multilingual optimized)

### IngestionServices (`app/services/ingestion_service.py`)

Fetch comments from each platform:

- `InstagramIngestionService` → Fetch from Meta Graph API
- `FacebookIngestionService` → Fetch from Meta Graph API
- `XIngestionService` → Fetch from X (Twitter) API
- `TripAdvisorIngestionService` → Fetch from TripAdvisor API

Each follows pattern:

1. Get credentials (for OAuth platforms)
2. Fetch posts
3. For each post, fetch comments
4. Transform to internal format
5. Check for duplicates
6. Store in DB

---

## 🚀 Production Deployment

### Before Deploying

```bash
# 1. Set DEBUG=False in .env
DEBUG=False

# 2. Switch to PostgreSQL
DATABASE_URL=postgresql://user:password@prod-server:5432/social_listening

# 3. Use strong ENCRYPTION_KEY
ENCRYPTION_KEY=your_very_long_random_string_minimum_32_chars_xxxxxxx

# 4. Update CORS origins
# In main.py, change allow_origins=["*"] to specific domains
allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"]

# 5. Use strong Meta App Secret
# Make sure META_APP_SECRET is not hardcoded anywhere

# 6. Run migrations
alembic upgrade head

# 7. Seed initial data (optional)
python -m app.seed
```

### Running in Production

```bash
# With Gunicorn (ASGI)
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or Docker (if containerized)
docker run -p 8000:8000 --env-file .env social-listening:latest
```

---

## 📝 License

This project is licensed under MIT License. See LICENSE file.

---

## 💡 Next Steps / Future Improvements

- [ ] Add support for more platforms (LinkedIn, TikTok)
- [ ] Implement real-time websocket updates
- [ ] Add data export (CSV, JSON)
- [ ] Build dashboard UI
- [ ] Add scheduled ingestion jobs (background tasks)
- [ ] Implement user accounts & multi-tenant support
- [ ] Add advanced filtering & analytics
- [ ] Set up automated testing & CI/CD
- [ ] Add Docker support for easier deployment

---

**For questions or issues, refer to the troubleshooting section or check the inline code documentation.**
