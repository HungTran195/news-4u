# Cronjobs Documentation

Automated tasks for the News 4U RSS Aggregator using APScheduler.

## Overview

The system runs automated tasks at specified intervals using APScheduler integrated into the FastAPI application.

## Scheduled Jobs

### 1. Feed Fetching
- **Schedule**: Every 5 minutes
- **Purpose**: Fetches RSS feeds and stores new articles
- **Job ID**: `fetch_all_feeds`

### 2. Content Extraction
- **Schedule**: Every minute
- **Purpose**: Extracts full content for articles without content
- **Job ID**: `extract_content`
- **Limit**: Top 20 latest articles per run

## API Endpoints

### Scheduler Management

#### Get Status
```http
GET /api/news/scheduler/status
```

#### Start/Stop Scheduler
```http
POST /api/news/scheduler/start
POST /api/news/scheduler/stop
```

## Configuration

**Dependency**: `apscheduler==3.10.4`

The scheduler starts automatically with the FastAPI application.

## Testing

```bash
cd backend
python scripts/test_cronjobs.py
```

## Monitoring

- **Logs**: All activities logged with descriptive prefixes
- **Database**: Feed logs in `feed_fetch_logs` table, article updates tracked via `updated_at`

## Troubleshooting

### Common Issues
1. **Scheduler not starting**: Check APScheduler installation
2. **Jobs not running**: Verify scheduler status via API endpoint
3. **Database issues**: Ensure database is accessible

### Manual Execution
- Feed fetching: `POST /api/news/fetch`
- Content extraction: Use article extraction endpoint for specific articles

## Performance

- Content extraction limited to 20 articles per run
- Jobs have `max_instances=1` to prevent concurrent execution
- Database connections properly managed 