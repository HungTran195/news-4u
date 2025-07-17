#!/usr/bin/env python3
"""
Database migration script to add slug column to news_articles table.
This script should be run before running the add_slugs_to_existing_articles.py script.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_slug_column():
    """Add slug column to news_articles table if it doesn't exist."""
    try:
        with engine.connect() as conn:
            # Check if slug column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) FROM pragma_table_info('news_articles') 
                WHERE name = 'slug'
            """))
            count = result.scalar()
            column_exists = count is not None and count > 0
            
            if column_exists:
                logger.info("Slug column already exists in news_articles table")
                return
            
            # Add slug column
            logger.info("Adding slug column to news_articles table...")
            conn.execute(text("""
                ALTER TABLE news_articles 
                ADD COLUMN slug VARCHAR(100)
            """))
            
            # Create index on slug column
            logger.info("Creating index on slug column...")
            conn.execute(text("""
                CREATE INDEX idx_article_slug ON news_articles(slug)
            """))
            
            # Make slug column unique
            logger.info("Making slug column unique...")
            conn.execute(text("""
                CREATE UNIQUE INDEX idx_article_slug_unique ON news_articles(slug)
            """))
            
            conn.commit()
            logger.info("Successfully added slug column to news_articles table")
            
    except Exception as e:
        logger.error(f"Error adding slug column: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting database migration...")
    add_slug_column()
    logger.info("Database migration completed!") 