"""
Debug script to examine CHIPS.gov HTML structure.
"""

import sys
from pathlib import Path
from loguru import logger
import requests
from bs4 import BeautifulSoup

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.chips_gov import CHIPSGovCollector


def main():
    """Debug CHIPS.gov HTML structure."""
    logger.info("Examining CHIPS.gov HTML structure...")
    
    # Create a CHIPS collector to get the page
    collector = CHIPSGovCollector()
    
    # Get the news page
    url = "https://www.chips.gov/news-and-updates"
    response = collector._make_request(url, collector._get_source_config("chips_gov"))
    
    if response:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for common container patterns
        logger.info("Looking for announcement containers...")
        
        # Try different selectors
        selectors_to_try = [
            'article',
            'div[class*="news"]',
            'div[class*="announcement"]',
            'div[class*="post"]',
            'div[class*="item"]',
            'div[class*="entry"]',
            'div[class*="card"]',
            '.news-item',
            '.announcement',
            '.post',
            '.entry',
            '.card'
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                if len(elements) > 0:
                    logger.info(f"First element classes: {elements[0].get('class', [])}")
                    logger.info(f"First element text preview: {elements[0].get_text()[:100]}...")
                    break
        
        # Look for headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        logger.info(f"Found {len(headings)} headings")
        for i, heading in enumerate(headings[:5]):
            logger.info(f"  Heading {i+1}: {heading.get_text().strip()}")
        
        # Look for links
        links = soup.find_all('a', href=True)
        logger.info(f"Found {len(links)} links")
        for i, link in enumerate(links[:5]):
            logger.info(f"  Link {i+1}: {link.get_text().strip()} -> {link['href']}")
        
        # Save HTML for inspection
        with open('debug_chips.html', 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        logger.info("Saved HTML to debug_chips.html")
    
    else:
        logger.error("Failed to fetch CHIPS.gov page")


if __name__ == '__main__':
    main()
