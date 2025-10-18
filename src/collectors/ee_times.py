"""EE Times collector for CHIPS Act intelligence."""

import re
from typing import List, Dict, Any, Optional
from loguru import logger
from .base_collector import BaseCollector


class EETimesCollector(BaseCollector):
    """Collector for EE Times articles."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.eetimes.com"
        self.search_url = "https://www.eetimes.com/search"
        
    def get_source_name(self) -> str:
        """Get the source name."""
        return "ee_times"
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect CHIPS Act related articles from EE Times."""
        logger.info("Starting EE Times collection...")
        
        collected_data = []
        
        # Search for CHIPS Act related articles
        chips_keywords = [
            "CHIPS Act",
            "semiconductor manufacturing",
            "chip manufacturing"
        ]
        
        for keyword in chips_keywords:
            try:
                logger.info(f"Searching for: {keyword}")
                articles = self._search_articles(keyword)
                collected_data.extend(articles)
            except Exception as e:
                logger.error(f"Error searching for {keyword}: {e}")
        
        logger.info(f"EE Times collection completed. Found {len(collected_data)} articles.")
        return collected_data
    
    def _search_articles(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for articles containing the keyword."""
        articles = []
        
        try:
            # Search parameters
            search_params = {
                'q': keyword,
                'type': 'article'
            }
            
            # Make request to search page
            response = self._make_request(self.search_url, self._get_source_config(self.get_source_name()), params=search_params)
            if not response or response.status_code != 200:
                logger.warning(f"Failed to search EE Times for {keyword}")
                return articles
            
            # Parse search results
            articles = self._parse_search_results(response.text, keyword)
            
        except Exception as e:
            logger.error(f"Error searching EE Times: {e}")
        
        return articles
    
    def _parse_search_results(self, html_content: str, keyword: str) -> List[Dict[str, Any]]:
        """Parse search results from HTML."""
        articles = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for article links and titles
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Check if this looks like an article
                if self._is_article_link(href, title, keyword):
                    article_data = {
                        'title': title,
                        'url': self._make_absolute_url(href),
                        'source': 'EE Times',
                        'keyword': keyword,
                        'content': '',  # Would need to fetch full article
                        'entities': self._extract_entity_names(title)
                    }
                    articles.append(article_data)
            
        except Exception as e:
            logger.error(f"Error parsing EE Times results: {e}")
        
        return articles
    
    def _is_article_link(self, href: str, title: str, keyword: str) -> bool:
        """Check if a link appears to be a relevant article."""
        if not href or not title:
            return False
        
        # Skip non-article links
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/',
            '/search', '/contact', '/about', '/privacy'
        ]
        
        for pattern in skip_patterns:
            if pattern in href.lower():
                return False
        
        # Check if title contains keyword or related terms
        title_lower = title.lower()
        keyword_lower = keyword.lower()
        
        if keyword_lower in title_lower:
            return True
        
        # Check for semiconductor-related terms
        semiconductor_terms = [
            'chip', 'semiconductor', 'manufacturing', 'foundry',
            'fab', 'wafer', 'packaging', 'design'
        ]
        
        return any(term in title_lower for term in semiconductor_terms)
    
    def _make_absolute_url(self, href: str) -> str:
        """Convert relative URL to absolute URL."""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"{self.base_url}{href}"
        else:
            return f"{self.base_url}/{href}"
    
    def _extract_entity_names(self, text: str) -> List[str]:
        """Extract potential entity names from text."""
        if not text:
            return []
        
        entities = []
        
        # Common entity name patterns
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|Limited|Company|Co\.?))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+University)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Institute)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Laboratory)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Consortium)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Technology)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Semiconductor)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Systems)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Solutions)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        # Remove duplicates and clean up
        entities = list(set(entities))
        entities = [entity.strip() for entity in entities if len(entity.strip()) > 3]
        
        return entities
