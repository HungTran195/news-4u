"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from config.rss_feeds import NewsCategory


class RSSFeedBase(BaseModel):
    name: str
    url: str
    category: NewsCategory


class RSSFeedCreate(RSSFeedBase):
    pass


class RSSFeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[NewsCategory] = None
    is_active: Optional[bool] = None


class RSSFeedResponse(BaseModel):
    name: str
    url: str
    category: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NewsArticleBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    link: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    category: str
    source_name: str
    source_url: Optional[str] = None
    image_url: Optional[str] = None


class NewsArticleCreate(NewsArticleBase):
    pass


class NewsArticleResponse(BaseModel):
    article_name: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    link: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    category: str
    source_name: str
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    is_processed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class NewsArticleList(BaseModel):
    articles: List[NewsArticleResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class FeedFetchLogResponse(BaseModel):
    feed_name: str
    fetch_timestamp: datetime
    status: str
    articles_found: int
    articles_processed: int
    error_message: Optional[str] = None
    execution_time: Optional[int] = None


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    s3_connected: bool
    feeds_count: int
    articles_count: int


class StatsResponse(BaseModel):
    """Response model for statistics."""
    total_feeds: int
    active_feeds: int
    total_articles: int
    articles_by_category: Dict[str, int]
    articles_by_source: Dict[str, int]
    recent_fetch_logs: List[FeedFetchLogResponse]
    last_updated: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now() 