#!/usr/bin/env python3
"""
Batch Entity Enrichment Script

Uses AI to enrich all entities in the database with missing company information.
This script processes entities in batches to avoid API rate limits.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.ai_company_enricher import AICompanyEnricher
from loguru import logger


def main():
    """Main batch enrichment function."""
    print("🤖 Batch Entity Enrichment Script")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize components
    db = DatabaseOperations()
    enricher = AICompanyEnricher(api_key=api_key)
    
    # Get all entities
    entities = db.get_all_entities()
    print(f"📊 Found {len(entities)} entities to enrich")
    
    if len(entities) == 0:
        print("❌ No entities found in database")
        return
    
    # Check which entities need enrichment
    entities_to_enrich = []
    already_enriched = []
    
    for entity in entities:
        if entity.headquarters:
            already_enriched.append(entity)
        else:
            entities_to_enrich.append(entity)
    
    print(f"✅ Already enriched: {len(already_enriched)}")
    print(f"🔄 Need enrichment: {len(entities_to_enrich)}")
    
    if len(entities_to_enrich) == 0:
        print("🎉 All entities already enriched!")
        return
    
    # Process entities in batches
    batch_size = 10  # Process 10 entities at a time
    total_batches = (len(entities_to_enrich) + batch_size - 1) // batch_size
    
    print(f"\\n🚀 Starting batch enrichment...")
    print(f"📦 Processing {len(entities_to_enrich)} entities in {total_batches} batches of {batch_size}")
    
    enriched_count = 0
    failed_count = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(entities_to_enrich))
        batch_entities = entities_to_enrich[start_idx:end_idx]
        
        print(f"\\n📦 Batch {batch_num + 1}/{total_batches} ({len(batch_entities)} entities)")
        
        for i, entity in enumerate(batch_entities, 1):
            print(f"  🔍 {i}/{len(batch_entities)}: {entity.name}")
            
            try:
                # Enrich entity
                company_info = enricher.enrich_entity(entity)
                
                # Update database
                success = db.update_entity_info(entity.id, company_info)
                
                if success:
                    enriched_count += 1
                    print(f"    ✅ Enriched: {company_info.headquarters}")
                else:
                    failed_count += 1
                    print(f"    ❌ Database update failed")
                
                # Add delay between entities to avoid rate limiting
                if i < len(batch_entities):
                    time.sleep(2)  # 2 second delay
                    
            except Exception as e:
                failed_count += 1
                print(f"    ❌ Error: {e}")
        
        # Add delay between batches
        if batch_num < total_batches - 1:
            print(f"  ⏳ Waiting 5 seconds before next batch...")
            time.sleep(5)
    
    # Final summary
    print(f"\\n🎉 Batch Enrichment Complete!")
    print(f"  ✅ Successfully enriched: {enriched_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"  📊 Total processed: {enriched_count + failed_count}")
    
    # Check final status
    final_entities = db.get_all_entities()
    enriched_final = sum(1 for e in final_entities if e.headquarters)
    
    print(f"\\n📈 Final Database Status:")
    print(f"  - Total entities: {len(final_entities)}")
    print(f"  - Enriched entities: {enriched_final}")
    print(f"  - Completion rate: {(enriched_final/len(final_entities)*100):.1f}%")
    
    if enriched_final > 0:
        print(f"\\n🔄 Next step: Regenerate all reports with enriched data")
        print(f"Run: python scripts/generate_reports.py --all")


if __name__ == "__main__":
    main()
