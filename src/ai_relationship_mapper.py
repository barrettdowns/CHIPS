"""
AI-Powered Entity Relationship Mapper

Uses OpenAI API to analyze entity content and identify relationships
between CHIPS Act recipients including partnerships, parent-subsidiary,
consortiums, and supply chain relationships.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
from loguru import logger

from src.database.models import Entity, Relationship, RelationshipType


class RelationshipType(Enum):
    """Types of entity relationships."""
    PARENT_SUBSIDIARY = "parent_subsidiary"
    PARTNERSHIP = "partnership"
    CONSORTIUM = "consortium"
    SUPPLY_CHAIN = "supply_chain"
    JOINT_VENTURE = "joint_venture"
    MERGER_ACQUISITION = "merger_acquisition"
    RESEARCH_COLLABORATION = "research_collaboration"
    INVESTMENT = "investment"


@dataclass
class RelationshipMapping:
    """Represents a relationship between two entities."""
    entity1_id: int
    entity2_id: int
    relationship_type: RelationshipType
    confidence_score: float
    evidence: str
    description: str


class AIRelationshipMapper:
    """AI-powered entity relationship mapper using OpenAI API."""
    
    def __init__(self, api_key: str):
        """Initialize the AI relationship mapper."""
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        
        # Relationship detection prompts
        self.relationship_prompts = {
            "parent_subsidiary": """
            Analyze the following text for parent-subsidiary relationships between companies.
            Look for indicators like:
            - "subsidiary of", "parent company", "wholly owned"
            - "acquired by", "purchased by", "owned by"
            - Corporate structure mentions
            
            Return JSON format: {"relationships": [{"entity1": "name", "entity2": "name", "type": "parent_subsidiary", "confidence": 0.0-1.0, "evidence": "quote"}]}
            """,
            
            "partnership": """
            Analyze the following text for partnership relationships between companies.
            Look for indicators like:
            - "partnership with", "collaborating with", "working with"
            - "strategic alliance", "joint development", "cooperation"
            - "partner", "alliance", "collaboration"
            
            Return JSON format: {"relationships": [{"entity1": "name", "entity2": "name", "type": "partnership", "confidence": 0.0-1.0, "evidence": "quote"}]}
            """,
            
            "consortium": """
            Analyze the following text for consortium relationships between companies.
            Look for indicators like:
            - "consortium", "coalition", "alliance"
            - "joint initiative", "collaborative effort"
            - "group of companies", "industry partnership"
            
            Return JSON format: {"relationships": [{"entity1": "name", "entity2": "name", "type": "consortium", "confidence": 0.0-1.0, "evidence": "quote"}]}
            """,
            
            "supply_chain": """
            Analyze the following text for supply chain relationships between companies.
            Look for indicators like:
            - "supplier", "customer", "vendor"
            - "provides", "supplies", "sources from"
            - "manufacturing partner", "supply agreement"
            
            Return JSON format: {"relationships": [{"entity1": "name", "entity2": "name", "type": "supply_chain", "confidence": 0.0-1.0, "evidence": "quote"}]}
            """,
            
            "joint_venture": """
            Analyze the following text for joint venture relationships between companies.
            Look for indicators like:
            - "joint venture", "JV", "jointly owned"
            - "co-owned", "shared ownership"
            - "jointly established", "collaborative entity"
            
            Return JSON format: {"relationships": [{"entity1": "name", "entity2": "name", "type": "joint_venture", "confidence": 0.0-1.0, "evidence": "quote"}]}
            """,
            
            "research_collaboration": """
            Analyze the following text for research collaboration relationships between companies and universities.
            Look for indicators like:
            - "research partnership", "collaborative research"
            - "university collaboration", "academic partnership"
            - "joint research", "R&D collaboration"
            
            Return JSON format: {"relationships": [{"entity1": "name", "entity2": "name", "type": "research_collaboration", "confidence": 0.0-1.0, "evidence": "quote"}]}
            """
        }
        
        logger.info("AI Relationship Mapper initialized")
    
    def map_relationships(self, entities: List[Entity], content_sources: List[Dict[str, Any]]) -> List[RelationshipMapping]:
        """
        Map relationships between entities using AI analysis.
        
        Args:
            entities: List of entities to analyze
            content_sources: List of content sources containing entity information
            
        Returns:
            List of relationship mappings
        """
        logger.info(f"Mapping relationships for {len(entities)} entities")
        
        # Combine all content for analysis
        combined_content = self._combine_content_sources(content_sources)
        
        # Extract entity names for context
        entity_names = [entity.name for entity in entities]
        
        # Analyze relationships using different prompts
        all_relationships = []
        
        for relationship_type, prompt in self.relationship_prompts.items():
            try:
                relationships = self._analyze_relationships(
                    combined_content, 
                    entity_names, 
                    prompt, 
                    relationship_type
                )
                all_relationships.extend(relationships)
            except Exception as e:
                logger.error(f"Error analyzing {relationship_type} relationships: {e}")
        
        # Deduplicate and validate relationships
        validated_relationships = self._validate_relationships(all_relationships, entities)
        
        logger.info(f"Found {len(validated_relationships)} valid relationships")
        return validated_relationships
    
    def _combine_content_sources(self, content_sources: List[Dict[str, Any]]) -> str:
        """Combine content from multiple sources."""
        combined = []
        for source in content_sources:
            if source.get('content'):
                combined.append(f"Source: {source.get('title', 'Unknown')}\n{source['content']}\n")
        return "\n".join(combined)
    
    def _analyze_relationships(self, content: str, entity_names: List[str], prompt: str, relationship_type: str) -> List[RelationshipMapping]:
        """Analyze relationships using AI."""
        
        # Create context with entity names
        context = f"""
        Entity Names to Look For: {', '.join(entity_names)}
        
        Content to Analyze:
        {content}
        """
        
        full_prompt = f"{prompt}\n\n{context}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert analyst specializing in corporate relationships and business intelligence. Analyze the provided text and identify relationships between entities. Return only valid JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response (handle markdown code blocks)
            try:
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                result = json.loads(response_text)
                relationships = []
                
                for rel in result.get('relationships', []):
                    relationship = RelationshipMapping(
                        entity1_id=0,  # Will be resolved later
                        entity2_id=0,  # Will be resolved later
                        relationship_type=RelationshipType(rel['type']),
                        confidence_score=float(rel['confidence']),
                        evidence=rel['evidence'],
                        description=f"{rel['entity1']} - {rel['entity2']} ({rel['type']})"
                    )
                    relationships.append(relationship)
                
                return relationships
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return []
    
    def _validate_relationships(self, relationships: List[RelationshipMapping], entities: List[Entity]) -> List[RelationshipMapping]:
        """Validate and resolve entity IDs in relationships."""
        entity_name_to_id = {entity.name: entity.id for entity in entities}
        validated = []
        
        for rel in relationships:
            # Extract entity names from description
            parts = rel.description.split(' - ')
            if len(parts) >= 2:
                entity1_name = parts[0].strip()
                entity2_name = parts[1].split(' (')[0].strip()
                
                # Find entity IDs
                entity1_id = entity_name_to_id.get(entity1_name)
                entity2_id = entity_name_to_id.get(entity2_name)
                
                if entity1_id and entity2_id and entity1_id != entity2_id:
                    rel.entity1_id = entity1_id
                    rel.entity2_id = entity2_id
                    validated.append(rel)
        
        return validated
    
    def get_relationship_summary(self, relationships: List[RelationshipMapping]) -> Dict[str, Any]:
        """Get summary statistics of relationships."""
        summary = {
            "total_relationships": len(relationships),
            "by_type": {},
            "high_confidence": 0,
            "entity_pairs": set()
        }
        
        for rel in relationships:
            rel_type = rel.relationship_type.value
            summary["by_type"][rel_type] = summary["by_type"].get(rel_type, 0) + 1
            
            if rel.confidence_score >= 0.7:
                summary["high_confidence"] += 1
            
            summary["entity_pairs"].add((rel.entity1_id, rel.entity2_id))
        
        summary["unique_entity_pairs"] = len(summary["entity_pairs"])
        return summary


def create_relationship_mapper(api_key: str) -> AIRelationshipMapper:
    """Factory function to create relationship mapper."""
    return AIRelationshipMapper(api_key)
