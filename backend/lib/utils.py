import re
import random
import string
from typing import Optional


def generate_slug(title: str, article_id: Optional[int] = None) -> str:
    """
    Generate a URL-friendly slug from an article title.
    Format: first 15 characters of title + 8 random alphanumeric characters
    
    Args:
        title: The article title
        article_id: Optional article ID to ensure uniqueness
    
    Returns:
        A URL-friendly slug
    """
    # Clean the title: remove special characters, convert to lowercase
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
    
    # Take first 15 characters, remove extra spaces
    title_part = re.sub(r'\s+', '', clean_title)[:15]
    
    # Generate 8 random alphanumeric characters
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Combine title part and random part
    slug = f"{title_part}{random_part}"
    
    return slug


def generate_unique_slug(title: str, existing_slugs: set, article_id: Optional[int] = None) -> str:
    """
    Generate a unique slug, ensuring it doesn't conflict with existing slugs.
    
    Args:
        title: The article title
        existing_slugs: Set of existing slugs to avoid conflicts
        article_id: Optional article ID to ensure uniqueness
    
    Returns:
        A unique URL-friendly slug
    """
    max_attempts = 10
    for attempt in range(max_attempts):
        slug = generate_slug(title, article_id)
        if slug not in existing_slugs:
            return slug
    
    # If we still have conflicts after max attempts, add a number
    base_slug = generate_slug(title, article_id)
    counter = 1
    while f"{base_slug}{counter}" in existing_slugs:
        counter += 1
    
    return f"{base_slug}{counter}" 