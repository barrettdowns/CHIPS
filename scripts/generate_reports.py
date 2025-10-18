"""
Generate reports for entities and capability clusters.
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import CapabilityType
from src.report_generator.entity_report import ReportGenerator


def main():
    """Generate reports."""
    parser = argparse.ArgumentParser(description='Generate CHIPS Act Entity Reports')
    parser.add_argument('--entity-id', type=int, help='Generate report for specific entity ID')
    parser.add_argument('--capability', type=str, choices=[ct.name for ct in CapabilityType],
                       help='Generate cluster report for specific capability')
    parser.add_argument('--all', action='store_true', help='Generate all reports')
    parser.add_argument('--entities', action='store_true', help='Generate all entity reports')
    parser.add_argument('--clusters', action='store_true', help='Generate all cluster reports')
    
    args = parser.parse_args()
    
    # Initialize components
    db_ops = DatabaseOperations()
    report_generator = ReportGenerator(db_ops)
    
    try:
        if args.entity_id:
            report_path = report_generator.generate_entity_report(args.entity_id)
            logger.info(f"Entity report generated: {report_path}")
        
        elif args.capability:
            capability_type = CapabilityType[args.capability]
            report_path = report_generator.generate_capability_cluster_report(capability_type)
            logger.info(f"Cluster report generated: {report_path}")
        
        elif args.all:
            entity_reports = report_generator.generate_all_entity_reports()
            cluster_reports = report_generator.generate_all_cluster_reports()
            logger.info(f"Generated {len(entity_reports)} entity reports and {len(cluster_reports)} cluster reports")
        
        elif args.entities:
            entity_reports = report_generator.generate_all_entity_reports()
            logger.info(f"Generated {len(entity_reports)} entity reports")
        
        elif args.clusters:
            cluster_reports = report_generator.generate_all_cluster_reports()
            logger.info(f"Generated {len(cluster_reports)} cluster reports")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
