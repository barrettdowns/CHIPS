"""
Review queue management for low confidence items.
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from database.db import DatabaseOperations
from database.models import ReviewStatus


def main():
    """Manage review queue."""
    parser = argparse.ArgumentParser(description='Manage CHIPS Act Review Queue')
    parser.add_argument('--list', action='store_true', help='List items in review queue')
    parser.add_argument('--resolve', type=int, help='Resolve review item by ID')
    parser.add_argument('--notes', type=str, help='Notes for resolution')
    parser.add_argument('--status', type=str, choices=['pending', 'reviewed', 'resolved'],
                       default='resolved', help='Status to set when resolving')
    
    args = parser.parse_args()
    
    # Initialize components
    db_ops = DatabaseOperations()
    
    try:
        if args.list:
            review_items = db_ops.db_manager.get_review_queue()
            logger.info(f"Review queue: {len(review_items)} items")
            
            for item in review_items:
                entity = db_ops.db_manager.get_entity_by_id(item.entity_id)
                entity_name = entity.name if entity else f"Entity {item.entity_id}"
                
                logger.info(f"  ID: {item.id}")
                logger.info(f"    Entity: {entity_name}")
                logger.info(f"    Issue: {item.issue_type}")
                logger.info(f"    Confidence: {item.confidence_score:.2f}")
                logger.info(f"    Status: {item.status.value}")
                logger.info(f"    Notes: {item.notes}")
                logger.info("")
        
        elif args.resolve:
            notes = args.notes or "Resolved via CLI"
            db_ops.db_manager.mark_review_item_resolved(args.resolve, notes)
            logger.info(f"Resolved review item {args.resolve}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Review queue management failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
