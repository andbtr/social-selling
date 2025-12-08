@echo off
REM Quick Start script for Social Listening Platform (Windows)

echo Social Listening Platform - Quick Start
echo ==========================================
echo.

echo.
echo Starting FastAPI server...
echo.
echo API Documentation will be available at:
echo    - Swagger UI: http://localhost:8000/docs
echo    - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
