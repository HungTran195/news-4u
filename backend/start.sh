#!/bin/bash

# News 4U Backend Startup Script
# This script activates the virtual environment and starts the FastAPI server

echo "Starting News 4U Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Setting default DATABASE_URL..."
    export DATABASE_URL="postgresql://postgres:password@localhost:5432/news_4u"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if PostgreSQL URL is valid
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
    echo "Error: DATABASE_URL must be a PostgreSQL connection string (start with 'postgresql://')"
    echo "Current DATABASE_URL: $DATABASE_URL"
    exit 1
fi

echo "Starting FastAPI server with DATABASE_URL: $DATABASE_URL"
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 