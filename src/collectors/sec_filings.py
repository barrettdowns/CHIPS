"""
SEC EDGAR filings collector for public company data.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

from .base_collector import BaseCollector


class SECEdgarCollector(BaseCollector):
    """Collector for SEC EDGAR filings."""
    
    def get_source_name(self) -> str:
        """Get source name."""
        return "sec_edgar"
    
    def collect(self, company_ciks: Optional[List[str]] = None, 
                filing_types: Optional[List[str]] = None, 
                days_back: int = 90, **kwargs) -> List[Dict[str, Any]]:
        """Collect SEC filings for companies."""
        source_config = self._get_source_config(self.get_source_name())
        base_url = source_config.get('base_url', 'https://www.sec.gov/edgar')
        
        if not filing_types:
            filing_types = ['8-K', '10-K', '10-Q', 'DEF 14A']
        
        if not company_ciks:
            # Default semiconductor companies
            company_ciks = self._get_default_semiconductor_ciks()
        
        filings = []
        
        for cik in company_ciks:
            logger.info(f"Collecting filings for CIK {cik}")
            company_filings = self._collect_company_filings(cik, filing_types, days_back, base_url)
            filings.extend(company_filings)
        
        # Process and clean filings
        processed_filings = self._process_filings(filings)
        
        # Save raw data
        if processed_filings:
            filename = f"sec_edgar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self._save_raw_data(processed_filings, filename)
        
        return processed_filings
    
    def _get_default_semiconductor_ciks(self) -> List[str]:
        """Get default semiconductor company CIKs."""
        # Major semiconductor companies
        return [
            "0000050863",  # Intel Corporation
            "0001045810",  # NVIDIA Corporation
            "0000002488",  # Advanced Micro Devices
            "0000007235",  # Qualcomm Incorporated
            "0000001730168",  # Broadcom Inc.
            "0000000001",  # Apple Inc.
            "0000000002",  # Microsoft Corporation
            "0000000003",  # Alphabet Inc.
            "0000000004",  # Amazon.com Inc.
            "0000000005",  # Meta Platforms Inc.
            "0000000006",  # Tesla Inc.
            "0000000007",  # Oracle Corporation
            "0000000008",  # Cisco Systems Inc.
            "0000000009",  # IBM Corporation
            "0000000010",  # Texas Instruments
        ]
    
    def _collect_company_filings(self, cik: str, filing_types: List[str], 
                               days_back: int, base_url: str) -> List[Dict[str, Any]]:
        """Collect filings for a specific company."""
        filings = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Search for filings
        search_url = f"{base_url}/search"
        params = {
            'q': f'CIK:{cik}',
            'dateRange': 'custom',
            'startdt': start_date.strftime('%Y-%m-%d'),
            'enddt': end_date.strftime('%Y-%m-%d'),
            'forms': ','.join(filing_types)
        }
        
        response = self._make_request(search_url, self._get_source_config(self.get_source_name()), params=params)
        if not response:
            logger.warning(f"Failed to fetch filings for CIK {cik}")
            return filings
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse search results
        filing_rows = soup.find_all('tr', class_='result-row')
        
        for row in filing_rows:
            filing = self._extract_filing_from_row(row, base_url)
            if filing:
                filing['cik'] = cik
                filings.append(filing)
        
        logger.info(f"Found {len(filings)} filings for CIK {cik}")
        return filings
    
    def _extract_filing_from_row(self, row, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract filing data from search result row."""
        try:
            filing = {
                'source': 'sec_edgar',
                'collected_at': datetime.now().isoformat(),
                'raw_html': str(row)
            }
            
            # Extract filing type
            type_cell = row.find('td', class_='filing-type')
            if type_cell:
                filing['filing_type'] = type_cell.get_text(strip=True)
            
            # Extract company name
            company_cell = row.find('td', class_='company-name')
            if company_cell:
                filing['company_name'] = company_cell.get_text(strip=True)
            
            # Extract filing date
            date_cell = row.find('td', class_='filing-date')
            if date_cell:
                filing['filing_date'] = date_cell.get_text(strip=True)
            
            # Extract document link
            link_cell = row.find('td', class_='document-link')
            if link_cell:
                link_elem = link_cell.find('a', href=True)
                if link_elem:
                    filing['document_url'] = urljoin(base_url, link_elem['href'])
            
            # Extract accession number
            accession_cell = row.find('td', class_='accession-number')
            if accession_cell:
                filing['accession_number'] = accession_cell.get_text(strip=True)
            
            return filing if filing.get('filing_type') else None
            
        except Exception as e:
            logger.error(f"Error extracting filing from row: {e}")
            return None
    
    def _process_filings(self, filings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean filings."""
        processed = []
        
        for filing in filings:
            # Clean and validate data
            if not filing.get('filing_type'):
                continue
            
            # Parse date
            parsed_date = self._parse_date(filing.get('filing_date', ''))
            filing['parsed_date'] = parsed_date.isoformat() if parsed_date else None
            
            # Extract content if document URL available
            if filing.get('document_url'):
                content = self._extract_document_content(filing['document_url'])
                if content:
                    filing['content'] = content
                    
                    # Extract CHIPS Act mentions
                    chips_mentions = self._extract_chips_mentions(content)
                    if chips_mentions:
                        filing['chips_mentions'] = chips_mentions
                    
                    # Extract funding information
                    funding_info = self._extract_funding_info(content)
                    if funding_info:
                        filing['funding_info'] = funding_info
                    
                    # Extract capabilities
                    capabilities = self._extract_capabilities(content)
                    if capabilities:
                        filing['capabilities'] = capabilities
            
            # Calculate confidence score
            confidence = self._calculate_confidence(filing)
            filing['confidence_score'] = confidence
            
            processed.append(filing)
        
        return processed
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_document_content(self, document_url: str) -> Optional[str]:
        """Extract content from SEC document."""
        try:
            response = self._make_request(document_url, self._get_source_config(self.get_source_name()))
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find document content
            content_elem = soup.find('div', class_='document')
            if not content_elem:
                content_elem = soup.find('body')
            
            if content_elem:
                return content_elem.get_text(strip=True)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting document content from {document_url}: {e}")
            return None
    
    def _extract_chips_mentions(self, content: str) -> List[Dict[str, Any]]:
        """Extract CHIPS Act mentions from content."""
        if not content:
            return []
        
        mentions = []
        content_lower = content.lower()
        
        # CHIPS Act keywords
        chips_keywords = [
            'chips act',
            'chips and science act',
            'semiconductor manufacturing',
            'semiconductor production',
            'semiconductor supply chain',
            'semiconductor funding',
            'semiconductor investment',
            'semiconductor grant',
            'semiconductor subsidy',
        ]
        
        for keyword in chips_keywords:
            if keyword in content_lower:
                # Find context around the mention
                start = content_lower.find(keyword)
                if start != -1:
                    context_start = max(0, start - 200)
                    context_end = min(len(content), start + len(keyword) + 200)
                    context = content[context_start:context_end]
                    
                    mentions.append({
                        'keyword': keyword,
                        'context': context,
                        'position': start
                    })
        
        return mentions
    
    def _extract_funding_info(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract funding information from content."""
        if not content:
            return None
        
        funding_info = {}
        
        # Extract funding amounts
        funding_amount = self._extract_funding_amount(content)
        if funding_amount:
            funding_info['amount'] = funding_amount
        
        # Extract funding sources
        funding_sources = self._extract_funding_sources(content)
        if funding_sources:
            funding_info['sources'] = funding_sources
        
        # Extract project descriptions
        project_desc = self._extract_project_description(content)
        if project_desc:
            funding_info['project_description'] = project_desc
        
        return funding_info if funding_info else None
    
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
    
    def _extract_funding_sources(self, content: str) -> List[str]:
        """Extract funding sources from content."""
        if not content:
            return []
        
        sources = []
        content_lower = content.lower()
        
        # Common funding source keywords
        source_keywords = [
            'department of commerce',
            'national institute of standards',
            'nist',
            'department of energy',
            'national science foundation',
            'nsf',
            'department of defense',
            'darpa',
            'state funding',
            'federal grant',
            'government funding',
            'public funding',
        ]
        
        for keyword in source_keywords:
            if keyword in content_lower:
                sources.append(keyword)
        
        return sources
    
    def _extract_project_description(self, content: str) -> Optional[str]:
        """Extract project description from content."""
        if not content:
            return None
        
        # Look for project description patterns
        patterns = [
            r'project.*?description[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'proposed.*?project[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'funding.*?for[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                return matches[0].strip()
        
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
    
    def _calculate_confidence(self, filing: Dict[str, Any]) -> float:
        """Calculate confidence score for filing."""
        confidence = 0.0
        
        # Base confidence for SEC filing
        confidence += 0.9
        
        # Boost for having CHIPS mentions
        if filing.get('chips_mentions'):
            confidence += 0.05
        
        # Boost for having funding info
        if filing.get('funding_info'):
            confidence += 0.05
        
        # Boost for having capabilities
        if filing.get('capabilities'):
            confidence += 0.05
        
        return min(confidence, 1.0)
