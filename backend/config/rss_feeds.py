"""
RSS Feeds Configuration
"""

from typing import Dict, List, NamedTuple
from enum import Enum


class NewsCategory(str, Enum):
    TECH = "Tech"
    GLOBAL_NEWS = "Global News"
    VIETNAMESE_NEWS = "Vietnamese News"
    US_NEWS = "US News"

class RSSFeed(NamedTuple):
    name: str
    url: str
    category: NewsCategory

# RSS Feeds Configuration
RSS_FEEDS: Dict[NewsCategory, List[RSSFeed]] = {
    NewsCategory.VIETNAMESE_NEWS: [
        RSSFeed(
            name="Vnexpress",
            url="https://vnexpress.net/rss/tin-moi-nhat.rss",
            category=NewsCategory.VIETNAMESE_NEWS
        ),
        RSSFeed(
            name="Tuoitre",
            url="https://tuoitre.vn/rss/tin-moi-nhat.rss",
            category=NewsCategory.VIETNAMESE_NEWS
        ),
        RSSFeed(
            name="Kenh14",
            url="https://kenh14.vn/rss/home.rss",
            category=NewsCategory.VIETNAMESE_NEWS
        ),
    ],
    NewsCategory.TECH: [
        RSSFeed(
            name="TechCrunch",
            url="https://techcrunch.com/feed/",
            category=NewsCategory.TECH
        ),
        RSSFeed(
            name="The Verge",
            url="https://www.theverge.com/rss/index.xml",
            category=NewsCategory.TECH
        ),
        RSSFeed(
            name="Engadget",
            url="https://www.engadget.com/rss.xml",
            category=NewsCategory.TECH
        )
    ],
    NewsCategory.US_NEWS: [
        RSSFeed(
            name="CNBC",
            url="https://www.cnbc.com/id/100003114/device/rss/rss.html",
            category=NewsCategory.US_NEWS
        ),
        RSSFeed(
            name="NBC News",
            url="https://feeds.nbcnews.com/nbcnews/public/news",
            category=NewsCategory.US_NEWS
        ),
        RSSFeed(
            name= "ABC News",
            url="https://abcnews.go.com/abcnews/usheadlines",
            category=NewsCategory.US_NEWS
        ),
    ],

    NewsCategory.GLOBAL_NEWS: [
        RSSFeed(
            name="BBC News",
            url="https://feeds.bbci.co.uk/news/rss.xml",
            category=NewsCategory.GLOBAL_NEWS
        ),
        RSSFeed(
            name="CNBC Global",
            url="https://www.cnbc.com/id/100727362/device/rss/rss.html",
            category=NewsCategory.GLOBAL_NEWS
        ),
        RSSFeed(
            name="CBSNews",
            url="https://www.cbsnews.com/latest/rss/world",
            category=NewsCategory.GLOBAL_NEWS
        ),
    ]    
}


def get_all_feeds() -> List[RSSFeed]:
    """Get all RSS feeds as a flat list."""
    all_feeds = []
    for category_feeds in RSS_FEEDS.values():
        all_feeds.extend(category_feeds)
    return all_feeds


def get_feed_by_name(name: str) -> RSSFeed | None:
    """Get a specific RSS feed by name."""
    for feed in get_all_feeds():
        if feed.name.lower() == name.lower():
            return feed
    return None


# TODO: The following functions are defined for future use but not currently used in the codebase
# They can be uncommented and implemented when needed for dynamic feed management

# def get_feeds_by_category(category: NewsCategory) -> List[RSSFeed]:
#     """Get RSS feeds for a specific category."""
#     return RSS_FEEDS.get(category, [])

# def add_feed(feed: RSSFeed) -> None:
#     """Add a new RSS feed to the configuration."""
#     if feed.category not in RSS_FEEDS:
#         RSS_FEEDS[feed.category] = []
#     RSS_FEEDS[feed.category].append(feed)

# def remove_feed(name: str) -> bool:
#     """Remove an RSS feed by name."""
#     for category in RSS_FEEDS:
#         RSS_FEEDS[category] = [
#             feed for feed in RSS_FEEDS[category] 
#             if feed.name.lower() != name.lower()
#         ]
#     return True

# def update_feed(name: str, updated_feed: RSSFeed) -> bool:
#     """Update an existing RSS feed."""
#     if remove_feed(name):
#         add_feed(updated_feed)
#         return True
#     return False