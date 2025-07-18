"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from pathlib import Path

# Database URL - Support persistent disk and local development
def get_database_url() -> str:
    """
    Get the database URL based on environment.
    The persistent disk can be mounted at /var/data
    For local development, use the current directory
    """
    persistent_data_path = "/var/data"
    if os.path.exists(persistent_data_path):
        # Ensure the data directory exists
        os.makedirs(persistent_data_path, exist_ok=True)
        db_path = os.path.join(persistent_data_path, "news_4u.db")
        return f"sqlite:///{db_path}"
    else:
        # Local development - use current directory
        return "sqlite:///./news_4u.db"

# Get database URL
DATABASE_URL = get_database_url()
print(f"[INFO] Using database: {DATABASE_URL}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database (create tables if not exist).
    """
    from models.database import Base
    Base.metadata.create_all(bind=engine)

def get_db_url() -> str:
    """
    Get the database URL.
    """
    return DATABASE_URL 