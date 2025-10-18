"""
Master Control Script - Automated CHIPS Act Intelligence System
Orchestrates all phases: collection, processing, quality control, and reporting.
"""

import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.auto_collect import AutomatedBatchCollector
from scripts.smart_scheduler import SmartScheduler
from scripts.quality_control import QualityControlManager
from src.database.db import DatabaseOperations
from src.collectors.chips_gov import CHIPSGovCollector
from src.collectors.sec_edgar import SECEdgarCollector
from src.collectors.university_press import UniversityPressCollector
from src.collectors.news_aggregator import NewsAggregatorCollector
from src.collectors.semiconductor_digest import SemiconductorDigestCollector
from src.collectors.ee_times import EETimesCollector
from src.collectors.anandtech import AnandTechCollector


class CHIPSIntelligenceSystem:
    """Master control system for CHIPS Act intelligence collection."""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.batch_collector = AutomatedBatchCollector(max_entities=20)
        self.scheduler = SmartScheduler()
        self.quality_control = QualityControlManager()
        
        # System configuration
        self.config = {
            'auto_quality_control': True,
            'auto_report_generation': True,
            'notification_enabled': True,
            'backup_enabled': True,
        }
    
    def run_full_cycle(self, sources=None, skip_processing=False, skip_reports=False):
        """Run complete intelligence cycle: collect, process, quality control, report."""
        logger.info("🚀 Starting Full CHIPS Intelligence Cycle")
        start_time = datetime.now()
        
        try:
            # Phase 1: Collection
            logger.info("📡 Phase 1: Automated Collection")
            collection_stats = self.batch_collector.run_batch_collection(
                sources=sources,
                skip_processing=skip_processing,
                skip_reports=skip_reports
            )
            
            if collection_stats['errors']:
                logger.warning(f"⚠️ Collection completed with {len(collection_stats['errors'])} errors")
            
            # Phase 2: Quality Control (if not skipped)
            if not skip_processing and self.config['auto_quality_control']:
                logger.info("🔍 Phase 2: Quality Control")
                self.quality_control.process_review_queue()
            
            # Phase 3: Report Generation (if not skipped)
            if not skip_reports and self.config['auto_report_generation']:
                logger.info("📄 Phase 3: Report Generation")
                # Reports are generated during collection, but we can regenerate if needed
                self._generate_system_reports()
            
            # Phase 4: System Health Check
            logger.info("🏥 Phase 4: System Health Check")
            self._perform_health_check()
            
            # Phase 5: Backup (if enabled)
            if self.config['backup_enabled']:
                logger.info("💾 Phase 5: Data Backup")
                self._create_backup()
            
            # Final statistics
            duration = (datetime.now() - start_time).total_seconds()
            self._log_cycle_completion(duration, collection_stats)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Full cycle failed: {e}")
            return False
    
    def run_daily_cycle(self):
        """Run daily intelligence cycle with smart scheduling."""
        logger.info("🌅 Running Daily Intelligence Cycle")
        
        # Get current pattern from scheduler
        pattern = self.scheduler._get_current_pattern()
        
        # Run collection with current pattern
        success = self.run_full_cycle(sources=pattern['sources'])
        
        if success:
            logger.info("✅ Daily cycle completed successfully")
        else:
            logger.error("❌ Daily cycle failed")
        
        return success
    
    def run_weekly_cycle(self):
        """Run comprehensive weekly cycle."""
        logger.info("📊 Running Weekly Comprehensive Cycle")
        
        # Use comprehensive pattern for weekly
        comprehensive_pattern = self.scheduler.collection_patterns[0]
        
        success = self.run_full_cycle(sources=comprehensive_pattern['sources'])
        
        if success:
            logger.info("✅ Weekly cycle completed successfully")
        else:
            logger.error("❌ Weekly cycle failed")
        
        return success
    
    def start_automated_system(self):
        """Start the fully automated system with scheduling."""
        logger.info("🤖 Starting Automated CHIPS Intelligence System")
        
        # Setup scheduler
        self.scheduler.setup_schedule()
        
        # Add our cycles to the scheduler
        schedule.every().day.at("02:00").do(self.run_daily_cycle)
        schedule.every().sunday.at("03:00").do(self.run_weekly_cycle)
        
        logger.info("⏰ Automated system running... Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Automated system stopped by user")
    
    def _generate_system_reports(self):
        """Generate system-wide reports."""
        from src.report_generator.entity_report import ReportGenerator
        
        report_generator = ReportGenerator(self.db_ops)
        
        # Generate entity reports
        entity_reports = report_generator.generate_all_entity_reports()
        
        # Generate cluster reports
        cluster_reports = report_generator.generate_all_cluster_reports()
        
        # Generate system summary report
        self._generate_system_summary_report()
        
        logger.info(f"📄 Generated {len(entity_reports)} entity reports and {len(cluster_reports)} cluster reports")
    
    def _generate_system_summary_report(self):
        """Generate system summary report."""
        from jinja2 import Environment, FileSystemLoader
        
        # Get system statistics
        db_stats = self.db_ops.get_database_stats()
        quality_metrics = self.quality_control.get_quality_metrics()
        
        # Load template
        template_path = Path(__file__).parent.parent / "src" / "report_generator" / "templates"
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("system_summary.md")
        
        # Generate report
        report_content = template.render(
            generated_at=datetime.now(),
            db_stats=db_stats,
            quality_metrics=quality_metrics,
            system_config=self.config
        )
        
        # Save report
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        summary_file = reports_dir / f"system_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        summary_file.write_text(report_content)
        
        logger.info(f"📊 System summary report: {summary_file}")
    
    def _perform_health_check(self):
        """Perform system health check."""
        logger.info("🏥 Performing system health check...")
        
        # Check database connectivity
        try:
            stats = self.db_ops.get_database_stats()
            logger.info("✅ Database: Healthy")
        except Exception as e:
            logger.error(f"❌ Database: Unhealthy - {e}")
            return False
        
        # Check data quality
        quality_metrics = self.quality_control.get_quality_metrics()
        if quality_metrics['data_quality_score'] < 0.7:
            logger.warning(f"⚠️ Data quality score: {quality_metrics['data_quality_score']:.2f}")
        else:
            logger.info(f"✅ Data quality score: {quality_metrics['data_quality_score']:.2f}")
        
        # Check review queue
        pending_reviews = quality_metrics['pending_reviews']
        if pending_reviews > 200:
            logger.warning(f"⚠️ Review queue: {pending_reviews} items pending")
        else:
            logger.info(f"✅ Review queue: {pending_reviews} items pending")
        
        logger.info("✅ System health check complete")
        return True
    
    def _create_backup(self):
        """Create system backup."""
        import shutil
        from datetime import datetime
        
        backup_dir = Path(__file__).parent.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"chips_backup_{timestamp}.db"
        
        # Copy database
        db_file = Path(__file__).parent.parent / "data" / "chips_entities.db"
        if db_file.exists():
            shutil.copy2(db_file, backup_file)
            logger.info(f"💾 Backup created: {backup_file}")
        else:
            logger.warning("⚠️ Database file not found for backup")
    
    def _log_cycle_completion(self, duration, collection_stats):
        """Log cycle completion statistics."""
        logger.info("🎉 Full Intelligence Cycle Complete!")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"📡 Sources collected: {len(collection_stats['sources_collected'])}")
        logger.info(f"📊 Items collected: {collection_stats['total_items']}")
        logger.info(f"👥 Entities created: {collection_stats['entities_created']}")
        logger.info(f"📄 Reports generated: {collection_stats['reports_generated']}")
        
        if collection_stats['errors']:
            logger.warning(f"⚠️ Errors: {len(collection_stats['errors'])}")
        
        # Database statistics
        db_stats = self.db_ops.get_database_stats()
        logger.info(f"🗄️  Total entities: {sum(db_stats.get('entities_by_type', {}).values())}")
        logger.info(f"💰 Total funding: ${db_stats.get('total_funding', 0):,.0f}M")
    
    def get_system_status(self):
        """Get comprehensive system status."""
        logger.info("📊 CHIPS Intelligence System Status")
        
        # Database statistics
        db_stats = self.db_ops.get_database_stats()
        logger.info(f"🗄️  Database: {sum(db_stats.get('entities_by_type', {}).values())} entities, ${db_stats.get('total_funding', 0):,.0f}M funding")
        
        # Quality metrics
        quality_metrics = self.quality_control.get_quality_metrics()
        logger.info(f"🔍 Quality: {quality_metrics['data_quality_score']:.2f} score, {quality_metrics['pending_reviews']} pending reviews")
        
        # Scheduler status
        self.scheduler.get_schedule_status()
        
        # System configuration
        logger.info("⚙️  System Configuration:")
        for key, value in self.config.items():
            logger.info(f"   {key}: {value}")


def main():
    """Main function for master control system."""
    parser = argparse.ArgumentParser(description='CHIPS Intelligence System Master Control')
    
    # Main operations
    parser.add_argument('--run-full', action='store_true',
                       help='Run full intelligence cycle')
    parser.add_argument('--run-daily', action='store_true',
                       help='Run daily cycle')
    parser.add_argument('--run-weekly', action='store_true',
                       help='Run weekly comprehensive cycle')
    parser.add_argument('--start-automated', action='store_true',
                       help='Start automated system with scheduling')
    
    # Collection options
    parser.add_argument('--sources', nargs='+',
                       choices=['chips_gov', 'sec_edgar', 'university_press', 'news_aggregator', 'semiconductor_digest', 'ee_times', 'anandtech', 'usaspending'],
                       help='Sources to collect from')
    parser.add_argument('--skip-processing', action='store_true',
                       help='Skip data processing')
    parser.add_argument('--skip-reports', action='store_true',
                       help='Skip report generation')
    
    # System management
    parser.add_argument('--status', action='store_true',
                       help='Show system status')
    parser.add_argument('--health-check', action='store_true',
                       help='Perform health check')
    parser.add_argument('--backup', action='store_true',
                       help='Create system backup')
    
    args = parser.parse_args()
    
    system = CHIPSIntelligenceSystem()
    
    if args.run_full:
        success = system.run_full_cycle(
            sources=args.sources,
            skip_processing=args.skip_processing,
            skip_reports=args.skip_reports
        )
        sys.exit(0 if success else 1)
    elif args.run_daily:
        success = system.run_daily_cycle()
        sys.exit(0 if success else 1)
    elif args.run_weekly:
        success = system.run_weekly_cycle()
        sys.exit(0 if success else 1)
    elif args.start_automated:
        system.start_automated_system()
    elif args.status:
        system.get_system_status()
    elif args.health_check:
        system._perform_health_check()
    elif args.backup:
        system._create_backup()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
