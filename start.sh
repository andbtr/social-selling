#!/bin/bash

echo "🚀 Social Listening Platform - Quick Start"
echo "=========================================="
echo ""

if command -v conda &> /dev/null; then
    # Conda detected
    CONDA_ENV_NAME="social-selling"
    echo "🔄 Activating conda environment: $CONDA_ENV_NAME"
    conda activate $CONDA_ENV_NAME
else
    # Fallback to venv
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    echo "✓ Python 3 detected"
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
fi

echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API credentials"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting FastAPI server..."
echo ""
echo "📖 API Documentation will be available at:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
