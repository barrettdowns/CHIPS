"""
Capability classification system for semiconductor entities.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import yaml
from pathlib import Path

from ..database.models import (
    DatabaseManager, Capability, CapabilityType, Entity
)


class CapabilityClassifier:
    """Classify entities into semiconductor capability areas."""
    
    def __init__(self, config_path: str = "config/capabilities.yaml"):
        self.config = self._load_config(config_path)
        self.capabilities = self.config.get('capabilities', {})
        self.confidence_config = self.config.get('confidence_scoring', {})
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def classify_entity(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Capability]:
        """Classify entity capabilities from content sources."""
        capabilities = []
        
        # Combine all content for analysis
        combined_content = self._combine_content_sources(content_sources)
        
        if not combined_content:
            return capabilities
        
        # Classify each capability area
        for capability_id, capability_config in self.capabilities.items():
            capability_type = CapabilityType(int(capability_id))
            confidence_score = self._calculate_capability_confidence(
                capability_config, combined_content, content_sources
            )
            
            if confidence_score > 0.3:  # Minimum threshold
                evidence = self._extract_capability_evidence(
                    capability_config, combined_content
                )
                
                capability = Capability(
                    entity_id=entity.id,
                    capability_type=capability_type,
                    confidence_score=confidence_score,
                    evidence=evidence
                )
                
                capabilities.append(capability)
        
        return capabilities
    
    def _combine_content_sources(self, content_sources: List[Dict[str, Any]]) -> str:
        """Combine content from multiple sources."""
        combined = []
        
        for source in content_sources:
            content = source.get('content', '')
            if content:
                combined.append(content)
            
            # Also include project descriptions
            project_desc = source.get('project_description', '')
            if project_desc:
                combined.append(project_desc)
            
            # Include funding info
            funding_info = source.get('funding_info', {})
            if funding_info:
                project_desc = funding_info.get('project_description', '')
                if project_desc:
                    combined.append(project_desc)
        
        return ' '.join(combined)
    
    def _calculate_capability_confidence(self, capability_config: Dict[str, Any], 
                                        content: str, content_sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for a capability."""
        if not content:
            return 0.0
        
        confidence = 0.0
        content_lower = content.lower()
        
        # Check primary keywords
        primary_keywords = capability_config.get('keywords', {}).get('primary', [])
        primary_matches = 0
        for keyword in primary_keywords:
            if keyword.lower() in content_lower:
                primary_matches += 1
        
        if primary_matches > 0:
            confidence += (primary_matches / len(primary_keywords)) * 0.4
        
        # Check secondary keywords
        secondary_keywords = capability_config.get('keywords', {}).get('secondary', [])
        secondary_matches = 0
        for keyword in secondary_keywords:
            if keyword.lower() in content_lower:
                secondary_matches += 1
        
        if secondary_matches > 0:
            confidence += (secondary_matches / len(secondary_keywords)) * 0.2
        
        # Check patterns
        patterns = capability_config.get('patterns', [])
        pattern_matches = 0
        for pattern in patterns:
            if re.search(pattern, content_lower):
                pattern_matches += 1
        
        if pattern_matches > 0:
            confidence += (pattern_matches / len(patterns)) * 0.3
        
        # Apply evidence type multipliers
        multipliers = self.confidence_config.get('multipliers', {})
        
        # Multiple sources multiplier
        if len(content_sources) > 1:
            confidence *= multipliers.get('multiple_sources', 1.0)
        
        # Recent evidence multiplier
        recent_sources = self._count_recent_sources(content_sources)
        if recent_sources > 0:
            confidence *= multipliers.get('recent_evidence', 1.0)
        
        # Specific technical details multiplier
        if self._has_technical_details(content):
            confidence *= multipliers.get('specific_technical_details', 1.0)
        
        # Funding amount multiplier
        if self._has_large_funding(content_sources):
            confidence *= multipliers.get('funding_amount_large', 1.0)
        
        return min(confidence, 1.0)
    
    def _extract_capability_evidence(self, capability_config: Dict[str, Any], content: str) -> str:
        """Extract evidence for capability classification."""
        evidence_parts = []
        
        # Find sentences containing capability keywords
        sentences = re.split(r'[.!?]', content)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check for primary keywords
            primary_keywords = capability_config.get('keywords', {}).get('primary', [])
            for keyword in primary_keywords:
                if keyword.lower() in sentence_lower:
                    evidence_parts.append(sentence.strip())
                    break
            
            # Check for secondary keywords
            secondary_keywords = capability_config.get('keywords', {}).get('secondary', [])
            for keyword in secondary_keywords:
                if keyword.lower() in sentence_lower:
                    evidence_parts.append(sentence.strip())
                    break
        
        # Limit evidence length
        evidence = ' '.join(evidence_parts[:5])  # First 5 relevant sentences
        return evidence[:1000]  # Limit to 1000 characters
    
    def _count_recent_sources(self, content_sources: List[Dict[str, Any]]) -> int:
        """Count sources from recent time period."""
        from datetime import datetime, timedelta
        
        recent_threshold = datetime.now() - timedelta(days=90)
        recent_count = 0
        
        for source in content_sources:
            collected_at = source.get('collected_at')
            if collected_at:
                try:
                    collected_date = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
                    if collected_date > recent_threshold:
                        recent_count += 1
                except ValueError:
                    continue
        
        return recent_count
    
    def _has_technical_details(self, content: str) -> bool:
        """Check if content contains technical details."""
        technical_indicators = [
            'nm', 'nanometer', 'process node', 'transistor', 'wafer',
            'lithography', 'deposition', 'etch', 'packaging', 'interconnect',
            'frequency', 'bandwidth', 'power consumption', 'efficiency',
            'architecture', 'design', 'fabrication', 'manufacturing'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in technical_indicators)
    
    def _has_large_funding(self, content_sources: List[Dict[str, Any]]) -> bool:
        """Check if content sources mention large funding amounts."""
        for source in content_sources:
            funding_amount = source.get('funding_amount')
            if funding_amount and funding_amount > 100:  # > $100M
                return True
            
            funding_info = source.get('funding_info', {})
            amount = funding_info.get('amount')
            if amount and amount > 100:  # > $100M
                return True
        
        return False
    
    def classify_all_entities(self, entities: List[Entity], content_sources: List[Dict[str, Any]]) -> Dict[int, List[Capability]]:
        """Classify capabilities for all entities."""
        entity_capabilities = {}
        
        for entity in entities:
            logger.info(f"Classifying capabilities for {entity.name}")
            
            # Get content sources relevant to this entity
            entity_sources = self._get_entity_sources(entity, content_sources)
            
            # Classify capabilities
            capabilities = self.classify_entity(entity, entity_sources)
            entity_capabilities[entity.id] = capabilities
            
            logger.info(f"Found {len(capabilities)} capabilities for {entity.name}")
        
        return entity_capabilities
    
    def _get_entity_sources(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get content sources relevant to specific entity."""
        relevant_sources = []
        entity_name_lower = entity.name.lower()
        
        for source in content_sources:
            content = source.get('content', '').lower()
            entities = source.get('entities', [])
            
            # Check if entity name appears in content
            if entity_name_lower in content:
                relevant_sources.append(source)
                continue
            
            # Check if entity is in entities list
            if any(entity_name_lower in entity_name.lower() for entity_name in entities):
                relevant_sources.append(source)
                continue
            
            # Check project description
            project_desc = source.get('project_description', '').lower()
            if entity_name_lower in project_desc:
                relevant_sources.append(source)
                continue
        
        return relevant_sources
    
    def get_capability_summary(self, capability_type: CapabilityType) -> Dict[str, Any]:
        """Get summary for a specific capability type."""
        capability_id = str(capability_type.value)
        capability_config = self.capabilities.get(capability_id, {})
        
        return {
            'id': capability_id,
            'name': capability_config.get('name', ''),
            'description': capability_config.get('description', ''),
            'keywords': capability_config.get('keywords', {}),
            'patterns': capability_config.get('patterns', []),
            'confidence_weights': capability_config.get('confidence_weights', {})
        }
    
    def get_all_capabilities_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary for all capabilities."""
        summary = {}
        
        for capability_id, capability_config in self.capabilities.items():
            summary[capability_id] = {
                'name': capability_config.get('name', ''),
                'description': capability_config.get('description', ''),
                'keyword_count': len(capability_config.get('keywords', {}).get('primary', [])) + 
                               len(capability_config.get('keywords', {}).get('secondary', [])),
                'pattern_count': len(capability_config.get('patterns', []))
            }
        
        return summary
    
    def validate_capability_classification(self, entity_id: int, 
                                         capabilities: List[Capability]) -> List[Dict[str, Any]]:
        """Validate capability classification and flag for review if needed."""
        validation_issues = []
        
        for capability in capabilities:
            # Flag low confidence capabilities
            if capability.confidence_score < 0.7:
                validation_issues.append({
                    'entity_id': entity_id,
                    'capability_type': capability.capability_type.value,
                    'confidence_score': capability.confidence_score,
                    'issue_type': 'low_confidence',
                    'message': f"Low confidence capability classification: {capability.confidence_score:.2f}"
                })
            
            # Flag capabilities with insufficient evidence
            if len(capability.evidence) < 50:
                validation_issues.append({
                    'entity_id': entity_id,
                    'capability_type': capability.capability_type.value,
                    'confidence_score': capability.confidence_score,
                    'issue_type': 'insufficient_evidence',
                    'message': "Insufficient evidence for capability classification"
                })
        
        return validation_issues
