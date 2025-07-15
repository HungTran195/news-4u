"""
Site-specific content extractors for different news websites.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict, Any
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

class BaseSiteExtractor(ABC):
    """Base class for site-specific content extractors."""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        pass
    
    @abstractmethod
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract content from the BeautifulSoup object."""
        pass
    
    def clean_html_content(self, content: str) -> str:
        """Clean and format HTML content for better visibility."""
        if not content:
            return ""
        
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
        
        # Remove elements that only contain single action words
        action_words = ['share', 'save', 'like', 'follow', 'subscribe', 'bookmark', 'print']
        for element in content_area.find_all(['div', 'span', 'p', 'a', 'button']):
            text_content = element.get_text(strip=True).lower()
            if text_content in action_words:
                element.decompose()

    def extract_with_fallbacks(self, soup: BeautifulSoup, base_url: str, primary_selectors: List[str], fallback_selectors: Optional[List[str]] = None) -> Optional[str]:
        """Generic extraction method with fallback selectors."""
        try:
            # Try primary selectors first
            for selector in primary_selectors:
                if selector.startswith('.'):
                    content_area = soup.find('div', class_=selector[1:])  # type: ignore
                elif selector.startswith('#'):
                    content_area = soup.find('div', id=selector[1:])  # type: ignore
                else:
                    content_area = soup.find(selector)
                
                if content_area:
                    self.remove_ads_and_unwanted_elements(content_area)
                    content_html = str(content_area)
                    return self.clean_html_content(content_html)
            
            # Try fallback selectors if provided
            if fallback_selectors:
                for selector in fallback_selectors:
                    if selector.startswith('.'):
                        content_area = soup.find('div', class_=selector[1:])  # type: ignore
                    elif selector.startswith('#'):
                        content_area = soup.find('div', id=selector[1:])  # type: ignore
                    else:
                        content_area = soup.find(selector)
                    
                    if content_area:
                        self.remove_ads_and_unwanted_elements(content_area)
                        content_html = str(content_area)
                        return self.clean_html_content(content_html)
            
            return None
            
        except Exception as e:
            print(f"Error in extract_with_fallbacks: {e}")
            return None

class Kenh14Extractor(BaseSiteExtractor):
    """Content extractor for kenh14.vn."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from kenh14.vn."""
        return 'kenh14.vn' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract content from kenh14.vn using the detail-content class."""
        primary_selectors = ['.detail-content', '.knc-content']
        fallback_selectors = ['article']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors, fallback_selectors)

class VnExpressExtractor(BaseSiteExtractor):
    """Content extractor for vnexpress.net."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from vnexpress.net."""
        return 'vnexpress.net' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract content from vnexpress.net."""
        try:
            # Find the container first
            container = soup.find('div', class_='container')  # type: ignore
            if not container:
                return None
            
            # Find the sidebar-1 content area inside container
            content_area = container.find('div', class_='sidebar-1')  # type: ignore
            
            if not content_area:
                # Fallback: try other common selectors
                primary_selectors = ['.fck_detail']
                fallback_selectors = ['article']
                return self.extract_with_fallbacks(soup, base_url, primary_selectors, fallback_selectors)
            
            self.remove_ads_and_unwanted_elements(content_area)
            content_html = str(content_area)
            return self.clean_html_content(content_html)
            
        except Exception as e:
            print(f"Error extracting content from vnexpress.net: {e}")
            return None

class TuoiTreExtractor(BaseSiteExtractor):
    """Content extractor for tuoitre.vn."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from tuoitre.vn."""
        return 'tuoitre.vn' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract content from tuoitre.vn."""
        try:
            # Find the main detail container first
            detail_main = soup.find('div', class_='detail__main')  # type: ignore
            if not detail_main:
                return None
            
            # Find the main-detail ID inside detail__main
            main_detail = detail_main.find('div', id='main-detail')  # type: ignore
            if not main_detail:
                return None
            
            # Find the detail-content class inside main-detail
            content_area = main_detail.find('div', class_='detail-content')  # type: ignore
            
            if not content_area:
                # Fallback: try other common selectors
                primary_selectors = ['.detail-content', '.content-detail']
                return self.extract_with_fallbacks(soup, base_url, primary_selectors)
            
            self.remove_ads_and_unwanted_elements(content_area)
            content_html = str(content_area)
            return self.clean_html_content(content_html)
            
        except Exception as e:
            print(f"Error extracting content from tuoitre.vn: {e}")
            return None

class TechCrunchExtractor(BaseSiteExtractor):
    """Content extractor for techcrunch.com."""
    def can_handle(self, url: str) -> bool:
        return 'techcrunch.com' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['.entry-content']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)

class BBCExtractor(BaseSiteExtractor):
    """Content extractor for bbc.com."""
    def can_handle(self, url: str) -> bool:
        return 'bbc.com' in url.lower() or 'bbc.co.uk' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['article']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)

class CNBCExtractor(BaseSiteExtractor):
    """Content extractor for cnbc.com."""
    def can_handle(self, url: str) -> bool:
        return 'cnbc.com' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        primary_selectors = ['.ArticleBody-articleBody']
        return self.extract_with_fallbacks(soup, base_url, primary_selectors)

class TheVergeExtractor(BaseSiteExtractor):
    """Content extractor for theverge.com."""
    def can_handle(self, url: str) -> bool:
        return 'theverge.com' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        try:
            main_content = soup.find('main', id='content')  # type: ignore
            if not main_content:
                return None

            # Find article inside main
            content_area = main_content.find('article')  # type: ignore
            if not content_area:
                return None 
            
            self.remove_ads_and_unwanted_elements(content_area)
            content_html = str(content_area)
            return self.clean_html_content(content_html)
        except Exception as e:
            print(f"Error extracting content from theverge.com: {e}")
            return None

class YahooFinanceExtractor(BaseSiteExtractor):
    """Content extractor for finance.yahoo.com."""
    def can_handle(self, url: str) -> bool:
        return 'finance.yahoo.com' in url.lower()
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        try:
            # child of div.grid-cols-article-mobile with class="col-body"
            grid_container = soup.find('div', class_='grid-cols-article-mobile')  # type: ignore
            if not grid_container:
                return None
            content_area = grid_container.find('div', class_='col-body')  # type: ignore
            if not content_area:
                return None
            
            self.remove_ads_and_unwanted_elements(content_area)
            content_html = str(content_area)
            return self.clean_html_content(content_html)
        except Exception as e:
            print(f"Error extracting content from finance.yahoo.com: {e}")
            return None

# Domain to extractor mapping for O(1) lookup
SITE_EXTRACTORS_MAP = {
    'kenh14.vn': Kenh14Extractor(),
    'vnexpress.net': VnExpressExtractor(),
    'tuoitre.vn': TuoiTreExtractor(),
    'techcrunch.com': TechCrunchExtractor(),
    'bbc.com': BBCExtractor(),
    'cnbc.com': CNBCExtractor(),
    'theverge.com': TheVergeExtractor(),
    'finance.yahoo.com': YahooFinanceExtractor(),
}

# Alternative domains that should use the same extractor
DOMAIN_ALIASES = {
    'www.kenh14.vn': 'kenh14.vn',
    'www.vnexpress.net': 'vnexpress.net',
    'www.tuoitre.vn': 'tuoitre.vn',
    'www.techcrunch.com': 'techcrunch.com',
    'www.bbc.com': 'bbc.com',
    'www.cnbc.com': 'cnbc.com',
    'www.theverge.com': 'theverge.com',
    'tech.kenh14.vn': 'kenh14.vn',
    'vnexpress.net': 'vnexpress.net',
    'finance.yahoo.com': 'finance.yahoo.com',
}

class SiteExtractorManager:
    """Manager for site-specific content extractors."""
    
    def __init__(self):
        self.extractors: List[BaseSiteExtractor] = [
            Kenh14Extractor(),
            VnExpressExtractor(),
            TuoiTreExtractor(),
            TechCrunchExtractor(),
            BBCExtractor(),
            CNBCExtractor(),
            TheVergeExtractor(),
            YahooFinanceExtractor(),
        ]

    def get_domain(self, url: str) -> str:
        """Get the domain of the given URL."""
        return urlparse(url).netloc.replace('www.', '')
    
    def get_extractor(self, url: str) -> Optional[BaseSiteExtractor]:
        """Get the appropriate extractor for the given URL with O(1) lookup."""
        domain = self.get_domain(url)
        
        # Direct lookup in the main map
        if domain in SITE_EXTRACTORS_MAP:
            return SITE_EXTRACTORS_MAP[domain]
        
        # Check domain aliases for subdomains or variations
        if domain in DOMAIN_ALIASES:
            canonical_domain = DOMAIN_ALIASES[domain]
            if canonical_domain in SITE_EXTRACTORS_MAP:
                return SITE_EXTRACTORS_MAP[canonical_domain]
        
        return None
    
    def add_extractor(self, extractor: BaseSiteExtractor):
        """Add a new site extractor."""
        self.extractors.append(extractor)
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract content using the appropriate site-specific extractor."""
        extractor = self.get_extractor(url)
        if extractor:
            return extractor.extract_content(soup, url)
        return None
    
    def add_extractor_for_domain(self, domain: str, extractor: BaseSiteExtractor) -> None:
        """Add a new extractor for a specific domain."""
        SITE_EXTRACTORS_MAP[domain] = extractor
    
    def get_supported_domains(self) -> List[str]:
        """Get list of all supported domains."""
        return list(SITE_EXTRACTORS_MAP.keys())
    
    def get_extractor_stats(self) -> Dict[str, Any]:
        """Get statistics about extractors."""
        return {
            'total_extractors': len(SITE_EXTRACTORS_MAP),
            'total_aliases': len(DOMAIN_ALIASES),
            'supported_domains': list(SITE_EXTRACTORS_MAP.keys()),
            'domain_aliases': DOMAIN_ALIASES
        }


# Global instance for easy access
site_extractor_manager = SiteExtractorManager() 