#!/bin/bash

# News 4U Backend Startup Script
# This script activates the virtual environment and starts the FastAPI server

echo "Starting News 4U Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Check for persistent disk
PERSISTENT_DATA_PATH="/var/data"
if [ -d "$PERSISTENT_DATA_PATH" ]; then
    echo "Found persistent disk at $PERSISTENT_DATA_PATH"
    echo "Database will be stored in persistent storage"
    # Ensure the data directory exists and has proper permissions
    mkdir -p "$PERSISTENT_DATA_PATH"
    chmod 755 "$PERSISTENT_DATA_PATH"
else
    echo "Persistent disk not found, using local storage"
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Setting default DATABASE_URL..."
    export DATABASE_URL="sqlite:///./news_4u.db"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting FastAPI server with DATABASE_URL: $DATABASE_URL"
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 