#!/usr/bin/env python3
"""
Database initialization script for SQLite.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import init_db, get_db
from models.database import RSSFeed, NewsArticle, RawFeedData, FeedFetchLog
from config.rss_feeds import get_all_feeds


def main():
    """Initialize database and load initial data."""
    print("Initializing News 4U SQLite database...")
    
    # Initialize database tables
    init_db()
    print("✓ Database tables created")

    # Delete all RSSFeeds
    db = next(get_db())
    db.query(RSSFeed).delete()
    db.commit()
    print("✓ All RSSFeeds deleted")
    
    # Load RSS feeds
    db = next(get_db())
    try:
        feeds = get_all_feeds()
        loaded_count = 0
        
        for feed in feeds:
            existing = db.query(RSSFeed).filter(RSSFeed.name == feed.name).first()
            if not existing:
                db_feed = RSSFeed(
                    name=feed.name,
                    url=feed.url,
                    category=feed.category.value,
                    is_active=True
                )
                db.add(db_feed)
                loaded_count += 1
        
        db.commit()
        print(f"✓ Loaded {loaded_count} RSS feeds")
        
        # Show database status
        total_feeds = db.query(RSSFeed).count()
        total_articles = db.query(NewsArticle).count()
        total_raw_data = db.query(RawFeedData).count()
        total_logs = db.query(FeedFetchLog).count()
        
        print(f"\nDatabase Status:")
        print(f"  RSS Feeds: {total_feeds}")
        print(f"  Articles: {total_articles}")
        print(f"  Raw Feed Data: {total_raw_data}")
        print(f"  Fetch Logs: {total_logs}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    print("\n✓ SQLite database initialization completed successfully!")


if __name__ == "__main__":
    main() 