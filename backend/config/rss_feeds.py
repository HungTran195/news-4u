"""
RSS Feeds Configuration
"""

from typing import Dict, List, NamedTuple
from enum import Enum


class NewsCategory(str, Enum):
    TECH = "tech"
    FINANCE = "finance"
    GLOBAL_NEWS = "global_news"


class RSSFeed(NamedTuple):
    name: str
    url: str
    category: NewsCategory
    description: str


# RSS Feeds Configuration
RSS_FEEDS: Dict[NewsCategory, List[RSSFeed]] = {
    NewsCategory.TECH: [
        RSSFeed(
            name="TechCrunch",
            url="https://techcrunch.com/feed/",
            category=NewsCategory.TECH,
            description="Latest technology news and startup information"
        ),
        RSSFeed(
            name="The Verge",
            url="https://www.theverge.com/rss/index.xml",
            category=NewsCategory.TECH,
            description="Technology, science, art, and culture news"
        ),
    ],
    
    NewsCategory.FINANCE: [
        RSSFeed(
            name="Yahoo Finance",
            url="https://news.yahoo.com/rss/finance",
            category=NewsCategory.FINANCE,
            description="Financial news and market updates"
        ),
        RSSFeed(
            name="Financial Times",
            url="https://www.ft.com/rss/home",
            category=NewsCategory.FINANCE,
            description="International business and financial news"
        ),
        RSSFeed(
            name="CNBC",
            url="https://feeds.nbcnews.com/nbcnews/public/business",
            category=NewsCategory.FINANCE,
            description="Business and financial news from CNBC"
        ),
    ],
    
    NewsCategory.GLOBAL_NEWS: [
        RSSFeed(
            name="BBC News",
            url="https://feeds.bbci.co.uk/news/rss.xml",
            category=NewsCategory.GLOBAL_NEWS,
            description="International news from BBC"
        ),
        RSSFeed(
            name="BBC News – World",
            url="https://feeds.bbci.co.uk/news/world/rss.xml",
            category=NewsCategory.GLOBAL_NEWS,
            description="World news from BBC"
        ),
        RSSFeed(
            name="Reuters World News",
            url="https://feeds.reuters.com/Reuters/worldNews",
            category=NewsCategory.GLOBAL_NEWS,
            description="Global news coverage from Reuters"
        ),
        RSSFeed(
            name="Vox",
            url="https://www.vox.com/rss/index.xml",
            category=NewsCategory.GLOBAL_NEWS,
            description="Explanatory journalism and news analysis"
        ),
    ]
}


def get_all_feeds() -> List[RSSFeed]:
    """Get all RSS feeds as a flat list."""
    all_feeds = []
    for category_feeds in RSS_FEEDS.values():
        all_feeds.extend(category_feeds)
    return all_feeds


def get_feeds_by_category(category: NewsCategory) -> List[RSSFeed]:
    """Get RSS feeds for a specific category."""
    return RSS_FEEDS.get(category, [])


def get_feed_by_name(name: str) -> RSSFeed | None:
    """Get a specific RSS feed by name."""
    for feed in get_all_feeds():
        if feed.name.lower() == name.lower():
            return feed
    return None


def add_feed(feed: RSSFeed) -> None:
    """Add a new RSS feed to the configuration."""
    if feed.category not in RSS_FEEDS:
        RSS_FEEDS[feed.category] = []
    RSS_FEEDS[feed.category].append(feed)


def remove_feed(name: str) -> bool:
    """Remove an RSS feed by name."""
    for category in RSS_FEEDS:
        RSS_FEEDS[category] = [
            feed for feed in RSS_FEEDS[category] 
            if feed.name.lower() != name.lower()
        ]
    return True


def update_feed(name: str, updated_feed: RSSFeed) -> bool:
    """Update an existing RSS feed."""
    if remove_feed(name):
        add_feed(updated_feed)
        return True
    return False 