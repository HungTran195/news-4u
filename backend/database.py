"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from pathlib import Path

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/news_4u")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    """
    from models.database import Base
    Base.metadata.create_all(bind=engine)


def get_db_url() -> str:
    """
    Get the database URL.
    """
    return DATABASE_URL 