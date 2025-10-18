"""
Smart Scheduling System - Phase 2
Schedules collections at different times with pattern rotation and random delays.
"""

import sys
import time
import random
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.auto_collect import AutomatedBatchCollector


class SmartScheduler:
    """Smart scheduling system with pattern rotation and delays."""
    
    def __init__(self):
        self.collector = AutomatedBatchCollector()
        self.schedule_config = {
            'daily_collection_time': '02:00',  # 2 AM daily
            'weekly_full_collection': 'sunday',  # Sunday weekly
            'random_delay_range': (300, 1800),  # 5-30 minutes random delay
            'pattern_rotation_days': 7,  # Rotate patterns every 7 days
        }
        
        # Collection patterns for rotation
        self.collection_patterns = [
            {
                'name': 'comprehensive',
                'sources': ['chips_gov', 'sec_edgar', 'semiconductor_digest', 'ee_times', 'anandtech', 'university_press'],
                'config': {'max_pages': 10, 'days_back': 90}
            },
            {
                'name': 'focused',
                'sources': ['chips_gov', 'sec_edgar'],
                'config': {'max_pages': 15, 'days_back': 120}
            },
            {
                'name': 'news_focused',
                'sources': ['chips_gov', 'semiconductor_digest', 'ee_times', 'anandtech'],
                'config': {'max_pages': 8, 'days_back': 60}
            },
            {
                'name': 'academic',
                'sources': ['chips_gov', 'university_press'],
                'config': {'max_pages': 12, 'days_back': 90}
            }
        ]
        
        self.current_pattern_index = 0
        self.last_pattern_change = datetime.now()
    
    def setup_schedule(self):
        """Setup the collection schedule."""
        logger.info("📅 Setting up smart collection schedule")
        
        # Daily collection with random delay
        schedule.every().day.at(self.schedule_config['daily_collection_time']).do(
            self._daily_collection_with_delay
        )
        
        # Weekly comprehensive collection
        schedule.every().sunday.at("03:00").do(
            self._weekly_comprehensive_collection
        )
        
        # Pattern rotation check
        schedule.every().day.at("01:00").do(
            self._check_pattern_rotation
        )
        
        logger.info("✅ Schedule configured:")
        logger.info(f"   📅 Daily collection: {self.schedule_config['daily_collection_time']}")
        logger.info(f"   📅 Weekly comprehensive: Sunday 03:00")
        logger.info(f"   🔄 Pattern rotation: Every {self.schedule_config['pattern_rotation_days']} days")
    
    def _daily_collection_with_delay(self):
        """Daily collection with random delay."""
        logger.info("🌅 Starting daily collection with smart delay")
        
        # Add random delay to avoid detection patterns
        delay = random.randint(*self.schedule_config['random_delay_range'])
        logger.info(f"⏳ Random delay: {delay} seconds")
        time.sleep(delay)
        
        # Get current pattern
        pattern = self._get_current_pattern()
        
        # Run collection with current pattern
        self._run_scheduled_collection(pattern, "daily")
    
    def _weekly_comprehensive_collection(self):
        """Weekly comprehensive collection."""
        logger.info("📊 Starting weekly comprehensive collection")
        
        # Use comprehensive pattern for weekly collection
        pattern = self.collection_patterns[0]  # comprehensive pattern
        
        # Run collection
        self._run_scheduled_collection(pattern, "weekly")
    
    def _check_pattern_rotation(self):
        """Check if pattern should be rotated."""
        days_since_change = (datetime.now() - self.last_pattern_change).days
        
        if days_since_change >= self.schedule_config['pattern_rotation_days']:
            self._rotate_pattern()
    
    def _rotate_pattern(self):
        """Rotate to next collection pattern."""
        self.current_pattern_index = (self.current_pattern_index + 1) % len(self.collection_patterns)
        self.last_pattern_change = datetime.now()
        
        new_pattern = self.collection_patterns[self.current_pattern_index]
        logger.info(f"🔄 Rotated to pattern: {new_pattern['name']}")
        logger.info(f"   Sources: {', '.join(new_pattern['sources'])}")
    
    def _get_current_pattern(self):
        """Get current collection pattern."""
        return self.collection_patterns[self.current_pattern_index]
    
    def _run_scheduled_collection(self, pattern, collection_type):
        """Run collection with specified pattern."""
        logger.info(f"🚀 Running {collection_type} collection with pattern: {pattern['name']}")
        
        try:
            # Adjust collector config for this pattern
            for source_config in self.collector.collection_config.values():
                if 'max_pages' in source_config and 'max_pages' in pattern['config']:
                    source_config['max_pages'] = pattern['config']['max_pages']
                if 'days_back' in source_config and 'days_back' in pattern['config']:
                    source_config['days_back'] = pattern['config']['days_back']
            
            # Run collection
            stats = self.collector.run_batch_collection(sources=pattern['sources'])
            
            logger.info(f"✅ {collection_type.capitalize()} collection complete")
            logger.info(f"   📊 Items: {stats['total_items']}")
            logger.info(f"   👥 Entities: {stats['entities_created']}")
            logger.info(f"   📄 Reports: {stats['reports_generated']}")
            
        except Exception as e:
            logger.error(f"❌ Error in {collection_type} collection: {e}")
    
    def run_scheduler(self):
        """Run the scheduler continuously."""
        logger.info("🔄 Starting smart scheduler")
        self.setup_schedule()
        
        logger.info("⏰ Scheduler running... Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
    
    def run_manual_collection(self, pattern_name=None):
        """Run manual collection with specified pattern."""
        if pattern_name:
            pattern = next((p for p in self.collection_patterns if p['name'] == pattern_name), None)
            if not pattern:
                logger.error(f"❌ Pattern '{pattern_name}' not found")
                return
        else:
            pattern = self._get_current_pattern()
        
        logger.info(f"🔧 Manual collection with pattern: {pattern['name']}")
        self._run_scheduled_collection(pattern, "manual")
    
    def get_schedule_status(self):
        """Get current schedule status."""
        next_run = schedule.next_run()
        current_pattern = self._get_current_pattern()
        
        logger.info("📅 Schedule Status:")
        logger.info(f"   ⏰ Next run: {next_run}")
        logger.info(f"   🎯 Current pattern: {current_pattern['name']}")
        logger.info(f"   📡 Sources: {', '.join(current_pattern['sources'])}")
        logger.info(f"   🔄 Last pattern change: {self.last_pattern_change}")


def main():
    """Main function for smart scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Collection Scheduler')
    parser.add_argument('--run', action='store_true',
                       help='Run scheduler continuously')
    parser.add_argument('--manual', type=str,
                       choices=['comprehensive', 'focused', 'news_focused', 'academic'],
                       help='Run manual collection with specified pattern')
    parser.add_argument('--status', action='store_true',
                       help='Show schedule status')
    parser.add_argument('--test', action='store_true',
                       help='Test collection with current pattern')
    
    args = parser.parse_args()
    
    scheduler = SmartScheduler()
    
    if args.run:
        scheduler.run_scheduler()
    elif args.manual:
        scheduler.run_manual_collection(args.manual)
    elif args.status:
        scheduler.get_schedule_status()
    elif args.test:
        scheduler.run_manual_collection()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
