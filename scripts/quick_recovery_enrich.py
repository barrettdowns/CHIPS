#!/usr/bin/env python3
"""
Quick Entity Recovery and Enrichment Script

Recovers entities from existing reports and enriches them with AI.
This is much faster than re-collecting from scratch.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import Entity, EntityType
from src.ai_company_enricher import AICompanyEnricher
from loguru import logger


def extract_entity_names_from_reports():
    """Extract entity names from existing report files."""
    reports_dir = Path('reports/entities')
    report_files = list(reports_dir.glob('*_report.md'))
    
    entity_names = []
    for report_file in report_files:
        try:
            with open(report_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                if lines:
                    title = lines[0].strip('# ').strip()
                    # Clean up HTML entities
                    title = title.replace('&amp;', '&')
                    entity_names.append(title)
        except Exception as e:
            logger.error(f"Error reading {report_file}: {e}")
    
    return entity_names


def create_entities_in_database(entity_names):
    """Create Entity objects in database from names."""
    db = DatabaseOperations()
    created_entities = []
    
    print(f"💾 Creating {len(entity_names)} entities in database...")
    
    for i, name in enumerate(entity_names, 1):
        print(f"  {i}/{len(entity_names)}: {name}")
        
        # Create entity
        entity = Entity(
            name=name,
            legal_name=name,
            entity_type=EntityType.COMPANY,  # Default to company
            confidence_score=0.5
        )
        
        # Insert into database
        try:
            entity_id = db.add_entity_with_sources(entity, [])
            entity.id = entity_id
            created_entities.append(entity)
        except Exception as e:
            logger.error(f"Error creating entity {name}: {e}")
    
    print(f"✅ Created {len(created_entities)} entities")
    return created_entities


def enrich_all_entities(entities, api_key):
    """Enrich all entities with AI-powered company information."""
    enricher = AICompanyEnricher(api_key=api_key)
    db = DatabaseOperations()
    
    print(f"🤖 Enriching {len(entities)} entities with AI...")
    
    enriched_count = 0
    failed_count = 0
    
    for i, entity in enumerate(entities, 1):
        print(f"  {i}/{len(entities)}: {entity.name}")
        
        try:
            # Enrich entity
            company_info = enricher.enrich_entity(entity)
            
            # Update database
            success = db.update_entity_info(entity.id, company_info)
            
            if success:
                enriched_count += 1
                print(f"    ✅ {company_info.headquarters}")
            else:
                failed_count += 1
                print(f"    ❌ Database update failed")
            
            # Add delay to avoid rate limiting
            if i < len(entities):
                time.sleep(2)  # 2 second delay
                
        except Exception as e:
            failed_count += 1
            print(f"    ❌ Error: {e}")
    
    print(f"\\n🎉 Enrichment Complete!")
    print(f"  ✅ Successfully enriched: {enriched_count}")
    print(f"  ❌ Failed: {failed_count}")
    
    return enriched_count, failed_count


def main():
    """Main function."""
    print("🚀 Quick Entity Recovery and Enrichment")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Step 1: Extract entity names from existing reports
    print("📄 Step 1: Extracting entity names from existing reports...")
    entity_names = extract_entity_names_from_reports()
    print(f"✅ Found {len(entity_names)} entity names")
    
    # Step 2: Create entities in database
    print("\\n💾 Step 2: Creating entities in database...")
    entities = create_entities_in_database(entity_names)
    
    # Step 3: Enrich entities with AI
    print("\\n🤖 Step 3: Enriching entities with AI...")
    enriched_count, failed_count = enrich_all_entities(entities, api_key)
    
    # Final summary
    print(f"\\n🎉 Process Complete!")
    print(f"  📊 Total entities: {len(entities)}")
    print(f"  ✅ Enriched: {enriched_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"  📈 Success rate: {(enriched_count/len(entities)*100):.1f}%")
    
    print(f"\\n🔄 Next step: Regenerate all reports with enriched data")
    print(f"Run: python scripts/generate_reports.py --all")
    
    print(f"\\n📋 This approach is much faster than re-collecting!")
    print(f"  - No web scraping delays")
    print(f"  - No rate limiting issues")
    print(f"  - Direct AI enrichment")
    print(f"  - Ready for customer delivery!")


if __name__ == "__main__":
    main()
