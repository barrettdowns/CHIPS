"""
Debug script to test CHIPS.gov scraping.
"""

import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.chips_gov import CHIPSGovCollector


def main():
    """Debug CHIPS.gov collection."""
    logger.info("Testing CHIPS.gov collection...")
    
    collector = CHIPSGovCollector()
    
    # Test collection with debug output
    results = collector.collect(max_pages=1)
    
    logger.info(f"Collected {len(results)} items")
    
    for i, item in enumerate(results):
        logger.info(f"Item {i+1}:")
        logger.info(f"  Title: {item.get('title', 'N/A')}")
        logger.info(f"  Date: {item.get('date', 'N/A')}")
        logger.info(f"  Content: {item.get('content', 'N/A')[:100]}...")
        logger.info(f"  Entities: {item.get('entities', [])}")
        logger.info(f"  Funding: {item.get('funding_amount', 'N/A')}")
        logger.info("")


if __name__ == '__main__':
    main()
