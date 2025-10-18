#!/usr/bin/env python3
"""
AI Capability Classifier - Plug and Play Test
Test the AI classifier as a drop-in replacement without affecting existing system.
"""

import os
import sys
import json
from pathlib import Path
from loguru import logger
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ai_capability_classifier import AICapabilityClassifier
from src.database.db import DatabaseOperations
from src.database.models import Entity, CapabilityType


class AIClassifierTester:
    """Test AI classifier as drop-in replacement."""
    
    def __init__(self, api_key: str):
        self.ai_classifier = AICapabilityClassifier(api_key)
        self.db_ops = DatabaseOperations()
        
        # Create test results directory
        self.test_dir = Path("ai_test_results")
        self.test_dir.mkdir(exist_ok=True)
        
        logger.info("AI Classifier Tester initialized")
    
    def test_single_entity(self, entity_id: int) -> dict:
        """Test AI classification on a single entity."""
        logger.info(f"Testing AI classification for entity {entity_id}")
        
        try:
            # Get entity data
            entity_summary = self.db_ops.get_entity_summary(entity_id)
            if not entity_summary:
                return {'error': 'Entity not found'}
            
            entity = entity_summary['entity']
            
            # Get existing capabilities for comparison
            existing_capabilities = entity_summary['capabilities']
            
            # Prepare content sources (mock for testing)
            content_sources = self._prepare_test_content_sources(entity_summary)
            
            # Test AI classification
            ai_capabilities = self.ai_classifier.classify_entity(entity, content_sources)
            
            # Compare results
            comparison = self._compare_classifications(existing_capabilities, ai_capabilities)
            
            # Save test results
            test_result = {
                'entity_id': entity_id,
                'entity_name': entity.name,
                'test_timestamp': datetime.now().isoformat(),
                'existing_capabilities': [
                    {
                        'type': cap.capability_type.name,
                        'confidence': cap.confidence_score,
                        'evidence': cap.evidence[:200] + '...' if len(cap.evidence) > 200 else cap.evidence
                    }
                    for cap in existing_capabilities
                ],
                'ai_capabilities': [
                    {
                        'type': cap.capability_type.name,
                        'confidence': cap.confidence_score,
                        'evidence': cap.evidence[:200] + '...' if len(cap.evidence) > 200 else cap.evidence
                    }
                    for cap in ai_capabilities
                ],
                'comparison': comparison
            }
            
            # Save to file
            result_file = self.test_dir / f"entity_{entity_id}_test.json"
            with open(result_file, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            logger.info(f"Test results saved to {result_file}")
            return test_result
            
        except Exception as e:
            logger.error(f"Test failed for entity {entity_id}: {e}")
            return {'error': str(e)}
    
    def test_multiple_entities(self, entity_ids: list = None, limit: int = 5) -> dict:
        """Test AI classification on multiple entities."""
        logger.info(f"Testing AI classification on multiple entities")
        
        if entity_ids is None:
            # Get entities from database
            entities = self.db_ops.search_entities("")
            entity_ids = [entity.id for entity in entities[:limit]]
        
        results = {
            'total_tested': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'improvements': 0,
            'new_capabilities': 0,
            'test_results': []
        }
        
        for entity_id in entity_ids:
            try:
                test_result = self.test_single_entity(entity_id)
                
                if 'error' not in test_result:
                    results['successful_tests'] += 1
                    results['test_results'].append(test_result)
                    
                    # Count improvements
                    comparison = test_result.get('comparison', {})
                    results['improvements'] += comparison.get('improvements', 0)
                    results['new_capabilities'] += comparison.get('new_capabilities', 0)
                else:
                    results['failed_tests'] += 1
                
                results['total_tested'] += 1
                
            except Exception as e:
                logger.error(f"Failed to test entity {entity_id}: {e}")
                results['failed_tests'] += 1
                results['total_tested'] += 1
        
        # Save summary
        summary_file = self.test_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Test summary saved to {summary_file}")
        return results
    
    def _prepare_test_content_sources(self, entity_summary: dict) -> list:
        """Prepare test content sources from entity summary."""
        content_sources = []
        
        # Use funding information
        funding = entity_summary.get('funding', [])
        for fund in funding:
            content_sources.append({
                'content': fund.project_description or '',
                'project_description': fund.project_description or '',
                'funding_amount': fund.amount or 0,
                'collected_at': fund.announcement_date.isoformat() if fund.announcement_date else datetime.now().isoformat()
            })
        
        # Use data sources
        data_sources = entity_summary.get('data_sources', [])
        for source in data_sources:
            content_sources.append({
                'content': source.raw_data or '',
                'project_description': '',
                'funding_amount': 0,
                'collected_at': source.collected_at.isoformat() if source.collected_at else datetime.now().isoformat()
            })
        
        # If no content sources, create mock data
        if not content_sources:
            entity = entity_summary['entity']
            content_sources.append({
                'content': f"Test content for {entity.name}",
                'project_description': f"Project description for {entity.name}",
                'funding_amount': 100,
                'collected_at': datetime.now().isoformat()
            })
        
        return content_sources
    
    def _compare_classifications(self, existing: list, ai_enhanced: list) -> dict:
        """Compare existing vs AI-enhanced classifications."""
        comparison = {
            'existing_count': len(existing),
            'ai_count': len(ai_enhanced),
            'improvements': 0,
            'new_capabilities': 0,
            'improved_confidence': 0,
            'details': []
        }
        
        # Count new capabilities
        existing_types = {cap.capability_type for cap in existing}
        ai_types = {cap.capability_type for cap in ai_enhanced}
        
        new_capabilities = ai_types - existing_types
        comparison['new_capabilities'] = len(new_capabilities)
        
        # Count improved confidence scores
        for ai_cap in ai_enhanced:
            for existing_cap in existing:
                if (ai_cap.capability_type == existing_cap.capability_type and 
                    ai_cap.confidence_score > existing_cap.confidence_score + 0.1):
                    comparison['improved_confidence'] += 1
                    comparison['details'].append({
                        'type': ai_cap.capability_type.name,
                        'existing_confidence': existing_cap.confidence_score,
                        'ai_confidence': ai_cap.confidence_score,
                        'improvement': ai_cap.confidence_score - existing_cap.confidence_score
                    })
        
        comparison['improvements'] = comparison['new_capabilities'] + comparison['improved_confidence']
        
        return comparison
    
    def generate_test_report(self, test_results: dict) -> str:
        """Generate a human-readable test report."""
        report = f"""
AI Capability Classifier Test Report
====================================

Test Summary:
- Total entities tested: {test_results['total_tested']}
- Successful tests: {test_results['successful_tests']}
- Failed tests: {test_results['failed_tests']}
- Total improvements: {test_results['improvements']}
- New capabilities found: {test_results['new_capabilities']}

Detailed Results:
"""
        
        for result in test_results['test_results']:
            report += f"""
Entity: {result['entity_name']} (ID: {result['entity_id']})
--------------------------------------------------------
Existing capabilities: {len(result['existing_capabilities'])}
AI capabilities: {len(result['ai_capabilities'])}
Improvements: {result['comparison']['improvements']}
New capabilities: {result['comparison']['new_capabilities']}
Improved confidence: {result['comparison']['improved_confidence']}

"""
        
        return report


def main():
    """Main function for testing AI classifier."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test AI Capability Classifier')
    parser.add_argument('--api-key', required=True, help='OpenAI API key')
    parser.add_argument('--entity-id', type=int, help='Test specific entity ID')
    parser.add_argument('--test-all', action='store_true', help='Test all entities')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of entities to test')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = AIClassifierTester(args.api_key)
    
    if args.entity_id:
        # Test single entity
        logger.info(f"Testing single entity: {args.entity_id}")
        result = tester.test_single_entity(args.entity_id)
        
        if 'error' not in result:
            print(f"\n✅ Test successful for {result['entity_name']}")
            print(f"Existing capabilities: {len(result['existing_capabilities'])}")
            print(f"AI capabilities: {len(result['ai_capabilities'])}")
            print(f"Improvements: {result['comparison']['improvements']}")
        else:
            print(f"❌ Test failed: {result['error']}")
    
    elif args.test_all:
        # Test multiple entities
        logger.info("Testing multiple entities")
        results = tester.test_multiple_entities(limit=args.limit)
        
        print(f"\n{'='*50}")
        print(f"AI CLASSIFIER TEST RESULTS")
        print(f"{'='*50}")
        print(f"Total tested: {results['total_tested']}")
        print(f"Successful: {results['successful_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Total improvements: {results['improvements']}")
        print(f"New capabilities: {results['new_capabilities']}")
        
        # Generate report
        report = tester.generate_test_report(results)
        report_file = tester.test_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        if results['improvements'] > 0:
            print(f"✅ AI classifier shows improvements!")
        else:
            print(f"⚠️ No improvements detected - may need tuning")
    
    else:
        print("Please specify --entity-id or --test-all")


if __name__ == "__main__":
    main()
