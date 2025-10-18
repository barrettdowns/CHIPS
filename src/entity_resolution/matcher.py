"""
Entity resolution and relationship mapping engine.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from fuzzywuzzy import fuzz, process
from loguru import logger
import yaml
from pathlib import Path

from ..database.models import (
    DatabaseManager, Entity, Relationship, EntityType, RelationshipType
)


class EntityMatcher:
    """Fuzzy matching for entity names."""
    
    def __init__(self, config_path: str = "config/capabilities.yaml"):
        self.config = self._load_config(config_path)
        self.normalization_config = self.config.get('entity_resolution', {})
        self.fuzzy_thresholds = self.normalization_config.get('fuzzy_thresholds', {})
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for matching."""
        if not name:
            return ""
        
        normalized = name.strip()
        
        # Remove corporate suffixes
        if self.normalization_config.get('remove_corporate_suffixes', True):
            suffixes = self.normalization_config.get('corporate_suffixes', [])
            for suffix in suffixes:
                if normalized.endswith(suffix):
                    normalized = normalized[:-len(suffix)].strip()
                    break
        
        # Remove common words
        if self.normalization_config.get('remove_common_words', True):
            common_words = self.normalization_config.get('common_words', [])
            words = normalized.split()
            words = [word for word in words if word not in common_words]
            normalized = ' '.join(words)
        
        # Normalize case
        if self.normalization_config.get('normalize_case', True):
            normalized = normalized.title()
        
        # Remove punctuation
        if self.normalization_config.get('remove_punctuation', True):
            normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized.strip()
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize both names
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use fuzzy matching
        similarity = fuzz.ratio(norm1, norm2) / 100.0
        
        # Boost for exact match after normalization
        if norm1 == norm2:
            similarity = 1.0
        
        return similarity
    
    def find_matches(self, target_name: str, candidate_names: List[str], 
                    threshold: float = 0.8) -> List[Tuple[str, float]]:
        """Find matches for target name among candidates."""
        matches = []
        
        for candidate in candidate_names:
            similarity = self.calculate_similarity(target_name, candidate)
            if similarity >= threshold:
                matches.append((candidate, similarity))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def get_match_threshold(self, match_type: str = 'medium_confidence') -> float:
        """Get threshold for match type."""
        return self.fuzzy_thresholds.get(match_type, 0.8)


class RelationshipDetector:
    """Detect relationships between entities."""
    
    def __init__(self, config_path: str = "config/capabilities.yaml"):
        self.config = self._load_config(config_path)
        self.relationship_config = self.config.get('entity_resolution', {}).get('relationships', {})
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def detect_relationships(self, text: str) -> List[Dict[str, Any]]:
        """Detect relationships from text content."""
        if not text:
            return []
        
        relationships = []
        text_lower = text.lower()
        
        # Parent-subsidiary relationships
        parent_keywords = self.relationship_config.get('parent_subsidiary_keywords', [])
        for keyword in parent_keywords:
            if keyword in text_lower:
                relationships.append({
                    'type': RelationshipType.PARENT_SUBSIDIARY,
                    'keyword': keyword,
                    'confidence': 0.8
                })
        
        # Consortium relationships
        consortium_keywords = self.relationship_config.get('consortium_keywords', [])
        for keyword in consortium_keywords:
            if keyword in text_lower:
                relationships.append({
                    'type': RelationshipType.CONSORTIUM_MEMBER,
                    'keyword': keyword,
                    'confidence': 0.8
                })
        
        # Partner relationships
        partner_keywords = self.relationship_config.get('partner_keywords', [])
        for keyword in partner_keywords:
            if keyword in text_lower:
                relationships.append({
                    'type': RelationshipType.PARTNER,
                    'keyword': keyword,
                    'confidence': 0.7
                })
        
        return relationships
    
    def extract_entity_pairs(self, text: str, entities: List[str]) -> List[Tuple[str, str, str]]:
        """Extract entity pairs and their relationship from text."""
        if not text or not entities:
            return []
        
        pairs = []
        
        # Look for patterns like "Entity A and Entity B"
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i != j:
                    # Check if both entities appear in the same sentence
                    sentences = re.split(r'[.!?]', text)
                    for sentence in sentences:
                        if entity1.lower() in sentence.lower() and entity2.lower() in sentence.lower():
                            # Detect relationship type
                            relationships = self.detect_relationships(sentence)
                            if relationships:
                                for rel in relationships:
                                    pairs.append((entity1, entity2, rel['type'].value))
        
        return pairs


class EntityResolver:
    """Main entity resolution engine."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.matcher = EntityMatcher()
        self.relationship_detector = RelationshipDetector()
    
    def resolve_entities(self, raw_entities: List[Dict[str, Any]]) -> List[Entity]:
        """Resolve and deduplicate entities."""
        resolved_entities = []
        processed_names = set()
        
        for raw_entity in raw_entities:
            name = raw_entity.get('name', '')
            if not name or name in processed_names:
                continue
            
            # Check for existing entity in database
            existing_entities = self.db_manager.get_entities_by_name(name)
            
            if existing_entities:
                # Use existing entity
                entity = existing_entities[0]
                logger.info(f"Found existing entity: {entity.name}")
            else:
                # Create new entity
                entity = Entity(
                    name=name,
                    legal_name=raw_entity.get('legal_name', name),
                    entity_type=EntityType(raw_entity.get('entity_type', 'company')),
                    confidence_score=raw_entity.get('confidence_score', 0.5)
                )
                
                entity_id = self.db_manager.insert_entity(entity)
                entity.id = entity_id
                logger.info(f"Created new entity: {entity.name}")
            
            resolved_entities.append(entity)
            processed_names.add(name)
        
        return resolved_entities
    
    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Deduplicate entities using fuzzy matching."""
        if not entities:
            return []
        
        # Group entities by similarity
        groups = []
        processed = set()
        
        for i, entity1 in enumerate(entities):
            if i in processed:
                continue
            
            group = [entity1]
            processed.add(i)
            
            for j, entity2 in enumerate(entities[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self.matcher.calculate_similarity(entity1.name, entity2.name)
                threshold = self.matcher.get_match_threshold('high_confidence')
                
                if similarity >= threshold:
                    group.append(entity2)
                    processed.add(j)
            
            groups.append(group)
        
        # Select best entity from each group
        deduplicated = []
        for group in groups:
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Select entity with highest confidence score
                best_entity = max(group, key=lambda e: e.confidence_score)
                deduplicated.append(best_entity)
                
                # Flag others for review
                for entity in group:
                    if entity != best_entity:
                        self.db_manager.insert_review_item(
                            ReviewItem(
                                entity_id=entity.id,
                                issue_type="duplicate_entity",
                                confidence_score=entity.confidence_score,
                                notes=f"Potential duplicate of {best_entity.name}"
                            )
                        )
        
        return deduplicated
    
    def map_relationships(self, entities: List[Entity], content_sources: List[Dict[str, Any]]) -> List[Relationship]:
        """Map relationships between entities."""
        relationships = []
        
        for source in content_sources:
            content = source.get('content', '')
            if not content:
                continue
            
            # Extract entity names from content
            entity_names = [entity.name for entity in entities]
            
            # Detect relationships
            entity_pairs = self.relationship_detector.extract_entity_pairs(content, entity_names)
            
            for entity1_name, entity2_name, relationship_type in entity_pairs:
                # Find entity IDs
                entity1 = next((e for e in entities if e.name == entity1_name), None)
                entity2 = next((e for e in entities if e.name == entity2_name), None)
                
                if entity1 and entity2 and entity1.id != entity2.id:
                    # Check if relationship already exists
                    existing_rels = self.db_manager.get_relationships_by_entity(entity1.id)
                    if not any(rel.entity_b_id == entity2.id for rel in existing_rels):
                        relationship = Relationship(
                            entity_a_id=entity1.id,
                            entity_b_id=entity2.id,
                            relationship_type=RelationshipType(relationship_type),
                            confidence_score=0.8,
                            evidence=content[:500]  # First 500 chars as evidence
                        )
                        
                        relationship_id = self.db_manager.insert_relationship(relationship)
                        relationship.id = relationship_id
                        relationships.append(relationship)
        
        return relationships
    
    def update_entity_confidence(self, entity_id: int, new_confidence: float):
        """Update entity confidence score."""
        self.db_manager.update_entity_confidence(entity_id, new_confidence)
    
    def get_entity_graph(self, entity_id: int) -> Dict[str, Any]:
        """Get entity relationship graph."""
        entity = self.db_manager.get_entity_by_id(entity_id)
        if not entity:
            return {}
        
        relationships = self.db_manager.get_relationships_by_entity(entity_id)
        
        graph = {
            'entity': entity,
            'relationships': relationships,
            'connected_entities': []
        }
        
        for rel in relationships:
            if rel.entity_a_id == entity_id:
                connected_entity = self.db_manager.get_entity_by_id(rel.entity_b_id)
            else:
                connected_entity = self.db_manager.get_entity_by_id(rel.entity_a_id)
            
            if connected_entity:
                graph['connected_entities'].append({
                    'entity': connected_entity,
                    'relationship': rel
                })
        
        return graph
    
    def resolve_all_entities(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve all entities from raw data."""
        logger.info("Starting entity resolution process")
        
        # Extract entities from raw data
        raw_entities = []
        for data_item in raw_data:
            entities = data_item.get('entities', [])
            for entity_name in entities:
                raw_entities.append({
                    'name': entity_name,
                    'entity_type': 'company',  # Default type
                    'confidence_score': data_item.get('confidence_score', 0.5)
                })
        
        # Resolve entities
        resolved_entities = self.resolve_entities(raw_entities)
        
        # Deduplicate entities
        deduplicated_entities = self.deduplicate_entities(resolved_entities)
        
        # Map relationships
        relationships = self.map_relationships(deduplicated_entities, raw_data)
        
        logger.info(f"Entity resolution complete: {len(deduplicated_entities)} entities, {len(relationships)} relationships")
        
        return {
            'entities': deduplicated_entities,
            'relationships': relationships,
            'raw_entities_count': len(raw_entities),
            'resolved_entities_count': len(resolved_entities),
            'deduplicated_entities_count': len(deduplicated_entities)
        }
