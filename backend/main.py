"""
Main FastAPI application for the News 4U RSS aggregator.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from routers import news
from config.rss_feeds import get_all_feeds
from services.scheduler_service import scheduler_service
from services.s3_service import S3Service
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""

    logger.info("Starting News 4U RSS Aggregator v2...")
    
    # Initialize S3 service and load feeds
    try:
        s3_service = S3Service()
        feeds = get_all_feeds()
        
        # Convert feeds to dict format and save to S3
        feeds_data = []
        for feed in feeds:
            feeds_data.append({
                'name': feed.name,
                'url': feed.url,
                'category': feed.category.value,
                'is_active': True
            })
        
        s3_service.save_rss_feeds(feeds_data)
        logger.info(f"Loaded {len(feeds)} RSS feeds to S3")
        
        # Update stats
        s3_service.update_stats()
        logger.info("Initial stats updated")
        
    except Exception as e:
        logger.error(f"Error initializing S3 service: {e}")
        raise e
    
    # Start the scheduler
    # scheduler_service.start()
    logger.info("Scheduler started with cronjobs")
    
    yield
    
    # Stop the scheduler
    scheduler_service.stop()
    logger.info("Scheduler stopped")
    logger.info("Shutting down News 4U RSS Aggregator...")


app = FastAPI(
    title="News 4U RSS Aggregator v2",
    description="A professional news aggregation platform that fetches and categorizes news from popular RSS feeds using S3 storage.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://news-4u.onrender.com",
        "https://news-4u.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "News 4U RSS Aggregator API v2",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/news/health"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 