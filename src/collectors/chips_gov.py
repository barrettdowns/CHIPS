"""
CHIPS.gov funding announcements scraper.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

from .base_collector import BaseCollector


class CHIPSGovCollector(BaseCollector):
    """Collector for CHIPS.gov funding announcements."""
    
    def get_source_name(self) -> str:
        """Get source name."""
        return "chips_gov"
    
    def collect(self, max_pages: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Collect funding announcements from CHIPS.gov."""
        source_config = self._get_source_config(self.get_source_name())
        base_url = source_config.get('base_url', 'https://www.chips.gov')
        endpoints = source_config.get('endpoints', {})
        selectors = source_config.get('selectors', {})
        
        announcements = []
        
        # Collect from news and updates
        news_url = urljoin(base_url, endpoints.get('announcements', '/news-and-updates'))
        news_announcements = self._collect_from_news_page(news_url, selectors, max_pages)
        announcements.extend(news_announcements)
        
        # Collect from funding opportunities
        funding_url = urljoin(base_url, endpoints.get('awards', '/funding-opportunities'))
        funding_announcements = self._collect_from_funding_page(funding_url, selectors, max_pages)
        announcements.extend(funding_announcements)
        
        # Process and clean announcements
        processed_announcements = self._process_announcements(announcements)
        
        # Save raw data
        if processed_announcements:
            filename = f"chips_gov_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self._save_raw_data(processed_announcements, filename)
        
        return processed_announcements
    
    def _collect_from_news_page(self, url: str, selectors: Dict[str, str], max_pages: int) -> List[Dict[str, Any]]:
        """Collect announcements from news page."""
        announcements = []
        
        for page in range(1, max_pages + 1):
            page_url = f"{url}?page={page}" if page > 1 else url
            
            response = self._make_request(page_url, self._get_source_config(self.get_source_name()))
            if not response:
                logger.warning(f"Failed to fetch page {page} from {page_url}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find announcement containers - CHIPS.gov uses article.nist-teaser
            announcement_containers = soup.find_all('article', class_='nist-teaser')
            
            if not announcement_containers:
                # Try alternative selectors
                announcement_containers = soup.find_all(['article', 'div'], class_=re.compile(r'news|announcement|post'))
            
            if not announcement_containers:
                logger.warning(f"No announcement containers found on page {page}")
                break
            
            for container in announcement_containers:
                announcement = self._extract_announcement_from_container(container, selectors, url)
                if announcement:
                    announcements.append(announcement)
            
            logger.info(f"Collected {len(announcement_containers)} announcements from page {page}")
        
        return announcements
    
    def _collect_from_funding_page(self, url: str, selectors: Dict[str, str], max_pages: int) -> List[Dict[str, Any]]:
        """Collect announcements from funding opportunities page."""
        announcements = []
        
        for page in range(1, max_pages + 1):
            page_url = f"{url}?page={page}" if page > 1 else url
            
            response = self._make_request(page_url, self._get_source_config(self.get_source_name()))
            if not response:
                logger.warning(f"Failed to fetch funding page {page} from {page_url}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find funding opportunity containers
            funding_containers = soup.find_all(['article', 'div'], class_=re.compile(r'funding|opportunity|award'))
            
            if not funding_containers:
                # Try alternative selectors
                funding_containers = soup.find_all('div', class_=re.compile(r'item|entry|card'))
            
            if not funding_containers:
                logger.warning(f"No funding containers found on page {page}")
                break
            
            for container in funding_containers:
                announcement = self._extract_funding_from_container(container, selectors, url)
                if announcement:
                    announcements.append(announcement)
            
            logger.info(f"Collected {len(funding_containers)} funding opportunities from page {page}")
        
        return announcements
    
    def _extract_announcement_from_container(self, container, selectors: Dict[str, str], base_url: str) -> Optional[Dict[str, Any]]:
        """Extract announcement data from container element."""
        try:
            announcement = {
                'source': 'chips_gov_news',
                'url': base_url,
                'collected_at': datetime.now().isoformat(),
                'raw_html': str(container)
            }
            
            # Extract title - CHIPS.gov uses h3 in nist-teaser
            title_elem = container.find('h3')
            if not title_elem:
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|headline'))
            if not title_elem:
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
            announcement['title'] = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract date
            date_elem = container.find(class_=re.compile(r'date|time|published'))
            if not date_elem:
                date_elem = container.find('time')
            announcement['date'] = date_elem.get_text(strip=True) if date_elem else ""
            
            # Extract content
            content_elem = container.find(class_=re.compile(r'content|body|text|summary'))
            if not content_elem:
                content_elem = container.find(['p', 'div'])
            announcement['content'] = content_elem.get_text(strip=True) if content_elem else ""
            
            # Extract link
            link_elem = container.find('a', href=True)
            if link_elem:
                announcement['link'] = urljoin(base_url, link_elem['href'])
            
            # Extract funding amount if mentioned
            funding_amount = self._extract_funding_amount(announcement['content'])
            if funding_amount:
                announcement['funding_amount'] = funding_amount
            
            # Extract entity names
            entities = self._extract_entity_names(announcement['content'])
            if entities:
                announcement['entities'] = entities
            
            return announcement if announcement['title'] else None
            
        except Exception as e:
            logger.error(f"Error extracting announcement: {e}")
            return None
    
    def _extract_funding_from_container(self, container, selectors: Dict[str, str], base_url: str) -> Optional[Dict[str, Any]]:
        """Extract funding opportunity data from container element."""
        try:
            announcement = {
                'source': 'chips_gov_funding',
                'url': base_url,
                'collected_at': datetime.now().isoformat(),
                'raw_html': str(container)
            }
            
            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|headline'))
            if not title_elem:
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
            announcement['title'] = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract date
            date_elem = container.find(class_=re.compile(r'date|time|published'))
            if not date_elem:
                date_elem = container.find('time')
            announcement['date'] = date_elem.get_text(strip=True) if date_elem else ""
            
            # Extract content
            content_elem = container.find(class_=re.compile(r'content|body|text|summary'))
            if not content_elem:
                content_elem = container.find(['p', 'div'])
            announcement['content'] = content_elem.get_text(strip=True) if content_elem else ""
            
            # Extract link
            link_elem = container.find('a', href=True)
            if link_elem:
                announcement['link'] = urljoin(base_url, link_elem['href'])
            
            # Extract funding amount
            funding_amount = self._extract_funding_amount(announcement['content'])
            if funding_amount:
                announcement['funding_amount'] = funding_amount
            
            # Extract entity names
            entities = self._extract_entity_names(announcement['content'])
            if entities:
                announcement['entities'] = entities
            
            return announcement if announcement['title'] else None
            
        except Exception as e:
            logger.error(f"Error extracting funding opportunity: {e}")
            return None
    
    def _extract_funding_amount(self, text: str) -> Optional[float]:
        """Extract funding amount from text."""
        if not text:
            return None
        
        # Common funding amount patterns
        patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|M|B)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:million|billion|M|B))',
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    amount_str = matches[0].replace(',', '')
                    amount = float(amount_str)
                    
                    # Convert to millions if needed
                    if 'billion' in text.lower() or 'B' in text.upper():
                        amount *= 1000
                    elif 'million' in text.lower() or 'M' in text.upper():
                        pass  # Already in millions
                    else:
                        # Assume millions if no unit specified and amount is large
                        if amount > 1000:
                            amount /= 1000
                    
                    return amount
                except ValueError:
                    continue
        
        return None
    
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
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Technology)',  # Added for companies like "Micron Technology"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Semiconductor)',  # Added for semiconductor companies
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Systems)',  # Added for systems companies
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Solutions)',  # Added for solutions companies
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        # Remove duplicates and clean up
        entities = list(set(entities))
        entities = [entity.strip() for entity in entities if len(entity.strip()) > 3]
        
        return entities
    
    def _process_announcements(self, announcements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean announcements."""
        processed = []
        
        for announcement in announcements:
            # Clean and validate data
            if not announcement.get('title'):
                continue
            
            # Parse date
            parsed_date = self._parse_date(announcement.get('date', ''))
            announcement['parsed_date'] = parsed_date.isoformat() if parsed_date else None
            
            # Extract capabilities from content
            capabilities = self._extract_capabilities(announcement.get('content', ''))
            if capabilities:
                announcement['capabilities'] = capabilities
            
            # Calculate confidence score
            confidence = self._calculate_confidence(announcement)
            announcement['confidence_score'] = confidence
            
            processed.append(announcement)
        
        return processed
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %Y',
            '%b %Y',
            '%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capability keywords from content."""
        if not content:
            return []
        
        capabilities = []
        content_lower = content.lower()
        
        # Capability keywords (from config)
        capability_keywords = {
            'advanced_packaging': ['3d packaging', 'chiplet', 'hbm', 'advanced packaging', 'heterogeneous integration'],
            'rfic_design': ['rfic', 'rf integrated circuit', 'millimeter wave', '5g', '6g', 'wireless'],
            'advanced_logic': ['euv', 'gaa', 'finfet', 'sub-7nm', 'advanced cmos', 'logic design'],
            'memory': ['dram', 'nand', 'flash memory', 'emerging memory', 'mram', 'reram'],
            'analog_power': ['power management', 'pmic', 'voltage regulator', 'sensor', 'analog design'],
            'materials_equipment': ['semiconductor equipment', 'lithography', 'deposition', 'wafer processing']
        }
        
        for capability, keywords in capability_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    capabilities.append(capability)
                    break
        
        return capabilities
    
    def _calculate_confidence(self, announcement: Dict[str, Any]) -> float:
        """Calculate confidence score for announcement."""
        confidence = 0.0
        
        # Base confidence for CHIPS.gov source
        confidence += 0.8
        
        # Boost for having funding amount
        if announcement.get('funding_amount'):
            confidence += 0.1
        
        # Boost for having entities
        if announcement.get('entities'):
            confidence += 0.05
        
        # Boost for having capabilities
        if announcement.get('capabilities'):
            confidence += 0.05
        
        # Boost for having parsed date
        if announcement.get('parsed_date'):
            confidence += 0.05
        
        return min(confidence, 1.0)
