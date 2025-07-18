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
from models.database import NewsArticle, RawFeedData, FeedFetchLog, RSSFeed

class ContentExtractionRequest(BaseModel):
    url: str

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
    """Get a specific article by ID."""
    from models.database import NewsArticle
    
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@router.get("/articles/slug/{slug}", response_model=NewsArticleResponse)
async def get_article_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific article by slug."""
    from models.database import NewsArticle
    
    article = db.query(NewsArticle).filter(NewsArticle.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
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
    articles = service.get_articles_by_category(category, per_page, offset)
    
    # Get total count
    from models.database import NewsArticle
    total = db.query(NewsArticle).filter(
        NewsArticle.category == category.value
    ).count()
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
    from models.database import RSSFeed
    feeds = db.query(RSSFeed).filter(RSSFeed.is_active == True).all()
    return feeds


@router.get("/logs", response_model=List[FeedFetchLogResponse])
async def get_fetch_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent RSS fetch logs."""
    from models.database import FeedFetchLog
    logs = db.query(FeedFetchLog).order_by(
        FeedFetchLog.fetch_timestamp.desc()
    ).limit(limit).all()
    return logs


@router.get("/feeds/status")
async def get_feeds_status(db: Session = Depends(get_db)):
    """Get status and last fetch time for all feeds."""
    from models.database import FeedFetchLog, RSSFeed
    
    # Get all feeds
    feeds = db.query(RSSFeed).all()
    
    # Get latest fetch log for each feed
    feed_status = []
    for feed in feeds:
        latest_log = db.query(FeedFetchLog).filter(
            FeedFetchLog.feed_name == feed.name
        ).order_by(
            FeedFetchLog.fetch_timestamp.desc()
        ).first()
        
        feed_status.append({
            "name": feed.name,
            "category": feed.category,
            "is_active": feed.is_active,
            "last_fetch": latest_log.fetch_timestamp if latest_log else None,
            "last_status": latest_log.status if latest_log else None,
            "last_articles_found": latest_log.articles_found if latest_log else 0,
            "last_articles_processed": latest_log.articles_processed if latest_log else 0
        })
    
    return feed_status


@router.post("/fetch")
async def fetch_all_feeds(db: Session = Depends(get_db)):
    """Manually trigger fetching of all RSS feeds."""
    service = RSSService(db)
    result = await service.fetch_all_feeds()
    return {
        "message": "Feed fetching completed",
        "result": result
    }


@router.post("/fetch/{feed_name}")
async def fetch_specific_feed(feed_name: str, db: Session = Depends(get_db)):
    """Manually trigger fetching of a specific RSS feed."""
    from config.rss_feeds import get_all_feeds
    
    # Find the feed by name
    feeds = get_all_feeds()
    target_feed = None
    for feed in feeds:
        if feed.name.lower() == feed_name.lower():
            target_feed = feed
            break
    
    if not target_feed:
        raise HTTPException(status_code=404, detail=f"Feed '{feed_name}' not found")
    
    service = RSSService(db)
    result = await service.fetch_feed_async(target_feed)
    
    return {
        "message": f"Feed '{feed_name}' fetching completed",
        "feed_name": feed_name,
        "result": result
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get news aggregation statistics."""
    from models.database import NewsArticle, RSSFeed, FeedFetchLog
    # TODO: optimize this. No need to run this query every time.
    # Article counts by category
    category_stats = db.query(
        NewsArticle.category,
        func.count(NewsArticle.id).label('count')
    ).group_by(NewsArticle.category).all()
    
    # Source counts
    source_stats = db.query(
        NewsArticle.source_name,
        func.count(NewsArticle.id).label('count')
    ).group_by(NewsArticle.source_name).all()
    
    # Recent activity
    recent_articles = db.query(NewsArticle).order_by(
        NewsArticle.created_at.desc()
    ).limit(5).all()
    
    # Feed status
    active_feeds = db.query(RSSFeed).filter(RSSFeed.is_active == True).count()
    total_feeds = db.query(RSSFeed).count()
    
    return {
        "total_articles": db.query(NewsArticle).count(),
        "articles_by_category": {cat: count for cat, count in category_stats},
        "articles_by_source": {src: count for src, count in source_stats},
        "recent_articles": recent_articles,
        "active_feeds": active_feeds,
        "total_feeds": total_feeds,
        "last_updated": datetime.now()
    }


@router.post("/articles/{article_id}/extract", response_model=NewsArticleResponse)
async def extract_article_content(article_id: int, db: Session = Depends(get_db)):
    """Manually extract content for a specific article and update missing fields."""
    from models.database import NewsArticle
    import logging
    logger = logging.getLogger("extract_article_content")

    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    if not getattr(article, "link", None):
        raise HTTPException(status_code=400, detail="Article has no link to extract from")

    service = RSSService(db)
    # Extract content (this will also update image_url if missing)
    if getattr(article, "content", None) is None or str(getattr(article, "content", "")).strip() == "":
        logger.info(f"Extracting content for article {article_id}")
        content, extracted_image_url = await service.extract_article_content(getattr(article, "link"))
    else:
        logger.info(f"Article {article_id} already has content, skipping extraction")
        content = getattr(article, "content", None)
        extracted_image_url = getattr(article, "image_url", None)

    updated = False
    updated_fields = []

    # Update content if empty and new content is found
    if (getattr(article, "content", None) is None or str(getattr(article, "content", "")).strip() == "") and content:
        setattr(article, "content", content)
        updated = True
        updated_fields.append("content")

    # Update image_url if it was extracted by the service
    if extracted_image_url and (not getattr(article, "image_url", None) or str(getattr(article, "image_url", "")).strip() == ""):
        setattr(article, "image_url", extracted_image_url)
        updated = True
        updated_fields.append("image_url")

    # Try to extract author from meta tags if missing
    if getattr(article, "author", None) is None or str(getattr(article, "author", "")).strip() == "":
        try:
            import httpx
            from bs4 import BeautifulSoup
            from bs4.element import Tag
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(getattr(article, "link"))
                soup = BeautifulSoup(response.text, 'html.parser')
                author_tag = soup.find('meta', attrs={'name': 'author'})
                if author_tag and isinstance(author_tag, Tag) and author_tag.get('content'):
                    author_val = author_tag.get('content', None)
                    if isinstance(author_val, str):
                        setattr(article, "author", author_val)
                        updated = True
                        updated_fields.append("author")
        except Exception as e:
            logger.warning(f"Could not extract author: {e}")

    # Try to extract summary/description if missing
    if getattr(article, "summary", None) is None or str(getattr(article, "summary", "")).strip() == "":
        try:
            import httpx
            from bs4 import BeautifulSoup
            from bs4.element import Tag
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(getattr(article, "link"))
                soup = BeautifulSoup(response.text, 'html.parser')
                desc_tag = soup.find('meta', attrs={'name': 'description'})
                if desc_tag and isinstance(desc_tag, Tag) and desc_tag.get('content'):
                    desc_val = desc_tag.get('content', None)
                    if isinstance(desc_val, str):
                        setattr(article, "summary", desc_val)
                        updated = True
                        updated_fields.append("summary")
        except Exception as e:
            logger.warning(f"Could not extract summary: {e}")

    if updated:
        setattr(article, "updated_at", datetime.now())
        db.commit()
        logger.info(f"Article {article_id} updated fields: {', '.join(updated_fields)}")
    else:
        logger.info(f"Article {article_id} extracted, but no new fields to update.")

    return NewsArticleResponse.model_validate(article)


@router.get("/feeds/names")
async def get_feed_names(db: Session = Depends(get_db)):
    """Get list of all feed names."""
    from models.database import RSSFeed
    
    feeds = db.query(RSSFeed.name).all()
    return {"feed_names": [feed[0] for feed in feeds]}


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get the status of the scheduler and its jobs."""
    return scheduler_service.get_job_status()


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler."""
    scheduler_service.start()
    return {"message": "Scheduler started successfully"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    scheduler_service.stop()
    return {"message": "Scheduler stopped successfully"}


@router.get("/search", response_model=NewsArticleList)
async def search_articles(
    query: str = Query("", description="Search query"),
    category: str = Query("all", description="Filter by category"),
    time_filter: str = Query("24h", description="Time filter"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Articles per page"),
    db: Session = Depends(get_db)
):
    """Search articles in the database with pagination."""
    from services.rss_service import RSSService
    from models.database import NewsArticle
    from sqlalchemy import or_
    from datetime import datetime, timedelta
    
    service = RSSService(db)
    offset = (page - 1) * per_page
    
    # Build search query
    search_query = db.query(NewsArticle)
    
    # Apply search filter
    if query.strip():
        search_term = f"%{query.strip()}%"
        search_query = search_query.filter(
            or_(
                NewsArticle.title.ilike(search_term),
                NewsArticle.summary.ilike(search_term),
                NewsArticle.content.ilike(search_term)
            )
        )
    
    # Apply category filter
    if category and category != "all":
        search_query = search_query.filter(NewsArticle.category == category)
    
    # Apply time filter
    if time_filter and time_filter != "all":
        now = datetime.now()
        if time_filter == "1h":
            time_threshold = now - timedelta(hours=1)
        elif time_filter == "24h":
            time_threshold = now - timedelta(days=1)
        elif time_filter == "7d":
            time_threshold = now - timedelta(days=7)
        elif time_filter == "1m":
            time_threshold = now - timedelta(days=30)
        else:
            time_threshold = now - timedelta(days=1)  # default to 24h
        
        search_query = search_query.filter(NewsArticle.published_date >= time_threshold)
    
    # Get total count for pagination
    total = search_query.count()
    
    # Get paginated results
    articles = search_query.order_by(
        NewsArticle.published_date.desc().nullslast(), 
        NewsArticle.created_at.desc()
    ).offset(offset).limit(per_page).all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return NewsArticleList(
        articles=[NewsArticleResponse.model_validate(article) for article in articles],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


"""
--------------------------------
Admin endpoints
These endpoints are used to clean up the database.
--------------------------------
"""
# TODO: Add authentication to these endpoints.
@router.delete("/admin/cleanup/all")
async def cleanup_all_data(db: Session = Depends(get_db)):
    """Clean up all data from the database."""
    from services.rss_service import RSSService
    service = RSSService(db)
    logger.warning("---- Cleaning up all data ----")
    await service.cleanup_all_data()
    return {"message": "All data cleaned up successfully"}

@router.delete("/admin/cleanup/feed/{feed_name}")
async def cleanup_feed_data(feed_name: str, db: Session = Depends(get_db)):
    """Clean up data for a specific feed."""
    from services.rss_service import RSSService
    service = RSSService(db)
    logger.warning(f"---- Cleaning up data for feed '{feed_name}' ----")
    await service.cleanup_feed_data(feed_name)
    return {"message": f"Data for feed '{feed_name}' cleaned up successfully"} 

@router.delete("/admin/cleanup/article/{article_id}")
async def delete_article_content(article_id: int, db: Session = Depends(get_db)):
    """Clean up data for a specific article."""
    from services.rss_service import RSSService
    service = RSSService(db)
    logger.warning(f"---- Deleting content for article '{article_id}' ----")
    await service.delete_article_content(article_id)
    return {"message": f"Content for article '{article_id}' deleted successfully"}

@router.post("/admin/content/clean-batch")
async def clean_content_batch(
    batch_size: int = Query(100, ge=10, le=1000, description="Number of articles to process per batch"),
    db: Session = Depends(get_db)
):
    """
    Clean HTML content for all articles in the database by removing class names, IDs, and data attributes.
    This endpoint processes articles in batches to avoid memory issues with large databases.
    """
    from services.rss_service import RSSService
    service = RSSService(db)
    logger.info(f"---- Starting batch content cleaning with batch size {batch_size} ----")
    
    result = await service.clean_content_batch(batch_size)
    
    if result["status"] == "success":
        logger.info(f"---- Batch content cleaning completed: {result['message']} ----")
    else:
        logger.error(f"---- Batch content cleaning failed: {result['message']} ----")
    
    return result