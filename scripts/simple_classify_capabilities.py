#!/usr/bin/env python3
"""
Simple Capability Classification
Classify capabilities based on entity names and company descriptions using AI.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.classifier_factory import ClassifierFactory
from src.database.models import CapabilityType

def main():
    """Main function to run capability classification on all entities."""
    logger.info("🤖 Starting Simple Capability Classification...")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set. Cannot perform AI classification.")
        sys.exit(1)
    
    # Initialize classifier
    classifier = ClassifierFactory().create_classifier(api_key=api_key)
    logger.info(f"Using {type(classifier).__name__} for capability classification")
    
    db = DatabaseOperations()
    entities = db.get_all_entities()
    
    if not entities:
        logger.warning("No entities found in database.")
        return
    
    logger.info(f"Found {len(entities)} entities to process")
    
    # Find entities without capabilities
    entities_without_capabilities = []
    for entity in entities:
        # Check if entity has capabilities
        capabilities_query = "SELECT COUNT(*) as count FROM capabilities WHERE entity_id = ?"
        result = db.db_manager.execute_query(capabilities_query, (entity.id,))
        capability_count = result[0]['count'] if result else 0
        
        if capability_count == 0:
            entities_without_capabilities.append(entity)
    
    logger.info(f"Found {len(entities_without_capabilities)} entities without capabilities")
    
    if not entities_without_capabilities:
        logger.info("All entities already have capabilities classified!")
        return
    
    # Process entities without capabilities
    classified_count = 0
    failed_count = 0
    
    for i, entity in enumerate(entities_without_capabilities):
        logger.info(f"[{i+1}/{len(entities_without_capabilities)}] Classifying {entity.name} (ID: {entity.id})...")
        
        try:
            # Create content for classification based on entity info
            content_parts = [entity.name]
            
            if entity.description:
                content_parts.append(entity.description)
            
            if entity.industry:
                content_parts.append(f"Industry: {entity.industry}")
            
            if entity.headquarters:
                content_parts.append(f"Headquarters: {entity.headquarters}")
            
            # Add entity type context
            if entity.entity_type:
                content_parts.append(f"Entity Type: {entity.entity_type.value}")
            
            combined_content = " ".join(content_parts)
            
            # Classify capabilities using the correct method
            capabilities = classifier.classify_entity(entity, [])
            
            if capabilities:
                # Insert capabilities into database
                for capability in capabilities:
                    db.insert_capability(
                        entity_id=entity.id,
                        capability_type=capability.capability_type,
                        confidence_score=capability.confidence_score,
                        evidence=capability.evidence
                    )
                
                logger.info(f"✅ Classified {entity.name}: {[cap.capability_type.value for cap in capabilities]}")
                classified_count += 1
            else:
                logger.warning(f"No capabilities found for {entity.name}")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Error classifying {entity.name}: {e}")
            failed_count += 1
    
    # Summary
    logger.info("🎉 Simple Capability Classification Complete!")
    logger.info(f"📊 Results:")
    logger.info(f"  ✅ Successfully classified: {classified_count}")
    logger.info(f"  ❌ Failed: {failed_count}")
    if classified_count + failed_count > 0:
        logger.info(f"  📈 Success rate: {(classified_count/(classified_count+failed_count)*100):.1f}%")
    
    # Show final capability distribution
    logger.info("\\n📊 Final Capability Distribution:")
    capabilities_query = "SELECT capability_type, COUNT(*) as count FROM capabilities GROUP BY capability_type"
    results = db.db_manager.execute_query(capabilities_query)
    
    capability_names = {
        1: "3D Packaging",
        2: "Heterogeneous Packaging", 
        3: "Multi Project Wafer",
        4: "Radio Frequency Integrated Circuit (RFIC) Design",
        5: "Monolithic Microwave Integrated Circuit (MMIC) Chips",
        6: "Radiation Hardened (RAD-HARD) Chips"
    }
    
    for result in results:
        cap_type = result['capability_type']
        count = result['count']
        cap_name = capability_names.get(cap_type, f"Unknown ({cap_type})")
        logger.info(f"  {cap_name}: {count}")

if __name__ == "__main__":
    main()
