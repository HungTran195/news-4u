# News Aggregator Backend

FastAPI backend for a professional news aggregation platform with SQLite database support.

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server (Option 1: Using the startup script)
./start.sh

# OR start manually (Option 2: Manual commands)
source venv/bin/activate
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

---

## Project Structure

```text
backend/
├── config/            # Configuration files (RSS feed sources)
├── models/            # SQLAlchemy ORM models (database tables)
├── routers/           # FastAPI route definitions (API endpoints)
├── schemas/           # Pydantic schemas for request/response validation
├── services/          # Business logic and integrations (RSS, content extraction)
├── scripts/           # Utility scripts (DB setup, initialization)
├── lib/               # Utility functions and helpers
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker build file
├── main.py            # FastAPI application entry point
├── database.py        # Database connection/session setup
└── README.md          # This documentation
```

### Folder & File Usage

- **config/**: Centralized configuration, e.g., `rss_feeds.py` lists all RSS sources and categories.
- **models/**: SQLAlchemy ORM models defining database tables and relationships.
- **routers/**: FastAPI API endpoints containing the main API logic.
- **schemas/**: Pydantic models for validating and serializing API requests and responses.
- **services/**: Core business logic including RSS feed processing and content extraction.
- **scripts/**: Utility scripts for database setup and initialization.
- **main.py**: FastAPI app entry point with app setup, middleware, and router registration.
- **database.py**: SQLAlchemy engine, session, and database initialization logic.

---

## Database Access

The backend uses SQLite by default. The database file will be created as `news_4u.db` in the backend directory.

### Python Shell Access

For advanced database operations:

```bash
# Activate virtual environment
source venv/bin/activate

# Start Python shell
python

# In Python shell:
from database import get_db
from models.database import NewsArticle, RSSFeed, FeedFetchLog
from sqlalchemy.orm import Session

db = next(get_db())
# Query examples
articles = db.query(NewsArticle).limit(5).all()
for article in articles:
    print(f"{article.title} - {article.source_name}")
db.close()
```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, no authentication is required for any endpoints.

### Response Format
All API responses are in JSON format.

### Error Handling
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## API Endpoints

### Health Check

#### GET `/api/news/health`
Check the health status of the API and database.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "database_connected": true,
  "feeds_count": 7,
  "articles_count": 150
}
```

---

### Articles

#### GET `/api/news/articles`
Get articles with optional filtering and pagination.

**Query Parameters:**
- `category` (optional): Filter by category
- `source` (optional): Filter by source name
- `feeds` (optional): Comma-separated list of feed names to filter by
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Articles per page (default: 20, max: 100)

**Example Request:**
```
GET /api/news/articles?category=tech&page=1&per_page=10
```

**Response:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Example Article Title",
      "summary": "Article summary...",
      "link": "https://example.com/article",
      "author": "John Doe",
      "published_date": "2024-01-15T10:00:00",
      "category": "tech",
      "source_name": "Example Source",
      "source_url": "https://example.com",
      "image_url": "https://example.com/image.jpg",
      "is_processed": true,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": null
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 10,
  "total_pages": 15
}
```

#### GET `/api/news/articles/{article_id}`
Get a specific article by ID.

**Path Parameters:**
- `article_id` (integer): Article ID

**Response:** Same format as individual article in the list response.

#### GET `/api/news/articles/slug/{slug}`
Get a specific article by slug.

**Path Parameters:**
- `slug` (string): Article slug

**Response:** Same format as individual article in the list response.

#### GET `/api/news/categories/{category}`
Get articles by specific category.

**Path Parameters:**
- `category` (string): Category name

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Articles per page (default: 20, max: 100)

**Response:** Same format as `/api/news/articles`

---

### Sources and Feeds

#### GET `/api/news/sources`
Get list of all news sources.

**Response:**
```json
[
  "Source 1",
  "Source 2",
  "Source 3"
]
```

#### GET `/api/news/feeds`
Get all configured RSS feeds.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Example Feed",
    "url": "https://example.com/feed/",
    "category": "tech",
    "description": "Example feed description",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": null
  }
]
```

#### GET `/api/news/feeds/names`
Get list of feed names.

**Response:**
```json
[
  "Feed 1",
  "Feed 2",
  "Feed 3"
]
```

---

### Fetch Operations

#### POST `/api/news/fetch`
Manually trigger fetching of all RSS feeds.

**Request:** No body required

**Response:**
```json
{
  "message": "Feed fetching completed",
  "result": {
    "total_feeds": 7,
    "results": [
      {
        "feed_name": "Example Feed",
        "category": "tech",
        "status": "success",
        "articles_found": 20,
        "articles_processed": 15,
        "execution_time": 2500
      }
    ]
  }
}
```

#### POST `/api/news/fetch/{feed_name}`
Manually trigger fetching of a specific RSS feed.

**Path Parameters:**
- `feed_name` (string): Name of the feed to fetch

**Response:** Same format as individual feed result in the fetch all response.

#### GET `/api/news/logs`
Get recent RSS fetch logs.

**Query Parameters:**
- `limit` (optional): Number of logs to return (default: 50, max: 100)

**Response:**
```json
[
  {
    "id": 1,
    "feed_name": "Example Feed",
    "fetch_timestamp": "2024-01-15T10:30:00",
    "status": "success",
    "articles_found": 20,
    "articles_processed": 15,
    "error_message": null,
    "execution_time": 2500
  }
]
```

---

### Search

#### GET `/api/news/search`
Search articles by query with optional filters.

**Query Parameters:**
- `query` (required): Search query string
- `category` (optional): Filter by category (default: "all")
- `time_filter` (optional): Time filter (default: "24h")
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Articles per page (default: 20, max: 100)

**Response:** Same format as `/api/news/articles`

---

### Statistics

#### GET `/api/news/stats`
Get news aggregation statistics.

**Response:**
```json
{
  "total_articles": 150,
  "articles_by_category": {
    "tech": 50,
    "finance": 60,
    "global_news": 40
  },
  "articles_by_source": {
    "Source 1": 25,
    "Source 2": 25,
    "Source 3": 30
  },
  "recent_articles": [
    {
      "id": 1,
      "title": "Recent Article",
      "source_name": "Example Source",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "active_feeds": 7,
  "total_feeds": 7,
  "last_updated": "2024-01-15T10:30:00"
}
```

---

### Content Extraction

#### POST `/api/news/articles/{article_id}/extract`
Manually trigger content extraction for a specific article.

**Path Parameters:**
- `article_id` (integer): Article ID

**Response:** Updated article with extracted content.

---

### Scheduler Management

#### GET `/api/news/scheduler/status`
Get scheduler status.

#### POST `/api/news/scheduler/start`
Start the scheduler.

#### POST `/api/news/scheduler/stop`
Stop the scheduler.

---

### Admin Operations

#### DELETE `/api/news/admin/cleanup/all`
Clean up all data from the database.

#### DELETE `/api/news/admin/cleanup/feed/{feed_name}`
Clean up data for a specific feed.

#### DELETE `/api/news/admin/cleanup/article/{article_id}`
Delete content for a specific article.

#### POST `/api/news/admin/content/clean-batch`
Clean content for articles in batches.

**Query Parameters:**
- `batch_size` (optional): Number of articles to process per batch (default: 100, min: 10, max: 1000)

---

## Database Schema

### Tables

#### `rss_feeds`
Stores RSS feed configuration.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(255) | Feed name |
| url | VARCHAR(500) | RSS feed URL |
| category | VARCHAR(50) | News category |
| is_active | BOOLEAN | Whether feed is active |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

#### `news_articles`
Stores processed news articles.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| title | VARCHAR(500) | Article title |
| summary | TEXT | Article summary |
| content | TEXT | Full article content |
| link | VARCHAR(1000) | Article URL |
| author | VARCHAR(255) | Article author |
| published_date | DATETIME | Publication date |
| category | VARCHAR(50) | News category |
| source_name | VARCHAR(255) | Source name |
| source_url | VARCHAR(500) | Source URL |
| image_url | VARCHAR(1000) | Featured image URL |
| slug | VARCHAR(100) | Article slug |
| is_processed | BOOLEAN | Processing status |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

#### `feed_fetch_logs`
Stores RSS feed fetch operation logs.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| feed_name | VARCHAR(255) | Feed name |
| fetch_timestamp | DATETIME | Fetch timestamp |
| status | VARCHAR(50) | Operation status |
| articles_found | INTEGER | Number of articles found |
| articles_processed | INTEGER | Number of articles processed |
| error_message | TEXT | Error message if any |
| execution_time | INTEGER | Execution time in milliseconds |

---

## Configuration

### RSS Feeds
RSS feeds are configured in `config/rss_feeds.py`. You can easily add, update, or remove feeds by modifying the `RSS_FEEDS` dictionary.

### Environment Variables
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)

---

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Formatting
```bash
# Install formatting tools
pip install black isort

# Format code
black .
isort .
```

---

## Troubleshooting

### Common Issues

1. **Database locked error**
   - Ensure no other process is accessing the database
   - Check if SQLite shell is open

2. **RSS feed fetch failures**
   - Check internet connectivity
   - Verify RSS feed URLs are accessible
   - Check feed_fetch_logs table for error details

3. **Import errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

### Logs
Check the console output for detailed error messages and fetch operation logs.

---

## API Documentation UI

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation with the ability to test endpoints directly. 