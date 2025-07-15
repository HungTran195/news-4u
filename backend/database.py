"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from pathlib import Path

# Database URL - Require PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Please set it to your PostgreSQL connection string. "
        "Example: postgresql://user:password@localhost:5432/dbname"
    )

# Validate that it's a PostgreSQL URL
if not DATABASE_URL.startswith("postgresql://"):
    raise ValueError(
        f"Invalid DATABASE_URL: {DATABASE_URL}. "
        "Only PostgreSQL URLs are supported (must start with 'postgresql://')"
    )

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
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
    return DATABASE_URL  # type: ignore - We validate DATABASE_URL is not None above 