"""
News aggregator collector for CHIPS Act related news.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from loguru import logger

from .base_collector import BaseCollector
from ..database.models import Entity, EntityType, Funding, Capability, CapabilityType


class NewsAggregatorCollector(BaseCollector):
    """Collector for CHIPS Act related news from various sources."""
    
    def __init__(self):
        super().__init__()
        self.news_sources = [
            {
                'name': 'Reuters',
                'url': 'https://www.reuters.com',
                'search_path': '/search/news',
                'article_selector': '.article-body'
            },
            {
                'name': 'Bloomberg',
                'url': 'https://www.bloomberg.com',
                'search_path': '/search',
                'article_selector': '.article-body'
            },
            {
                'name': 'TechCrunch',
                'url': 'https://techcrunch.com',
                'search_path': '/search',
                'article_selector': '.article-content'
            },
            {
                'name': 'Ars Technica',
                'url': 'https://arstechnica.com',
                'search_path': '/search',
                'article_selector': '.article-content'
            },
            {
                'name': 'IEEE Spectrum',
                'url': 'https://spectrum.ieee.org',
                'search_path': '/search',
                'article_selector': '.article-content'
            },
            {
                'name': 'Semiconductor Engineering',
                'url': 'https://semiengineering.com',
                'search_path': '/search',
                'article_selector': '.article-content'
            },
            {
                'name': 'EE Times',
                'url': 'https://www.eetimes.com',
                'search_path': '/search',
                'article_selector': '.article-content'
            },
            {
                'name': 'Electronics Weekly',
                'url': 'https://www.electronicsweekly.com',
                'search_path': '/search',
                'article_selector': '.article-content'
            }
        ]
        
        self.chips_keywords = [
            'CHIPS Act',
            'CHIPS and Science Act',
            'semiconductor manufacturing',
            'chip manufacturing',
            'semiconductor facility',
            'semiconductor investment',
            'semiconductor grant',
            'semiconductor funding',
            'semiconductor research',
            'semiconductor workforce',
            'semiconductor innovation',
            'semiconductor partnership',
            'semiconductor collaboration'
        ]
    
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        return "News Aggregators"
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect CHIPS Act related news from various sources."""
        logger.info("Starting news aggregator collection...")
        
        collected_data = []
        
        for source in self.news_sources:
            try:
                logger.info(f"Collecting from {source['name']}...")
                
                # Search for CHIPS Act related content
                articles = self._search_news_source(source)
                
                for article in articles:
                    entity_data = self._extract_entity_from_article(article, source)
                    if entity_data:
                        collected_data.append(entity_data)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting from {source['name']}: {e}")
                continue
        
        logger.info(f"News aggregator collection completed. Found {len(collected_data)} entities.")
        return collected_data
    
    def _search_news_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for CHIPS Act related news from a source."""
        articles = []
        
        for keyword in self.chips_keywords:
            try:
                # Construct search URL
                search_url = f"{source['url']}{source['search_path']}"
                search_params = {
                    'q': keyword,
                    'date': '2022-01-01'  # CHIPS Act was passed in 2022
                }
                
                response = self._make_request(
                    search_url,
                    self._get_source_config(self.get_source_name()),
                    params=search_params
                )
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    found_articles = self._parse_article_links(soup, source)
                    articles.extend(found_articles)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error searching {source['name']} for '{keyword}': {e}")
                continue
        
        return articles
    
    def _parse_article_links(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse article links from search results."""
        articles = []
        
        # Look for article links
        article_links = soup.find_all('a', href=True)
        
        for link in article_links:
            try:
                href = link.get('href')
                if href and self._is_article_link(href, source):
                    # Get full URL
                    if href.startswith('/'):
                        article_url = f"{source['url']}{href}"
                    elif href.startswith('http'):
                        article_url = href
                    else:
                        continue
                    
                    # Get article content
                    article_data = self._get_article_content(article_url, source)
                    if article_data:
                        articles.append(article_data)
                    
                    time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error parsing article link: {e}")
                continue
        
        return articles
    
    def _is_article_link(self, href: str, source: Dict[str, Any]) -> bool:
        """Check if a link is likely an article."""
        # Skip certain patterns
        skip_patterns = [
            '/search',
            '/category',
            '/tag',
            '/author',
            '/page',
            '#',
            'mailto:',
            'tel:',
            '.pdf',
            '.doc',
            '.jpg',
            '.png',
            '.gif'
        ]
        
        for pattern in skip_patterns:
            if pattern in href.lower():
                return False
        
        # Must contain article-like patterns
        article_patterns = [
            '/news/',
            '/article/',
            '/press/',
            '/announcement/',
            '/story/',
            '/2022/',
            '/2023/',
            '/2024/'
        ]
        
        for pattern in article_patterns:
            if pattern in href.lower():
                return True
        
        return False
    
    def _get_article_content(self, article_url: str, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get content from an article URL."""
        try:
            response = self._make_request(article_url, self._get_source_config(self.get_source_name()))
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            title = self._extract_title(soup)
            content = self._extract_content(soup, source)
            date = self._extract_date(soup)
            
            if not title or not content:
                return None
            
            article_data = {
                'url': article_url,
                'title': title,
                'content': content,
                'date': date,
                'source': source['name'],
                'source_url': source['url']
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error getting article content from {article_url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title."""
        title_selectors = [
            'h1',
            '.title',
            '.article-title',
            '.headline',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:
                    return title
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup, source: Dict[str, Any]) -> str:
        """Extract article content."""
        content = ""
        
        # Try source-specific selectors first
        if source.get('article_selector'):
            elements = soup.select(source['article_selector'])
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 100:
                    content += text + "\n"
        
        # Fallback to common selectors
        if not content:
            content_selectors = [
                '.article-content',
                '.content',
                '.post-content',
                '.entry-content',
                'article',
                '.main-content',
                'main'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 100:
                        content += text + "\n"
                        break
                if content:
                    break
        
        return content[:5000]  # Limit content length
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article date."""
        date_selectors = [
            '.date',
            '.publish-date',
            '.article-date',
            '.post-date',
            'time',
            '.timestamp'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                if date_text:
                    return date_text
        
        return None
    
    def _extract_entity_from_article(self, article: Dict[str, Any], source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract entity information from article."""
        if not article.get('title') or not article.get('content'):
            return None
        
        # Extract company names from title and content
        companies = self._extract_companies_from_content(article['title'] + " " + article['content'])
        
        entities = []
        
        # Add company entities
        for company in companies:
            company_entity = {
                'name': company,
                'legal_name': company,
                'entity_type': EntityType.COMPANY.value,
                'confidence_score': 0.6,  # Medium confidence for news mentions
                'source_url': article['url'],
                'source_data': {
                    'article_title': article['title'],
                    'article_date': article['date'],
                    'news_source': source['name'],
                    'source_url': source['url']
                },
                'funding': self._extract_funding_from_content(article['content']),
                'capabilities': self._extract_capabilities_from_content(article['content'])
            }
            entities.append(company_entity)
        
        return entities
    
    def _extract_companies_from_content(self, content: str) -> List[str]:
        """Extract company names from content."""
        companies = []
        
        if not content:
            return companies
        
        # Common company name patterns
        company_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Corporation|Corp|Inc|LLC|Ltd|Company|Co\.)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Technologies|Systems|Semiconductor|Chip|Micro)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Intel|AMD|NVIDIA|Qualcomm|Broadcom|TSMC)',
            r'\b(Intel|AMD|NVIDIA|Qualcomm|Broadcom|TSMC|Samsung|Micron|Applied Materials|Lam Research)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Semiconductor|Chip|Micro|Tech|Systems|Solutions)\b'
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                company_name = match.group(1) if match.groups() else match.group(0)
                if company_name and len(company_name) > 2:
                    companies.append(company_name.strip())
        
        return list(set(companies))  # Remove duplicates
    
    def _extract_funding_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract funding information from content."""
        funding_info = []
        
        if not content:
            return funding_info
        
        # Look for funding amounts
        funding_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|M|B)?',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|M|B)\s*(?:dollars?)?',
            r'funding[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'grant[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'investment[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'award[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in funding_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    
                    # Convert to millions if needed
                    if 'billion' in match.group(0).lower() or 'B' in match.group(0):
                        amount *= 1000
                    elif 'million' not in match.group(0).lower() and 'M' not in match.group(0) and amount > 1000:
                        amount /= 1000  # Assume it's in thousands
                    
                    funding_info.append({
                        'amount': amount,
                        'currency': 'USD',
                        'announcement_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'News Article',
                        'description': f"Funding mentioned in news: {match.group(0)}"
                    })
                    
                except ValueError:
                    continue
        
        return funding_info
    
    def _extract_capabilities_from_content(self, content: str) -> List[str]:
        """Extract capabilities from content."""
        capabilities = []
        
        if not content:
            return capabilities
        
        # Capability keywords mapping
        capability_keywords = {
            CapabilityType.THREE_D_PACKAGING: [
                '3D packaging', 'three-dimensional packaging', 'advanced packaging',
                'chiplet', 'heterogeneous integration', 'system-in-package'
            ],
            CapabilityType.RFIC_DESIGN: [
                'RFIC', 'radio frequency', 'RF design', 'wireless', '5G', '6G',
                'mmWave', 'millimeter wave', 'antenna', 'RF frontend'
            ],
            CapabilityType.ADVANCED_LOGIC: [
                'advanced logic', 'CPU', 'GPU', 'AI chip', 'processor',
                'EUV', 'extreme ultraviolet', '7nm', '5nm', '3nm', 'GAA',
                'gate-all-around', 'FinFET'
            ],
            CapabilityType.MEMORY: [
                'memory', 'DRAM', 'SRAM', 'NAND', 'flash', 'storage',
                'HBM', 'high bandwidth memory', 'DDR', 'GDDR'
            ],
            CapabilityType.ANALOG_POWER: [
                'analog', 'power management', 'PMIC', 'power IC',
                'voltage regulator', 'DC-DC', 'AC-DC', 'power conversion'
            ],
            CapabilityType.MATERIALS_EQUIPMENT: [
                'materials', 'equipment', 'semiconductor equipment',
                'wafer', 'substrate', 'lithography', 'etching', 'deposition'
            ]
        }
        
        content_lower = content.lower()
        
        for capability_type, keywords in capability_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    capabilities.append(capability_type.value)
                    break  # Only add each capability once
        
        return capabilities
