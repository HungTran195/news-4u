# News 4U - RSS News Aggregator

A news aggregation agent that fetches and categorizes news from popular RSS feeds.

## Project Structure

```
news-4u/
├── frontend/                 # Next.js frontend application
├── backend/                  # FastAPI backend application
├── shared/                   # Shared types and utilities
├── docker-compose.yml        # Docker configuration
└── README.md                 
```

## Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.9+
- PostgreSQL 12+ (or Docker)
- Docker (optional)

### Development Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Set up PostgreSQL database
   python scripts/setup_postgres.py
   
   # Or manually:
   # createdb -h localhost -U postgres news_4u
   # python scripts/init_db.py
   
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

w
## Configuration
RSS feeds can be easily configured in `backend/config/rss_feeds.py`.
If you modify the rss_feeds.py, you need to run `python backend/scripts/init_db.py` to update the databse.
