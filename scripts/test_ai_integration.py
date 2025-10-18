#!/usr/bin/env python3
"""
Cost-Effective AI Integration Test Script
Test AI enhancement with budget controls
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.cost_effective_ai import CostEffectiveAIEnhancer, SmartAIOrchestrator
from src.database.db import DatabaseOperations
from src.database.models import Entity


def test_ai_integration(api_key: str, test_budget: float = 2.0):
    """Test AI integration with budget controls."""
    
    logger.info(f"Testing AI integration with ${test_budget} budget")
    
    # Initialize cost-effective AI enhancer
    ai_enhancer = CostEffectiveAIEnhancer(api_key, daily_budget=test_budget)
    
    # Get some test entities from database
    db_ops = DatabaseOperations()
    entities = db_ops.search_entities("")[:5]  # Test with first 5 entities
    
    if not entities:
        logger.warning("No entities found in database for testing")
        return
    
    logger.info(f"Testing with {len(entities)} entities")
    
    # Test each entity
    for entity in entities:
        logger.info(f"Testing entity: {entity.name}")
        
        # Get entity content (mock data for testing)
        mock_content = [
            {
                'content': f"Test content for {entity.name}",
                'project_description': f"Project description for {entity.name}",
                'funding_amount': 100 if 'Intel' in entity.name else 25
            }
        ]
        
        # Test hybrid classification
        capabilities = ai_enhancer.classify_entity_hybrid(entity, mock_content)
        
        logger.info(f"Found {len(capabilities)} capabilities for {entity.name}")
        
        # Check cost tracking
        cost_summary = ai_enhancer.get_cost_summary()
        logger.info(f"Current cost: ${cost_summary['cost_estimate']:.4f}")
        
        # Stop if budget exceeded
        if cost_summary['cost_estimate'] >= test_budget:
            logger.warning("Budget exceeded, stopping test")
            break
    
    # Final cost summary
    final_summary = ai_enhancer.get_cost_summary()
    
    print(f"\n{'='*50}")
    print(f"AI INTEGRATION TEST RESULTS")
    print(f"{'='*50}")
    print(f"Entities tested: {len(entities)}")
    print(f"Total cost: ${final_summary['cost_estimate']:.4f}")
    print(f"Requests made: {final_summary['requests_made']}")
    print(f"Budget utilization: {final_summary['budget_utilization']:.1f}%")
    print(f"Cost per entity: ${final_summary['cost_estimate']/len(entities):.4f}")
    
    if final_summary['cost_estimate'] < test_budget:
        print(f"✅ Test successful - within budget!")
    else:
        print(f"⚠️ Budget exceeded - consider reducing scope")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test cost-effective AI integration')
    parser.add_argument('--api-key', required=True, help='OpenAI API key')
    parser.add_argument('--budget', type=float, default=2.0, help='Test budget in dollars')
    
    args = parser.parse_args()
    
    # Test AI integration
    test_ai_integration(args.api_key, args.budget)


if __name__ == "__main__":
    main()
