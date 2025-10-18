"""
Database initialization script.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations


def main():
    """Initialize the database."""
    print("Initializing CHIPS Act Entity Tracking Database...")
    
    # Create database operations instance
    db_ops = DatabaseOperations()
    
    # Initialize database
    db_ops.initialize_database()
    
    # Get and display statistics
    stats = db_ops.get_database_stats()
    
    print("\nDatabase initialized successfully!")
    print(f"Database location: {db_ops.db_path}")
    print("\nInitial statistics:")
    print(f"- Entities by type: {stats.get('entities_by_type', {})}")
    total_funding = stats.get('total_funding', 0) or 0
    print(f"- Total funding: ${total_funding:,.2f}")
    print(f"- Capabilities: {stats.get('capabilities', {})}")
    print(f"- Review queue: {stats.get('review_queue', {})}")


if __name__ == "__main__":
    main()
