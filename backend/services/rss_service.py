"""
RSS service for fetching and processing RSS feeds.
"""

import feedparser
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
import time
from bs4 import BeautifulSoup
import re
from newspaper import Article, Config
import logging

from config.rss_feeds import RSSFeed, get_all_feeds, NewsCategory
from models.database import RSSFeed as RSSFeedModel, RawFeedData, NewsArticle, FeedFetchLog
from sqlalchemy.orm import Session
from services.site_extractors import site_extractor_manager
from lib.utils import generate_unique_slug

# Set up logger
logger = logging.getLogger(__name__)


class RSSService:
    """Service for handling RSS feed operations."""
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.timeout = 30  # seconds
        self.batch_size = 100  # Batch size for database operations
    
    # ============================================================================
    # PUBLIC METHODS (Async)
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(feed.url)
                response.raise_for_status()
                
                # Store raw data
                raw_data = RawFeedData(
                    feed_id=self._get_or_create_feed_id(feed),
                    raw_content=response.text,
                    status_code=response.status_code
                )
                logger.info(f'---- Get raw data from {feed.name} ----')
                if self.db is not None:
                    self.db.add(raw_data)
                
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
    
    async def extract_article_content(self, article_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract full article content using site-specific extractors first, then fallback to Newspaper3k.
        If the article has no image_url, try to extract it before content extraction and update the DB.
        
        Returns:
            tuple: (content, image_url) - content is the extracted article content, 
                   image_url is the newly extracted image URL (if any was found and updated)
        """
        try:
            # First, try site-specific extractor
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(article_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # --- Custom: Try to update image_url if missing ---
                # Find the NewsArticle in the DB by link
                article_obj = None
                extracted_image_url = None
                if self.db is not None:
                    article_obj = self.db.query(NewsArticle).filter(NewsArticle.link == article_url).first()
                if article_obj and (not getattr(article_obj, 'image_url', None) or str(getattr(article_obj, 'image_url', '')).strip() == ''):
                    image_url = self._extract_main_image_url_from_html(response.text, article_url)
                    if image_url:
                        setattr(article_obj, 'image_url', image_url)
                        setattr(article_obj, 'updated_at', datetime.now())
                        extracted_image_url = image_url  # Return this to the caller
                        if self.db is not None:
                            self.db.commit()

                # Try site-specific extractor first
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
    
    async def search_articles(self, query: str, category: str, time_filter: str, max_results: int) -> List[NewsArticle]:
        """
        Search articles in the database.
        """
        if self.db is None:
            return []
        return self.db.query(NewsArticle).filter(
            NewsArticle.title.ilike(f"%{query}%")
        ).order_by(
            NewsArticle.published_date.desc()
        ).limit(max_results).all()

    async def cleanup_all_data(self):
        """
        Clean up all data from the database.
        """
        if self.db is not None:
            self.db.query(NewsArticle).delete()
            self.db.query(RawFeedData).delete()
            self.db.query(FeedFetchLog).delete()
            self.db.commit()

    async def cleanup_feed_data(self, feed_name: str):
        """
        Clean up data for a specific feed.
        """
        if self.db is not None:
            self.db.query(NewsArticle).filter(NewsArticle.source_name == feed_name).delete()
            self.db.query(RawFeedData).filter(RawFeedData.feed_id == feed_name).delete()
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
    
    # ============================================================================
    # PUBLIC METHODS (Sync)
    # ============================================================================
    
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
    
    # ============================================================================
    # PRIVATE METHODS (Async)
    # ============================================================================
    
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
        
        for entry in entries:
            link = entry.get('link', '').strip()
            if not link:
                logger.warning(f"Skipping entry from {feed.name} due to missing link: {entry.get('title', 'N/A')}")
                continue

            try:
                # Extract article data
                title = entry.get('title', '').strip()
                summary = self._extract_summary(entry)
                author = entry.get('author', '')
                published_date = self._extract_published_date(entry)
                image_url = self._extract_image(entry)
                
                if published_date is None:
                    logger.warning(f"Failed to parse published date for '{title}' from {feed.name}. Storing with None.")

                # Generate unique slug for the article
                existing_slugs = set()
                if self.db is not None:
                    existing_slugs = {article.slug for article in self.db.query(NewsArticle.slug).filter(NewsArticle.slug.isnot(None)).all()}
                
                slug = generate_unique_slug(title, existing_slugs)
                
                # Create article object
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
                # Log error for individual article and continue with the rest of the batch
                logger.error(f"Error extracting data for article '{entry.get('title', 'N/A')}' from {feed.name}: {e}")
                # No rollback here; we want to process other articles in the batch
                continue
        
        # --- Batch Insertion with ON CONFLICT for deduplication ---
        if not articles_to_add:
            logger.info(f"No new articles to add from {feed.name}.")
            return 0

        try:
            # Use SQLAlchemy's bulk_insert_mappings for efficiency, especially with ON CONFLICT
            # Note: For ON CONFLICT, we often need to construct the raw statement or use specific ORM features.
            # SQLAlchemy ORM doesn't have a direct `add_all_on_conflict_do_nothing` method.
            # The most straightforward way with SQLite and ORM is to use `insert` with `on_conflict_do_nothing`.
            # This requires converting objects back to dicts for `insert().values()`.

            # Prepare data for bulk insertion with ON CONFLICT
            # This relies on 'link' being a UNIQUE constraint on NewsArticle table
            
            # This is a critical part for scaling:
            # Instead of `session.add_all()` and then hoping for `flush` to handle conflicts
            # (which often requires specific drivers/db features, and can still lead to rollbacks),
            # we explicitly use an `INSERT ... ON CONFLICT DO NOTHING` statement.

            # IMPORTANT: For `session.execute(insert_stmt)`, SQLAlchemy 1.4+ (and 2.0) is needed
            # For `async` operations, this needs to be awaited.
            
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert

            # Convert ORM objects to dictionaries for bulk insertion
            # Exclude fields like 'id' if it's auto-incrementing
            article_dicts = []
            for article_obj in articles_to_add:
                # Create a dictionary from the ORM object, excluding any auto-generated PK if applicable
                article_dict = {
                    col.name: getattr(article_obj, col.name)
                    for col in NewsArticle.__table__.columns if col.name != 'id'  # Exclude 'id' if it's auto-pk
                }
                article_dicts.append(article_dict)

            if not article_dicts:
                logger.info(f"No valid articles for batch insertion from {feed.name}.")
                return 0

            # Construct the ON CONFLICT statement using SQLite-specific insert
            insert_stmt = sqlite_insert(NewsArticle).values(article_dicts)
            on_conflict_stmt = insert_stmt.on_conflict_do_nothing(index_elements=['link'])
            
            # Execute the statement. This must be `await`ed if self.db uses an async driver.
            # For a synchronous SQLite connection, this would just be `self.db.execute(...)`
            # and the `async def` would be more of a conceptual wrapper.
            if self.db is not None:
                self.db.execute(on_conflict_stmt)  # Or self.db.execute(on_conflict_stmt) if synchronous

            # Flush/commit the changes. For bulk inserts with on_conflict_do_nothing,
            # this usually means just committing the transaction.
            if self.db is not None:
                self.db.commit()  # Or self.db.commit() if synchronous

            # Determine processed count. SQLite's ON CONFLICT DO NOTHING does not return
            # the number of inserted rows directly. We can't use `rowcount` easily here
            # for *just* the new inserts without a subsequent query or tracking.
            # For simplicity, we'll assume all were attempted, but actual inserted count
            # would require a specific mechanism (e.g., fetching after the fact, or
            # more complex statement with RETURNING if not SQLite).
            # For now, let's just count how many we *attempted* to add.
            processed_successfully_count = len(articles_to_add)

            logger.info(f"Successfully attempted to add {processed_successfully_count} articles from {feed.name}.")

        except Exception as e:
            logger.error(f"Critical error during batch database insertion for {feed.name}: {e}")
            if self.db is not None:
                self.db.rollback()  # Rollback only on a batch-level failure
            return 0  # Indicate that this batch failed to insert

        return processed_successfully_count
    
    async def _extract_with_newspaper3k(self, article_url: str) -> Optional[str]:
        """
        Extract content using Newspaper3k as fallback.
        """
        try:
            # Configure Newspaper3k
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            config.request_timeout = 15
            config.fetch_images = True
            config.memoize_articles = False
            
            # Create article object
            article = Article(article_url, config=config)
            
            # Download and parse
            article.download()
            article.parse()
            
            if hasattr(article, 'html') and article.html:
                soup = BeautifulSoup(article.html, 'html.parser')
                
                # Find the main content area
                content_area = self._find_main_content_area(soup)
                
                if content_area:
                    # Extract text with embedded images
                    content_with_images = self._extract_text_with_images(content_area, article_url)
                    if content_with_images:
                        return self._clean_extracted_content(content_with_images)
            
            # Fallback to plain text if HTML extraction fails
            if hasattr(article, 'text') and article.text:
                return self._clean_extracted_content(article.text)

        except Exception as e:
            logger.error(f"Error extracting content with Newspaper3k from {article_url}: {e}")
        
        return None
    
    # ============================================================================
    # PRIVATE METHODS (Sync)
    # ============================================================================
    
    def _get_or_create_feed_id(self, feed: RSSFeed) -> int:
        """
        Get or create RSS feed ID in database.
        """
        if self.db is None:
            return 0
        db_feed = self.db.query(RSSFeedModel).filter(
            RSSFeedModel.name == feed.name
        ).first()
        
        if not db_feed:
            db_feed = RSSFeedModel(
                name=feed.name,
                url=feed.url,
                category=feed.category.value
            )
            if self.db is not None:
                self.db.add(db_feed)
                self.db.commit()
                self.db.refresh(db_feed)
        
        db_feed_id = getattr(db_feed, 'id', None)
        if db_feed_id is None:
            raise ValueError('db_feed.id is None')
        return int(db_feed_id)
    
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
    
    def _extract_published_date(self, entry) -> Optional[datetime]:
        """
        Robustly extract published date from RSS entry, trying all common fields.
        Always returns a UTC datetime (with tzinfo=timezone.utc).
        """
        from dateutil import parser as dateutil_parser
        from datetime import timezone
        import re
        
        date_fields = [
            'published', 'pubDate', 'updated', 'created', 'date',
            'dc:date', 'dc:created', 'dc:issued', 'dc:modified', 'issued', 'modified'
        ]
        
        for field in date_fields:
            date_str = entry.get(field)
            if date_str:
                # Normalize timezone format: GMT+7 -> +07, GMT-5 -> -05
                date_str = re.sub(r'GMT\+(\d{1,2})', r'+\1', date_str)
                date_str = re.sub(r'GMT-(\d{1,2})', r'-\1', date_str)
                
                try:
                    dt = dateutil_parser.parse(date_str)
                    if dt.tzinfo is not None:
                        return dt.astimezone(timezone.utc)
                    else:
                        return dt.replace(tzinfo=timezone.utc)
                except Exception:
                    logger.warning(f"---- Error parsing date {date_str} ----")
                    pass
        return None
    
    def _extract_image(self, entry) -> Optional[str]:
        """
        Extract image URL from RSS entry, including <image> tags, <img> tags, or <a> tags containing an <img> tag.
        """
        from bs4.element import Tag
        image_url = None

        # Check media:content
        if 'media_content' in entry and entry['media_content']:
            image_url = entry['media_content'][0].get('url')
        elif 'media_thumbnail' in entry and entry['media_thumbnail']:
            image_url = entry['media_thumbnail'][0].get('url')
        elif 'enclosures' in entry and entry['enclosures']:
            for enclosure in entry['enclosures']:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break

        # If not found, try to extract from HTML content (summary/description/content)
        if not image_url:
            html_fields = []
            content_field = entry.get('content')
            if isinstance(content_field, list):
                for item in content_field:
                    if isinstance(item, dict):
                        html_fields.append(item.get('value', ''))
                    elif isinstance(item, str):
                        html_fields.append(item)
            elif isinstance(content_field, dict):
                html_fields.append(content_field.get('value', ''))
            elif isinstance(content_field, str):
                html_fields.append(content_field)
            for key in ['summary', 'description']:
                val = entry.get(key)
                if isinstance(val, str):
                    html_fields.append(val)
            for html in html_fields:
                if not html:
                    continue
                soup = BeautifulSoup(html, 'xml')
                # Try <image> tag
                image_tag = soup.find('image')
                if isinstance(image_tag, Tag):
                    # Prefer src attribute, but fallback to text content
                    if image_tag.has_attr('src'):
                        image_url = image_tag['src']
                        break
                    elif image_tag.string and image_tag.string.strip().startswith('http'):
                        image_url = image_tag.string.strip()
                        break
                # Try <img> tag
                img_tag = soup.find('img')
                if isinstance(img_tag, Tag) and img_tag.has_attr('src'):
                    image_url = img_tag['src']
                    break
                # Try <a> tag containing <img>
                a_tag = soup.find('a')
                if isinstance(a_tag, Tag):
                    img_in_a = a_tag.find('img')
                    if isinstance(img_in_a, Tag) and img_in_a.has_attr('src'):
                        image_url = img_in_a['src']
                        break
        # Ensure return type is str or None
        if isinstance(image_url, list):
            return image_url[0] if image_url else None
        if isinstance(image_url, str):
            return image_url
        return None
    
    def _find_main_content_area(self, soup: BeautifulSoup):
        """
        Find the main content area in the HTML.
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="post"]',
            '[class*="entry"]',
            'main',
            '.entry-content',
            '.post-content',
            '.article-content',
            '.story-content',
            '.content-body'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content and len(content.get_text(strip=True)) > 500:
                return content
        
        # If no specific content area found, return body
        return soup.find('body')

    def _extract_text_with_images(self, content_area, base_url: str) -> str:
        """
        Extract text content with embedded image references.
        """
        if not content_area:
            return ""
        
        # Process the content area to extract text and images
        content_parts = []
        
        # Process each element in the content area
        for element in content_area.find_all(['p', 'div', 'img', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if element.name == 'img':
                # Handle image element
                img_src = element.get('src') or element.get('data-src') or element.get('data-lazy-src')
                if img_src:
                    # Convert to absolute URL
                    img_src = self._make_absolute_url(img_src, base_url)
                    if self._is_valid_content_image(img_src):
                        # Add image reference to content
                        alt_text = element.get('alt', '')
                        content_parts.append(f"\n[IMAGE: {img_src}]\n")
                        if alt_text:
                            content_parts.append(f"[Image description: {alt_text}]\n")
            elif element.name == 'figure':
                # Handle figure element (often contains images with captions)
                img = element.find('img')
                if img:
                    img_src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if img_src:
                        img_src = self._make_absolute_url(img_src, base_url)
                        if self._is_valid_content_image(img_src):
                            content_parts.append(f"\n[IMAGE: {img_src}]\n")
                            # Add caption if available
                            figcaption = element.find('figcaption')
                            if figcaption:
                                caption_text = figcaption.get_text(strip=True)
                                if caption_text:
                                    content_parts.append(f"[Image caption: {caption_text}]\n")
            else:
                # Handle text elements
                text = element.get_text(strip=True)
                if text:
                    content_parts.append(text + "\n")
        
        return " ".join(content_parts)

    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """
        Convert relative URL to absolute URL.
        """
        if not url:
            return ""
        
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            from urllib.parse import urljoin
            return urljoin(base_url, url)
        elif not url.startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            return urljoin(base_url, url)
        
        return url

    def _is_valid_content_image(self, image_url: str) -> bool:
        """
        Check if an image URL is valid for content embedding.
        """
        if not image_url or len(image_url) < 10:
            return False
        
        # Skip data URIs
        if image_url.startswith('data:'):
            return False
        
        # Skip common unwanted patterns
        unwanted_patterns = [
            'avatar', 'icon', 'logo', 'banner', 'ad', 'advertisement',
            'social', 'share', 'facebook', 'twitter', 'instagram',
            'pixel', 'tracking', 'analytics', '1x1', 'blank',
            'spacer', 'clear', 'transparent'
        ]
        
        image_url_lower = image_url.lower()
        for pattern in unwanted_patterns:
            if pattern in image_url_lower:
                return False
        
        return True

    def _clean_extracted_content(self, text: str) -> str:
        """
        Clean and format extracted content.
        """
        # Check if content contains HTML tags
        if '<' in text and '>' in text:
            # Apply HTML sanitization first
            text = self._sanitize_html_attributes(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common unwanted patterns
        text = re.sub(r'Share this article.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Follow us.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Subscribe.*', '', text, flags=re.IGNORECASE)
        
        # Limit content length to avoid database issues
        # SQLite TEXT can handle up to 1GB, so we can be more generous
        if len(text) > 200_000:
            text = text[:200_000] + "..."
        
        return text.strip()
    
    def _sanitize_html_attributes(self, html_content: str) -> str:
        """
        Remove all class names, IDs, and data attributes from HTML tags while preserving content structure.
        This creates clean, minimal HTML that's easier to style and maintain.
        """
        if not html_content:
            return ""
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Define attributes to remove
        attributes_to_remove = [
            'class', 'id', 'style', 'onclick', 'onload', 'onerror',
            'onmouseover', 'onmouseout', 'onfocus', 'onblur', 'onchange',
            'oninput', 'onsubmit', 'onreset', 'onselect', 'onunload',
            'onkeydown', 'onkeyup', 'onkeypress', 'onmousedown', 'onmouseup',
            'onmousemove', 'onmouseenter', 'onmouseleave', 'oncontextmenu',
            'onabort', 'onbeforeunload', 'onerror', 'onhashchange', 'onmessage',
            'onoffline', 'ononline', 'onpagehide', 'onpageshow', 'onpopstate',
            'onresize', 'onstorage', 'onbeforeprint', 'onafterprint',
            'role', 'tabindex', 'accesskey', 'contenteditable',
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
    
    async def clean_content_batch(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Clean HTML content for all articles in the database in batches.
        This removes class names, IDs, and data attributes from existing content.
        """
        if self.db is None:
            return {"status": "error", "message": "Database not available"}
        
        try:
            # Get total count of articles with content
            total_articles = self.db.query(NewsArticle).filter(
                NewsArticle.content.isnot(None)
            ).count()
            
            if total_articles == 0:
                return {
                    "status": "success",
                    "message": "No articles with content found",
                    "total_articles": 0,
                    "processed_articles": 0,
                    "updated_articles": 0
                }
            
            processed_count = 0
            updated_count = 0
            
            # Process in batches
            offset = 0
            while offset < total_articles:
                # Get batch of articles
                articles = self.db.query(NewsArticle).filter(
                    NewsArticle.content.isnot(None)
                ).offset(offset).limit(batch_size).all()
                
                for article in articles:
                    processed_count += 1
                    
                    if getattr(article, 'content', None):
                        # Clean the content
                        cleaned_content = self._clean_extracted_content(getattr(article, 'content'))
                        
                        # Update if content changed
                        if cleaned_content != getattr(article, 'content'):
                            setattr(article, 'content', cleaned_content)
                            setattr(article, 'updated_at', datetime.now())
                            updated_count += 1
                
                # Commit batch
                self.db.commit()
                offset += batch_size
                
                logger.info(f"Processed {processed_count}/{total_articles} articles, updated {updated_count}")
            
            return {
                "status": "success",
                "message": f"Successfully cleaned content for {total_articles} articles",
                "total_articles": total_articles,
                "processed_articles": processed_count,
                "updated_articles": updated_count
            }
            
        except Exception as e:
            logger.error(f"Error during batch content cleaning: {e}")
            if self.db is not None:
                self.db.rollback()
            return {
                "status": "error",
                "message": f"Error during batch content cleaning: {str(e)}",
                "total_articles": 0,
                "processed_articles": 0,
                "updated_articles": 0
            }

    def _extract_main_image_url_from_html(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract the main image URL from HTML using meta tags and first <img> in main content area.
        """
        from bs4 import BeautifulSoup
        from bs4.element import Tag
        soup = BeautifulSoup(html, 'html.parser')
        # 1. Try og:image
        og_image = soup.find('meta', property='og:image')
        if isinstance(og_image, Tag):
            val = og_image.get('content')
            if isinstance(val, list):
                val = val[0] if val else None
            if isinstance(val, str):
                return self._make_absolute_url(val, base_url)
        # 2. Try twitter:image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if isinstance(twitter_image, Tag):
            val = twitter_image.get('content')
            if isinstance(val, list):
                val = val[0] if val else None
            if isinstance(val, str):
                return self._make_absolute_url(val, base_url)
        # 3. Try first <img> in main content area
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        if isinstance(main_content, Tag):
            img_tag = main_content.find('img')
            if isinstance(img_tag, Tag):
                val = img_tag.get('src')
                if isinstance(val, list):
                    val = val[0] if val else None
                if isinstance(val, str):
                    return self._make_absolute_url(val, base_url)
        # 4. Fallback: any <img> in the page
        img_tag = soup.find('img')
        if isinstance(img_tag, Tag):
            val = img_tag.get('src')
            if isinstance(val, list):
                val = val[0] if val else None
            if isinstance(val, str):
                return self._make_absolute_url(val, base_url)
        return None