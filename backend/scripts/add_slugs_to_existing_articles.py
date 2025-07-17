#!/usr/bin/env python3
"""
Script to add slugs to existing articles in the database.
This script should be run after adding the slug column to the NewsArticle table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models.database import NewsArticle
from lib.utils import generate_unique_slug
from sqlalchemy.orm import Session
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_slugs_to_existing_articles():
    """Add slugs to all existing articles that don't have them."""
    db = next(get_db())
    
    try:
        # Get all articles without slugs
        articles_without_slugs = db.query(NewsArticle).filter(
            NewsArticle.slug.is_(None)
        ).all()
        
        logger.info(f"Found {len(articles_without_slugs)} articles without slugs")
        
        if not articles_without_slugs:
            logger.info("No articles need slug updates")
            return
        
        # Get existing slugs to avoid conflicts
        existing_slugs = {article.slug for article in db.query(NewsArticle.slug).filter(NewsArticle.slug.isnot(None)).all()}
        
        updated_count = 0
        for article in articles_without_slugs:
            try:
                # Generate unique slug
                slug = generate_unique_slug(str(article.title), existing_slugs)
                
                # Update the article
                setattr(article, 'slug', slug)
                existing_slugs.add(slug)  # Add to set to avoid conflicts in this batch
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} articles so far...")
                    
            except Exception as e:
                logger.error(f"Error updating slug for article {article.id} ({article.title}): {e}")
                continue
        
        # Commit all changes
        db.commit()
        logger.info(f"Successfully updated {updated_count} articles with slugs")
        
    except Exception as e:
        logger.error(f"Error in add_slugs_to_existing_articles: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting slug update process...")
    add_slugs_to_existing_articles()
    logger.info("Slug update process completed!") 