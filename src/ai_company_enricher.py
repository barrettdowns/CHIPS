"""
AI-Powered Company Information Enricher

Uses OpenAI API to search the internet and enrich entity records with missing
basic company information like headquarters, website, employees, revenue, founded date, etc.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from openai import OpenAI
from loguru import logger

from src.database.models import Entity


@dataclass
class CompanyInfo:
    """Company information data structure."""
    headquarters: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[str] = None
    revenue: Optional[str] = None
    founded: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    parent_company: Optional[str] = None
    subsidiaries: Optional[List[str]] = None
    confidence_score: float = 0.0
    sources: Optional[List[str]] = None


class AICompanyEnricher:
    """AI-powered company information enricher using OpenAI API."""
    
    def __init__(self, api_key: str):
        """Initialize the AI company enricher."""
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        
        logger.info("AI Company Enricher initialized")
    
    def enrich_entity(self, entity: Entity) -> CompanyInfo:
        """
        Enrich entity with missing company information using AI-powered internet search.
        
        Args:
            entity: Entity to enrich
            
        Returns:
            CompanyInfo object with enriched data
        """
        logger.info(f"Enriching company information for {entity.name}")
        
        try:
            # Create search query for the company
            search_query = f"{entity.name} company headquarters website employees revenue founded"
            
            # Use AI to search and extract company information
            company_info = self._search_company_info(entity.name, search_query)
            
            logger.info(f"Successfully enriched {entity.name} with {len([v for v in company_info.__dict__.values() if v])} data points")
            return company_info
            
        except Exception as e:
            logger.error(f"Error enriching {entity.name}: {e}")
            return CompanyInfo()
    
    def _search_company_info(self, company_name: str, search_query: str) -> CompanyInfo:
        """Search for company information using AI."""
        
        prompt = f"""
        You are a business intelligence researcher. Search for and extract comprehensive company information for "{company_name}".
        
        Please provide the following information in JSON format:
        {{
            "headquarters": "City, State, Country",
            "website": "https://company-website.com",
            "employees": "Number of employees (e.g., '1,000-5,000' or '500')",
            "revenue": "Annual revenue (e.g., '$100M' or '$1.2B')",
            "founded": "Year founded (e.g., '1995')",
            "description": "Brief company description (1-2 sentences)",
            "industry": "Primary industry",
            "parent_company": "Parent company name if applicable",
            "subsidiaries": ["Subsidiary 1", "Subsidiary 2"],
            "confidence_score": 0.0-1.0,
            "sources": ["Source 1", "Source 2"]
        }}
        
        Search for: {search_query}
        
        Instructions:
        - Be accurate and factual
        - If information is not available, use null
        - Provide confidence score based on data availability
        - Include sources where information was found
        - Focus on current/recent information
        - For semiconductor companies, emphasize their semiconductor focus
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert business intelligence researcher specializing in company information gathering. Provide accurate, factual information in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response (handle markdown code blocks)
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Create CompanyInfo object
            company_info = CompanyInfo(
                headquarters=result.get('headquarters'),
                website=result.get('website'),
                employees=result.get('employees'),
                revenue=result.get('revenue'),
                founded=result.get('founded'),
                description=result.get('description'),
                industry=result.get('industry'),
                parent_company=result.get('parent_company'),
                subsidiaries=result.get('subsidiaries', []),
                confidence_score=float(result.get('confidence_score', 0.0)),
                sources=result.get('sources', [])
            )
            
            return company_info
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response: {response_text}")
            return CompanyInfo()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return CompanyInfo()
    
    def batch_enrich_entities(self, entities: List[Entity], max_entities: int = 20) -> Dict[int, CompanyInfo]:
        """
        Enrich multiple entities in batch.
        
        Args:
            entities: List of entities to enrich
            max_entities: Maximum number of entities to process
            
        Returns:
            Dictionary mapping entity_id to CompanyInfo
        """
        logger.info(f"Batch enriching {min(len(entities), max_entities)} entities")
        
        enriched_data = {}
        
        for i, entity in enumerate(entities[:max_entities], 1):
            logger.info(f"Processing {i}/{min(len(entities), max_entities)}: {entity.name}")
            
            try:
                company_info = self.enrich_entity(entity)
                enriched_data[entity.id] = company_info
                
                # Add delay to avoid rate limiting
                if i < max_entities:
                    import time
                    time.sleep(2)  # 2 second delay between requests
                    
            except Exception as e:
                logger.error(f"Error processing {entity.name}: {e}")
                enriched_data[entity.id] = CompanyInfo()
        
        logger.info(f"Batch enrichment complete. Enriched {len(enriched_data)} entities")
        return enriched_data
    
    def get_enrichment_summary(self, enriched_data: Dict[int, CompanyInfo]) -> Dict[str, Any]:
        """Get summary of enrichment results."""
        summary = {
            "total_entities": len(enriched_data),
            "fields_enriched": {
                "headquarters": 0,
                "website": 0,
                "employees": 0,
                "revenue": 0,
                "founded": 0,
                "description": 0,
                "industry": 0
            },
            "avg_confidence": 0.0,
            "high_confidence": 0
        }
        
        total_confidence = 0.0
        
        for company_info in enriched_data.values():
            if company_info.headquarters:
                summary["fields_enriched"]["headquarters"] += 1
            if company_info.website:
                summary["fields_enriched"]["website"] += 1
            if company_info.employees:
                summary["fields_enriched"]["employees"] += 1
            if company_info.revenue:
                summary["fields_enriched"]["revenue"] += 1
            if company_info.founded:
                summary["fields_enriched"]["founded"] += 1
            if company_info.description:
                summary["fields_enriched"]["description"] += 1
            if company_info.industry:
                summary["fields_enriched"]["industry"] += 1
            
            total_confidence += company_info.confidence_score
            
            if company_info.confidence_score >= 0.7:
                summary["high_confidence"] += 1
        
        summary["avg_confidence"] = total_confidence / len(enriched_data) if enriched_data else 0.0
        
        return summary


def create_company_enricher(api_key: str) -> AICompanyEnricher:
    """Factory function to create company enricher."""
    return AICompanyEnricher(api_key)
