#!/bin/bash
# Run the project locally without Docker

set -e

echo "🚀 Setting up local development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set DATABASE_URL to your local PostgreSQL"
    echo "   Example: DATABASE_URL=postgresql://localhost:5432/recapp"
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL doesn't seem to be running"
    echo "   On macOS: brew services start postgresql@16"
    echo "   Or start Docker: docker-compose up -d db"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
else
    source venv/bin/activate
fi

# Initialize database
echo "🗄️  Initializing database..."
alembic upgrade head

# Start the server
echo "✅ Starting server on http://localhost:8000"
echo "   Press Ctrl+C to stop"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
