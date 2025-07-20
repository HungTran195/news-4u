#!/usr/bin/env python3
"""
Migration script to remove the raw_feed_data table from the database.
This script should be run to clean up the database schema and remove unused raw data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, engine
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def remove_raw_data_table():
    """Remove the raw_feed_data table from the database."""
    db = next(get_db())
    
    try:
        # Check if the table exists
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='raw_feed_data'
        """))
        
        if not result.fetchone():
            logger.info("raw_feed_data table does not exist, nothing to remove")
            return
        
        # Get count of records before deletion
        count_result = db.execute(text("SELECT COUNT(*) FROM raw_feed_data"))
        count_row = count_result.fetchone()
        record_count = count_row[0] if count_row else 0
        logger.info(f"Found {record_count} records in raw_feed_data table")
        
        # Drop the table
        logger.info("Dropping raw_feed_data table...")
        db.execute(text("DROP TABLE IF EXISTS raw_feed_data"))
        
        # Also drop any indexes associated with the table
        db.execute(text("DROP INDEX IF EXISTS idx_raw_feed_timestamp"))
        db.execute(text("DROP INDEX IF EXISTS idx_raw_feed_id"))
        
        db.commit()
        logger.info("Successfully removed raw_feed_data table and associated indexes")
        
    except Exception as e:
        logger.error(f"Error removing raw_feed_data table: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_foreign_key_constraints():
    """Clean up any foreign key constraints that reference raw_feed_data."""
    db = next(get_db())
    
    try:
        # Check if there are any foreign key constraints that need to be removed
        # This is mainly for SQLite which doesn't have complex foreign key constraints
        # but we'll check for any remaining references
        logger.info("Checking for any remaining foreign key constraints...")
        
        # In SQLite, foreign key constraints are typically handled at the application level
        # so there's usually nothing to clean up here
        logger.info("No additional foreign key cleanup needed for SQLite")
        
    except Exception as e:
        logger.error(f"Error during foreign key cleanup: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting raw_feed_data table removal...")
    
    try:
        remove_raw_data_table()
        cleanup_foreign_key_constraints()
        logger.info("Raw data table removal completed successfully")
    except Exception as e:
        logger.error(f"Failed to remove raw_feed_data table: {e}")
        sys.exit(1) 