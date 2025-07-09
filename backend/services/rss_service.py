"""
RSS service for fetching and processing RSS feeds.
"""

import feedparser
import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import time
from bs4 import BeautifulSoup
import re
import trafilatura

from config.rss_feeds import RSSFeed, get_all_feeds, NewsCategory
from models.database import RSSFeed as RSSFeedModel, RawFeedData, NewsArticle, FeedFetchLog
from sqlalchemy.orm import Session
from schemas.news import NewsArticleCreate


class RSSService:
    """Service for handling RSS feed operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.timeout = 30  # seconds
    
    async def fetch_feed_async(self, feed: RSSFeed) -> Dict:
        """
        Fetch RSS feed asynchronously.
        """
        start_time = time.time()
        log_entry = FeedFetchLog(
            feed_name=feed.name,
            status="fetching",
            articles_found=0,
            articles_processed=0
        )
        self.db.add(log_entry)
        self.db.commit()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(feed.url)
                response.raise_for_status()
                
                # Store raw data
                raw_data = RawFeedData(
                    feed_id=self._get_or_create_feed_id(feed),
                    raw_content=response.text,
                    status_code=response.status_code
                )
                self.db.add(raw_data)
                
                # Parse feed
                parsed_feed = feedparser.parse(response.text)
                articles_found = len(parsed_feed.entries)
                
                # Process articles
                articles_processed = await self._process_articles(parsed_feed.entries, feed)
                
                # Update log
                execution_time = int((time.time() - start_time) * 1000)
                log_entry.status = "success"
                log_entry.articles_found = articles_found
                log_entry.articles_processed = articles_processed
                log_entry.execution_time = execution_time
                
                self.db.commit()
                
                return {
                    "status": "success",
                    "articles_found": articles_found,
                    "articles_processed": articles_processed,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            log_entry.status = "error"
            log_entry.error_message = str(e)
            log_entry.execution_time = execution_time
            self.db.commit()
            
            return {
                "status": "error",
                "error": str(e),
                "execution_time": execution_time
            }
    
    def _get_or_create_feed_id(self, feed: RSSFeed) -> int:
        """
        Get or create RSS feed ID in database.
        """
        db_feed = self.db.query(RSSFeedModel).filter(
            RSSFeedModel.name == feed.name
        ).first()
        
        if not db_feed:
            db_feed = RSSFeedModel(
                name=feed.name,
                url=feed.url,
                category=feed.category.value,
                description=feed.description
            )
            self.db.add(db_feed)
            self.db.commit()
            self.db.refresh(db_feed)
        
        return db_feed.id
    
    async def _process_articles(self, entries: List, feed: RSSFeed) -> int:
        """
        Process RSS feed entries into news articles.
        """
        processed_count = 0
        
        for entry in entries:
            try:
                # Check if article already exists
                existing = self.db.query(NewsArticle).filter(
                    NewsArticle.link == entry.get('link', '')
                ).first()
                
                if existing:
                    continue
                
                # Extract article data
                title = entry.get('title', '').strip()
                link = entry.get('link', '')
                summary = self._extract_summary(entry)
                author = entry.get('author', '')
                published_date = self._parse_date(entry.get('published', ''))
                image_url = self._extract_image(entry)
                
                # Extract full content from the article URL
                content = None
                if link:
                    content = await self._extract_article_content(link)
                
                # Create article
                article = NewsArticle(
                    title=title,
                    summary=summary,
                    content=content,
                    link=link,
                    author=author,
                    published_date=published_date,
                    category=feed.category.value,
                    source_name=feed.name,
                    source_url=feed.url,
                    image_url=image_url,
                    is_processed=True
                )
                
                self.db.add(article)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing article from {feed.name}: {e}")
                continue
        
        self.db.commit()
        return processed_count
    
    def _extract_summary(self, entry) -> Optional[str]:
        """
        Extract summary from RSS entry.
        """
        # Try different summary fields
        summary = entry.get('summary', '') or entry.get('description', '')
        
        if summary:
            # Clean HTML tags
            soup = BeautifulSoup(summary, 'html.parser')
            return soup.get_text().strip()
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        """
        if not date_str:
            return None
        
        try:
            # Try parsing with feedparser
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6])
        except:
            pass
        
        return None
    
    def _extract_image(self, entry) -> Optional[str]:
        """
        Extract image URL from RSS entry.
        """
        # Try different image fields
        image_url = None
        
        # Check media:content
        if 'media_content' in entry and entry['media_content']:
            image_url = entry['media_content'][0].get('url')
        
        # Check media:thumbnail
        elif 'media_thumbnail' in entry and entry['media_thumbnail']:
            image_url = entry['media_thumbnail'][0].get('url')
        
        # Check enclosures
        elif 'enclosures' in entry and entry['enclosures']:
            for enclosure in entry['enclosures']:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break
        
        return image_url
    
    async def _extract_article_content(self, article_url: str) -> Optional[str]:
        """
        Extract full article content from the original website.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(article_url)
                response.raise_for_status()
                
                # Use trafilatura to extract main content
                extracted_text = trafilatura.extract(response.text, include_formatting=True)
                
                if extracted_text:
                    # Clean up the extracted text
                    cleaned_text = self._clean_extracted_content(extracted_text)
                    return cleaned_text
                
                # Fallback to BeautifulSoup if trafilatura fails
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Try to find main content areas
                content_selectors = [
                    'article',
                    '[class*="content"]',
                    '[class*="article"]',
                    '[class*="post"]',
                    'main',
                    '.entry-content',
                    '.post-content',
                    '.article-content'
                ]
                
                for selector in content_selectors:
                    content = soup.select_one(selector)
                    if content:
                        text = content.get_text(separator='\n', strip=True)
                        if len(text) > 200:  # Ensure we have substantial content
                            return self._clean_extracted_content(text)
                
                # If no specific content area found, get body text
                body = soup.find('body')
                if body:
                    text = body.get_text(separator='\n', strip=True)
                    return self._clean_extracted_content(text)
                
        except Exception as e:
            print(f"Error extracting content from {article_url}: {e}")
        
        return None
    
    def _clean_extracted_content(self, text: str) -> str:
        """
        Clean and format extracted content.
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common unwanted patterns
        text = re.sub(r'Share this article.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Follow us.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Subscribe.*', '', text, flags=re.IGNORECASE)
        
        # Limit content length to avoid database issues
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text.strip()
    
    async def fetch_all_feeds(self) -> Dict:
        """
        Fetch all configured RSS feeds.
        """
        feeds = get_all_feeds()
        results = []
        
        for feed in feeds:
            result = await self.fetch_feed_async(feed)
            results.append({
                "feed_name": feed.name,
                "category": feed.category.value,
                **result
            })
        
        return {
            "total_feeds": len(feeds),
            "results": results
        }
    
    def get_articles_by_category(self, category: NewsCategory, limit: int = 50, offset: int = 0) -> List[NewsArticle]:
        """
        Get articles by category with pagination.
        """
        return self.db.query(NewsArticle).filter(
            NewsArticle.category == category.value
        ).order_by(
            NewsArticle.published_date.desc()
        ).offset(offset).limit(limit).all()
    
    def get_recent_articles(self, limit: int = 50) -> List[NewsArticle]:
        """
        Get recent articles across all categories.
        """
        return self.db.query(NewsArticle).order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
    
    def get_articles_by_source(self, source_name: str, limit: int = 50) -> List[NewsArticle]:
        """
        Get articles by source name.
        """
        return self.db.query(NewsArticle).filter(
            NewsArticle.source_name == source_name
        ).order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all() 