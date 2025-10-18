"""
Database operations and utilities for CHIPS Act entity tracking system.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger

from .models import (
    DatabaseManager, Entity, Funding, Capability, Relationship, 
    DataSource, ReviewItem, EntityType, CapabilityType, RelationshipType, ReviewStatus
)


class DatabaseOperations:
    """High-level database operations."""
    
    def __init__(self, db_path: str = "data/chips.db"):
        self.db_manager = DatabaseManager(db_path)
        self.db_path = db_path
    
    def ensure_data_directory(self):
        """Ensure data directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def initialize_database(self):
        """Initialize database with schema."""
        self.ensure_data_directory()
        self.db_manager._init_database()
    
    def add_entity_with_sources(self, entity: Entity, sources: List[DataSource]) -> int:
        """Add entity with associated data sources."""
        entity_id = self.db_manager.insert_entity(entity)
        
        for source in sources:
            source.entity_id = entity_id
            self.db_manager.insert_data_source(source)
        
        return entity_id
    
    def add_funding_with_evidence(self, funding: Funding, evidence_sources: List[str]) -> int:
        """Add funding record with evidence sources."""
        funding_id = self.db_manager.insert_funding(funding)
        
        # Add evidence as data sources
        for source_url in evidence_sources:
            data_source = DataSource(
                entity_id=funding.entity_id,
                source_type="funding_evidence",
                url=source_url,
                collected_at=datetime.now()
            )
            self.db_manager.insert_data_source(data_source)
        
        return funding_id
    
    def add_capability_with_evidence(self, capability: Capability, evidence_sources: List[str]) -> int:
        """Add capability with evidence sources."""
        capability_id = self.db_manager.insert_capability(capability)
        
        # Add evidence as data sources
        for source_url in evidence_sources:
            data_source = DataSource(
                entity_id=capability.entity_id,
                source_type="capability_evidence",
                url=source_url,
                collected_at=datetime.now()
            )
            self.db_manager.insert_data_source(data_source)
        
        return capability_id
    
    def flag_for_review(self, entity_id: int, issue_type: str, confidence_score: float, notes: str = ""):
        """Flag entity for manual review."""
        review_item = ReviewItem(
            entity_id=entity_id,
            issue_type=issue_type,
            confidence_score=confidence_score,
            status=ReviewStatus.PENDING,
            notes=notes
        )
        return self.db_manager.insert_review_item(review_item)
    
    def get_entity_summary(self, entity_id: int) -> Dict[str, Any]:
        """Get comprehensive entity summary."""
        entity = self.db_manager.get_entity_by_id(entity_id)
        if not entity:
            return {}
        
        funding = self.db_manager.get_funding_by_entity(entity_id)
        capabilities = self.db_manager.get_capabilities_by_entity(entity_id)
        relationships = self.db_manager.get_relationships_by_entity(entity_id)
        
        # Get data sources
        sources_query = "SELECT * FROM data_sources WHERE entity_id = ?"
        sources = self.db_manager.execute_query(sources_query, (entity_id,))
        
        return {
            "entity": entity,
            "funding": funding,
            "capabilities": capabilities,
            "relationships": relationships,
            "data_sources": sources,
            "total_funding": sum(f.amount for f in funding if f.amount),
            "capability_count": len(capabilities),
            "relationship_count": len(relationships),
            "source_count": len(sources)
        }
    
    def search_entities(self, query: str, entity_type: Optional[EntityType] = None) -> List[Entity]:
        """Search entities by name with optional type filter."""
        if entity_type:
            sql_query = "SELECT * FROM entities WHERE (name LIKE ? OR legal_name LIKE ?) AND entity_type = ?"
            params = (f"%{query}%", f"%{query}%", entity_type.value)
        else:
            sql_query = "SELECT * FROM entities WHERE name LIKE ? OR legal_name LIKE ?"
            params = (f"%{query}%", f"%{query}%")
        
        results = self.db_manager.execute_query(sql_query, params)
        entities = []
        for row in results:
            entities.append(Entity(
                id=row['id'],
                name=row['name'],
                legal_name=row['legal_name'],
                entity_type=EntityType(row['entity_type']),
                confidence_score=row['confidence_score'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return entities
    
    def get_entities_by_capability(self, capability_type: CapabilityType) -> List[Entity]:
        """Get entities with specific capability."""
        query = """
            SELECT DISTINCT e.* FROM entities e
            JOIN capabilities c ON e.id = c.entity_id
            WHERE c.capability_type = ?
            ORDER BY c.confidence_score DESC
        """
        results = self.db_manager.execute_query(query, (capability_type.value,))
        entities = []
        for row in results:
            entities.append(Entity(
                id=row['id'],
                name=row['name'],
                legal_name=row['legal_name'],
                entity_type=EntityType(row['entity_type']),
                confidence_score=row['confidence_score'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return entities
    
    def get_top_funded_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top funded entities by total amount."""
        query = """
            SELECT e.*, SUM(f.amount) as total_funding, COUNT(f.id) as funding_count
            FROM entities e
            LEFT JOIN funding f ON e.id = f.entity_id
            GROUP BY e.id
            HAVING total_funding > 0
            ORDER BY total_funding DESC
            LIMIT ?
        """
        results = self.db_manager.execute_query(query, (limit,))
        entities = []
        for row in results:
            entities.append({
                "entity": Entity(
                    id=row['id'],
                    name=row['name'],
                    legal_name=row['legal_name'],
                    entity_type=EntityType(row['entity_type']),
                    confidence_score=row['confidence_score'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                ),
                "total_funding": row['total_funding'],
                "funding_count": row['funding_count']
            })
        return entities
    
    def get_capability_statistics(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for each capability type."""
        query = """
            SELECT capability_type, 
                   COUNT(*) as entity_count,
                   AVG(confidence_score) as avg_confidence,
                   MAX(confidence_score) as max_confidence
            FROM capabilities
            GROUP BY capability_type
        """
        results = self.db_manager.execute_query(query)
        stats = {}
        for row in results:
            stats[row['capability_type']] = {
                "entity_count": row['entity_count'],
                "avg_confidence": row['avg_confidence'],
                "max_confidence": row['max_confidence']
            }
        return stats
    
    def update_entity_confidence(self, entity_id: int, new_confidence: float):
        """Update entity confidence score."""
        query = """
            UPDATE entities 
            SET confidence_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self.db_manager.execute_update(query, (new_confidence, entity_id))
    
    def mark_review_item_resolved(self, review_id: int, notes: str = ""):
        """Mark review item as resolved."""
        query = """
            UPDATE review_queue 
            SET status = 'resolved', reviewed_at = CURRENT_TIMESTAMP, notes = ?
            WHERE id = ?
        """
        self.db_manager.execute_update(query, (notes, review_id))
    
    def get_all_entities(self) -> List[Entity]:
        """Get all entities."""
        return self.db_manager.get_all_entities()
    
    def get_entities_by_name(self, name: str) -> List[Entity]:
        """Get entities by name."""
        return self.db_manager.get_entities_by_name(name)
    
    def get_review_items_by_status(self, status):
        """Get review items by status."""
        return self.db_manager.get_review_items_by_status(status)
    
    def get_review_items(self, filters, limit=50):
        """Get review items with filters."""
        return self.db_manager.get_review_items(filters, limit)
    
    def get_review_item_by_id(self, item_id):
        """Get review item by ID."""
        return self.db_manager.get_review_item_by_id(item_id)
    
    def update_review_item(self, item):
        """Update review item."""
        return self.db_manager.update_review_item(item)
    
    def insert_capability(self, capability):
        """Insert capability."""
        return self.db_manager.insert_capability(capability)
    
    def insert_funding(self, funding):
        """Insert funding."""
        return self.db_manager.insert_funding(funding)
    
    def insert_relationship(self, relationship):
        """Insert relationship."""
        return self.db_manager.insert_relationship(relationship)
    
    def update_entity_info(self, entity_id: int, company_info) -> bool:
        """Update entity with enriched company information."""
        try:
            # Convert subsidiaries list to JSON string if provided
            subsidiaries_json = None
            if company_info.subsidiaries:
                import json
                subsidiaries_json = json.dumps(company_info.subsidiaries)
            
            # Update entity with enriched information
            query = """
            UPDATE entities SET 
                headquarters = ?,
                website = ?,
                employees = ?,
                revenue = ?,
                founded = ?,
                description = ?,
                industry = ?,
                parent_company = ?,
                subsidiaries = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            params = (
                company_info.headquarters,
                company_info.website,
                company_info.employees,
                company_info.revenue,
                company_info.founded,
                company_info.description,
                company_info.industry,
                company_info.parent_company,
                subsidiaries_json,
                entity_id
            )
            
            self.db_manager.execute_update(query, params)
            
            logger.info(f"Updated entity {entity_id} with enriched company information")
            return True
            
        except Exception as e:
            logger.error(f"Error updating entity {entity_id}: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        stats = {}
        
        # Entity count by type
        entity_query = "SELECT entity_type, COUNT(*) as count FROM entities GROUP BY entity_type"
        entity_results = self.db_manager.execute_query(entity_query)
        stats["entities_by_type"] = {row['entity_type']: row['count'] for row in entity_results}
        
        # Total funding
        funding_query = "SELECT SUM(amount) as total FROM funding WHERE amount IS NOT NULL"
        funding_result = self.db_manager.execute_query(funding_query)
        stats["total_funding"] = funding_result[0]['total'] if funding_result else 0
        
        # Capability distribution
        capability_query = "SELECT capability_type, COUNT(*) as count FROM capabilities GROUP BY capability_type"
        capability_results = self.db_manager.execute_query(capability_query)
        stats["capabilities"] = {row['capability_type']: row['count'] for row in capability_results}
        
        # Review queue status
        review_query = "SELECT status, COUNT(*) as count FROM review_queue GROUP BY status"
        review_results = self.db_manager.execute_query(review_query)
        stats["review_queue"] = {row['status']: row['count'] for row in review_results}
        
        # Top entities by funding
        top_entities_query = """
        SELECT e.name, SUM(f.amount) as total_funding
        FROM entities e
        LEFT JOIN funding f ON e.id = f.entity_id
        WHERE f.amount IS NOT NULL
        GROUP BY e.id, e.name
        ORDER BY total_funding DESC
        LIMIT 10
        """
        top_entities_results = self.db_manager.execute_query(top_entities_query)
        stats["top_entities_by_funding"] = [
            {"name": row['name'], "total_funding": row['total_funding'] or 0}
            for row in top_entities_results
        ]
        
        # Last collection date
        last_collection_query = "SELECT MAX(created_at) as last_collection FROM entities"
        last_collection_result = self.db_manager.execute_query(last_collection_query)
        last_collection_date = last_collection_result[0]['last_collection'] if last_collection_result else None
        
        # Convert string to datetime if needed
        if last_collection_date and isinstance(last_collection_date, str):
            try:
                from datetime import datetime
                last_collection_date = datetime.fromisoformat(last_collection_date.replace('Z', '+00:00'))
            except:
                last_collection_date = None
        
        stats["last_collection_date"] = last_collection_date
        
        # Last collection count
        stats["last_collection_count"] = len(entity_results) if entity_results else 0
        
        return stats
    
    def export_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """Export all data for an entity as JSON."""
        summary = self.get_entity_summary(entity_id)
        
        # Convert dataclasses to dictionaries
        export_data = {
            "entity": {
                "id": summary["entity"].id,
                "name": summary["entity"].name,
                "legal_name": summary["entity"].legal_name,
                "entity_type": summary["entity"].entity_type.value,
                "confidence_score": summary["entity"].confidence_score,
                "created_at": summary["entity"].created_at.isoformat() if summary["entity"].created_at else None,
                "updated_at": summary["entity"].updated_at.isoformat() if summary["entity"].updated_at else None
            },
            "funding": [
                {
                    "id": f.id,
                    "amount": f.amount,
                    "currency": f.currency,
                    "announcement_date": f.announcement_date.isoformat() if f.announcement_date else None,
                    "project_description": f.project_description,
                    "source_url": f.source_url,
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                for f in summary["funding"]
            ],
            "capabilities": [
                {
                    "id": c.id,
                    "capability_type": c.capability_type.value,
                    "confidence_score": c.confidence_score,
                    "evidence": c.evidence,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in summary["capabilities"]
            ],
            "relationships": [
                {
                    "id": r.id,
                    "entity_a_id": r.entity_a_id,
                    "entity_b_id": r.entity_b_id,
                    "relationship_type": r.relationship_type.value,
                    "confidence_score": r.confidence_score,
                    "evidence": r.evidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in summary["relationships"]
            ],
            "data_sources": [
                {
                    "id": s['id'],
                    "source_type": s['source_type'],
                    "url": s['url'],
                    "collected_at": s['collected_at'],
                    "raw_data": json.loads(s['raw_data']) if s['raw_data'] else None,
                    "created_at": s['created_at']
                }
                for s in summary["data_sources"]
            ],
            "summary": {
                "total_funding": summary["total_funding"],
                "capability_count": summary["capability_count"],
                "relationship_count": summary["relationship_count"],
                "source_count": summary["source_count"]
            }
        }
        
        return export_data
