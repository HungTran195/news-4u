"""
RSS service for fetching and processing RSS feeds.
"""

import asyncio
from datetime import timezone
from datetime import datetime
import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from config.rss_feeds import NewsCategory, RSSFeed
import feedparser
import httpx
from lib.utils import generate_unique_slug
from models.database import FeedFetchLog, NewsArticle, RSSFeed as RSSFeedModel
from newspaper import Article, Config
from services.site_extractors import site_extractor_manager
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

# Set up logger
logger = logging.getLogger(__name__)


class RSSService:
    """Service for handling RSS feed operations."""
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.timeout = 30  # seconds
        self.batch_size = 100  # Batch size for database operations
        self._slug_cache = set()  # Cache for existing slugs
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL
        
        # HTTP client headers to avoid 403 errors
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================
    
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
        if self.db is not None:
            self.db.add(log_entry)
            self.db.commit()
        
        try:
            logger.info(f'---- Fetching feed from {feed.name} ----')
            response = await self._fetch_with_retry(feed.url)
            
            # Parse feed
            parsed_feed = feedparser.parse(response.text)
            articles_found = len(parsed_feed.entries)
            logger.info(f'---- Found {articles_found} articles from {feed.name} ----')
            
            # Process articles
            articles_processed = await self._process_articles_batch(parsed_feed.entries, feed)
            
            # Update log
            execution_time = int((time.time() - start_time) * 1000)
            object.__setattr__(log_entry, 'status', 'success')  # type: ignore
            object.__setattr__(log_entry, 'articles_found', articles_found)  # type: ignore
            object.__setattr__(log_entry, 'articles_processed', articles_processed)  # type: ignore
            object.__setattr__(log_entry, 'execution_time', execution_time)  # type: ignore
            
            if self.db is not None:
                self.db.commit()
            
            return {
                "status": "success",
                "articles_found": articles_found,
                "articles_processed": articles_processed,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed.name}: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            object.__setattr__(log_entry, 'status', 'error')  # type: ignore
            object.__setattr__(log_entry, 'error_message', str(e))  # type: ignore
            object.__setattr__(log_entry, 'execution_time', execution_time)  # type: ignore
            if self.db is not None:
                self.db.commit()
            
            return {
                "status": "error",
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def fetch_all_feeds(self) -> Dict:
        """
        Fetch all active RSS feeds.
        """
        if self.db is None:
            return {"status": "error", "message": "No database connection"}
        
        db_feeds = self.db.query(RSSFeedModel).filter(RSSFeedModel.is_active == True).all()
        
        results = []
        for db_feed in db_feeds:
            logger.info(f"---- Fetching feed from {db_feed.name} ----")
            feed = RSSFeed(
                name=db_feed.name,
                url=db_feed.url,
                category=NewsCategory(db_feed.category),
                is_active=db_feed.is_active
            )
            
            result = await self.fetch_feed_async(feed)
            results.append({
                "feed_name": feed.name,
                "category": feed.category.value,
                **result
            })
        
        return {
            "total_feeds": len(db_feeds),
            "results": results
        }
    
    async def extract_article_content(self, article_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract full article content from URL using multiple strategies.
        """
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                try: 
                    response = await client.get(article_url)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Error fetching article from {article_url}: {e}. trying with headers")
                    response = await client.get(article_url, headers=self._headers)
                    response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                extracted_image_url = self._extract_main_image_url_from_html(response.text, article_url)
                extractor = site_extractor_manager.get_extractor(article_url)
                
                if extractor:
                    logger.info(f"---- Extracting content with {extractor.__class__.__name__} ----")
                    content = extractor.extract_content(soup, article_url)
                    if content:
                        return self._clean_extracted_content(content), extracted_image_url
                
                # Fallback to Newspaper3k
                content = await self._extract_with_newspaper3k(article_url)
                return content, extracted_image_url
        except Exception as e:
            logger.error(f"Error extracting content from {article_url}: {e}")
            return None, None
    
    async def cleanup_all_data(self):
        """
        Clean up all data from the database.
        """
        if self.db is not None:
            self.db.query(NewsArticle).delete()
            self.db.query(FeedFetchLog).delete()
            self.db.commit()

    async def cleanup_feed_data(self, feed_name: str):
        """
        Clean up data for a specific feed.
        """
        if self.db is not None:
            self.db.query(NewsArticle).filter(NewsArticle.source_name == feed_name).delete()
            self.db.query(FeedFetchLog).filter(FeedFetchLog.feed_name == feed_name).delete()
            self.db.commit()
    
    async def delete_article_content(self, article_id: int):
        """
        Delete content for a specific article.
        """
        if self.db is not None:
            self.db.query(NewsArticle).filter(NewsArticle.id == article_id).update({
                NewsArticle.content: None,
                NewsArticle.image_url: None
            })
            self.db.commit()

    def get_articles_by_category(self, category: NewsCategory, limit: int = 50, offset: int = 0) -> List[NewsArticle]:
        """
        Get articles by category with pagination.
        """
        if self.db is None:
            return []
        return self.db.query(NewsArticle).filter(
            NewsArticle.category == category.value
        ).order_by(
            NewsArticle.published_date.desc()
        ).offset(offset).limit(limit).all()
    
    def get_recent_articles(self, limit: int = 50) -> List[NewsArticle]:
        """
        Get recent articles across all categories.
        """
        if self.db is None:
            return []
        return self.db.query(NewsArticle).order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
    
    def get_articles_by_source(self, source_name: str, limit: int = 50) -> List[NewsArticle]:
        """
        Get articles by source name.
        """
        if self.db is None:
            return []
        return self.db.query(NewsArticle).filter(
            NewsArticle.source_name == source_name
        ).order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
    
    def get_feed_by_name_from_db(self, name: str) -> RSSFeedModel | None:
        """
        Get a specific RSS feed from database by name.
        """
        if self.db is None:
            return None
        return self.db.query(RSSFeedModel).filter(RSSFeedModel.name == name).first()
    
    def toggle_feed_status(self, feed_name: str) -> Dict:
        """
        Toggle the active status of a feed.
        """
        if self.db is None:
            return {"status": "error", "message": "No database connection"}
        
        feed = self.get_feed_by_name_from_db(feed_name)
        if not feed:
            return {"status": "error", "message": f"Feed '{feed_name}' not found"}
        
        feed.is_active = not feed.is_active
        self.db.commit()
        
        return {
            "status": "success",
            "feed_name": feed.name,
            "is_active": feed.is_active,
            "message": f"Feed '{feed_name}' {'activated' if feed.is_active else 'deactivated'}"
        }  
    
    def delete_feed(self, feed_name: str) -> Dict:
        """
        Delete a feed from the database.
        """
        if self.db is None:
            return {"status": "error", "message": "No database connection"}
        
        self.db.query(RSSFeedModel).filter(RSSFeedModel.name == feed_name).delete()
        self.db.commit()
    
    def get_all_feed_names(self) -> List[str]:
        """
        Get all feed names from the database.
        """
        if self.db is None:
            return []
        return [feed.name for feed in self.db.query(RSSFeedModel).all()]
    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================
    
    async def _fetch_with_retry(self, url: str, max_retries: int = 3) -> httpx.Response:
        """
        Fetch URL with retry logic and proper headers to avoid 403 errors.
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout, 
                    follow_redirects=True,
                    headers=self._headers
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403 and attempt < max_retries - 1:
                    logger.warning(f"403 Forbidden on attempt {attempt + 1} for {url}, retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise e
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed on attempt {attempt + 1} for {url}: {e}, retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise e
        
        raise Exception(f"Failed to fetch {url} and all fallbacks after {max_retries} attempts each")
    
    async def _process_articles_batch(self, entries: List, feed: RSSFeed) -> int:
        """
        Process RSS feed entries into news articles (metadata only, no content extraction).
        Handles robust deduplication using ON CONFLICT and efficient batch insertion.
        """
        if not entries:
            return 0
        
        # List to hold article objects ready for batch insertion
        articles_to_add = []
        processed_successfully_count = 0

        logger.info(f'---- Processing {len(entries)} articles from {feed.name} ----')
        
        # Get cached existing slugs or refresh cache if needed
        existing_slugs = self._get_cached_existing_slugs()
        
        for entry in entries:
            link = self._safe_get_string(entry, 'link')
            if not link:
                logger.warning(f"Skipping entry from {feed.name} due to missing link: {self._safe_get_string(entry, 'title', 'N/A')}")
                continue

            try:
                title = self._safe_get_string(entry, 'title')
                summary = self._extract_summary(entry)
                author = self._safe_get_string(entry, 'author')
                published_date = self._extract_published_date(entry)
                image_url = self._extract_image(entry)
                
                if published_date is None:
                    logger.warning(f"Failed to parse published date for '{title}' from {feed.name}. Storing with None.")

                slug = generate_unique_slug(title, existing_slugs)
                existing_slugs.add(slug)  # Add to cache to avoid duplicates in this batch
                
                article = NewsArticle(
                    title=title,
                    summary=summary,
                    content=None,  # Will be None
                    link=link,
                    author=author,
                    published_date=published_date,
                    category=feed.category.value,
                    source_name=feed.name,
                    source_url=feed.url,
                    image_url=image_url,
                    slug=slug,
                    created_at=datetime.now(),
                    is_processed=True  # Marks as metadata-processed
                )
                
                articles_to_add.append(article)
                
            except Exception as e:
                logger.error(f"Error extracting data for article '{self._safe_get_string(entry, 'title', 'N/A')}' from {feed.name}: {e}")
                continue
        
        # --- Batch Insertion with ON CONFLICT for deduplication ---
        if not articles_to_add:
            logger.info(f"No new articles to add from {feed.name}.")
            return 0

        try:
            

            article_dicts = []
            for article_obj in articles_to_add:
                article_dict = {
                    col.name: getattr(article_obj, col.name)
                    for col in NewsArticle.__table__.columns if col.name != 'id'
                }
                article_dicts.append(article_dict)

            if not article_dicts:
                logger.info(f"No valid articles for batch insertion from {feed.name}.")
                return 0

            insert_stmt = sqlite_insert(NewsArticle).values(article_dicts)
            on_conflict_stmt = insert_stmt.on_conflict_do_nothing(index_elements=['link'])
            
            if self.db is not None:
                self.db.execute(on_conflict_stmt)

            if self.db is not None:
                self.db.commit()

            processed_successfully_count = len(articles_to_add)

            logger.info(f"Successfully attempted to add {processed_successfully_count} articles from {feed.name}.")

        except Exception as e:
            logger.error(f"Critical error during batch database insertion for {feed.name}: {e}")
            if self.db is not None:
                self.db.rollback()
            return 0

        return processed_successfully_count
    
    async def _extract_with_newspaper3k(self, article_url: str) -> Optional[str]:
        try:

            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            config.request_timeout = 15
            config.memoize_articles = False
            
            article = Article(article_url, config=config)
            article.download()
            article.parse()
            
            if hasattr(article, 'text') and article.text:
                cleaned_text = self._clean_extracted_content(article.text)
                if cleaned_text and len(cleaned_text.strip()) > 100:
                    return cleaned_text
            
        except Exception as e:
            logger.error(f"Error extracting content with Newspaper3k from {article_url}: {e}")
        
        return None
        
    def _get_cached_existing_slugs(self) -> set:
        """
        Get cached existing slugs or refresh cache if needed.
        """
        current_time = time.time()
        
        # Check if cache is valid
        if (self._cache_timestamp is None or 
            current_time - self._cache_timestamp > self._cache_ttl or
            not self._slug_cache):
            
            # Refresh cache
            if self.db is not None:
                existing_slugs = {article.slug for article in self.db.query(NewsArticle.slug).filter(NewsArticle.slug.isnot(None)).all()}
                self._slug_cache = existing_slugs
                self._cache_timestamp = current_time
                logger.debug(f"Refreshed slug cache with {len(existing_slugs)} existing slugs")
            else:
                self._slug_cache = set()
                self._cache_timestamp = current_time
        
        return self._slug_cache.copy()
    
    def _extract_summary(self, entry) -> Optional[str]:
        """
        Extract summary from RSS entry.
        """
        # Try different summary fields
        summary = self._safe_get_string(entry, 'summary') or self._safe_get_string(entry, 'description')
        
        if summary:
            # Clean HTML tags
            soup = BeautifulSoup(summary, 'html.parser')
            return soup.get_text().strip()
        
        return None
    
    def _extract_published_date(self, entry) -> Optional[datetime]:
        """
        Robustly extract published date from RSS entry, trying all common fields.
        Always returns a UTC datetime (with tzinfo=timezone.utc).
        """
        
        
        date_fields = [
            'published', 'pubDate', 'updated', 'created', 'date',
            'dc:date', 'dc:created', 'dc:issued', 'dc:modified', 'issued', 'modified'
        ]
        
        for field in date_fields:
            date_str = entry.get(field, '')
            if date_str:
                # Normalize timezone format: GMT+7 -> +07, GMT-5 -> -05
                date_str = re.sub(r'GMT\+(\d{1,2})', r'+\1', date_str)
                date_str = re.sub(r'GMT-(\d{1,2})', r'-\1', date_str)
                
                try:
                    parsed_date = dateutil_parser.parse(date_str)
                    
                    # Ensure it has timezone info, default to UTC if not
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    else:
                        # Convert to UTC
                        parsed_date = parsed_date.astimezone(timezone.utc)
                    
                    return parsed_date
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date from field '{field}': {date_str}, error: {e}")
                    continue
        
        # If no date found, return None
        return None
    
    def _extract_image(self, entry) -> Optional[str]:
        """
        Extract image URL from RSS entry.
        """
        image_fields = ['media_content', 'media:thumbnail', 'enclosure', 'image']
        
        for field in image_fields:
            if field in entry:
                media_content = entry[field]
                
                # Handle different media content formats
                if isinstance(media_content, list) and len(media_content) > 0:
                    # Take the first media item
                    media_item = media_content[0]
                    if isinstance(media_item, dict):
                        url = media_item.get('url') or media_item.get('href')
                        if url:
                            return url
                elif isinstance(media_content, dict):
                    # Single media item
                    url = media_content.get('url') or media_content.get('href')
                    if url:
                        return url
                elif isinstance(media_content, str):
                    # Direct URL string
                    return media_content
        
        # Try to extract from content/summary if no media found
        content_fields = ['summary', 'description', 'content']
        for field in content_fields:
            content = self._safe_get_string(entry, field)
            if content:
                # Look for img tags
                soup = BeautifulSoup(content, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    return img_tag.get('src')
        
        return None
    
    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """
        Convert relative URL to absolute URL.
        """
        return urljoin(base_url, url)
    
    def _is_valid_content_image(self, image_url: str) -> bool:
        """
        Check if image URL is valid for content.
        """
        if not image_url:
            return False
        
        # Skip data URLs
        if image_url.startswith('data:'):
            return False
        
        # Skip very small images (likely icons)
        if any(size in image_url.lower() for size in ['16x16', '32x32', '48x48']):
            return False
        
        # Skip tracking pixels
        if any(tracker in image_url.lower() for tracker in ['tracking', 'pixel', 'beacon']):
            return False
        
        return True
    
    def _clean_extracted_content(self, text: str) -> str:
        """
        Clean and format extracted content.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # Clean up line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _sanitize_html_attributes(self, html_content: str) -> str:
        """
        Remove unwanted HTML attributes while preserving content structure.
        """
        if not html_content:
            return ""
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Define attributes to remove
        attributes_to_remove = [
            'class', 'id', 'style', 'data-*', 'onclick', 'onload', 'onerror',
            'onmouseover', 'onmouseout', 'onfocus', 'onblur', 'onchange',
            'oninput', 'onsubmit', 'onreset', 'onselect', 'onunload',
            'onkeydown', 'onkeyup', 'onkeypress', 'onmousedown', 'onmouseup',
            'onmousemove', 'onmouseenter', 'onmouseleave', 'oncontextmenu',
            'onabort', 'onbeforeunload', 'onerror', 'onhashchange', 'onmessage',
            'onoffline', 'ononline', 'onpagehide', 'onpageshow', 'onpopstate',
            'onresize', 'onstorage', 'onbeforeprint', 'onafterprint',
            'aria-*', 'role', 'tabindex', 'accesskey', 'contenteditable',
            'draggable', 'dropzone', 'spellcheck', 'translate'
        ]
        
        # Process all tags
        for tag in soup.find_all():
            if tag.name:  # Ensure it's a tag
                # Remove specified attributes
                for attr in list(tag.attrs.keys()):
                    # Remove data-* attributes
                    if attr.startswith('data-'):
                        del tag[attr]
                    # Remove aria-* attributes
                    elif attr.startswith('aria-'):
                        del tag[attr]
                    # Remove other specified attributes
                    elif attr in attributes_to_remove:
                        del tag[attr]
                
                # Special handling for img tags - preserve essential attributes
                if tag.name == 'img':
                    # Keep only essential img attributes
                    essential_img_attrs = ['src', 'alt', 'title', 'width', 'height']
                    for attr in list(tag.attrs.keys()):
                        if attr not in essential_img_attrs:
                            del tag[attr]
                
                # Special handling for a tags - preserve href
                elif tag.name == 'a':
                    # Keep only href attribute
                    for attr in list(tag.attrs.keys()):
                        if attr != 'href':
                            del tag[attr]
                
                # Special handling for table tags - preserve basic table structure
                elif tag.name in ['table', 'tr', 'td', 'th']:
                    # Keep only essential table attributes
                    essential_table_attrs = ['colspan', 'rowspan']
                    for attr in list(tag.attrs.keys()):
                        if attr not in essential_table_attrs:
                            del tag[attr]
        
        return str(soup)
    

    def _extract_main_image_url_from_html(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract the main image URL from HTML content.
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for Open Graph image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return self._make_absolute_url(og_image.get('content'), base_url)
            
            # Look for Twitter image
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                return self._make_absolute_url(twitter_image.get('content'), base_url)
            
            # Look for the first large image in the content
            images = soup.find_all('img')
            for img in images:
                src = img.get('src', '')
                if src and self._is_valid_content_image(src):
                    # Check if it's a large image (likely main content image)
                    width = img.get('width', '0')
                    height = img.get('height', '0')
                    
                    try:
                        width_int = int(width) if width.isdigit() else 0
                        height_int = int(height) if height.isdigit() else 0
                        
                        # Consider it a main image if it's reasonably large
                        if width_int > 300 or height_int > 200:
                            return self._make_absolute_url(src, base_url)
                    except (ValueError, AttributeError):
                        # If we can't parse dimensions, check if it's a reasonable URL
                        if len(src) > 20:  # Likely a real image URL
                            return self._make_absolute_url(src, base_url)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting main image from HTML: {e}")
            return None

    def _safe_get_string(self, entry, key: str, default: str = "") -> str:
        """
        Safely extract a string value from an entry, handling potential list/dict issues.
        """
        value = entry.get(key)
        if isinstance(value, (list, tuple)):
            return default if not value else str(value[0])
        return str(value) if value is not None else default