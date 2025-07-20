# News 4U v2 - RSS News Aggregator

A modern news aggregation platform that fetches and categorizes news from popular RSS feeds using AWS S3 for storage.

## Project Structure

```
news-4u/
├── frontend/                 # Next.js frontend application
├── backend/                  # FastAPI backend application
├── docker-compose.yml        # Docker configuration
└── README.md                 
```

## Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.9+
- AWS S3 bucket and credentials
- Docker (optional)

### Development Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Copy and configure environment variables
   cp config.env.example config.env
   # Edit config.env with your AWS credentials and S3 bucket name
   
   # Test S3 connection
   python test_s3.py
   
   uvicorn main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Setup
```bash
docker-compose up --build
```

## API Documentation

Once the backend is running, visit:
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Configuration

### Environment Variables
Copy `backend/config.env.example` to `backend/config.env` and configure:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### RSS Feeds
RSS feeds can be easily configured in `backend/config/rss_feeds.py`.

## Key Features

- **S3 Storage**: All data is stored in AWS S3 instead of a traditional database
- **Article Names**: Uses article names instead of slugs for URLs
- **Load More/Load Older**: Dynamic loading instead of traditional pagination
- **Feed Refresh**: Manual refresh button to fetch latest news
- **No Search**: Simplified interface without search functionality
- **Hourly Updates**: Automatic feed fetching every hour
- **Content Extraction**: Automatic content extraction for articles

## Version 2 Changes

- Removed SQLite database dependency
- Migrated to AWS S3 for all data storage
- Removed search functionality
- Changed from slug-based to article name-based URLs
- Replaced pagination with Load More/Load Older buttons
- Added manual feed refresh functionality
- Updated scheduler to run every hour instead of every 5 minutes
