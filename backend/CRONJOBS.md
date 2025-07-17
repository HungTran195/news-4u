# Cronjobs Documentation

This document describes the automated cronjobs implemented in the News 4U RSS Aggregator.

## Overview

The system uses APScheduler (Advanced Python Scheduler) to run automated tasks at specified intervals. The scheduler is integrated into the FastAPI application and starts automatically when the application starts.

## Cronjobs

### 1. Feed Fetching Job
- **Schedule**: Every 5 minutes (`*/5 * * * *`)
- **Purpose**: Fetches all configured RSS feeds and stores new articles in the database
- **Job ID**: `fetch_all_feeds`
- **Function**: `_fetch_all_feeds_job()`

### 2. Content Extraction Job
- **Schedule**: Every minute (`* * * * *`)
- **Purpose**: Extracts full content for articles that don't have content yet
- **Job ID**: `extract_content`
- **Function**: `_extract_content_job()`
- **Limit**: Processes only the top 20 latest articles without content

## API Endpoints

### Scheduler Management

#### Get Scheduler Status
```http
GET /api/news/scheduler/status
```

Returns the current status of the scheduler and all scheduled jobs.

**Response:**
```json
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "fetch_all_feeds",
      "name": "Fetch all RSS feeds",
      "next_run_time": "2024-01-01T12:05:00Z",
      "trigger": "cron[minute='*/5']"
    },
    {
      "id": "extract_content",
      "name": "Extract article content",
      "next_run_time": "2024-01-01T12:01:00Z",
      "trigger": "cron[minute='*']"
    }
  ]
}
```

#### Start Scheduler
```http
POST /api/news/scheduler/start
```

Manually starts the scheduler if it's not running.

#### Stop Scheduler
```http
POST /api/news/scheduler/stop
```

Manually stops the scheduler.

## Configuration

### Dependencies
The scheduler requires APScheduler to be installed:
```bash
pip install apscheduler==3.10.4
```

### Automatic Startup
The scheduler starts automatically when the FastAPI application starts and stops when the application shuts down.

## Testing

You can test the cronjobs manually using the test script:

```bash
cd backend
python scripts/test_cronjobs.py
```

This script will:
1. Test the feed fetching functionality
2. Test the content extraction functionality
3. Test the scheduler start/stop functionality

## Monitoring

### Logs
All cronjob activities are logged with the following prefixes:
- Feed fetching: `---- Starting scheduled feed fetching job ----`
- Content extraction: `---- Starting scheduled content extraction job ----`

### Database
- Feed fetch logs are stored in the `feed_fetch_logs` table
- Article updates are tracked via the `updated_at` timestamp

## Troubleshooting

### Common Issues

1. **Scheduler not starting**: Check if APScheduler is installed correctly
2. **Jobs not running**: Verify the scheduler is running via the status endpoint
3. **Database connection issues**: Ensure the database is accessible and properly configured

### Manual Execution
You can manually trigger the jobs using the existing API endpoints:
- Feed fetching: `POST /api/news/fetch`
- Content extraction: Use the existing article extraction endpoint for specific articles

## Performance Considerations

- The content extraction job is limited to 20 articles per run to prevent overwhelming the system
- Jobs have `max_instances=1` to prevent multiple instances from running simultaneously
- Database connections are properly managed and closed after each job execution 