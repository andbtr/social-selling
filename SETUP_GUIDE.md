# Setup Guide - X API Integration

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- X Developer Account with Bearer Token

## Step-by-Step Setup

### 1. Install Dependencies

Open a terminal in the project directory and run:

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

This will install:

- fastapi
- uvicorn
- httpx
- pydantic
- sqlalchemy
- tweepy
- and other dependencies

### 2. Configure X API Credentials

1. **Get your X Bearer Token:**

   - Go to https://developer.x.com
   - Sign in with your X account
   - Create a new Project and App
   - Generate a Bearer Token
   - Copy the token (you won't see it again!)

2. **Create .env file:**

```bash
# Copy the example file
cp .env.example .env

# Or on Windows PowerShell:
copy .env.example .env
```

3. **Edit .env and add your token:**

```bash
# Open .env in your text editor and add:
X_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAABearerTokenHere%2FExample
```

### 3. Initialize Database

```bash
# The database will be created automatically when you start the app
# But you can also initialize it with Alembic:

alembic upgrade head
```

### 4. Start the Application

```bash
uvicorn main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 5. Test the Installation

Open a new terminal and test the endpoints:

```bash
# Test health check
curl http://localhost:8000/x/health

# Expected response:
# {
#   "success": true,
#   "message": "X API service is configured",
#   "has_bearer_token": true
# }
```

### 6. View API Documentation

Open your browser and visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

You'll see all the X API endpoints documented and ready to test!

### 7. Run Test Suite (Optional)

```bash
# Make sure the server is running first, then in another terminal:
python test_x_api.py
```

## Troubleshooting

### Issue: "Import errors" in IDE

**Solution**: Make sure you've:

1. Created and activated the virtual environment
2. Installed dependencies with `pip install -r requirements.txt`
3. Selected the correct Python interpreter in your IDE (the one in venv)

### Issue: "X_BEARER_TOKEN is required"

**Solution**:

1. Make sure `.env` file exists in the project root
2. Verify you added `X_BEARER_TOKEN=your_token` to the .env file
3. Restart the server after adding the token

### Issue: "401 Unauthorized" from X API

**Solution**:

1. Check that your Bearer Token is correct
2. Make sure you copied the entire token (they're long!)
3. Regenerate the token in the X Developer Portal if needed

### Issue: "Module not found: httpx/fastapi/etc"

**Solution**:

```bash
# Make sure virtual environment is activated
# On Windows:
venv\Scripts\activate

# Then reinstall dependencies
pip install -r requirements.txt
```

### Issue: Port 8000 already in use

**Solution**:

```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

## Quick Verification Checklist

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list` shows fastapi, uvicorn, etc.)
- [ ] `.env` file exists with `X_BEARER_TOKEN`
- [ ] Server starts without errors
- [ ] `/x/health` endpoint returns success
- [ ] API docs accessible at `/docs`

## Next Steps

Once setup is complete:

1. **Read the documentation:**

   - `X_API_GUIDE.md` - Complete API guide
   - `API_REFERENCE.md` - Quick reference
   - `X_API_IMPLEMENTATION.md` - Implementation details

2. **Try the examples:**

   - Visit http://localhost:8000/docs
   - Try the "GET /x/tweets/{tweet_id}" endpoint
   - Use a real tweet ID from X.com

3. **Test with real data:**

   ```bash
   # Get a tweet (use a real tweet ID)
   curl "http://localhost:8000/x/tweets/1234567890?include_author=true"

   # Get a user
   curl "http://localhost:8000/x/users/by-username/elonmusk"
   ```

4. **Monitor your usage:**
   - Remember: Free tier = 100 reads/month
   - Each API call = 1 read
   - Use batch endpoints to maximize efficiency

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in the terminal where the server is running
3. Check X API status: https://api.twitterstat.us/
4. Verify your API credentials in the X Developer Portal

## Additional Resources

- **X API Docs**: https://developer.x.com/en/docs/twitter-api
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Python httpx**: https://www.python-httpx.org/

---

**Setup Time**: ~10 minutes
**Difficulty**: Beginner-friendly
**Requirements**: X Developer Account (Free)
