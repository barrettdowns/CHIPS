"""
Semi-automated workflow scripts for CHIPS Act entity tracking.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import CapabilityType
from src.collectors.chips_gov import CHIPSGovCollector
from src.collectors.sec_filings import SECEdgarCollector
from src.entity_resolution.matcher import EntityResolver
from src.capability_classifier.classifier import CapabilityClassifier
from src.report_generator.entity_report import ReportGenerator


class CHIPSTracker:
    """Main CHIPS Act entity tracking system."""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.entity_resolver = EntityResolver(self.db_ops.db_manager)
        self.capability_classifier = CapabilityClassifier()
        self.report_generator = ReportGenerator(self.db_ops)
        
        # Initialize collectors
        self.chips_collector = CHIPSGovCollector()
        self.sec_collector = SECEdgarCollector()
    
    def run_collection(self, sources: List[str], **kwargs) -> List[dict]:
        """Run data collection from specified sources."""
        logger.info(f"Starting collection from sources: {sources}")
        
        all_data = []
        
        if 'chips_gov' in sources:
            logger.info("Collecting from CHIPS.gov")
            chips_data = self.chips_collector.run_collection(**kwargs)
            all_data.extend(chips_data)
        
        if 'sec_edgar' in sources:
            logger.info("Collecting from SEC EDGAR")
            sec_data = self.sec_collector.run_collection(**kwargs)
            all_data.extend(sec_data)
        
        logger.info(f"Collection complete: {len(all_data)} items collected")
        return all_data
    
    def process_data(self, raw_data: List[dict]) -> dict:
        """Process raw data through entity resolution and capability classification."""
        logger.info("Starting data processing")
        
        # Entity resolution
        resolution_result = self.entity_resolver.resolve_all_entities(raw_data)
        entities = resolution_result['entities']
        
        # Capability classification
        entity_capabilities = self.capability_classifier.classify_all_entities(entities, raw_data)
        
        # Store capabilities in database
        for entity_id, capabilities in entity_capabilities.items():
            for capability in capabilities:
                self.db_ops.db_manager.insert_capability(capability)
        
        logger.info(f"Processing complete: {len(entities)} entities, {sum(len(caps) for caps in entity_capabilities.values())} capabilities")
        
        return {
            'entities': entities,
            'capabilities': entity_capabilities,
            'resolution_result': resolution_result
        }
    
    def generate_reports(self, entity_ids: Optional[List[int]] = None, 
                        capability_types: Optional[List[CapabilityType]] = None) -> List[str]:
        """Generate reports for entities and capability clusters."""
        logger.info("Starting report generation")
        
        report_paths = []
        
        # Generate entity reports
        if entity_ids:
            for entity_id in entity_ids:
                try:
                    report_path = self.report_generator.generate_entity_report(entity_id)
                    if report_path:
                        report_paths.append(report_path)
                except Exception as e:
                    logger.error(f"Failed to generate report for entity {entity_id}: {e}")
        else:
            # Generate all entity reports
            entity_report_paths = self.report_generator.generate_all_entity_reports()
            report_paths.extend(entity_report_paths)
        
        # Generate cluster reports
        if capability_types:
            for capability_type in capability_types:
                try:
                    report_path = self.report_generator.generate_capability_cluster_report(capability_type)
                    if report_path:
                        report_paths.append(report_path)
                except Exception as e:
                    logger.error(f"Failed to generate cluster report for {capability_type.name}: {e}")
        else:
            # Generate all cluster reports
            cluster_report_paths = self.report_generator.generate_all_cluster_reports()
            report_paths.extend(cluster_report_paths)
        
        logger.info(f"Report generation complete: {len(report_paths)} reports generated")
        return report_paths
    
    def get_review_queue(self) -> List[dict]:
        """Get items in review queue."""
        review_items = self.db_ops.db_manager.get_review_queue()
        
        return [
            {
                'id': item.id,
                'entity_id': item.entity_id,
                'issue_type': item.issue_type,
                'confidence_score': item.confidence_score,
                'status': item.status.value,
                'notes': item.notes,
                'created_at': item.created_at.isoformat() if item.created_at else None
            }
            for item in review_items
        ]
    
    def get_database_stats(self) -> dict:
        """Get database statistics."""
        return self.db_ops.get_database_stats()
    
    def run_full_pipeline(self, sources: List[str], **kwargs) -> dict:
        """Run the complete pipeline: collection -> processing -> reporting."""
        logger.info("Starting full pipeline")
        
        # Step 1: Data collection
        raw_data = self.run_collection(sources, **kwargs)
        
        # Step 2: Data processing
        processed_data = self.process_data(raw_data)
        
        # Step 3: Report generation
        report_paths = self.generate_reports()
        
        # Step 4: Get final statistics
        stats = self.get_database_stats()
        
        logger.info("Full pipeline complete")
        
        return {
            'raw_data_count': len(raw_data),
            'entities_count': len(processed_data['entities']),
            'capabilities_count': sum(len(caps) for caps in processed_data['capabilities'].values()),
            'reports_generated': len(report_paths),
            'report_paths': report_paths,
            'database_stats': stats
        }


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='CHIPS Act Entity Tracking System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Collection command
    collection_parser = subparsers.add_parser('collect', help='Run data collection')
    collection_parser.add_argument('--sources', nargs='+', 
                                 choices=['chips_gov', 'sec_edgar', 'news'],
                                 default=['chips_gov', 'sec_edgar'],
                                 help='Data sources to collect from')
    collection_parser.add_argument('--max-pages', type=int, default=10,
                                 help='Maximum pages to collect per source')
    collection_parser.add_argument('--days-back', type=int, default=90,
                                 help='Days back to collect data')
    
    # Processing command
    processing_parser = subparsers.add_parser('process', help='Process collected data')
    processing_parser.add_argument('--raw-data', type=str,
                                 help='Path to raw data file (optional)')
    
    # Report generation command
    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--entity-id', type=int,
                              help='Generate report for specific entity ID')
    report_parser.add_argument('--capability', type=str,
                              choices=[ct.name for ct in CapabilityType],
                              help='Generate cluster report for specific capability')
    report_parser.add_argument('--all', action='store_true',
                              help='Generate all reports')
    
    # Review queue command
    review_parser = subparsers.add_parser('review', help='Manage review queue')
    review_parser.add_argument('--list', action='store_true',
                              help='List items in review queue')
    review_parser.add_argument('--resolve', type=int,
                              help='Resolve review item by ID')
    review_parser.add_argument('--notes', type=str,
                              help='Notes for resolution')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run full pipeline')
    pipeline_parser.add_argument('--sources', nargs='+',
                                choices=['chips_gov', 'sec_edgar', 'news'],
                                default=['chips_gov', 'sec_edgar'],
                                help='Data sources to collect from')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tracker
    tracker = CHIPSTracker()
    
    try:
        if args.command == 'collect':
            sources = args.sources
            raw_data = tracker.run_collection(sources, max_pages=args.max_pages, days_back=args.days_back)
            logger.info(f"Collection complete: {len(raw_data)} items collected")
        
        elif args.command == 'process':
            # This would load raw data and process it
            logger.info("Processing data...")
            # Implementation would go here
        
        elif args.command == 'report':
            if args.entity_id:
                report_path = tracker.report_generator.generate_entity_report(args.entity_id)
                logger.info(f"Entity report generated: {report_path}")
            elif args.capability:
                capability_type = CapabilityType[args.capability]
                report_path = tracker.report_generator.generate_capability_cluster_report(capability_type)
                logger.info(f"Cluster report generated: {report_path}")
            elif args.all:
                report_paths = tracker.generate_reports()
                logger.info(f"All reports generated: {len(report_paths)} reports")
            else:
                logger.error("Please specify --entity-id, --capability, or --all")
        
        elif args.command == 'review':
            if args.list:
                review_items = tracker.get_review_queue()
                logger.info(f"Review queue: {len(review_items)} items")
                for item in review_items:
                    logger.info(f"  {item['id']}: {item['issue_type']} (confidence: {item['confidence_score']:.2f})")
            elif args.resolve:
                # Resolve review item
                logger.info(f"Resolving review item {args.resolve}")
                # Implementation would go here
        
        elif args.command == 'stats':
            stats = tracker.get_database_stats()
            logger.info("Database Statistics:")
            logger.info(f"  Entities by type: {stats.get('entities_by_type', {})}")
            logger.info(f"  Total funding: ${stats.get('total_funding', 0):,.2f}M")
            logger.info(f"  Capabilities: {stats.get('capabilities', {})}")
            logger.info(f"  Review queue: {stats.get('review_queue', {})}")
        
        elif args.command == 'pipeline':
            sources = args.sources
            result = tracker.run_full_pipeline(sources)
            logger.info("Full pipeline complete:")
            logger.info(f"  Raw data: {result['raw_data_count']} items")
            logger.info(f"  Entities: {result['entities_count']}")
            logger.info(f"  Capabilities: {result['capabilities_count']}")
            logger.info(f"  Reports: {result['reports_generated']}")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
