"""
Scheduler service for managing cronjobs.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from services.rss_service import RSSService
from services.s3_service import S3Service

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler started")
            
            # Add the cronjobs
            self._add_feed_fetching_job()
            self._add_content_extraction_job()
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def _add_feed_fetching_job(self):
        """Add the job to fetch all feeds every hour."""
        self.scheduler.add_job(
            func=self._fetch_all_feeds_job,
            trigger=CronTrigger(hour="*"),  # Every hour
            id="fetch_all_feeds",
            name="Fetch all RSS feeds",
            replace_existing=True,
            max_instances=1
        )
        logger.info("Added feed fetching job (every hour)")
    
    def _add_content_extraction_job(self):
        """Add the job to extract content every minute."""
        self.scheduler.add_job(
            func=self._extract_content_job,
            trigger=CronTrigger(minute="*"),  # Every minute
            id="extract_content",
            name="Extract article content",
            replace_existing=True,
            max_instances=1
        )
        logger.info("Added content extraction job (every minute)")
    
    async def _fetch_all_feeds_job(self):
        """Job to fetch all RSS feeds."""
        logger.info("---- Starting scheduled feed fetching job ----")
        try:
            service = RSSService()
            result = await service.fetch_all_feeds()
            logger.info(f"Feed fetching completed: {result}")
            
            # Update stats after fetching
            s3_service = S3Service()
            s3_service.update_stats()
            
        except Exception as e:
            logger.error(f"Error in feed fetching job: {e}")
    
    async def _extract_content_job(self):
        """Job to extract content for articles that haven't been extracted."""
        logger.info("---- Starting scheduled content extraction job ----")
        try:
            s3_service = S3Service()
            
            # Get all articles and filter those without content
            all_articles = s3_service.get_all_articles(limit=1000)
            articles_without_content = []
            
            for article in all_articles['articles']:
                content = article.get('content')
                if not content or content == "" or content == "None":
                    articles_without_content.append(article)
                    if len(articles_without_content) >= 20:  # Limit to 20 articles
                        break
            
            if not articles_without_content:
                logger.info("No articles found that need content extraction")
                return
            
            logger.info(f"Found {len(articles_without_content)} articles that need content extraction")
            
            service = RSSService()
            extracted_count = 0
            
            for article in articles_without_content:
                try:
                    article_name = article.get('article_name')
                    if not article_name:
                        continue
                        
                    if not article.get('link'):
                        logger.warning(f"Article {article_name} has no link, skipping")
                        continue
                    
                    logger.info(f"Extracting content for article {article_name}: {article['title']}")
                    content, extracted_image_url = await service.extract_article_content(article['link'])
                    
                    updates = {}
                    
                    if content:
                        updates['content'] = content
                        extracted_count += 1
                        logger.info(f"Successfully extracted content for article {article_name}")
                    
                    if extracted_image_url and not article.get('image_url'):
                        updates['image_url'] = extracted_image_url
                        logger.info(f"Updated image URL for article {article_name}")
                    
                    # Update in S3 if any changes were made
                    if updates:
                        s3_service.update_article(article_name, updates)
                    
                except Exception as e:
                    logger.error(f"Error extracting content for article {article_name}: {e}")
                    continue
            
            logger.info(f"Content extraction job completed. Extracted content for {extracted_count} articles")
            
        except Exception as e:
            logger.error(f"Error in content extraction job: {e}")
    
    def get_job_status(self) -> dict:
        """Get the status of all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "scheduler_running": self.is_running,
            "jobs": jobs
        }


# Global scheduler instance
scheduler_service = SchedulerService() 