"""
Google News Service
Fetches news from Google News with search and time filtering capabilities.
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote_plus

from models.database import NewsArticle
from sqlalchemy.orm import Session
from schemas.news import NewsArticleCreate


class GoogleNewsService:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://news.google.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def search_news(
        self, 
        query: str = "", 
        category: str = "all",
        time_filter: str = "24h",
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search Google News with various filters.
        
        Args:
            query: Search query
            category: News category (all, tech, business, world, etc.)
            time_filter: Time filter (1h, 24h, 7d, 1m)
            max_results: Maximum number of results to return
        """
        try:
            # Build Google News URL
            url = self._build_search_url(query, category, time_filter)
            
            async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract news articles
                articles = self._parse_google_news(soup, max_results)
                
                return articles
                
        except Exception as e:
            print(f"Error fetching Google News: {e}")
            return []

    def _build_search_url(self, query: str, category: str, time_filter: str) -> str:
        """Build Google News search URL."""
        base_url = "https://news.google.com/search"
        
        # Add query parameter
        if query:
            base_url += f"?q={quote_plus(query)}"
        else:
            base_url += "?q=news"
        
        # Add category parameter
        if category and category != "all":
            base_url += f"&hl=en&gl=US&ceid=US:en&topic={category.upper()}"
        
        # Add time filter
        if time_filter:
            base_url += f"&tbm=nws&tbs=qdr:{time_filter}"
        
        return base_url

    def _parse_google_news(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """Parse Google News HTML and extract articles."""
        articles = []
        
        # Find article containers
        article_containers = soup.find_all('article', class_='MQsxIb')
        
        for container in article_containers[:max_results]:
            try:
                article = self._extract_article_data(container)
                if article:
                    articles.append(article)
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
        
        return articles

    def _extract_article_data(self, container) -> Optional[Dict]:
        """Extract article data from a container element."""
        try:
            # Extract title and link
            title_element = container.find('h3') or container.find('h4')
            if not title_element:
                return None
            
            title = title_element.get_text(strip=True)
            if not title:
                return None
            
            # Extract link
            link_element = title_element.find_parent('a') or container.find('a')
            if not link_element:
                return None
            
            link = link_element.get('href', '')
            if link.startswith('./'):
                link = self.base_url + link[1:]
            elif link.startswith('/'):
                link = self.base_url + link
            
            # Extract source and time
            source_element = container.find('time') or container.find('span', class_='vr1PYe')
            source = "Google News"
            published_date = datetime.now()
            
            if source_element:
                source_text = source_element.get_text(strip=True)
                if source_text:
                    # Try to extract source from the text
                    source_match = re.search(r'([A-Za-z\s]+)', source_text)
                    if source_match:
                        source = source_match.group(1).strip()
            
            # Extract summary/snippet
            summary_element = container.find('div', class_='VDXfz') or container.find('p')
            summary = ""
            if summary_element:
                summary = summary_element.get_text(strip=True)
            
            # Determine category based on content or use default
            category = "global_news"
            
            return {
                'title': title,
                'link': link,
                'summary': summary,
                'source_name': source,
                'source_url': self.base_url,
                'category': category,
                'published_date': published_date,
                'image_url': None,
                'author': None
            }
            
        except Exception as e:
            print(f"Error extracting article data: {e}")
            return None

    async def save_google_news_articles(self, articles: List[Dict]) -> int:
        """Save Google News articles to database."""
        saved_count = 0
        
        for article_data in articles:
            try:
                # Check if article already exists
                existing = self.db.query(NewsArticle).filter(
                    NewsArticle.title == article_data['title'],
                    NewsArticle.source_name == article_data['source_name']
                ).first()
                
                if existing:
                    continue
                
                # Create new article
                article = NewsArticle(
                    title=article_data['title'],
                    summary=article_data['summary'],
                    link=article_data['link'],
                    author=article_data['author'],
                    published_date=article_data['published_date'],
                    category=article_data['category'],
                    source_name=article_data['source_name'],
                    source_url=article_data['source_url'],
                    image_url=article_data['image_url'],
                    is_processed=True
                )
                
                self.db.add(article)
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving Google News article: {e}")
                continue
        
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error committing Google News articles: {e}")
        
        return saved_count

    async def fetch_and_save_google_news(
        self, 
        query: str = "", 
        category: str = "all",
        time_filter: str = "24h",
        max_results: int = 50
    ) -> Dict:
        """Fetch Google News and save to database."""
        start_time = time.time()
        
        try:
            # Fetch articles
            articles = await self.search_news(query, category, time_filter, max_results)
            
            # Save to database
            saved_count = await self.save_google_news_articles(articles)
            
            execution_time = time.time() - start_time
            
            return {
                "status": "success",
                "articles_found": len(articles),
                "articles_saved": saved_count,
                "execution_time": execution_time,
                "query": query,
                "category": category,
                "time_filter": time_filter
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "status": "error",
                "error_message": str(e),
                "execution_time": execution_time,
                "query": query,
                "category": category,
                "time_filter": time_filter
            } 