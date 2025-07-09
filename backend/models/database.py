"""
Database models for the news aggregation system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class RSSFeed(Base):
    """Model for storing RSS feed information."""
    __tablename__ = "rss_feeds"
    
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    url = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to raw feed data
    raw_feeds = relationship("RawFeedData", back_populates="feed", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_feed_category', 'category'),
        Index('idx_feed_active', 'is_active'),
    )


class RawFeedData(Base):
    """Model for storing raw RSS feed data before processing."""
    __tablename__ = "raw_feed_data"
    
    id = Column(BigInteger, primary_key=True, index=True)
    feed_id = Column(BigInteger, ForeignKey("rss_feeds.id", ondelete="CASCADE"), nullable=False)
    raw_content = Column(Text, nullable=False)  # Raw XML content
    fetch_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status_code = Column(Integer)
    error_message = Column(Text)
    
    # Relationship to RSS feed
    feed = relationship("RSSFeed", back_populates="raw_feeds")
    
    __table_args__ = (
        Index('idx_raw_feed_timestamp', 'fetch_timestamp'),
        Index('idx_raw_feed_id', 'feed_id'),
    )


class NewsArticle(Base):
    """Model for storing processed news articles."""
    __tablename__ = "news_articles"
    
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    summary = Column(Text)
    content = Column(Text)
    link = Column(String(1000), nullable=False, unique=True, index=True)
    author = Column(String(255))
    published_date = Column(DateTime(timezone=True))
    category = Column(String(50), nullable=False, index=True)
    source_name = Column(String(255), nullable=False, index=True)
    source_url = Column(String(500))
    image_url = Column(String(1000))
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_article_category', 'category'),
        Index('idx_article_source', 'source_name'),
        Index('idx_article_published', 'published_date'),
        Index('idx_article_processed', 'is_processed'),
        Index('idx_article_title', 'title'),
    )


class FeedFetchLog(Base):
    """Model for logging RSS feed fetch operations."""
    __tablename__ = "feed_fetch_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    feed_name = Column(String(255), nullable=False, index=True)
    fetch_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False)  # success, error, partial
    articles_found = Column(Integer, default=0)
    articles_processed = Column(Integer, default=0)
    error_message = Column(Text)
    execution_time = Column(Integer)  # in milliseconds
    
    __table_args__ = (
        Index('idx_log_feed_name', 'feed_name'),
        Index('idx_log_timestamp', 'fetch_timestamp'),
        Index('idx_log_status', 'status'),
    ) 