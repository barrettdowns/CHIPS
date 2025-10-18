#!/usr/bin/env python3
"""
Fix Entity Type Classification
Properly classify entities as Companies, Universities, or Consortiums based on their names.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import EntityType

def classify_entity_type(entity_name: str) -> EntityType:
    """Classify entity type based on name patterns."""
    name_upper = entity_name.upper()
    
    # University/Research Institution keywords
    university_keywords = [
        'UNIVERSITY', 'INSTITUTE', 'COLLEGE', 'ACADEMY', 'LABORATORY', 
        'RESEARCH', 'SCHOOL', 'CAMPUS', 'FOUNDATION'
    ]
    
    # Consortium/Partnership keywords
    consortium_keywords = [
        'CONSORTIUM', 'PARTNERSHIP', 'ALLIANCE', 'CENTER', 'COLLABORATIVE', 
        'JOINT VENTURE', 'COALITION', 'NETWORK', 'GROUP', 'ASSOCIATION'
    ]
    
    # Check for universities first
    if any(keyword in name_upper for keyword in university_keywords):
        return EntityType.UNIVERSITY
    
    # Check for consortiums
    if any(keyword in name_upper for keyword in consortium_keywords):
        return EntityType.CONSORTIUM
    
    # Default to company
    return EntityType.COMPANY

def main():
    """Main function to fix entity type classifications."""
    logger.info("🔧 Starting Entity Type Classification Fix...")
    
    db = DatabaseOperations()
    entities = db.get_all_entities()
    
    if not entities:
        logger.warning("No entities found in database.")
        return
    
    logger.info(f"Found {len(entities)} entities to classify")
    
    # Track changes
    changes = {
        EntityType.COMPANY: 0,
        EntityType.UNIVERSITY: 0,
        EntityType.CONSORTIUM: 0,
        EntityType.OTHER: 0
    }
    
    # Classify each entity
    for entity in entities:
        new_type = classify_entity_type(entity.name)
        
        if entity.entity_type != new_type:
            logger.info(f"Reclassifying {entity.name}: {entity.entity_type.value} → {new_type.value}")
            
            # Update in database
            query = "UPDATE entities SET entity_type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            db.db_manager.execute_update(query, (new_type.value, entity.id))
            
            changes[new_type] += 1
    
    # Summary
    logger.info("🎉 Entity Type Classification Complete!")
    logger.info("📊 Final Distribution:")
    
    # Get updated counts
    updated_entities = db.get_all_entities()
    type_counts = {}
    for entity in updated_entities:
        entity_type = entity.entity_type.value if entity.entity_type else 'unknown'
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
    
    for entity_type, count in type_counts.items():
        logger.info(f"  {entity_type}: {count}")
    
    logger.info(f"📈 Changes made: {sum(changes.values())} entities reclassified")

if __name__ == "__main__":
    main()
