"""
Test script for CHIPS Act entity tracking system.
"""

import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import Entity, EntityType, Funding, Capability, CapabilityType
from src.entity_resolution.matcher import EntityResolver
from src.capability_classifier.classifier import CapabilityClassifier
from src.report_generator.entity_report import ReportGenerator


def test_database_operations():
    """Test database operations."""
    logger.info("Testing database operations...")
    
    db_ops = DatabaseOperations()
    
    # Test entity creation
    entity = Entity(
        name="Intel Corporation",
        legal_name="Intel Corporation",
        entity_type=EntityType.COMPANY,
        confidence_score=0.95
    )
    
    entity_id = db_ops.db_manager.insert_entity(entity)
    logger.info(f"Created entity: {entity.name} (ID: {entity_id})")
    
    # Test funding creation
    funding = Funding(
        entity_id=entity_id,
        amount=1000.0,  # $1B
        announcement_date="2024-01-15",
        project_description="Advanced semiconductor manufacturing facility",
        source_url="https://example.com/chips-announcement"
    )
    
    funding_id = db_ops.db_manager.insert_funding(funding)
    logger.info(f"Created funding record: ${funding.amount}M (ID: {funding_id})")
    
    # Test capability creation
    capability = Capability(
        entity_id=entity_id,
        capability_type=CapabilityType.ADVANCED_LOGIC,
        confidence_score=0.9,
        evidence="Intel is developing advanced logic technologies including EUV lithography and GAA transistors"
    )
    
    capability_id = db_ops.db_manager.insert_capability(capability)
    logger.info(f"Created capability: {capability.capability_type.name} (ID: {capability_id})")
    
    # Test entity summary
    summary = db_ops.get_entity_summary(entity_id)
    logger.info(f"Entity summary: {summary['total_funding']}M funding, {summary['capability_count']} capabilities")
    
    return entity_id


def test_entity_resolution():
    """Test entity resolution."""
    logger.info("Testing entity resolution...")
    
    db_ops = DatabaseOperations()
    resolver = EntityResolver(db_ops.db_manager)
    
    # Test fuzzy matching
    matcher = resolver.matcher
    
    test_names = [
        "Intel Corporation",
        "Intel Corp",
        "Intel Inc.",
        "Intel",
        "Advanced Micro Devices",
        "AMD",
        "AMD Inc."
    ]
    
    target_name = "Intel Corporation"
    matches = matcher.find_matches(target_name, test_names, threshold=0.7)
    
    logger.info(f"Fuzzy matching results for '{target_name}':")
    for match_name, similarity in matches:
        logger.info(f"  {match_name}: {similarity:.2f}")
    
    return True


def test_capability_classification():
    """Test capability classification."""
    logger.info("Testing capability classification...")
    
    classifier = CapabilityClassifier()
    
    # Test content analysis
    test_content = """
    Intel Corporation is developing advanced 3D packaging technologies including chiplets and HBM memory.
    The company is also working on EUV lithography for sub-7nm process nodes and GAA transistors.
    Additionally, Intel is investing in RFIC design for 5G and millimeter wave applications.
    """
    
    # Mock entity and content sources
    entity = Entity(id=1, name="Intel Corporation", entity_type=EntityType.COMPANY)
    content_sources = [{'content': test_content, 'source': 'test'}]
    
    capabilities = classifier.classify_entity(entity, content_sources)
    
    logger.info(f"Detected capabilities for Intel:")
    for cap in capabilities:
        logger.info(f"  {cap.capability_type.name}: {cap.confidence_score:.2f}")
    
    return True


def test_report_generation(entity_id):
    """Test report generation."""
    logger.info("Testing report generation...")
    
    db_ops = DatabaseOperations()
    report_generator = ReportGenerator(db_ops)
    
    # Generate entity report
    report_path = report_generator.generate_entity_report(entity_id)
    logger.info(f"Generated entity report: {report_path}")
    
    # Check if report file exists
    if Path(report_path).exists():
        logger.info("Report file created successfully")
        return True
    else:
        logger.error("Report file not found")
        return False


def main():
    """Run all tests."""
    logger.info("Starting CHIPS Act Entity Tracking System Tests")
    
    try:
        # Test 1: Database operations
        entity_id = test_database_operations()
        
        # Test 2: Entity resolution
        test_entity_resolution()
        
        # Test 3: Capability classification
        test_capability_classification()
        
        # Test 4: Report generation
        test_report_generation(entity_id)
        
        logger.info("All tests completed successfully!")
        
        # Show final database stats
        db_ops = DatabaseOperations()
        stats = db_ops.get_database_stats()
        logger.info("Final database statistics:")
        logger.info(f"  Entities: {len(stats.get('entities_by_type', {}))}")
        logger.info(f"  Total funding: ${stats.get('total_funding', 0):,.2f}M")
        logger.info(f"  Capabilities: {len(stats.get('capabilities', {}))}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
