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
from newspaper import Article, Config

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
                print(f'---- Get raw data from {feed.name} ----')
                self.db.add(raw_data)
                
                # Parse feed
                parsed_feed = feedparser.parse(response.text)
                articles_found = len(parsed_feed.entries)
                print(f'---- Found {articles_found} articles from {feed.name} ----')
                
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
            print(f"Error fetching feed {feed.name}: {e}")
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

        print(f'---- Processing {len(entries)} articles from {feed.name} ----')
        all_links = set()
        
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
                additional_images = []
                if link:
                    if link in all_links:
                        print(f'---- Link {link} already processed ----')
                        continue
                    all_links.add(link)
                    content, additional_images = await self._extract_article_content_and_images(link)
                
                # Use the best available image (RSS image first, then content images)
                final_image_url = image_url
                if not final_image_url and additional_images:
                    final_image_url = additional_images[0]
                
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
                    image_url=final_image_url,
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

    async def _extract_article_content_and_images(self, article_url: str) -> tuple[Optional[str], list[str]]:
        """
        Extract full article content and images using Newspaper3k.
        Returns tuple of (content_text, image_urls)
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
            
            # Extract text content with embedded images
            content = self._extract_content_with_images(article, article_url)
            
            # Extract standalone images for the image_url field
            images = []
            
            # Get top images from article
            if hasattr(article, 'top_image') and article.top_image:
                images.append(article.top_image)
            
            # Get all images (limit to 5)
            if hasattr(article, 'images') and article.images:
                # Filter and add unique images
                seen = set()
                for img in article.images:
                    if img and img not in seen and self._is_valid_newspaper_image(img):
                        seen.add(img)
                        images.append(img)
                        if len(images) >= 5:  # Limit to 5 images
                            break
            
            # Fallback to meta images if no images found
            if not images and hasattr(article, 'meta_img') and article.meta_img:
                images.append(article.meta_img)
            
            return content, images
            
        except Exception as e:
            print(f"Error extracting content with Newspaper3k from {article_url}: {e}")
            # Fallback to original method
            return await self._extract_article_content_fallback(article_url)

    def _extract_content_with_images(self, article, article_url: str) -> Optional[str]:
        """
        Extract content with embedded images from Newspaper3k article.
        """
        try:
            # Get the raw HTML content
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
            print(f"Error extracting content with images: {e}")
        
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

    def _is_valid_newspaper_image(self, image_url: str) -> bool:
        """
        Check if a Newspaper3k image URL is valid.
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
            'pixel', 'tracking', 'analytics', '1x1', 'blank'
        ]
        
        image_url_lower = image_url.lower()
        for pattern in unwanted_patterns:
            if pattern in image_url_lower:
                return False
        
        return True

    async def _extract_article_content_fallback(self, article_url: str) -> tuple[Optional[str], list[str]]:
        """
        Fallback content extraction method using BeautifulSoup.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(article_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract images first
                image_urls = self._extract_images_from_soup(soup, article_url)
                
                # Use trafilatura to extract main content
                extracted_text = trafilatura.extract(response.text, include_formatting=True)
                
                if extracted_text:
                    # Clean up the extracted text
                    cleaned_text = self._clean_extracted_content(extracted_text)
                    return cleaned_text, image_urls
                
                # Fallback to BeautifulSoup if trafilatura fails
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
                            return self._clean_extracted_content(text), image_urls
                
                # If no specific content area found, get body text
                body = soup.find('body')
                if body:
                    text = body.get_text(separator='\n', strip=True)
                    return self._clean_extracted_content(text), image_urls
                
        except Exception as e:
            print(f"Error in fallback extraction from {article_url}: {e}")
        
        return None, []

    def _extract_images_from_soup(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """
        Extract image URLs from BeautifulSoup object (fallback method).
        """
        image_urls = []
        
        # Find all img tags
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                
                # Filter out small images, icons, and common unwanted images
                if self._is_valid_article_image(img, src):
                    image_urls.append(src)
        
        # Also check for Open Graph and Twitter Card images
        try:
            og_image = soup.find('meta', attrs={'property': 'og:image'})
            if og_image and og_image.get('content'):
                image_urls.append(og_image['content'])
            
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                image_urls.append(twitter_image['content'])
        except Exception as e:
            print(f"Error extracting meta images: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in image_urls:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images[:5]  # Limit to 5 images per article

    def _is_valid_article_image(self, img_tag, src: str) -> bool:
        """
        Check if an image is likely to be a valid article image.
        """
        # Skip very small images (likely icons)
        width = img_tag.get('width')
        height = img_tag.get('height')
        if width and height:
            try:
                if int(width) < 100 or int(height) < 100:
                    return False
            except ValueError:
                pass
        
        # Skip common unwanted image patterns
        unwanted_patterns = [
            'avatar', 'icon', 'logo', 'banner', 'ad', 'advertisement',
            'social', 'share', 'facebook', 'twitter', 'instagram',
            'pixel', 'tracking', 'analytics', '1x1', 'blank'
        ]
        
        src_lower = src.lower()
        for pattern in unwanted_patterns:
            if pattern in src_lower:
                return False
        
        # Skip data URIs and very short URLs
        if src.startswith('data:') or len(src) < 10:
            return False
        
        return True
    
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