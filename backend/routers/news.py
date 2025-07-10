"""
News API routes for fetching articles and managing RSS feeds.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func
from models.database import NewsArticle, RawFeedData, FeedFetchLog, RSSFeed

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


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute("SELECT 1")
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
        articles=articles,
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
        articles=articles,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/sources", response_model=List[str])
async def get_sources(db: Session = Depends(get_db)):
    """Get list of all news sources."""
    from models.database import NewsArticle
    sources = db.query(NewsArticle.source_name).distinct().all()
    return [source[0] for source in sources]


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


@router.post("/fetch")
async def fetch_all_feeds(db: Session = Depends(get_db)):
    """Manually trigger fetching of all RSS feeds."""
    service = RSSService(db)
    result = await service.fetch_all_feeds()
    return {
        "message": "Feed fetching completed",
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


@router.post("/articles/{article_id}/extract")
async def extract_article_content(article_id: int, db: Session = Depends(get_db)):
    """Manually extract content for a specific article."""
    from models.database import NewsArticle
    
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.link:
        raise HTTPException(status_code=400, detail="Article has no link to extract from")
    
    # Extract content
    service = RSSService(db)
    content = await service._extract_article_content(article.link)
    
    if content:
        article.content = content
        article.updated_at = datetime.now()
        db.commit()
        
        return {
            "message": "Content extracted successfully",
            "article_id": article_id,
            "content_length": len(content)
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to extract content")


@router.delete("/cleanup/all")
async def cleanup_all_data(db: Session = Depends(get_db)):
    """Clean up all data from the database."""
    
    try:
        # Delete all articles
        articles_deleted = db.query(NewsArticle).delete()
        
        # Delete all raw feed data
        raw_data_deleted = db.query(RawFeedData).delete()
        
        # Delete all fetch logs
        logs_deleted = db.query(FeedFetchLog).delete()
        
        db.commit()
        
        return {
            "message": "All data cleaned up successfully",
            "articles_deleted": articles_deleted,
            "raw_data_deleted": raw_data_deleted,
            "logs_deleted": logs_deleted
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cleanup data: {str(e)}")


@router.delete("/cleanup/feed/{feed_name}")
async def cleanup_feed_data(feed_name: str, db: Session = Depends(get_db)):
    """Clean up data for a specific feed."""
    print(f"Attempting to cleanup feed data for {feed_name}")
    try:
        feed_id = db.query(RSSFeed).filter(RSSFeed.name == feed_name).first().id
        # Delete articles from this feed
        articles_deleted = db.query(NewsArticle).filter(
            NewsArticle.source_name == feed_name
        ).delete()
        
        # Delete raw feed data for this feed
        raw_data_deleted = db.query(RawFeedData).filter(
            RawFeedData.feed_id == feed_id
        ).delete()
        
        # Delete fetch logs for this feed
        logs_deleted = db.query(FeedFetchLog).filter(
            FeedFetchLog.feed_name == feed_name
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Data for feed '{feed_name}' cleaned up successfully",
            "feed_name": feed_name,
            "articles_deleted": articles_deleted,
            "raw_data_deleted": raw_data_deleted,
            "logs_deleted": logs_deleted
        }
    except Exception as e:
        print(f"Error cleaning up feed data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cleanup feed data: {str(e)}")


@router.get("/feeds/names")
async def get_feed_names(db: Session = Depends(get_db)):
    """Get list of all feed names."""
    from models.database import RSSFeed
    
    feeds = db.query(RSSFeed.name).all()
    return {"feed_names": [feed[0] for feed in feeds]}


@router.post("/google-news/search")
async def search_google_news(
    query: str = "",
    category: str = "all",
    time_filter: str = "24h",
    max_results: int = 50,
    db: Session = Depends(get_db)
):
    """Search Google News and save results to database."""
    from services.google_news_service import GoogleNewsService
    
    service = GoogleNewsService(db)
    result = await service.fetch_and_save_google_news(query, category, time_filter, max_results)
    
    return result


@router.get("/google-news/search")
async def search_google_news_only(
    query: str = "",
    category: str = "all",
    time_filter: str = "24h",
    max_results: int = 50,
    db: Session = Depends(get_db)
):
    """Search Google News without saving to database (for preview)."""
    from services.google_news_service import GoogleNewsService
    
    service = GoogleNewsService(db)
    articles = await service.search_news(query, category, time_filter, max_results)
    
    return {
        "articles": articles,
        "total": len(articles),
        "query": query,
        "category": category,
        "time_filter": time_filter
    } 