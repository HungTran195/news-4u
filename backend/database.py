"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from pathlib import Path

# Database URL - Use SQLite only
DATABASE_URL = "sqlite:///./news_4u.db"
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