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
    # Extract content and images
    content, images = await service._extract_article_content_and_images(getattr(article, "link"))

    updated = False
    updated_fields = []

    # Update content if empty and new content is found
    if (getattr(article, "content", None) is None or str(getattr(article, "content", "")).strip() == "") and content:
        setattr(article, "content", content)
        updated = True
        updated_fields.append("content")

    # Update image_url if empty and new image is found
    if (getattr(article, "image_url", None) is None or str(getattr(article, "image_url", "")).strip() == "") and images:
        setattr(article, "image_url", images[0])
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


@router.post("/extract-content", response_model=Dict[str, Any])
async def extract_content_from_url(
    request: ContentExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extract content and images from any URL for testing purposes.
    """
    try:
        rss_service = RSSService(db)
        
        # Extract content and images
        content, images = await rss_service._extract_article_content_and_images(request.url)
        
        # Count embedded images in content
        embedded_image_count = 0
        if content:
            embedded_image_count = content.count('[IMAGE:')
        
        return {
            "success": True,
            "url": request.url,
            "content": content,
            "content_length": len(content) if content else 0,
            "embedded_images": embedded_image_count,
            "standalone_images": images,
            "standalone_image_count": len(images),
            "extracted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extracting content from {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract content: {str(e)}"
        )


@router.get("/feeds/names")
async def get_feed_names(db: Session = Depends(get_db)):
    """Get list of all feed names."""
    from models.database import RSSFeed
    
    feeds = db.query(RSSFeed.name).all()
    return {"feed_names": [feed[0] for feed in feeds]}


@router.post("/search")
async def search_articles(
    query: str = "",
    category: str = "all",
    time_filter: str = "24h",
    max_results: int = 50,
    db: Session = Depends(get_db)
):
    """Search articles in the database."""
    from services.rss_service import RSSService
    service = RSSService(db)
    articles = await service.search_articles(query, category, time_filter, max_results)
    return articles


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
    await service.cleanup_all_data()
    return {"message": "All data cleaned up successfully"}

@router.delete("/admin/cleanup/feed/{feed_name}")
async def cleanup_feed_data(feed_name: str, db: Session = Depends(get_db)):
    """Clean up data for a specific feed."""
    from services.rss_service import RSSService
    service = RSSService(db)
    await service.cleanup_feed_data(feed_name)
    return {"message": f"Data for feed '{feed_name}' cleaned up successfully"} 
    