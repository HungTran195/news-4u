"""
News API routes for fetching articles and managing RSS feeds.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy import func
from models.database import NewsArticle, FeedFetchLog, RSSFeed
from config.rss_feeds import RSSFeedCreate

from database import get_db
from services.rss_service import RSSService
from services.scheduler_service import scheduler_service
from schemas.news import (
    NewsArticleResponse, 
    NewsArticleList, 
    RSSFeedResponse,
    FeedFetchLogResponse,
    HealthCheckResponse
)
from config.rss_feeds import NewsCategory, get_all_feeds

router = APIRouter(prefix="/api/news", tags=["news"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        database_connected = True
        
        # Get counts
        from models.database import RSSFeed, NewsArticle
        feeds_count = db.query(RSSFeed).count()
        articles_count = db.query(NewsArticle).count()
        
    except Exception as e:
        database_connected = False
        feeds_count = 0
        articles_count = 0
    
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(),
        database_connected=database_connected,
        feeds_count=feeds_count,
        articles_count=articles_count
    )


@router.get("/articles", response_model=NewsArticleList)
async def get_articles(
    category: Optional[NewsCategory] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    feeds: Optional[str] = Query(None, description="Comma-separated list of feed names to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Articles per page"),
    db: Session = Depends(get_db)
):
    logger.info(f"---- Getting articles with filters: category={category}, source={source}, feeds={feeds}, page={page}, per_page={per_page} ----")
    """Get articles with optional filtering and pagination."""
    service = RSSService(db)
    offset = (page - 1) * per_page
    
    # Build query with filters
    from models.database import NewsArticle
    query = db.query(NewsArticle)
    
    if category:
        query = query.filter(NewsArticle.category == category.value)
    
    if source:
        query = query.filter(NewsArticle.source_name == source)
    
    if feeds:
        feed_names = [name.strip() for name in feeds.split(',') if name.strip()]
        if feed_names:
            query = query.filter(NewsArticle.source_name.in_(feed_names))
    
    # Get total count for pagination
    total = query.count()
    
    # Get paginated results
    articles = query.order_by(NewsArticle.published_date.desc().nullslast(), NewsArticle.created_at.desc()) \
                   .offset(offset) \
                   .limit(per_page) \
                   .all()
    
    total_pages = (total + per_page - 1) // per_page

    
    return NewsArticleList(
        articles=[NewsArticleResponse.model_validate(article) for article in articles],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/articles/{article_id}", response_model=NewsArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific article by ID. Automatically extracts content if missing."""
    from models.database import NewsArticle
    import logging
    logger = logging.getLogger("get_article")
    
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if article has content, if not, extract it automatically
    if not getattr(article, "content", None) or str(getattr(article, "content", "")).strip() == "":
        logger.info(f"Article {article_id} has no content, extracting automatically")
        
        if not getattr(article, "link", None):
            logger.warning(f"Article {article_id} has no link, cannot extract content")
            return article
        
        try:
            service = RSSService(db)
            content, extracted_image_url = await service.extract_article_content(getattr(article, "link"))
            
            updated = False
            
            # Update content if extracted
            if content:
                setattr(article, "content", content)
                updated = True
                logger.info(f"Successfully extracted content for article {article_id}")
            
            # Update image_url if extracted and missing
            if extracted_image_url and (not getattr(article, "image_url", None) or str(getattr(article, "image_url", "")).strip() == ""):
                setattr(article, "image_url", extracted_image_url)
                updated = True
                logger.info(f"Updated image URL for article {article_id}")
            
            # Update timestamp if any changes were made
            if updated:
                setattr(article, "updated_at", datetime.now())
                db.commit()
                logger.info(f"Article {article_id} updated with extracted content")
            
        except Exception as e:
            logger.error(f"Error extracting content for article {article_id}: {e}")
            # Continue and return the article even if extraction fails
    
    return article


@router.get("/articles/slug/{slug}", response_model=NewsArticleResponse)
async def get_article_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific article by slug. Automatically extracts content if missing."""
    from models.database import NewsArticle
    import logging
    logger = logging.getLogger("get_article_by_slug")
    
    article = db.query(NewsArticle).filter(NewsArticle.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if article has content, if not, extract it automatically
    if not getattr(article, "content", None) or str(getattr(article, "content", "")).strip() == "":
        logger.info(f"Article {article.id} (slug: {slug}) has no content, extracting automatically")
        
        if not getattr(article, "link", None):
            logger.warning(f"Article {article.id} has no link, cannot extract content")
            return article
        
        try:
            service = RSSService(db)
            content, extracted_image_url = await service.extract_article_content(getattr(article, "link"))
            
            updated = False
            
            # Update content if extracted
            if content:
                setattr(article, "content", content)
                updated = True
                logger.info(f"Successfully extracted content for article {article.id}")
            
            # Update image_url if extracted and missing
            if extracted_image_url and (not getattr(article, "image_url", None) or str(getattr(article, "image_url", "")).strip() == ""):
                setattr(article, "image_url", extracted_image_url)
                updated = True
                logger.info(f"Updated image URL for article {article.id}")
            
            # Update timestamp if any changes were made
            if updated:
                setattr(article, "updated_at", datetime.now())
                db.commit()
                logger.info(f"Article {article.id} updated with extracted content")
            
        except Exception as e:
            logger.error(f"Error extracting content for article {article.id}: {e}")
            # Continue and return the article even if extraction fails
    
    return article


@router.get("/categories/{category}", response_model=NewsArticleList)
async def get_articles_by_category(
    category: NewsCategory,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get articles by specific category."""
    service = RSSService(db)
    offset = (page - 1) * per_page
    
    query = db.query(NewsArticle).filter(NewsArticle.category == category.value)
    total = query.count()
    
    articles = query.order_by(NewsArticle.published_date.desc().nullslast(), NewsArticle.created_at.desc()) \
                   .offset(offset) \
                   .limit(per_page) \
                   .all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return NewsArticleList(
        articles=[NewsArticleResponse.model_validate(article) for article in articles],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/feeds", response_model=List[RSSFeedResponse])
async def get_feeds(db: Session = Depends(get_db)):
    """Get all configured RSS feeds."""
    feeds = db.query(RSSFeed).filter(RSSFeed.is_active == True).all()
    return [RSSFeedResponse.model_validate(feed) for feed in feeds]


@router.get("/logs", response_model=List[FeedFetchLogResponse])
async def get_fetch_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent RSS fetch logs."""
    logs = db.query(FeedFetchLog).order_by(FeedFetchLog.fetch_timestamp.desc()).limit(limit).all()
    return [FeedFetchLogResponse.model_validate(log) for log in logs]


@router.get("/feeds/status")
async def get_feeds_status(db: Session = Depends(get_db)):
    """Get status of all RSS feeds."""
    feeds = db.query(RSSFeed).all()
    
    # Get recent logs for each feed
    feed_status = []
    for feed in feeds:
        recent_log = db.query(FeedFetchLog).filter(
            FeedFetchLog.feed_name == feed.name
        ).order_by(FeedFetchLog.fetch_timestamp.desc()).first()
        
        status = {
            "name": feed.name,
            "url": feed.url,
            "category": feed.category,
            "is_active": feed.is_active,
            "last_fetch": recent_log.fetch_timestamp if recent_log else None,
            "last_status": recent_log.status if recent_log else None,
            "articles_found": recent_log.articles_found if recent_log else 0,
            "articles_processed": recent_log.articles_processed if recent_log else 0,
            "error_message": recent_log.error_message if recent_log else None
        }
        feed_status.append(status)
    
    return feed_status


@router.post("/fetch")
async def fetch_all_feeds(db: Session = Depends(get_db)):
    """Manually trigger fetching of all RSS feeds."""
    service = RSSService(db)
    result = await service.fetch_all_feeds()
    return {"message": "Feed fetching completed", "result": result}


@router.post("/fetch/{feed_name}")
async def fetch_specific_feed(feed_name: str, db: Session = Depends(get_db)):
    """Manually trigger fetching of a specific RSS feed."""
    from config.rss_feeds import get_feed_by_name
    
    feed = get_feed_by_name(feed_name)
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed '{feed_name}' not found")
    
    service = RSSService(db)
    result = await service.fetch_feed_async(feed)
    
    return {
        "feed_name": feed.name,
        "category": feed.category.value,
        **result
    }


@router.post("/feeds/{feed_name}/toggle")
async def toggle_feed_status(feed_name: str, db: Session = Depends(get_db)):
    """Toggle the active status of a feed."""
    service = RSSService(db)
    result = service.toggle_feed_status(feed_name)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get news aggregation statistics."""
    # Get articles by category
    category_stats = db.query(
        NewsArticle.category,
        func.count(NewsArticle.id).label('count')
    ).group_by(NewsArticle.category).all()
    
    articles_by_category = {stat.category: stat.count for stat in category_stats}
    
    # Get articles by source
    source_stats = db.query(
        NewsArticle.source_name,
        func.count(NewsArticle.id).label('count')
    ).group_by(NewsArticle.source_name).all()
    
    articles_by_source = {stat.source_name: stat.count for stat in source_stats}
    
    # Get recent articles
    recent_articles = db.query(NewsArticle).order_by(NewsArticle.created_at.desc()).limit(5).all()
    
    # Get feed counts
    active_feeds = db.query(RSSFeed).filter(RSSFeed.is_active == True).count()
    total_feeds = db.query(RSSFeed).count()
    
    return {
        "total_articles": db.query(NewsArticle).count(),
        "articles_by_category": articles_by_category,
        "articles_by_source": articles_by_source,
        "recent_articles": [
            {
                "id": article.id,
                "title": article.title,
                "source_name": article.source_name,
                "created_at": article.created_at
            }
            for article in recent_articles
        ],
        "active_feeds": active_feeds,
        "total_feeds": total_feeds,
        "last_updated": datetime.now()
    }


@router.post("/articles/{article_id}/extract", response_model=NewsArticleResponse)
async def extract_article_content(article_id: int, db: Session = Depends(get_db)):
    """Manually trigger content extraction for a specific article."""
    from models.database import NewsArticle
    
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.link:
        raise HTTPException(status_code=400, detail="Article has no link to extract content from")
    
    try:
        service = RSSService(db)
        content, extracted_image_url = await service.extract_article_content(article.link)
        
        updated = False
        
        # Update content if extracted
        if content:
            article.content = content
            updated = True
            logger.info(f"Successfully extracted content for article {article_id}")
        
        # Update image_url if extracted and missing
        if extracted_image_url and (not article.image_url or article.image_url.strip() == ""):
            article.image_url = extracted_image_url
            updated = True
            logger.info(f"Updated image URL for article {article_id}")
        
        # Update timestamp if any changes were made
        if updated:
            article.updated_at = datetime.now()
            db.commit()
            logger.info(f"Article {article_id} updated with extracted content")
        else:
            logger.warning(f"No content extracted for article {article_id}")
        
        return NewsArticleResponse.model_validate(article)
        
    except Exception as e:
        logger.error(f"Error extracting content for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting content: {str(e)}")


@router.get("/feeds/names")
async def get_feed_names(db: Session = Depends(get_db)):
    """Get list of feed names."""
    feeds = db.query(RSSFeed.name).all()
    return [feed.name for feed in feeds]


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


@router.get("/search", response_model=NewsArticleList)
async def search_articles(
    query: str = Query("", description="Search query"),
    category: str = Query("all", description="Filter by category"),
    time_filter: str = Query("24h", description="Time filter"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Articles per page"),
    db: Session = Depends(get_db)
):
    """Search articles by query with optional filters."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query is required")
    
    offset = (page - 1) * per_page
    
    # Build search query
    search_query = db.query(NewsArticle).filter(
        NewsArticle.title.contains(query) | 
        NewsArticle.summary.contains(query) |
        NewsArticle.content.contains(query)
    )
    
    # Apply category filter
    if category != "all":
        search_query = search_query.filter(NewsArticle.category == category)
    
    # Apply time filter
    if time_filter == "24h":
        time_threshold = datetime.now() - timedelta(hours=24)
        search_query = search_query.filter(NewsArticle.created_at >= time_threshold)
    elif time_filter == "7d":
        time_threshold = datetime.now() - timedelta(days=7)
        search_query = search_query.filter(NewsArticle.created_at >= time_threshold)
    elif time_filter == "30d":
        time_threshold = datetime.now() - timedelta(days=30)
        search_query = search_query.filter(NewsArticle.created_at >= time_threshold)
    
    # Get total count
    total = search_query.count()
    
    # Get paginated results
    articles = search_query.order_by(NewsArticle.published_date.desc().nullslast(), NewsArticle.created_at.desc()) \
                          .offset(offset) \
                          .limit(per_page) \
                          .all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return NewsArticleList(
        articles=[NewsArticleResponse.model_validate(article) for article in articles],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


# Admin endpoints - Note: These endpoints should be protected with authentication in production
@router.delete("/admin/cleanup/all")
async def cleanup_all_data(db: Session = Depends(get_db)):
    """Clean up all data from the database."""
    service = RSSService(db)
    await service.cleanup_all_data()
    return {"message": "All data cleaned up successfully"}


@router.delete("/admin/cleanup/feed/{feed_name}")
async def cleanup_feed_data(feed_name: str, db: Session = Depends(get_db)):
    """Clean up data for a specific feed."""
    service = RSSService(db)
    await service.cleanup_feed_data(feed_name)
    return {"message": f"Data for feed '{feed_name}' cleaned up successfully"}


@router.delete("/admin/cleanup/article/{article_id}")
async def delete_article_content(article_id: int, db: Session = Depends(get_db)):
    """Delete content for a specific article."""
    service = RSSService(db)
    await service.delete_article_content(article_id)
    return {"message": f"Content for article {article_id} deleted successfully"}


@router.post("/admin/content/clean-batch")
async def clean_content_batch(
    batch_size: int = Query(100, ge=10, le=1000, description="Number of articles to process per batch"),
    db: Session = Depends(get_db)
):
    """Clean content for articles in batches."""
    service = RSSService(db)
    result = await service.clean_content_batch(batch_size)
    return result

@router.delete("/admin/feeds/delete/{feed_name}")
async def delete_feed(feed_name: str, db: Session = Depends(get_db)):
    """Delete a feed."""
    service = RSSService(db)
    service.delete_feed(feed_name)
    return {"message": f"Feed '{feed_name}' deleted successfully"}


@router.post("/admin/feeds/add")
async def add_feed(feed: RSSFeedCreate, db: Session = Depends(get_db)):
    """Add a feed."""
    db_feed = RSSFeed(**feed.model_dump())

    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return {"message": f"Feed {feed.name} added successfully"}
