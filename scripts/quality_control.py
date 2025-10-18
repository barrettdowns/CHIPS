"""
Quality Control System - Phase 3
Automated review queue management, confidence scoring, and manual review interface.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import ReviewStatus, ReviewPriority


class QualityControlManager:
    """Quality control system for automated review and confidence scoring."""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        
        # Quality thresholds
        self.thresholds = {
            'auto_approve_confidence': 0.85,  # Auto-approve above 85%
            'auto_reject_confidence': 0.30,   # Auto-reject below 30%
            'manual_review_confidence': 0.70,  # Manual review between 30-85%
            'funding_amount_threshold': 1000000,  # $1M threshold for funding review
            'entity_name_similarity': 0.80,   # 80% similarity for entity matching
        }
        
        # Review priorities
        self.priority_weights = {
            'funding_amount': 0.3,
            'confidence_score': 0.4,
            'source_reliability': 0.2,
            'entity_completeness': 0.1
        }
    
    def process_review_queue(self):
        """Process the review queue with automated decisions."""
        logger.info("🔍 Processing review queue...")
        
        # Get items needing review
        review_items = self.db_ops.db_manager.get_review_items_by_status(ReviewStatus.PENDING)
        
        if not review_items:
            logger.info("✅ No items in review queue")
            return
        
        logger.info(f"📋 Processing {len(review_items)} review items")
        
        auto_approved = 0
        auto_rejected = 0
        manual_review = 0
        
        for item in review_items:
            decision = self._make_automated_decision(item)
            
            if decision['action'] == 'approve':
                self._approve_item(item, decision['reason'])
                auto_approved += 1
            elif decision['action'] == 'reject':
                self._reject_item(item, decision['reason'])
                auto_rejected += 1
            else:  # manual_review
                self._flag_for_manual_review(item, decision['reason'])
                manual_review += 1
        
        logger.info(f"✅ Review processing complete:")
        logger.info(f"   ✅ Auto-approved: {auto_approved}")
        logger.info(f"   ❌ Auto-rejected: {auto_rejected}")
        logger.info(f"   👤 Manual review: {manual_review}")
    
    def _make_automated_decision(self, item):
        """Make automated decision for review item."""
        confidence = item.confidence_score or 0.0
        
        # High confidence - auto approve
        if confidence >= self.thresholds['auto_approve_confidence']:
            return {
                'action': 'approve',
                'reason': f'High confidence ({confidence:.2f})'
            }
        
        # Low confidence - auto reject
        if confidence <= self.thresholds['auto_reject_confidence']:
            return {
                'action': 'reject',
                'reason': f'Low confidence ({confidence:.2f})'
            }
        
        # Check for high-value funding that needs manual review
        if item.item_type == 'funding' and item.funding_amount:
            if item.funding_amount >= self.thresholds['funding_amount_threshold']:
                return {
                    'action': 'manual_review',
                    'reason': f'High-value funding (${item.funding_amount:,.0f})'
                }
        
        # Check for entity matching issues
        if item.item_type == 'entity' and item.entity_name:
            similar_entities = self._find_similar_entities(item.entity_name)
            if len(similar_entities) > 1:
                return {
                    'action': 'manual_review',
                    'reason': f'Potential duplicate entity ({len(similar_entities)} similar)'
                }
        
        # Medium confidence - manual review
        if confidence >= self.thresholds['manual_review_confidence']:
            return {
                'action': 'manual_review',
                'reason': f'Medium confidence ({confidence:.2f})'
            }
        
        # Default to manual review for edge cases
        return {
            'action': 'manual_review',
            'reason': 'Edge case requiring human review'
        }
    
    def _find_similar_entities(self, entity_name):
        """Find entities with similar names."""
        from src.entity_resolution.matcher import EntityResolver
        resolver = EntityResolver(self.db_ops.db_manager)
        
        # Get all entities
        all_entities = self.db_ops.db_manager.get_all_entities()
        
        # Find similar entities using fuzzy matching
        similar = []
        for entity in all_entities:
            similarity = resolver._calculate_similarity(entity_name, entity.name)
            if similarity >= self.thresholds['entity_name_similarity']:
                similar.append(entity)
        
        return similar
    
    def _approve_item(self, item, reason):
        """Approve a review item."""
        item.status = ReviewStatus.APPROVED
        item.reviewed_at = datetime.now()
        item.review_notes = f"Auto-approved: {reason}"
        
        self.db_ops.db_manager.update_review_item(item)
        logger.debug(f"✅ Approved: {item.item_type} - {reason}")
    
    def _reject_item(self, item, reason):
        """Reject a review item."""
        item.status = ReviewStatus.REJECTED
        item.reviewed_at = datetime.now()
        item.review_notes = f"Auto-rejected: {reason}"
        
        self.db_ops.db_manager.update_review_item(item)
        logger.debug(f"❌ Rejected: {item.item_type} - {reason}")
    
    def _flag_for_manual_review(self, item, reason):
        """Flag item for manual review."""
        item.priority = self._calculate_priority(item)
        item.review_notes = f"Flagged for manual review: {reason}"
        
        self.db_ops.db_manager.update_review_item(item)
        logger.debug(f"👤 Manual review: {item.item_type} - {reason}")
    
    def _calculate_priority(self, item):
        """Calculate priority score for manual review."""
        priority_score = 0.0
        
        # Funding amount weight
        if item.funding_amount:
            normalized_amount = min(item.funding_amount / 10000000, 1.0)  # Normalize to $10M max
            priority_score += normalized_amount * self.priority_weights['funding_amount']
        
        # Confidence score weight
        confidence = item.confidence_score or 0.0
        priority_score += confidence * self.priority_weights['confidence_score']
        
        # Source reliability weight (simplified)
        source_reliability = 0.8  # Default reliability
        if 'chips.gov' in (item.source_url or ''):
            source_reliability = 1.0
        elif 'sec.gov' in (item.source_url or ''):
            source_reliability = 0.9
        
        priority_score += source_reliability * self.priority_weights['source_reliability']
        
        # Entity completeness weight
        completeness = 0.5  # Default completeness
        if item.entity_name and item.funding_amount:
            completeness = 1.0
        
        priority_score += completeness * self.priority_weights['entity_completeness']
        
        # Convert to priority enum
        if priority_score >= 0.8:
            return ReviewPriority.HIGH
        elif priority_score >= 0.6:
            return ReviewPriority.MEDIUM
        else:
            return ReviewPriority.LOW
    
    def get_manual_review_items(self, priority=None, limit=50):
        """Get items requiring manual review."""
        filters = {'status': ReviewStatus.PENDING}
        if priority:
            filters['priority'] = priority
        
        items = self.db_ops.db_manager.get_review_items(filters, limit=limit)
        return items
    
    def manual_review_decision(self, item_id, decision, notes=None):
        """Process manual review decision."""
        item = self.db_ops.db_manager.get_review_item_by_id(item_id)
        if not item:
            logger.error(f"❌ Review item {item_id} not found")
            return False
        
        if decision == 'approve':
            item.status = ReviewStatus.APPROVED
        elif decision == 'reject':
            item.status = ReviewStatus.REJECTED
        else:
            logger.error(f"❌ Invalid decision: {decision}")
            return False
        
        item.reviewed_at = datetime.now()
        item.review_notes = notes or f"Manual review: {decision}"
        
        self.db_ops.db_manager.update_review_item(item)
        logger.info(f"✅ Manual review decision: {decision} for item {item_id}")
        
        return True
    
    def get_quality_metrics(self):
        """Get quality control metrics."""
        stats = self.db_ops.get_database_stats()
        
        # Review queue statistics
        pending_items = self.db_ops.db_manager.get_review_items_by_status(ReviewStatus.PENDING)
        approved_items = self.db_ops.db_manager.get_review_items_by_status(ReviewStatus.APPROVED)
        rejected_items = self.db_ops.db_manager.get_review_items_by_status(ReviewStatus.REJECTED)
        
        # Calculate quality metrics
        total_reviewed = len(approved_items) + len(rejected_items)
        approval_rate = len(approved_items) / total_reviewed if total_reviewed > 0 else 0
        
        # Average confidence scores
        all_items = pending_items + approved_items + rejected_items
        avg_confidence = sum(item.confidence_score or 0 for item in all_items) / len(all_items) if all_items else 0
        
        metrics = {
            'pending_reviews': len(pending_items),
            'approved_items': len(approved_items),
            'rejected_items': len(rejected_items),
            'approval_rate': approval_rate,
            'average_confidence': avg_confidence,
            'total_entities': stats.get('total_entities', 0),
            'total_funding': stats.get('total_funding', 0),
            'data_quality_score': self._calculate_data_quality_score(stats)
        }
        
        return metrics
    
    def _calculate_data_quality_score(self, stats):
        """Calculate overall data quality score."""
        score = 0.0
        
        # Entity completeness
        entities_by_type = stats.get('entities_by_type', {})
        total_entities = sum(entities_by_type.values())
        if total_entities > 0:
            # Higher score for more diverse entity types
            diversity_score = len(entities_by_type) / 6.0  # 6 expected types
            score += diversity_score * 0.3
        
        # Funding coverage
        total_funding = stats.get('total_funding', 0)
        if total_funding > 0:
            # Higher score for more funding data
            funding_score = min(total_funding / 1000000000, 1.0)  # Normalize to $1B
            score += funding_score * 0.4
        
        # Review queue health
        pending_reviews = len(self.db_ops.db_manager.get_review_items_by_status(ReviewStatus.PENDING))
        if pending_reviews < 100:  # Healthy queue size
            queue_score = 1.0 - (pending_reviews / 100.0)
            score += queue_score * 0.3
        
        return min(score, 1.0)  # Cap at 1.0


def main():
    """Main function for quality control."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quality Control System')
    parser.add_argument('--process', action='store_true',
                       help='Process review queue automatically')
    parser.add_argument('--manual-review', action='store_true',
                       help='Show items for manual review')
    parser.add_argument('--approve', type=int,
                       help='Approve review item by ID')
    parser.add_argument('--reject', type=int,
                       help='Reject review item by ID')
    parser.add_argument('--metrics', action='store_true',
                       help='Show quality metrics')
    parser.add_argument('--priority', type=str,
                       choices=['HIGH', 'MEDIUM', 'LOW'],
                       help='Filter manual review by priority')
    
    args = parser.parse_args()
    
    qc_manager = QualityControlManager()
    
    if args.process:
        qc_manager.process_review_queue()
    elif args.manual_review:
        items = qc_manager.get_manual_review_items(priority=args.priority)
        logger.info(f"👤 {len(items)} items need manual review")
        for item in items[:10]:  # Show first 10
            logger.info(f"   ID: {item.id} | {item.item_type} | Priority: {item.priority} | Confidence: {item.confidence_score:.2f}")
    elif args.approve:
        success = qc_manager.manual_review_decision(args.approve, 'approve')
        if success:
            logger.info(f"✅ Approved item {args.approve}")
    elif args.reject:
        success = qc_manager.manual_review_decision(args.reject, 'reject')
        if success:
            logger.info(f"❌ Rejected item {args.reject}")
    elif args.metrics:
        metrics = qc_manager.get_quality_metrics()
        logger.info("📊 Quality Control Metrics:")
        logger.info(f"   📋 Pending reviews: {metrics['pending_reviews']}")
        logger.info(f"   ✅ Approval rate: {metrics['approval_rate']:.1%}")
        logger.info(f"   🎯 Avg confidence: {metrics['average_confidence']:.2f}")
        logger.info(f"   📈 Data quality score: {metrics['data_quality_score']:.2f}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
