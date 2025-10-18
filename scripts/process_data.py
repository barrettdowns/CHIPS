"""
Process collected CHIPS.gov data and generate reports.
"""

import sys
import json
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import Entity, EntityType, Funding, Capability, CapabilityType
from src.entity_resolution.matcher import EntityResolver
from src.capability_classifier.classifier import CapabilityClassifier
from src.report_generator.entity_report import ReportGenerator


def main():
    """Process collected data and generate reports."""
    logger.info("Processing collected CHIPS.gov data...")
    
    # Initialize components
    db_ops = DatabaseOperations()
    entity_resolver = EntityResolver(db_ops.db_manager)
    capability_classifier = CapabilityClassifier()
    report_generator = ReportGenerator(db_ops)
    
    # Load raw data
    raw_data_files = list(Path("data/raw").glob("chips_gov_*.json"))
    if not raw_data_files:
        logger.error("No raw data files found")
        return
    
    latest_file = max(raw_data_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Loading data from {latest_file}")
    
    with open(latest_file, 'r') as f:
        raw_data = json.load(f)
    
    logger.info(f"Loaded {len(raw_data)} items from raw data")
    
    # Process data through entity resolution
    logger.info("Processing entities...")
    resolution_result = entity_resolver.resolve_all_entities(raw_data)
    entities = resolution_result['entities']
    
    logger.info(f"Resolved {len(entities)} entities")
    
    # Store entities in database
    for entity in entities:
        if not entity.id:  # New entity
            entity_id = db_ops.db_manager.insert_entity(entity)
            entity.id = entity_id
            logger.info(f"Created entity: {entity.name} (ID: {entity_id})")
    
    # Process funding information
    logger.info("Processing funding information...")
    for data_item in raw_data:
        if data_item.get('funding_amount'):
            # Find matching entity
            entities_in_content = data_item.get('entities', [])
            if entities_in_content:
                # Use first entity found
                entity_name = entities_in_content[0]
                matching_entities = db_ops.db_manager.get_entities_by_name(entity_name)
                if matching_entities:
                    entity = matching_entities[0]
                    
                    funding = Funding(
                        entity_id=entity.id,
                        amount=data_item['funding_amount'],
                        announcement_date=data_item.get('parsed_date'),
                        project_description=data_item.get('title', ''),
                        source_url=data_item.get('link', '')
                    )
                    
                    funding_id = db_ops.db_manager.insert_funding(funding)
                    logger.info(f"Created funding record: ${funding.amount}M for {entity.name}")
    
    # Process capabilities
    logger.info("Processing capabilities...")
    entity_capabilities = capability_classifier.classify_all_entities(entities, raw_data)
    
    for entity_id, capabilities in entity_capabilities.items():
        for capability in capabilities:
            db_ops.db_manager.insert_capability(capability)
        logger.info(f"Added {len(capabilities)} capabilities for entity {entity_id}")
    
    # Generate reports
    logger.info("Generating reports...")
    report_paths = report_generator.generate_all_entity_reports()
    cluster_paths = report_generator.generate_all_cluster_reports()
    
    logger.info(f"Generated {len(report_paths)} entity reports and {len(cluster_paths)} cluster reports")
    
    # Show final statistics
    stats = db_ops.get_database_stats()
    logger.info("Final database statistics:")
    logger.info(f"  Entities: {stats.get('entities_by_type', {})}")
    logger.info(f"  Total funding: ${stats.get('total_funding', 0):,.2f}M")
    logger.info(f"  Capabilities: {stats.get('capabilities', {})}")
    
    # List generated reports
    logger.info("Generated reports:")
    for report_path in report_paths:
        logger.info(f"  Entity: {report_path}")
    for report_path in cluster_paths:
        logger.info(f"  Cluster: {report_path}")


if __name__ == '__main__':
    main()
