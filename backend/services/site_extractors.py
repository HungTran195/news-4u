"""
Site-specific content extractors for different news websites.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class BaseSiteExtractor(ABC):
    """Base class for site-specific content extractors."""
    
    @abstractmethod
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract content from the BeautifulSoup object."""
        pass
    
    def clean_html_content(self, content: str) -> str:
        """Clean and format HTML content for better visibility."""
        if not content:
            return ""
        
        # First, sanitize the HTML by removing unwanted attributes
        content = self._sanitize_html_attributes(content)
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Add line breaks for better readability
        content = content.replace('</p>', '</p>\n\n')
        content = content.replace('</div>', '</div>\n')
        content = content.replace('</h1>', '</h1>\n\n')
        content = content.replace('</h2>', '</h2>\n\n')
        content = content.replace('</h3>', '</h3>\n\n')
        content = content.replace('</h4>', '</h4>\n\n')
        content = content.replace('</h5>', '</h5>\n\n')
        content = content.replace('</h6>', '</h6>\n\n')
        content = content.replace('</li>', '</li>\n')
        content = content.replace('</ul>', '</ul>\n\n')
        content = content.replace('</ol>', '</ol>\n\n')
        content = content.replace('</blockquote>', '</blockquote>\n\n')
        
        # Clean up multiple line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
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
    
    def remove_ads_and_unwanted_elements(self, content_area) -> None:
        """Remove ads and unwanted elements from content area."""
        if not content_area:
            return
        
        # Remove basic unwanted elements
        for unwanted in content_area.find_all(['script', 'style', 'iframe', 'ins']):
            unwanted.decompose()
        
        # Remove Google ads specifically
        for ad_element in content_area.find_all(attrs={'data-set': 'dfp'}):
            ad_element.decompose()
        
        # Remove other ad-related elements
        for ad_element in content_area.find_all(class_=lambda x: x and ('ad' in x.lower() or 'ads' in x.lower())):
            ad_element.decompose()
        
        # Remove elements with data-set attributes (usually ads)
        for ad_element in content_area.find_all(attrs={'data-set': True}):
            ad_element.decompose()
        
        # Remove Google AdSense elements
        for ad_element in content_area.find_all(id=lambda x: x and 'google_ads' in x.lower()):
            ad_element.decompose()
        
        # Remove elements with Google ad classes
        for ad_element in content_area.find_all(class_=lambda x: x and ('google' in x.lower() and 'ad' in x.lower())):
            ad_element.decompose()
        
        # Remove social media widgets
        for social_element in content_area.find_all(class_=lambda x: x and any(social in x.lower() for social in ['facebook', 'twitter', 'instagram', 'linkedin'])):
            social_element.decompose()
        
        # Remove newsletter signup forms
        for newsletter_element in content_area.find_all(class_=lambda x: x and any(term in x.lower() for term in ['newsletter', 'signup', 'subscribe'])):
            newsletter_element.decompose()
        
        # Remove comment sections
        for comment_element in content_area.find_all(class_=lambda x: x and any(term in x.lower() for term in ['comment', 'comments', 'disqus'])):
            comment_element.decompose()
        
        # Remove related news content
        for related_element in content_area.find_all(attrs={'type': 'RelatedOneNews'}):
            related_element.decompose()
        
        # Remove elements with related news indicators
        related_indicators = ['related', 'related-news', 'related-article', 'related-content', 'more-news']
        for related_element in content_area.find_all(class_=lambda x: x and any(indicator in x.lower() for indicator in related_indicators)):
            related_element.decompose()
        
        # Remove elements with related news IDs
        for related_element in content_area.find_all(id=lambda x: x and any(indicator in x.lower() for indicator in related_indicators)):
            related_element.decompose()
        
        # Remove elements that only contain single action words
        action_words = ['share', 'save', 'like', 'follow', 'subscribe', 'bookmark', 'print']
        for element in content_area.find_all(['div', 'span', 'p', 'a', 'button']):
            text_content = element.get_text(strip=True).lower()
            if text_content in action_words:
                element.decompose()

    def clean_image_tags(self, content_area) -> None:
        """Clean up image tags to handle nested a/img tags and prioritize captions."""
        if not content_area:
            return
        
        # Find all img tags
        for img_tag in content_area.find_all('img'):
            # Check if img is inside an a tag
            parent_a = img_tag.find_parent('a')
            
            if parent_a and parent_a.get('href'):
                # If both a tag and img tag have the same image URL, remove the a tag wrapper
                a_href = parent_a.get('href', '')
                img_src = img_tag.get('src', '')
                
                # Check if both point to the same image (case-insensitive comparison)
                if a_href.lower() == img_src.lower():
                    # Extract the img tag and replace the a tag with just the img
                    img_copy = img_tag.extract()
                    parent_a.replace_with(img_copy)
                
                # Handle caption prioritization
                caption = parent_a.get('title', '') or parent_a.get_text(strip=True)
                if caption and not img_tag.get('alt'):
                    img_tag['alt'] = caption

    def extract_with_fallbacks(self, soup: BeautifulSoup, base_url: str, primary_selectors: List[str]) -> Optional[str]:
        """
        Extract content using multiple CSS selectors with fallback strategy.
        """
        try:
            # Try primary selectors first
            for selector in primary_selectors:
                content_area = soup.select_one(selector)
                if content_area:
                    # Remove unwanted elements
                    self.remove_ads_and_unwanted_elements(content_area)
                    self.clean_image_tags(content_area)
                    
                    # Extract and clean content
                    content = self.clean_html_content(str(content_area))
                    if content and len(content.strip()) > 100:  # Minimum content length
                        return content
            
            return None
            
        except Exception as e:
            logger.error(f"Error in extract_with_fallbacks: {e}")
            return None


class Kenh14Extractor(BaseSiteExtractor):
    """Extractor for Kenh14.vn"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['div.detail-content', 'div.knc-content', 'article']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class VnExpressExtractor(BaseSiteExtractor):
    """Extractor for VnExpress.net"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['div.fck_detail', 'div.sidebar_1', 'div.content_detail', 'div.article_content', 'article']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)



class TuoiTreExtractor(BaseSiteExtractor):
    """Extractor for TuoiTre.vn"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['div[  data-role="content"]']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class TechCrunchExtractor(BaseSiteExtractor):
    """Extractor for TechCrunch.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['div.entry-content']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class BBCExtractor(BaseSiteExtractor):
    """Extractor for BBC.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['article', 'div[data-component="text-block"]']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class CNBCExtractor(BaseSiteExtractor):
    """Extractor for CNBC.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['div[data-module="ArticleBody"]']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class TheVergeExtractor(BaseSiteExtractor):
    """Extractor for TheVerge.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['div.duet--layout--entry-body-container', 'article']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class EngadgetExtractor(BaseSiteExtractor):
    """Extractor for Engadget.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = [
            'div.caas-body',
            'div.article-body'
        ]
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class ABCNewsExtractor(BaseSiteExtractor):
    """Extractor for ABCNews.go.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        # Get property data-testid = prism-article-body
        primary_selectors = [
            'div[data-testid="prism-article-body"]',
            'div.article-body',
            'div.content'
        ]
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class NBCNewsExtractor(BaseSiteExtractor):
    """Extractor for NBCNews.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = [
            'div.article-body__content',
            'div.article-content'
        ]
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


class CBSNewsExtractor(BaseSiteExtractor):
    """Extractor for CBSNews.com"""
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['section.content__body', 'div.article-content']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)


# Site Extractor Manager
class SiteExtractorManager:
    """Manages site-specific content extractors."""
    
    def __init__(self):
        self.extractors = {}
        self._register_default_extractors()
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower()
    
    def get_extractor(self, url: str) -> Optional[BaseSiteExtractor]:
        """Get appropriate extractor for the given URL."""
        domain = self.get_domain(url)
        
        # Check for exact domain match
        if domain in self.extractors:
            return self.extractors[domain]
        
        # Check for partial domain match
        for registered_domain, extractor in self.extractors.items():
            if registered_domain in domain or domain in registered_domain:
                return extractor
        
        return None
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract content using the appropriate extractor."""
        extractor = self.get_extractor(url)
        if extractor:
            return extractor.extract_content(soup, url)
        return None
    
    def _register_default_extractors(self):
        """Register default extractors for known sites."""
        self.extractors.update({
            'kenh14.vn': Kenh14Extractor(),
            'vnexpress.net': VnExpressExtractor(),
            'tuoitre.vn': TuoiTreExtractor(),
            'techcrunch.com': TechCrunchExtractor(),
            'bbc.com': BBCExtractor(),
            'cnbc.com': CNBCExtractor(),
            'theverge.com': TheVergeExtractor(),
            'engadget.com': EngadgetExtractor(),
            'abcnews.go.com': ABCNewsExtractor(),
            'nbcnews.com': NBCNewsExtractor(),
            'cbsnews.com': CBSNewsExtractor(),
        })


# Global instance
site_extractor_manager = SiteExtractorManager() 