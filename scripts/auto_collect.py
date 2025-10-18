"""
Automated Batch Collection Script - Phase 1
Collects from all sources in one run, processes data, and generates reports.
"""

import sys
import time
import random
from datetime import datetime
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.collectors.chips_gov import CHIPSGovCollector
from src.collectors.sec_edgar import SECEdgarCollector
from src.collectors.university_press import UniversityPressCollector
from src.collectors.news_aggregator import NewsAggregatorCollector
from src.entity_resolution.matcher import EntityResolver
from src.classifier_factory import ClassifierFactory
from src.report_generator.entity_report import ReportGenerator


class AutomatedBatchCollector:
    """Automated batch collection system."""
    
    def __init__(self, max_entities=20):
        self.db_ops = DatabaseOperations()
        self.entity_resolver = EntityResolver(self.db_ops.db_manager)
        
        # Use AI classifier factory
        self.classifier_factory = ClassifierFactory()
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        self.capability_classifier = self.classifier_factory.create_classifier(api_key)
        
        self.report_generator = ReportGenerator(self.db_ops)
        
        # Entity limit for batch collection
        self.max_entities = max_entities
        self.entities_found = 0
        
        # Initialize collectors
        self.chips_collector = CHIPSGovCollector()
        self.sec_collector = SECEdgarCollector()
        self.university_collector = UniversityPressCollector()
        self.news_collector = NewsAggregatorCollector()
        
        # Collection configuration
        self.collection_config = {
            'chips_gov': {'max_pages': 10, 'delay_min': 5, 'delay_max': 10},
            'sec_edgar': {'days_back': 90, 'delay_min': 10, 'delay_max': 15},
            'university_press': {'max_pages': 3, 'delay_min': 5, 'delay_max': 10},
            'news_aggregator': {'max_pages': 5, 'delay_min': 3, 'delay_max': 7}
        }
        
        # Statistics tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'sources_collected': [],
            'total_items': 0,
            'entities_created': 0,
            'reports_generated': 0,
            'errors': []
        }
    
    def run_batch_collection(self, sources=None, skip_processing=False, skip_reports=False):
        """Run automated batch collection from all sources."""
        logger.info("🚀 Starting Automated Batch Collection")
        self.stats['start_time'] = datetime.now()
        
        # Default to all enabled sources if none specified
        if sources is None:
            sources = ['chips_gov', 'sec_edgar', 'university_press', 'news_aggregator']
        
        logger.info(f"📋 Collection plan: {len(sources)} sources")
        
        all_raw_data = []
        
        # Collect from each source with delays
        for i, source in enumerate(sources):
            # Check entity limit before each source
            current_entity_count = len(self.db_ops.db_manager.get_all_entities())
            if current_entity_count >= self.max_entities:
                logger.info(f"🎯 Entity limit reached ({self.max_entities}). Stopping collection.")
                break
                
            try:
                logger.info(f"📡 Collecting from {source} ({i+1}/{len(sources)})")
                
                # Add delay between sources (except first)
                if i > 0:
                    delay = random.randint(30, 60)  # 30-60 second delay between sources
                    logger.info(f"⏳ Waiting {delay} seconds before next source...")
                    time.sleep(delay)
                
                # Collect from source
                source_data = self._collect_from_source(source)
                all_raw_data.extend(source_data)
                
                self.stats['sources_collected'].append(source)
                self.stats['total_items'] += len(source_data)
                
                logger.info(f"✅ {source}: {len(source_data)} items collected")
                
            except Exception as e:
                error_msg = f"❌ Error collecting from {source}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
        
        logger.info(f"📊 Collection complete: {self.stats['total_items']} total items from {len(self.stats['sources_collected'])} sources")
        
        # Process data if not skipped
        if not skip_processing and all_raw_data:
            logger.info("🔄 Processing collected data...")
            self._process_collected_data(all_raw_data)
        
        # Generate reports if not skipped
        if not skip_reports:
            logger.info("📄 Generating reports...")
            self._generate_all_reports()
        
        self.stats['end_time'] = datetime.now()
        self._log_final_stats()
        
        return self.stats
    
    def _collect_from_source(self, source):
        """Collect data from a specific source."""
        config = self.collection_config.get(source, {})
        
        if source == 'chips_gov':
            return self.chips_collector.collect()
        elif source == 'sec_edgar':
            return self.sec_collector.collect()
        elif source == 'university_press':
            return self.university_collector.collect()
        elif source == 'news_aggregator':
            return self.news_collector.collect()
        elif source == 'semiconductor_digest':
            from src.collectors.semiconductor_digest import SemiconductorDigestCollector
            collector = SemiconductorDigestCollector()
            return collector.collect()
        elif source == 'ee_times':
            from src.collectors.ee_times import EETimesCollector
            collector = EETimesCollector()
            return collector.collect()
        elif source == 'anandtech':
            from src.collectors.anandtech import AnandTechCollector
            collector = AnandTechCollector()
            return collector.collect()
        elif source == 'usaspending':
            from src.collectors.usaspending import USASpendingCollector
            collector = USASpendingCollector()
            return collector.collect()
        else:
            # For other sources, we'd need to implement their collectors
            logger.warning(f"⚠️ Source {source} not yet implemented, skipping...")
            return []
    
    def _process_collected_data(self, raw_data):
        """Process collected data through entity resolution and capability classification."""
        logger.info("🔍 Processing entities...")
        
        # Check if we've already reached the entity limit
        current_entity_count = len(self.db_ops.db_manager.get_all_entities())
        if current_entity_count >= self.max_entities:
            logger.info(f"🎯 Entity limit reached ({self.max_entities}). Stopping processing.")
            return
        
        # Entity resolution
        resolution_result = self.entity_resolver.resolve_all_entities(raw_data)
        entities = resolution_result['entities']
        
        # Limit entities to not exceed max_entities
        remaining_slots = self.max_entities - current_entity_count
        if len(entities) > remaining_slots:
            entities = entities[:remaining_slots]
            logger.info(f"🎯 Limiting to {remaining_slots} entities to stay within limit")
        
        logger.info(f"👥 Resolved {len(entities)} entities")
        
        # Capability classification
        entity_capabilities = self.capability_classifier.classify_all_entities(entities, raw_data)
        
        # Store capabilities in database
        total_capabilities = 0
        for entity_id, capabilities in entity_capabilities.items():
            for capability in capabilities:
                self.db_ops.db_manager.insert_capability(capability)
            total_capabilities += len(capabilities)
        
        logger.info(f"🎯 Classified {total_capabilities} capabilities")
        
        # Store funding information
        self._process_funding_data(raw_data, entities)
        
        self.stats['entities_created'] = len(entities)
    
    def _process_funding_data(self, raw_data, entities):
        """Process enhanced funding information from raw data."""
        logger.info("💰 Processing enhanced funding data...")
        
        funding_count = 0
        for data_item in raw_data:
            # Handle both old format (funding_amount) and new enhanced format
            funding_amount = data_item.get('funding_amount') or data_item.get('award_amount', 0)
            
            if funding_amount and funding_amount > 0:
                # Find matching entity
                entities_in_content = data_item.get('entities', [])
                if entities_in_content:
                    entity_name = entities_in_content[0]
                    matching_entities = self.db_ops.db_manager.get_entities_by_name(entity_name)
                    if matching_entities:
                        entity = matching_entities[0]
                        
                        from src.database.models import Funding, FundingStatus, FundingCategory
                        
                        # Create enhanced funding record
                        funding = Funding(
                            entity_id=entity.id,
                            amount=funding_amount,
                            currency=data_item.get('currency', 'USD'),
                            announcement_date=data_item.get('parsed_date') or data_item.get('award_date'),
                            project_description=data_item.get('title', '') or data_item.get('description', ''),
                            source_url=data_item.get('link', '') or data_item.get('source_url', ''),
                            
                            # Enhanced fields from USASpending collector
                            program_name=data_item.get('program_name'),
                            grant_id=data_item.get('grant_id') or data_item.get('award_id'),
                            funding_status=FundingStatus(data_item.get('funding_status', 'unknown')),
                            funding_category=FundingCategory(data_item.get('funding_category', 'other')),
                            funding_phase=data_item.get('funding_phase'),
                            project_location=data_item.get('project_location'),
                            jobs_created=data_item.get('jobs_created'),
                            confidence_score=data_item.get('confidence_score', 0.0),
                            verification_status=data_item.get('verification_status', 'unverified'),
                            notes=data_item.get('notes', f"Collected from {data_item.get('source', 'unknown source')}")
                        )
                        
                        self.db_ops.db_manager.insert_funding(funding)
                        funding_count += 1
                        logger.info(f"💰 Added funding: {entity_name} - ${funding_amount:,.0f}M ({funding.funding_category.value})")
        
        logger.info(f"💰 Processed {funding_count} enhanced funding records")
    
    def _generate_all_reports(self):
        """Generate all entity and cluster reports."""
        logger.info("📄 Generating entity reports...")
        entity_reports = self.report_generator.generate_all_entity_reports()
        
        logger.info("📊 Generating cluster reports...")
        cluster_reports = self.report_generator.generate_all_cluster_reports()
        
        self.stats['reports_generated'] = len(entity_reports) + len(cluster_reports)
        logger.info(f"📄 Generated {len(entity_reports)} entity reports and {len(cluster_reports)} cluster reports")
    
    def _log_final_stats(self):
        """Log final collection statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("🎉 Automated Batch Collection Complete!")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"📡 Sources: {len(self.stats['sources_collected'])}")
        logger.info(f"📊 Items collected: {self.stats['total_items']}")
        logger.info(f"👥 Entities created: {self.stats['entities_created']}")
        logger.info(f"📄 Reports generated: {self.stats['reports_generated']}")
        
        if self.stats['errors']:
            logger.warning(f"⚠️  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.warning(f"   {error}")
        
        # Database statistics
        db_stats = self.db_ops.get_database_stats()
        logger.info(f"🗄️  Database: {sum(db_stats.get('entities_by_type', {}).values())} entities, ${db_stats.get('total_funding', 0):,.0f}M funding")


def main():
    """Main function for automated batch collection."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Batch Collection for CHIPS Act Entities')
    parser.add_argument('--sources', nargs='+', 
                       choices=['chips_gov', 'sec_edgar', 'semiconductor_digest', 'ee_times', 'anandtech', 'university_press', 'usaspending'],
                       help='Sources to collect from (default: all)')
    parser.add_argument('--skip-processing', action='store_true',
                       help='Skip data processing step')
    parser.add_argument('--skip-reports', action='store_true',
                       help='Skip report generation step')
    parser.add_argument('--quick', action='store_true',
                       help='Quick collection (fewer pages, faster)')
    
    args = parser.parse_args()
    
    # Adjust config for quick mode
    collector = AutomatedBatchCollector()
    if args.quick:
        logger.info("🏃 Quick mode: Reducing collection scope")
        for source_config in collector.collection_config.values():
            if 'max_pages' in source_config:
                source_config['max_pages'] = min(source_config['max_pages'], 3)
            if 'days_back' in source_config:
                source_config['days_back'] = min(source_config['days_back'], 30)
    
    # Run batch collection
    stats = collector.run_batch_collection(
        sources=args.sources,
        skip_processing=args.skip_processing,
        skip_reports=args.skip_reports
    )
    
    # Exit with error code if there were errors
    if stats['errors']:
        sys.exit(1)


if __name__ == '__main__':
    main()
