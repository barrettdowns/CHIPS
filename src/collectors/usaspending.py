"""Enhanced USASpending.gov API collector for CHIPS Act intelligence."""

import requests
import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from .base_collector import BaseCollector
from ..database.models import Funding, FundingStatus, FundingCategory


class USASpendingCollector(BaseCollector):
    """Enhanced collector for USASpending.gov API data with comprehensive funding tracking."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.usaspending.gov/api/v2"
        self.session = requests.Session()
        
    def get_source_name(self) -> str:
        """Get the source name."""
        return "usaspending"
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect CHIPS Act related spending data from USASpending.gov."""
        logger.info("Starting enhanced USASpending.gov collection...")
        
        collected_data = []
        
        # Enhanced search terms for CHIPS Act funding
        search_terms = [
            "CHIPS Act",
            "semiconductor manufacturing", 
            "microelectronics",
            "integrated circuits",
            "chip manufacturing",
            "Department of Commerce",
            "NIST",
            "manufacturing incentives",
            "semiconductor R&D",
            "microelectronics R&D"
        ]
        
        for keyword in search_terms:
            try:
                logger.info(f"Searching for: {keyword}")
                spending_data = self._search_spending_by_award(keyword)
                collected_data.extend(spending_data)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching for {keyword}: {e}")
        
        logger.info(f"Enhanced USASpending.gov collection completed. Found {len(collected_data)} awards.")
        return collected_data
    
    def _search_spending_by_award(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for spending by award using USASpending API with enhanced data extraction."""
        awards = []
        
        try:
            # API endpoint for spending by award
            url = f"{self.base_url}/search/spending_by_award/"
            
            # Enhanced search parameters
            payload = {
                "filters": {
                    "keyword": keyword,
                    "award_type_codes": ["A", "B", "C", "D"],  # Use valid award type codes
                    "time_period": [
                        {
                            "start_date": "2022-01-01",
                            "end_date": "2025-12-31"
                        }
                    ]
                },
                "fields": [
                    "Award ID",
                    "Recipient Name", 
                    "Recipient DUNS Number",
                    "Award Amount",
                    "Award Date",
                    "Award Type",
                    "Description",
                    "NAICS Code",
                    "NAICS Description",
                    "Awarding Agency",
                    "Awarding Sub Agency",
                    "Place of Performance",
                    "Recipient Address",
                    "Awarding Office"
                ],
                "limit": 100,
                "page": 1
            }
            
            # Make API request directly (bypass VPN check for government API)
            logger.info(f"Making API request to {url}")
            try:
                response = requests.post(url, json=payload, timeout=30)
                logger.info(f"Response status: {response.status_code}")
            except Exception as req_e:
                logger.error(f"Request failed: {req_e}")
                return awards
            
            if response.status_code != 200:
                logger.warning(f"Failed to search USASpending for {keyword}: {response.status_code}")
                logger.warning(f"Error response: {response.text}")
                return awards
            
            data = response.json()
            
            # Extract awards from response
            if 'results' in data:
                for award in data['results']:
                    # Create enhanced funding data
                    award_data = self._create_enhanced_funding_data(award, keyword)
                    awards.append(award_data)
            
        except Exception as e:
            logger.error(f"Error searching USASpending API: {e}")
            import traceback
            traceback.print_exc()
        
        return awards
    
    def _create_enhanced_funding_data(self, award: Dict[str, Any], keyword: str) -> Dict[str, Any]:
        """Create enhanced funding data with all new fields."""
        # Extract basic information
        award_id = award.get('Award ID', '')
        recipient_name = award.get('Recipient Name', '')
        award_amount = award.get('Award Amount', 0)
        award_date = award.get('Award Date', '')
        description = award.get('Description', '')
        awarding_agency = award.get('Awarding Agency', '')
        
        # Determine funding status
        funding_status = self._determine_funding_status(award_date, description)
        
        # Determine funding category
        funding_category = self._determine_funding_category(description, awarding_agency)
        
        # Extract program name
        program_name = self._extract_program_name(description, awarding_agency)
        
        # Extract project location
        project_location = self._extract_project_location(award)
        
        # Extract jobs information
        jobs_created = self._extract_jobs_created(description)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(award, keyword)
        
        award_data = {
            'award_id': award_id,
            'recipient_name': recipient_name,
            'recipient_duns': award.get('Recipient DUNS Number', ''),
            'award_amount': award_amount,
            'award_date': award_date,
            'award_type': award.get('Award Type', ''),
            'description': description,
            'naics_code': award.get('NAICS Code', ''),
            'naics_description': award.get('NAICS Description', ''),
            'awarding_agency': awarding_agency,
            'awarding_sub_agency': award.get('Awarding Sub Agency', ''),
            'source': 'USASpending.gov',
            'keyword': keyword,
            'entities': self._extract_entity_names(recipient_name),
            
            # Enhanced funding fields
            'program_name': program_name,
            'grant_id': award_id,
            'funding_status': funding_status,
            'funding_category': funding_category,
            'funding_phase': self._extract_funding_phase(description),
            'project_location': project_location,
            'jobs_created': jobs_created,
            'confidence_score': confidence_score,
            'verification_status': 'api_verified',
            'notes': f"USASpending.gov award data for {keyword} search"
        }
        
        return award_data
    
    def _determine_funding_status(self, award_date: str, description: str) -> str:
        """Determine funding status based on award date and description."""
        if not award_date:
            return FundingStatus.UNKNOWN.value
        
        try:
            award_dt = datetime.fromisoformat(award_date.replace('Z', '+00:00'))
            current_dt = datetime.now()
            
            # If award date is recent (within 6 months), likely active
            if (current_dt - award_dt).days < 180:
                return FundingStatus.AWARDED.value
            else:
                return FundingStatus.COMPLETED.value
                
        except Exception:
            return FundingStatus.UNKNOWN.value
    
    def _determine_funding_category(self, description: str, awarding_agency: str) -> str:
        """Determine funding category based on description and agency."""
        description_lower = description.lower()
        agency_lower = awarding_agency.lower()
        
        # Manufacturing category keywords
        manufacturing_keywords = ['manufacturing', 'fabrication', 'production', 'facility', 'plant', 'fab']
        if any(keyword in description_lower for keyword in manufacturing_keywords):
            return FundingCategory.MANUFACTURING.value
        
        # R&D category keywords
        rd_keywords = ['research', 'development', 'r&d', 'innovation', 'technology', 'laboratory']
        if any(keyword in description_lower for keyword in rd_keywords):
            return FundingCategory.RESEARCH_DEVELOPMENT.value
        
        # Workforce development keywords
        workforce_keywords = ['workforce', 'training', 'education', 'skills', 'talent']
        if any(keyword in description_lower for keyword in workforce_keywords):
            return FundingCategory.WORKFORCE_DEVELOPMENT.value
        
        # Supply chain keywords
        supply_chain_keywords = ['supply chain', 'supplier', 'materials', 'equipment']
        if any(keyword in description_lower for keyword in supply_chain_keywords):
            return FundingCategory.SUPPLY_CHAIN.value
        
        return FundingCategory.OTHER.value
    
    def _extract_program_name(self, description: str, awarding_agency: str) -> Optional[str]:
        """Extract program name from description and agency."""
        if 'CHIPS' in description or 'CHIPS' in awarding_agency:
            return "CHIPS Act Program"
        elif 'NIST' in awarding_agency:
            return "NIST Semiconductor Program"
        elif 'Department of Commerce' in awarding_agency:
            return "Department of Commerce Semiconductor Initiative"
        
        return None
    
    def _extract_project_location(self, award: Dict[str, Any]) -> Optional[str]:
        """Extract project location from award data."""
        place_of_performance = award.get('Place of Performance', '')
        recipient_address = award.get('Recipient Address', '')
        
        if place_of_performance:
            return place_of_performance
        elif recipient_address:
            return recipient_address
        
        return None
    
    def _extract_jobs_created(self, description: str) -> Optional[int]:
        """Extract expected jobs created from description."""
        # Look for job numbers in description
        job_patterns = [
            r'(\d+)\s*jobs?',
            r'(\d+)\s*positions?',
            r'(\d+)\s*employees?',
            r'(\d+)\s*workers?'
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_funding_phase(self, description: str) -> Optional[str]:
        """Extract funding phase from description."""
        description_lower = description.lower()
        
        if 'phase 1' in description_lower or 'initial' in description_lower:
            return "Phase 1"
        elif 'phase 2' in description_lower:
            return "Phase 2"
        elif 'phase 3' in description_lower:
            return "Phase 3"
        elif 'final' in description_lower:
            return "Final Phase"
        
        return None
    
    def _calculate_confidence_score(self, award: Dict[str, Any], keyword: str) -> float:
        """Calculate confidence score for the funding data."""
        score = 0.5  # Base score
        
        # Increase confidence for CHIPS Act specific terms
        description = award.get('Description', '').lower()
        if 'chips' in description or 'chips' in keyword.lower():
            score += 0.3
        
        # Increase confidence for semiconductor-related terms
        semiconductor_terms = ['semiconductor', 'microelectronics', 'chip', 'integrated circuit']
        if any(term in description for term in semiconductor_terms):
            score += 0.2
        
        # Increase confidence for Department of Commerce/NIST
        awarding_agency = award.get('Awarding Agency', '').lower()
        if 'commerce' in awarding_agency or 'nist' in awarding_agency:
            score += 0.2
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _extract_entity_names(self, text: str) -> List[str]:
        """Extract potential entity names from text."""
        if not text:
            return []
        
        entities = []
        
        # Clean up the recipient name
        cleaned_name = text.strip()
        if cleaned_name and len(cleaned_name) > 3:
            entities.append(cleaned_name)
        
        return entities
