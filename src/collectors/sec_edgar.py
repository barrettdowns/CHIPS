"""
SEC EDGAR collector for CHIPS Act related filings.
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from loguru import logger

from .base_collector import BaseCollector
from ..database.models import Entity, EntityType, Funding, Capability, CapabilityType


class SECEdgarCollector(BaseCollector):
    """Collector for SEC EDGAR filings related to CHIPS Act."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.sec.gov/edgar/search/"
        self.api_url = "https://data.sec.gov/api/xbrl/companyfacts/"
    
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        return "SEC EDGAR"
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect CHIPS Act related filings from SEC EDGAR."""
        logger.info("Starting SEC EDGAR collection...")
        
        collected_data = []
        
        # Search for CHIPS Act related filings - REDUCED for better success
        chips_keywords = [
            "CHIPS Act",
            "semiconductor manufacturing"
        ]
        
        for keyword in chips_keywords:
            try:
                logger.info(f"Searching for: {keyword}")
                filings = self._search_filings(keyword)
                
                for filing in filings:
                    # Extract entity information
                    entity_data = self._extract_entity_from_filing(filing)
                    if entity_data:
                        collected_data.append(entity_data)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching for '{keyword}': {e}")
                continue
        
        logger.info(f"SEC EDGAR collection completed. Found {len(collected_data)} entities.")
        return collected_data
    
    def _search_filings(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for filings containing the keyword."""
        filings = []
        
        # Search in fewer forms - REDUCED for better success
        forms = ["10-K", "8-K"]
        
        for form_type in forms:
            try:
                # Search parameters
                search_params = {
                    'q': keyword,
                    'formType': form_type,
                    'dateRange': 'all',
                    'startdt': '2022-01-01',  # CHIPS Act was passed in 2022
                    'enddt': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Make search request
                response = self._make_request(
                    self.base_url,
                    self._get_source_config(self.get_source_name()),
                    params=search_params
                )
                
                if response and response.status_code == 200:
                    # Parse search results
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = self._parse_search_results(soup)
                    filings.extend(results)
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error searching form {form_type}: {e}")
                continue
        
        return filings
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse search results from SEC EDGAR."""
        results = []
        
        # Look for filing links and metadata
        filing_links = soup.find_all('a', href=re.compile(r'/Archives/edgar/data/'))
        
        for link in filing_links:
            try:
                filing_url = link.get('href')
                if filing_url:
                    filing_data = self._get_filing_details(filing_url)
                    if filing_data:
                        results.append(filing_data)
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error parsing filing link: {e}")
                continue
        
        return results
    
    def _get_filing_details(self, filing_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific filing."""
        try:
            # Construct full URL
            if filing_url.startswith('/'):
                filing_url = f"https://www.sec.gov{filing_url}"
            
            response = self._make_request(filing_url, self._get_source_config(self.get_source_name()))
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract filing metadata
            filing_data = {
                'url': filing_url,
                'company_name': self._extract_company_name(soup),
                'filing_date': self._extract_filing_date(soup),
                'form_type': self._extract_form_type(soup),
                'content': self._extract_filing_content(soup),
                'cik': self._extract_cik(soup)
            }
            
            return filing_data
            
        except Exception as e:
            logger.error(f"Error getting filing details from {filing_url}: {e}")
            return None
    
    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from filing."""
        # Look for company name in various locations
        company_selectors = [
            'span.companyName',
            '.companyName',
            'h1',
            '.filerName'
        ]
        
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and len(name) > 2:
                    return name
        
        return None
    
    def _extract_filing_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract filing date from filing."""
        # Look for filing date
        date_selectors = [
            '.filingDate',
            '.filing-date',
            'span[title*="Filing Date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                if date_text:
                    return date_text
        
        return None
    
    def _extract_form_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract form type from filing."""
        # Look for form type
        form_selectors = [
            '.formType',
            '.form-type',
            'span[title*="Form Type"]'
        ]
        
        for selector in form_selectors:
            element = soup.select_one(selector)
            if element:
                form_type = element.get_text(strip=True)
                if form_type:
                    return form_type
        
        return None
    
    def _extract_cik(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract CIK (Central Index Key) from filing."""
        # Look for CIK in links or text
        cik_pattern = r'CIK[:\s]*(\d{10})'
        
        # Search in text content
        text_content = soup.get_text()
        cik_match = re.search(cik_pattern, text_content, re.IGNORECASE)
        if cik_match:
            return cik_match.group(1)
        
        # Search in links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if 'cik=' in href:
                cik_match = re.search(r'cik=(\d{10})', href)
                if cik_match:
                    return cik_match.group(1)
        
        return None
    
    def _extract_filing_content(self, soup: BeautifulSoup) -> str:
        """Extract relevant content from filing."""
        # Look for main content areas
        content_selectors = [
            '.filingContent',
            '.document',
            'pre',
            '.text'
        ]
        
        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 100:  # Only include substantial content
                    content += text + "\n"
        
        return content[:5000]  # Limit content length
    
    def _extract_entity_from_filing(self, filing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract entity information from filing data."""
        if not filing.get('company_name'):
            return None
        
        # Determine entity type based on company name patterns
        entity_type = EntityType.COMPANY
        
        # Look for university patterns
        if any(keyword in filing['company_name'].lower() for keyword in ['university', 'college', 'institute']):
            entity_type = EntityType.UNIVERSITY
        
        # Look for government patterns
        if any(keyword in filing['company_name'].lower() for keyword in ['government', 'federal', 'state', 'department']):
            entity_type = EntityType.GOVERNMENT
        
        # Extract funding information from content
        funding_info = self._extract_funding_from_content(filing.get('content', ''))
        
        # Extract capabilities from content
        capabilities = self._extract_capabilities_from_content(filing.get('content', ''))
        
        entity_data = {
            'name': filing['company_name'],
            'legal_name': filing['company_name'],
            'entity_type': entity_type.value,
            'confidence_score': 0.8,  # High confidence for SEC filings
            'source_url': filing['url'],
            'source_data': {
                'filing_date': filing.get('filing_date'),
                'form_type': filing.get('form_type'),
                'cik': filing.get('cik'),
                'content_preview': filing.get('content', '')[:500]
            },
            'funding': funding_info,
            'capabilities': capabilities
        }
        
        return entity_data
    
    def _extract_funding_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract funding information from filing content."""
        funding_info = []
        
        if not content:
            return funding_info
        
        # Look for funding amounts in various formats
        funding_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|M|B)?',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|M|B)\s*(?:dollars?)?',
            r'funding[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'grant[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'investment[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
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
                        'source': 'SEC Filing',
                        'description': f"Funding mentioned in SEC filing: {match.group(0)}"
                    })
                    
                except ValueError:
                    continue
        
        return funding_info
    
    def _extract_capabilities_from_content(self, content: str) -> List[str]:
        """Extract capabilities from filing content."""
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
