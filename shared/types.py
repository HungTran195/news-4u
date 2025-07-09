"""
Shared type definitions for the News 4U project.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime


class NewsCategory(str, Enum):
    TECH = "tech"
    FINANCE = "finance"
    GLOBAL_NEWS = "global_news"


class NewsArticle:
    """News article data structure."""
    
    def __init__(
        self,
        id: int,
        title: str,
        link: str,
        category: NewsCategory,
        source_name: str,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        author: Optional[str] = None,
        published_date: Optional[datetime] = None,
        source_url: Optional[str] = None,
        image_url: Optional[str] = None,
        is_processed: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.title = title
        self.link = link
        self.category = category
        self.source_name = source_name
        self.summary = summary
        self.content = content
        self.author = author
        self.published_date = published_date
        self.source_url = source_url
        self.image_url = image_url
        self.is_processed = is_processed
        self.created_at = created_at
        self.updated_at = updated_at


class RSSFeed:
    """RSS feed configuration."""
    
    def __init__(
        self,
        name: str,
        url: str,
        category: NewsCategory,
        description: Optional[str] = None,
        is_active: bool = True,
    ):
        self.name = name
        self.url = url
        self.category = category
        self.description = description
        self.is_active = is_active


class FeedFetchLog:
    """RSS feed fetch log entry."""
    
    def __init__(
        self,
        feed_name: str,
        status: str,
        articles_found: int = 0,
        articles_processed: int = 0,
        error_message: Optional[str] = None,
        execution_time: Optional[int] = None,
        fetch_timestamp: Optional[datetime] = None,
    ):
        self.feed_name = feed_name
        self.status = status
        self.articles_found = articles_found
        self.articles_processed = articles_processed
        self.error_message = error_message
        self.execution_time = execution_time
        self.fetch_timestamp = fetch_timestamp or datetime.now()


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck:
    """Health check response."""
    
    def __init__(
        self,
        status: HealthStatus,
        timestamp: datetime,
        database_connected: bool,
        feeds_count: int,
        articles_count: int,
    ):
        self.status = status
        self.timestamp = timestamp
        self.database_connected = database_connected
        self.feeds_count = feeds_count
        self.articles_count = articles_count 