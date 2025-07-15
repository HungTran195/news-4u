"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List
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


class RSSFeedResponse(RSSFeedBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class NewsArticleResponse(NewsArticleBase):
    id: int
    is_processed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsArticleList(BaseModel):
    articles: List[NewsArticleResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class FeedFetchLogResponse(BaseModel):
    id: int
    feed_name: str
    fetch_timestamp: datetime
    status: str
    articles_found: int
    articles_processed: int
    error_message: Optional[str] = None
    execution_time: Optional[int] = None

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool
    feeds_count: int
    articles_count: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now() 