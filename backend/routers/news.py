"""
News API routes for fetching articles and managing RSS feeds.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.rss_service import RSSService
from services.s3_service import S3Service
from services.scheduler_service import scheduler_service
from schemas.news import (
    NewsArticleResponse, 
    NewsArticleList, 
    RSSFeedResponse,
    FeedFetchLogResponse,
    HealthCheckResponse,
    StatsResponse
)
from config.rss_feeds import NewsCategory, get_all_feeds

router = APIRouter(prefix="/api/news", tags=["news"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test S3 connection
        s3_service = S3Service()
        s3_connected = True
        
        # Get counts
        feeds = s3_service.get_rss_feeds()
        articles_data = s3_service.get_all_articles(limit=1)  # Just get count
        feeds_count = len(feeds)
        articles_count = articles_data['total']
        
    except Exception as e:
        s3_connected = False
        feeds_count = 0
        articles_count = 0
    
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(),
        s3_connected=s3_connected,
        feeds_count=feeds_count,
        articles_count=articles_count
    )


@router.get("/articles", response_model=NewsArticleList)
async def get_articles(
    category: Optional[NewsCategory] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    feeds: Optional[str] = Query(None, description="Comma-separated list of feed names to filter by"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip")
):
    logger.info(f"---- Getting articles with filters: category={category}, source={source}, feeds={feeds}, limit={limit}, offset={offset} ----")
    """Get articles with optional filtering and limit/offset pagination."""
    s3_service = S3Service()
    
    # Parse feeds parameter
    feed_list = None
    if feeds:
        feed_list = [name.strip() for name in feeds.split(',') if name.strip()]
    
    # Get articles from S3
    articles_data = s3_service.get_all_articles(
        limit=limit,
        offset=offset,
        category=category.value if category else None,
        source=source,
        feeds=feed_list
    )
    
    # Convert to response format
    articles = []
    for article in articles_data['articles']:
        # Convert datetime strings back to datetime objects
        published_date = None
        if article.get('published_date'):
            try:
                published_date = datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
            except:
                pass
        
        created_at = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
        updated_at = None
        if article.get('updated_at'):
            try:
                updated_at = datetime.fromisoformat(article['updated_at'].replace('Z', '+00:00'))
            except:
                pass
        
        articles.append(NewsArticleResponse(
            article_name=article['article_name'],
            title=article['title'],
            summary=article.get('summary'),
            content=article.get('content'),
            link=article['link'],
            author=article.get('author'),
            published_date=published_date,
            category=article['category'],
            source_name=article['source_name'],
            source_url=article.get('source_url'),
            image_url=article.get('image_url'),
            is_processed=article.get('is_processed', False),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    has_more = (offset + limit) < articles_data['total']
    
    return NewsArticleList(
        articles=articles,
        total=articles_data['total'],
        limit=limit,
        offset=offset,
        has_more=has_more
    )


@router.get("/articles/{article_name}", response_model=NewsArticleResponse)
async def get_article(article_name: str):
    """Get a specific article by name. Automatically extracts content if missing."""
    s3_service = S3Service()
    logger = logging.getLogger("get_article")
    
    article = s3_service.get_article_by_name(article_name)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if article has content, if not, extract it automatically
    if not article.get("content") or str(article.get("content", "")).strip() == "":
        logger.info(f"Article {article_name} has no content, extracting automatically")
        
        if not article.get("link"):
            logger.warning(f"Article {article_name} has no link, cannot extract content")
            return _convert_article_to_response(article)
        
        try:
            service = RSSService()
            content, extracted_image_url = await service.extract_article_content(article["link"])
            
            updates = {}
            
            # Update content if extracted
            if content:
                updates["content"] = content
                logger.info(f"Successfully extracted content for article {article_name}")
            
            # Update image_url if extracted and missing
            if extracted_image_url and (not article.get("image_url") or str(article.get("image_url", "")).strip() == ""):
                updates["image_url"] = extracted_image_url
                logger.info(f"Updated image URL for article {article_name}")
            
            # Update in S3 if any changes were made
            if updates:
                s3_service.update_article(article_name, updates)
                article.update(updates)
                logger.info(f"Article {article_name} updated with extracted content")
            
        except Exception as e:
            logger.error(f"Error extracting content for article {article_name}: {e}")
            # Continue and return the article even if extraction fails
    
    return _convert_article_to_response(article)


def _convert_article_to_response(article: Dict[str, Any]) -> NewsArticleResponse:
    """Convert article dict to NewsArticleResponse."""
    # Convert datetime strings back to datetime objects
    published_date = None
    if article.get('published_date'):
        try:
            published_date = datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
        except:
            pass
    
    created_at = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
    updated_at = None
    if article.get('updated_at'):
        try:
            updated_at = datetime.fromisoformat(article['updated_at'].replace('Z', '+00:00'))
        except:
            pass
    
    return NewsArticleResponse(
        article_name=article['article_name'],
        title=article['title'],
        summary=article.get('summary'),
        content=article.get('content'),
        link=article['link'],
        author=article.get('author'),
        published_date=published_date,
        category=article['category'],
        source_name=article['source_name'],
        source_url=article.get('source_url'),
        image_url=article.get('image_url'),
        is_processed=article.get('is_processed', False),
        created_at=created_at,
        updated_at=updated_at
    )


@router.get("/categories/{category}", response_model=NewsArticleList)
async def get_articles_by_category(
    category: NewsCategory,
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip")
):
    """Get articles by specific category."""
    s3_service = S3Service()
    
    # Get articles from S3 with category filter
    articles_data = s3_service.get_all_articles(
        limit=limit,
        offset=offset,
        category=category.value
    )
    
    # Convert to response format
    articles = []
    for article in articles_data['articles']:
        # Convert datetime strings back to datetime objects
        published_date = None
        if article.get('published_date'):
            try:
                published_date = datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
            except:
                pass
        
        created_at = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
        updated_at = None
        if article.get('updated_at'):
            try:
                updated_at = datetime.fromisoformat(article['updated_at'].replace('Z', '+00:00'))
            except:
                pass
        
        articles.append(NewsArticleResponse(
            article_name=article['article_name'],
            title=article['title'],
            summary=article.get('summary'),
            content=article.get('content'),
            link=article['link'],
            author=article.get('author'),
            published_date=published_date,
            category=article['category'],
            source_name=article['source_name'],
            source_url=article.get('source_url'),
            image_url=article.get('image_url'),
            is_processed=article.get('is_processed', False),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    has_more = (offset + limit) < articles_data['total']
    
    return NewsArticleList(
        articles=articles,
        total=articles_data['total'],
        limit=limit,
        offset=offset,
        has_more=has_more
    )


@router.get("/feeds", response_model=List[RSSFeedResponse])
async def get_feeds():
    """Get all configured RSS feeds."""
    s3_service = S3Service()
    feeds = s3_service.get_rss_feeds()
    
    # Convert to response format
    response_feeds = []
    for feed in feeds:
        if feed.get('is_active', True):
            created_at = None
            updated_at = None
            if feed.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(feed['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            if feed.get('updated_at'):
                try:
                    updated_at = datetime.fromisoformat(feed['updated_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            response_feeds.append(RSSFeedResponse(
                name=feed['name'],
                url=feed['url'],
                category=feed['category'],
                is_active=feed.get('is_active', True),
                created_at=created_at,
                updated_at=updated_at
            ))
    
    return response_feeds


@router.get("/logs", response_model=List[FeedFetchLogResponse])
async def get_fetch_logs(
    limit: int = Query(50, ge=1, le=100)
):
    """Get recent RSS fetch logs."""
    s3_service = S3Service()
    logs = s3_service.get_fetch_logs(limit=limit)
    
    # Convert to response format
    response_logs = []
    for log in logs:
        fetch_timestamp = datetime.fromisoformat(log['fetch_timestamp'].replace('Z', '+00:00'))
        
        response_logs.append(FeedFetchLogResponse(
            feed_name=log['feed_name'],
            fetch_timestamp=fetch_timestamp,
            status=log['status'],
            articles_found=log['articles_found'],
            articles_processed=log['articles_processed'],
            error_message=log.get('error_message'),
            execution_time=log.get('execution_time')
        ))
    
    return response_logs


@router.get("/feeds/status")
async def get_feeds_status():
    """Get status of all RSS feeds."""
    s3_service = S3Service()
    feeds = s3_service.get_rss_feeds()
    logs = s3_service.get_fetch_logs(limit=100)  # Get recent logs
    
    # Create a map of feed names to their recent logs
    feed_logs_map = {}
    for log in logs:
        feed_name = log['feed_name']
        if feed_name not in feed_logs_map:
            feed_logs_map[feed_name] = log
    
    feed_status = []
    for feed in feeds:
        recent_log = feed_logs_map.get(feed['name'])
        
        status = {
            "name": feed['name'],
            "url": feed['url'],
            "category": feed['category'],
            "is_active": feed.get('is_active', True),
            "last_fetch": recent_log['fetch_timestamp'] if recent_log else None,
            "last_status": recent_log['status'] if recent_log else None,
            "articles_found": recent_log['articles_found'] if recent_log else 0,
            "articles_processed": recent_log['articles_processed'] if recent_log else 0,
            "error_message": recent_log.get('error_message') if recent_log else None
        }
        feed_status.append(status)
    
    return feed_status


@router.post("/fetch")
async def fetch_all_feeds():
    """Manually trigger fetching of all RSS feeds."""
    service = RSSService()
    result = await service.fetch_all_feeds()
    
    # Update stats after fetching
    s3_service = S3Service()
    s3_service.update_stats()
    
    return {"message": "Feed fetching completed", "result": result}


@router.post("/fetch/{feed_name}")
async def fetch_specific_feed(feed_name: str):
    """Manually trigger fetching of a specific RSS feed."""
    from config.rss_feeds import get_feed_by_name
    
    feed = get_feed_by_name(feed_name)
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed '{feed_name}' not found")
    
    service = RSSService()
    result = await service.fetch_feed_async(feed)
    
    # Update stats after fetching
    s3_service = S3Service()
    s3_service.update_stats()
    
    return {
        "feed_name": feed.name,
        "category": feed.category.value,
        **result
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get news aggregation statistics."""
    try:
        s3_service = S3Service()
        stats = s3_service.get_stats()
        
        # Convert recent fetch logs to response format
        recent_fetch_logs = []
        for log in stats.get('recent_fetch_logs', []):
            fetch_timestamp = datetime.fromisoformat(log['fetch_timestamp'].replace('Z', '+00:00'))
            recent_fetch_logs.append(FeedFetchLogResponse(
                feed_name=log['feed_name'],
                fetch_timestamp=fetch_timestamp,
                status=log['status'],
                articles_found=log['articles_found'],
                articles_processed=log['articles_processed'],
                error_message=log.get('error_message'),
                execution_time=log.get('execution_time')
            ))
        
        last_updated = datetime.fromisoformat(stats['last_updated'].replace('Z', '+00:00'))
        
        return StatsResponse(
            total_feeds=stats['total_feeds'],
            active_feeds=stats['active_feeds'],
            total_articles=stats['total_articles'],
            articles_by_category=stats['articles_by_category'],
            articles_by_source=stats['articles_by_source'],
            recent_fetch_logs=recent_fetch_logs,
            last_updated=last_updated
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")


@router.post("/articles/{article_name}/extract", response_model=NewsArticleResponse)
async def extract_article_content(article_name: str):
    """Manually trigger content extraction for a specific article."""
    s3_service = S3Service()
    
    article = s3_service.get_article_by_name(article_name)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.get('link'):
        raise HTTPException(status_code=400, detail="Article has no link to extract content from")
    
    try:
        service = RSSService()
        content, extracted_image_url = await service.extract_article_content(article['link'])
        
        updates = {}
        
        # Update content if extracted
        if content:
            updates['content'] = content
            logger.info(f"Successfully extracted content for article {article_name}")
        
        # Update image_url if extracted and missing
        if extracted_image_url and (not article.get('image_url') or article['image_url'].strip() == ""):
            updates['image_url'] = extracted_image_url
            logger.info(f"Updated image URL for article {article_name}")
        
        # Update in S3 if any changes were made
        if updates:
            s3_service.update_article(article_name, updates)
            article.update(updates)
            logger.info(f"Article {article_name} updated with extracted content")
        else:
            logger.warning(f"No content extracted for article {article_name}")
        
        return _convert_article_to_response(article)
        
    except Exception as e:
        logger.error(f"Error extracting content for article {article_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting content: {str(e)}")


@router.get("/feeds/names")
async def get_feed_names():
    """Get list of feed names."""
    s3_service = S3Service()
    feeds = s3_service.get_rss_feeds()
    return [feed['name'] for feed in feeds if feed.get('is_active', True)]


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status."""
    return {"status": "running" if scheduler_service.scheduler.running else "stopped"}


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler."""
    scheduler_service.start()
    return {"message": "Scheduler started"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    scheduler_service.stop()
    return {"message": "Scheduler stopped"}





# Admin endpoints - Note: These endpoints should be protected with authentication in production
@router.delete("/admin/cleanup/all")
async def cleanup_all_data():
    """Clean up all data from S3."""
    service = RSSService()
    result = service.cleanup_all_data()
    return {"message": "All data cleaned up successfully", "deleted_counts": result}


@router.delete("/admin/cleanup/feed/{feed_name}")
async def cleanup_feed_data(feed_name: str):
    """Clean up data for a specific feed."""
    service = RSSService()
    deleted_count = service.cleanup_feed_data(feed_name)
    return {"message": f"Data for feed '{feed_name}' cleaned up successfully", "deleted_articles": deleted_count}


@router.delete("/admin/cleanup/article/{article_name}")
async def delete_article_content(article_name: str):
    """Delete content for a specific article."""
    service = RSSService()
    success = service.delete_article_content(article_name)
    if success:
        return {"message": f"Content for article {article_name} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Article not found")


@router.post("/admin/content/clean-batch")
async def clean_content_batch(
    batch_size: int = Query(100, ge=10, le=1000, description="Number of articles to process per batch")
):
    """Clean content for articles in batches."""
    service = RSSService()
    result = await service.clean_content_batch(batch_size)
    return result