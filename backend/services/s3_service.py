"""
S3 service for storing and retrieving news data.
"""

import boto3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging
from botocore.exceptions import ClientError, NoCredentialsError
import re
import random

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing news data in S3."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            endpoint_url=os.getenv('AWS_S3_ENDPOINT_URL') or None
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET environment variable is required")
    
    def _generate_article_name(self, title: str) -> str:
        """Generate a unique article name from title."""
        # Clean the title for use as a filename
        clean_title = re.sub(r'[^\w\s-]', '', title.lower())
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        clean_title = clean_title.strip('-')
        
        # Limit length
        if len(clean_title) > 100:
            clean_title = clean_title[:100]
        
        return clean_title
    
    def _ensure_unique_name(self, base_name: str, existing_names: List[str]) -> str:
        """Ensure the article name is unique by appending a random number if needed."""
        if base_name not in existing_names:
            return base_name
        
        # Append a random 4-digit number
        random_suffix = f"{random.randint(1000, 9999)}"
        new_name = f"{base_name}-{random_suffix}"
        
        # Keep trying until we get a unique name
        while new_name in existing_names:
            random_suffix = f"{random.randint(1000, 9999)}"
            new_name = f"{base_name}-{random_suffix}"
        
        return new_name
    
    def _get_object(self, key: str) -> Optional[Dict[str, Any]]:
        """Get an object from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"Error getting object {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting object {key}: {e}")
            return None
    
    def _put_object(self, key: str, data: Dict[str, Any]) -> bool:
        """Put an object to S3."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(data, default=str),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            logger.error(f"Error putting object {key}: {e}")
            return False
    
    def _delete_object(self, key: str) -> bool:
        """Delete an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting object {key}: {e}")
            return False
    
    def _list_objects(self, prefix: str) -> List[str]:
        """List objects with a given prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"Error listing objects with prefix {prefix}: {e}")
            return []
    
    # RSS Feed Management
    def get_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get all RSS feeds."""
        feeds = self._get_object('feeds/rss_feeds.json')
        return feeds.get('feeds', []) if feeds else []
    
    def save_rss_feeds(self, feeds: List[Dict[str, Any]]) -> bool:
        """Save RSS feeds."""
        return self._put_object('feeds/rss_feeds.json', {
            'feeds': feeds,
            'updated_at': datetime.now(timezone.utc).isoformat()
        })
    
    def get_feed_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific RSS feed by name."""
        feeds = self.get_rss_feeds()
        for feed in feeds:
            if feed.get('name') == name:
                return feed
        return None
    
    # Article Management
    def save_article(self, article_data: Dict[str, Any]) -> Optional[str]:
        """Save an article and return its name."""
        # Get existing article names to ensure uniqueness
        existing_articles = self.get_all_article_names()
        
        # Generate article name
        base_name = self._generate_article_name(article_data['title'])
        article_name = self._ensure_unique_name(base_name, existing_articles)
        
        # Add metadata
        article_data['article_name'] = article_name
        article_data['created_at'] = datetime.now(timezone.utc).isoformat()
        article_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Save to S3
        key = f"articles/{article_name}.json"
        if self._put_object(key, article_data):
            return article_name
        return None
    
    def get_article_by_name(self, article_name: str) -> Optional[Dict[str, Any]]:
        """Get an article by its name."""
        return self._get_object(f"articles/{article_name}.json")
    
    def get_all_articles(self, limit: int = 100, offset: int = 0, 
                        category: Optional[str] = None, 
                        source: Optional[str] = None,
                        feeds: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get articles with filtering and pagination."""
        # Get all article keys
        article_keys = self._list_objects('articles/')
        article_keys = [key for key in article_keys if key.endswith('.json')]
        
        # Sort by creation date (newest first)
        articles = []
        for key in article_keys:
            article = self._get_object(key)
            if article:
                articles.append(article)
        
        # Sort by published_date or created_at
        articles.sort(key=lambda x: x.get('published_date') or x.get('created_at', ''), reverse=True)
        
        # Apply filters
        if category:
            articles = [a for a in articles if a.get('category') == category]
        
        if source:
            articles = [a for a in articles if a.get('source_name') == source]
        
        if feeds:
            articles = [a for a in articles if a.get('source_name') in feeds]
        
        # Apply pagination
        total = len(articles)
        paginated_articles = articles[offset:offset + limit]
        
        return {
            'articles': paginated_articles,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def get_all_article_names(self) -> List[str]:
        """Get all article names."""
        article_keys = self._list_objects('articles/')
        return [key.replace('articles/', '').replace('.json', '') 
                for key in article_keys if key.endswith('.json')]
    
    def update_article(self, article_name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing article."""
        article = self.get_article_by_name(article_name)
        if not article:
            return False
        
        # Update fields
        article.update(updates)
        article['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        return self._put_object(f"articles/{article_name}.json", article)
    
    def delete_article(self, article_name: str) -> bool:
        """Delete an article."""
        return self._delete_object(f"articles/{article_name}.json")
    
    def delete_articles_by_source(self, source_name: str) -> int:
        """Delete all articles from a specific source."""
        articles = self.get_all_articles(limit=10000)  # Get all articles
        deleted_count = 0
        
        for article in articles['articles']:
            if article.get('source_name') == source_name:
                article_name = article.get('article_name')
                if article_name and self.delete_article(article_name):
                    deleted_count += 1
        
        return deleted_count
    
    # Feed Fetch Logs
    def save_fetch_log(self, log_data: Dict[str, Any]) -> bool:
        """Save a feed fetch log."""
        timestamp = datetime.now(timezone.utc)
        log_data['fetch_timestamp'] = timestamp.isoformat()
        
        # Get existing logs
        logs = self.get_fetch_logs()
        logs.append(log_data)
        
        # Keep only the last 1000 logs
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        return self._put_object('logs/feed_fetch_logs.json', {
            'logs': logs,
            'updated_at': timestamp.isoformat()
        })
    
    def get_fetch_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent fetch logs."""
        logs_data = self._get_object('logs/feed_fetch_logs.json')
        logs = logs_data.get('logs', []) if logs_data else []
        return logs[-limit:] if limit else logs
    
    # Statistics
    def update_stats(self) -> bool:
        """Update statistics."""
        try:
            # Get all data
            feeds = self.get_rss_feeds()
            articles_data = self.get_all_articles(limit=10000)
            articles = articles_data['articles']
            logs = self.get_fetch_logs(limit=1000)
            
            # Calculate statistics
            stats = {
                'total_feeds': len(feeds),
                'active_feeds': len([f for f in feeds if f.get('is_active', True)]),
                'total_articles': len(articles),
                'articles_by_category': {},
                'articles_by_source': {},
                'recent_fetch_logs': logs[-10:],  # Last 10 logs
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Count by category
            for article in articles:
                category = article.get('category', 'Unknown')
                stats['articles_by_category'][category] = stats['articles_by_category'].get(category, 0) + 1
                
                source = article.get('source_name', 'Unknown')
                stats['articles_by_source'][source] = stats['articles_by_source'].get(source, 0) + 1
            
            return self._put_object('stats/statistics.json', stats)
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        stats = self._get_object('stats/statistics.json')
        if not stats:
            # Generate stats if they don't exist
            self.update_stats()
            stats = self._get_object('stats/statistics.json') or {}
        return stats
    
    # Cleanup operations
    def cleanup_all_data(self) -> Dict[str, int]:
        """Clean up all data."""
        deleted_counts = {
            'articles': 0,
            'logs': 0
        }
        
        # Delete all articles
        article_keys = self._list_objects('articles/')
        for key in article_keys:
            if self._delete_object(key):
                deleted_counts['articles'] += 1
        
        # Delete logs
        log_keys = self._list_objects('logs/')
        for key in log_keys:
            if self._delete_object(key):
                deleted_counts['logs'] += 1
        
        # Reset stats
        self.update_stats()
        
        return deleted_counts 