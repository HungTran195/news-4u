# News 4U Backend

FastAPI backend for the News 4U RSS aggregator with SQLite database.

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

## Project Structure & Usage

```text
backend/
├── config/            # Configuration files (e.g., RSS feed sources)
├── models/            # SQLAlchemy ORM models (database tables)
├── routers/           # FastAPI route definitions (API endpoints)
├── schemas/           # Pydantic schemas for request/response validation
├── services/          # Business logic and integration (RSS, Google News)
├── scripts/           # Utility scripts (DB setup, initialization)
├── __pycache__/       # Python bytecode cache (auto-generated)
├── venv/              # Python virtual environment (local, not in repo)
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker build file
├── main.py            # FastAPI application entry point
├── database.py        # Database connection/session setup
└── README.md          # This documentation
```

### Folder & File Usage

- **config/**: Centralized configuration, e.g., `rss_feeds.py` lists all RSS sources and categories.
- **models/**: SQLAlchemy ORM models. Each file defines tables and relationships (e.g., `database.py`).
- **routers/**: FastAPI API endpoints. Main API logic is in `news.py`.
- **schemas/**: Pydantic models for validating and serializing API requests and responses.
- **services/**: Core business logic, such as fetching/parsing RSS feeds (`rss_service.py`) and Google News integration (`google_news_service.py`).
- **scripts/**: Utility scripts for database setup and initialization (e.g., `init_db.py`).
- **main.py**: FastAPI app entry point. Includes app setup, middleware, and router registration.
- **database.py**: Sets up the SQLAlchemy engine, session, and database initialization logic.
- **requirements.txt**: Lists all Python dependencies for the backend.
- **Dockerfile**: Containerizes the backend for deployment.
- **README.md**: This documentation file.

---

## Database Access

The backend uses SQLite by default. The database file will be created as `news_4u.db` in the backend directory.

### Python Shell Access

For more advanced database operations:

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
- `category` (optional): Filter by category (`tech`, `finance`, `global_news`)
- `source` (optional): Filter by source name
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
      "source_name": "TechCrunch",
      "source_url": "https://techcrunch.com",
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

**Example Request:**
```
GET /api/news/articles/123
```

**Response:**
```json
{
  "id": 123,
  "title": "Example Article Title",
  "summary": "Article summary...",
  "link": "https://example.com/article",
  "author": "John Doe",
  "published_date": "2024-01-15T10:00:00",
  "category": "tech",
  "source_name": "TechCrunch",
  "source_url": "https://techcrunch.com",
  "image_url": "https://example.com/image.jpg",
  "is_processed": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": null
}
```

#### GET `/api/news/categories/{category}`
Get articles by specific category.

**Path Parameters:**
- `category` (string): Category name (`tech`, `finance`, `global_news`)

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Articles per page (default: 20, max: 100)

**Example Request:**
```
GET /api/news/categories/tech?page=1&per_page=15
```

**Response:** Same format as `/api/news/articles`

---

### Sources and Feeds

#### GET `/api/news/sources`
Get list of all news sources.

**Response:**
```json
[
  "TechCrunch",
  "The Verge",
  "Bloomberg",
  "Yahoo Finance",
  "Financial Times",
  "BBC News",
  "Reuters World News"
]
```

#### GET `/api/news/feeds`
Get all configured RSS feeds.

**Response:**
```json
[
  {
    "id": 1,
    "name": "TechCrunch",
    "url": "https://techcrunch.com/feed/",
    "category": "tech",
    "description": "Latest technology news and startup information",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": null
  }
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
        "feed_name": "TechCrunch",
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

#### GET `/api/news/logs`
Get recent RSS fetch logs.

**Query Parameters:**
- `limit` (optional): Number of logs to return (default: 50, max: 100)

**Example Request:**
```
GET /api/news/logs?limit=20
```

**Response:**
```json
[
  {
    "id": 1,
    "feed_name": "TechCrunch",
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
    "TechCrunch": 25,
    "The Verge": 25,
    "Bloomberg": 30,
    "Yahoo Finance": 15,
    "Financial Times": 15,
    "BBC News": 20,
    "Reuters World News": 20
  },
  "recent_articles": [
    {
      "id": 1,
      "title": "Recent Article",
      "source_name": "TechCrunch",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "active_feeds": 7,
  "total_feeds": 7,
  "last_updated": "2024-01-15T10:30:00"
}
```

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
| description | TEXT | Feed description |
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
| is_processed | BOOLEAN | Processing status |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

#### `raw_feed_data`
Stores raw RSS feed data before processing.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| feed_id | INTEGER | Foreign key to rss_feeds |
| raw_content | TEXT | Raw XML content |
| fetch_timestamp | DATETIME | Fetch timestamp |
| status_code | INTEGER | HTTP status code |
| error_message | TEXT | Error message if any |

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
RSS feeds are configured in `config/rss_feeds.py`. You can easily add, update, or remove feeds:

```python
# Add a new feed
add_feed(RSSFeed(
    name="New Source",
    url="https://newsource.com/feed",
    category=NewsCategory.TECH,
    description="New tech news source"
))

# Remove a feed
remove_feed("Old Source")

# Update a feed
update_feed("Source Name", updated_feed)
```

### Environment Variables
- `DATABASE_URL`: PostgreSQL database connection string (required, example: `postgresql://postgres:password@localhost:5432/news_4u`)

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