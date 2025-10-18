"""
Database models and schema for CHIPS Act entity tracking system.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class EntityType(Enum):
    """Entity type enumeration."""
    COMPANY = "company"
    CONSORTIUM = "consortium"
    UNIVERSITY = "university"
    GOVERNMENT = "government"
    OTHER = "other"


class RelationshipType(Enum):
    """Relationship type enumeration."""
    PARENT_SUBSIDIARY = "parent_subsidiary"
    CONSORTIUM_MEMBER = "consortium_member"
    PARTNER = "partner"
    SUBCONTRACTOR = "subcontractor"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    OTHER = "other"


class CapabilityType(Enum):
    """Capability area enumeration."""
    THREE_D_PACKAGING = 1      # 3D Packaging
    HETEROGENEOUS_PACKAGING = 2 # Heterogeneous Packaging  
    MULTI_PROJECT_WAFER = 3    # Multi Project Wafer
    RFIC_DESIGN = 4            # Radio Frequency Integrated Circuit Design
    MMIC_CHIPS = 5             # Monolithic Microwave Integrated Circuit Chips
    RAD_HARD_CHIPS = 6         # Radiation Hardened Chips


class ReviewStatus(Enum):
    """Review queue status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class ReviewPriority(Enum):
    """Review priority enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ReviewItem:
    """Review queue item data model."""
    id: Optional[int] = None
    entity_id: Optional[int] = None
    item_type: str = field(default_factory=lambda: "")
    item_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    status: ReviewStatus = field(default=ReviewStatus.PENDING)
    priority: ReviewPriority = field(default=ReviewPriority.MEDIUM)
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    funding_amount: Optional[float] = None
    entity_name: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class ReviewQueue:
    """Review queue data model."""
    id: Optional[int] = None
    entity_id: Optional[int] = None
    item_type: str = field(default_factory=lambda: "")
    item_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    status: ReviewStatus = field(default=ReviewStatus.PENDING)
    priority: ReviewPriority = field(default=ReviewPriority.MEDIUM)
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    funding_amount: Optional[float] = None
    entity_name: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class Entity:
    """Entity data model."""
    id: Optional[int] = None
    name: str = field(default_factory=lambda: "")
    legal_name: str = field(default_factory=lambda: "")
    entity_type: EntityType = field(default=EntityType.COMPANY)
    confidence_score: float = field(default_factory=lambda: 0.0)
    # Enhanced fields for professional template
    headquarters: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[str] = None
    revenue: Optional[str] = None
    founded: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    parent_company: Optional[str] = None
    subsidiaries: Optional[str] = None  # JSON string of list
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FundingStatus(Enum):
    """Funding status enumeration."""
    ANNOUNCED = "announced"           # Publicly announced but not yet disbursed
    PENDING_NEGOTIATION = "pending_negotiation"  # Selected for negotiation
    AWARDED = "awarded"              # Officially awarded and disbursed
    COMPLETED = "completed"           # Project completed
    CANCELLED = "cancelled"          # Funding cancelled
    UNKNOWN = "unknown"               # Status unclear


class FundingCategory(Enum):
    """Funding category enumeration."""
    MANUFACTURING = "manufacturing"           # New fabrication plants (fabs)
    RESEARCH_DEVELOPMENT = "research_development"  # R&D programs
    WORKFORCE_DEVELOPMENT = "workforce_development"  # Training and education
    SUPPLY_CHAIN = "supply_chain"             # Supply chain capacity expansion
    INFRASTRUCTURE = "infrastructure"         # Supporting infrastructure
    OTHER = "other"                           # Other categories


@dataclass
class Funding:
    """Enhanced funding data model with comprehensive CHIPS Act fields."""
    id: Optional[int] = None
    entity_id: int = field(default_factory=lambda: 0)
    amount: Optional[float] = None
    currency: str = field(default_factory=lambda: "USD")
    announcement_date: Optional[datetime] = None
    project_description: str = field(default_factory=lambda: "")
    source_url: str = field(default_factory=lambda: "")
    created_at: Optional[datetime] = None
    
    # Enhanced fields for comprehensive funding tracking
    program_name: Optional[str] = None        # CHIPS Act program name
    grant_id: Optional[str] = None           # Official grant/award ID
    funding_status: FundingStatus = field(default=FundingStatus.UNKNOWN)  # Current status
    funding_category: FundingCategory = field(default=FundingCategory.OTHER)  # Project category
    funding_phase: Optional[str] = None       # Phase of funding (e.g., "Phase 1", "Initial")
    disbursement_date: Optional[datetime] = None  # When funds were actually disbursed
    completion_date: Optional[datetime] = None     # Project completion date
    project_location: Optional[str] = None    # Geographic location of project
    matching_funds: Optional[float] = None    # Required matching funds amount
    jobs_created: Optional[int] = None        # Expected/actual jobs created
    confidence_score: float = field(default_factory=lambda: 0.0)             # Confidence in funding data accuracy
    verification_status: str = field(default_factory=lambda: "unverified")   # Data verification status
    notes: Optional[str] = None               # Additional notes or context


@dataclass
class Capability:
    """Capability data model."""
    id: Optional[int] = None
    entity_id: int = field(default_factory=lambda: 0)
    capability_type: CapabilityType = field(default=CapabilityType.THREE_D_PACKAGING)
    confidence_score: float = field(default_factory=lambda: 0.0)
    evidence: str = field(default_factory=lambda: "")
    technical_details: str = field(default_factory=lambda: "")
    ai_insights: str = field(default_factory=lambda: "")
    created_at: Optional[datetime] = None


@dataclass
class Relationship:
    """Relationship data model."""
    id: Optional[int] = None
    entity_a_id: int = field(default_factory=lambda: 0)
    entity_b_id: int = field(default_factory=lambda: 0)
    relationship_type: RelationshipType = field(default=RelationshipType.OTHER)
    confidence_score: float = field(default_factory=lambda: 0.0)
    evidence: str = field(default_factory=lambda: "")
    created_at: Optional[datetime] = None


@dataclass
class DataSource:
    """Data source tracking model."""
    id: Optional[int] = None
    entity_id: int = field(default_factory=lambda: 0)
    source_type: str = field(default_factory=lambda: "")
    url: str = field(default_factory=lambda: "")
    collected_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class DatabaseManager:
    """SQLite database manager."""
    
    def __init__(self, db_path: str = "data/chips.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                legal_name TEXT,
                entity_type TEXT NOT NULL DEFAULT 'company',
                confidence_score REAL DEFAULT 0.0,
                -- Enhanced fields for professional template
                headquarters TEXT,
                website TEXT,
                employees TEXT,
                revenue TEXT,
                founded TEXT,
                description TEXT,
                industry TEXT,
                parent_company TEXT,
                subsidiaries TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funding (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                amount REAL,
                currency TEXT DEFAULT 'USD',
                announcement_date TIMESTAMP,
                project_description TEXT,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- Enhanced fields for comprehensive funding tracking
                program_name TEXT,
                grant_id TEXT,
                funding_status TEXT DEFAULT 'unknown',
                funding_category TEXT DEFAULT 'other',
                funding_phase TEXT,
                disbursement_date TIMESTAMP,
                completion_date TIMESTAMP,
                project_location TEXT,
                matching_funds REAL,
                jobs_created INTEGER,
                confidence_score REAL DEFAULT 0.0,
                verification_status TEXT DEFAULT 'unverified',
                notes TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                capability_type INTEGER NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_a_id INTEGER NOT NULL,
                entity_b_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_a_id) REFERENCES entities (id),
                FOREIGN KEY (entity_b_id) REFERENCES entities (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                url TEXT NOT NULL,
                collected_at TIMESTAMP,
                raw_data TEXT,  -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                issue_type TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities (id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities (name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funding_entity ON funding (entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capabilities_entity ON capabilities (entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capabilities_type ON capabilities (capability_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_a ON relationships (entity_a_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_b ON relationships (entity_b_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_sources_entity ON data_sources (entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue (status)")
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and return results."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute update query and return last row ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id
    
    def insert_entity(self, entity: Entity) -> int:
        """Insert entity and return ID."""
        query = """
            INSERT INTO entities (name, legal_name, entity_type, confidence_score)
            VALUES (?, ?, ?, ?)
        """
        params = (entity.name, entity.legal_name, entity.entity_type.value, entity.confidence_score)
        return self.execute_update(query, params)
    
    def insert_funding(self, funding: Funding) -> int:
        """Insert funding record with enhanced fields and deduplication logic."""
        # Check for existing funding record to prevent duplicates
        # Use entity_id + amount as primary deduplication key
        existing_query = """
            SELECT id FROM funding 
            WHERE entity_id = ? AND amount = ? 
            AND (grant_id = ? OR (grant_id IS NULL AND ? IS NULL))
        """
        existing_params = (funding.entity_id, funding.amount, funding.grant_id, funding.grant_id)
        existing = self.execute_query(existing_query, existing_params)
        
        if existing:
            # Update existing record with new information if available
            update_query = """
                UPDATE funding SET 
                    program_name = COALESCE(?, program_name),
                    funding_status = COALESCE(?, funding_status),
                    funding_category = COALESCE(?, funding_category),
                    funding_phase = COALESCE(?, funding_phase),
                    project_location = COALESCE(?, project_location),
                    jobs_created = COALESCE(?, jobs_created),
                    confidence_score = CASE 
                        WHEN ? > confidence_score THEN ?
                        ELSE confidence_score 
                    END,
                    verification_status = CASE 
                        WHEN ? = 'api_verified' THEN 'api_verified'
                        ELSE verification_status 
                    END,
                    notes = COALESCE(?, notes)
                WHERE id = ?
            """
            update_params = (
                funding.program_name, 
                funding.funding_status.value if funding.funding_status else None,
                funding.funding_category.value if funding.funding_category else None,
                funding.funding_phase, funding.project_location, funding.jobs_created,
                funding.confidence_score, funding.confidence_score, funding.verification_status, funding.notes,
                existing[0]['id']
            )
            self.execute_update(update_query, update_params)
            return existing[0]['id']
        
        # Insert new funding record
        query = """
            INSERT INTO funding (entity_id, amount, currency, announcement_date, 
                               project_description, source_url, program_name, grant_id,
                               funding_status, funding_category, funding_phase,
                               disbursement_date, completion_date, project_location,
                               matching_funds, jobs_created, confidence_score,
                               verification_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            funding.entity_id, funding.amount, funding.currency, 
            funding.announcement_date, funding.project_description, funding.source_url,
            funding.program_name, funding.grant_id,
            funding.funding_status.value if funding.funding_status else 'unknown',
            funding.funding_category.value if funding.funding_category else 'other',
            funding.funding_phase, funding.disbursement_date, funding.completion_date,
            funding.project_location, funding.matching_funds, funding.jobs_created,
            funding.confidence_score, funding.verification_status, funding.notes
        )
        return self.execute_update(query, params)
    
    def insert_capability(self, capability: Capability) -> int:
        """Insert capability record and return ID."""
        query = """
            INSERT INTO capabilities (entity_id, capability_type, confidence_score, evidence)
            VALUES (?, ?, ?, ?)
        """
        params = (capability.entity_id, capability.capability_type.value, 
                 capability.confidence_score, capability.evidence)
        return self.execute_update(query, params)
    
    def insert_relationship(self, relationship: Relationship) -> int:
        """Insert relationship record and return ID."""
        query = """
            INSERT INTO relationships (entity_a_id, entity_b_id, relationship_type, 
                                     confidence_score, evidence)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (relationship.entity_a_id, relationship.entity_b_id, 
                 relationship.relationship_type.value, relationship.confidence_score, 
                 relationship.evidence)
        return self.execute_update(query, params)
    
    def insert_data_source(self, data_source: DataSource) -> int:
        """Insert data source record and return ID."""
        import json
        query = """
            INSERT INTO data_sources (entity_id, source_type, url, collected_at, raw_data)
            VALUES (?, ?, ?, ?, ?)
        """
        raw_data_json = json.dumps(data_source.raw_data) if data_source.raw_data else None
        params = (data_source.entity_id, data_source.source_type, data_source.url, 
                 data_source.collected_at, raw_data_json)
        return self.execute_update(query, params)
    
    def insert_review_item(self, review_item: ReviewItem) -> int:
        """Insert review queue item and return ID."""
        query = """
            INSERT INTO review_queue (entity_id, issue_type, confidence_score, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (review_item.entity_id, review_item.issue_type, review_item.confidence_score,
                 review_item.status.value, review_item.notes)
        return self.execute_update(query, params)
    
    def get_entity_by_id(self, entity_id: int) -> Optional[Entity]:
        """Get entity by ID."""
        query = "SELECT * FROM entities WHERE id = ?"
        results = self.execute_query(query, (entity_id,))
        if results:
            row = results[0]
            # Handle entity_type conversion safely
            entity_type_str = str(row['entity_type'])
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                entity_type = EntityType.OTHER
            
            return Entity(
                id=row['id'],
                name=row['name'],
                legal_name=row['legal_name'],
                entity_type=entity_type,
                confidence_score=row['confidence_score'],
                # Enhanced fields for professional template
                headquarters=row['headquarters'] if row['headquarters'] else None,
                website=row['website'] if row['website'] else None,
                employees=row['employees'] if row['employees'] else None,
                revenue=row['revenue'] if row['revenue'] else None,
                founded=row['founded'] if row['founded'] else None,
                description=row['description'] if row['description'] else None,
                industry=row['industry'] if row['industry'] else None,
                parent_company=row['parent_company'] if row['parent_company'] else None,
                subsidiaries=row['subsidiaries'] if row['subsidiaries'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None
    
    def get_all_entities(self) -> List[Entity]:
        """Get all entities."""
        query = "SELECT * FROM entities ORDER BY name"
        results = self.execute_query(query)
        entities = []
        for row in results:
            # Handle entity_type conversion safely
            entity_type_str = str(row['entity_type'])
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                # Default to OTHER if conversion fails
                entity_type = EntityType.OTHER
            
            entities.append(Entity(
                id=row['id'],
                name=row['name'],
                legal_name=row['legal_name'],
                entity_type=entity_type,
                confidence_score=row['confidence_score'],
                # Enhanced fields for professional template
                headquarters=row['headquarters'] if row['headquarters'] else None,
                website=row['website'] if row['website'] else None,
                employees=row['employees'] if row['employees'] else None,
                revenue=row['revenue'] if row['revenue'] else None,
                founded=row['founded'] if row['founded'] else None,
                description=row['description'] if row['description'] else None,
                industry=row['industry'] if row['industry'] else None,
                parent_company=row['parent_company'] if row['parent_company'] else None,
                subsidiaries=row['subsidiaries'] if row['subsidiaries'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return entities
    
    def get_entities_by_name(self, name: str) -> List[Entity]:
        """Get entities by name (fuzzy matching)."""
        query = "SELECT * FROM entities WHERE name LIKE ? OR legal_name LIKE ?"
        params = (f"%{name}%", f"%{name}%")
        results = self.execute_query(query, params)
        entities = []
        for row in results:
            # Handle entity_type conversion safely
            entity_type_str = str(row['entity_type'])
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                entity_type = EntityType.OTHER
            
            entities.append(Entity(
                id=row['id'],
                name=row['name'],
                legal_name=row['legal_name'],
                entity_type=entity_type,
                confidence_score=row['confidence_score'],
                # Enhanced fields for professional template
                headquarters=row['headquarters'] if row['headquarters'] else None,
                website=row['website'] if row['website'] else None,
                employees=row['employees'] if row['employees'] else None,
                revenue=row['revenue'] if row['revenue'] else None,
                founded=row['founded'] if row['founded'] else None,
                description=row['description'] if row['description'] else None,
                industry=row['industry'] if row['industry'] else None,
                parent_company=row['parent_company'] if row['parent_company'] else None,
                subsidiaries=row['subsidiaries'] if row['subsidiaries'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return entities
    
    def get_funding_by_entity(self, entity_id: int) -> List[Funding]:
        """Get funding records for entity with all enhanced fields."""
        query = "SELECT * FROM funding WHERE entity_id = ? ORDER BY announcement_date DESC"
        results = self.execute_query(query, (entity_id,))
        funding_list = []
        for row in results:
            # Handle funding status conversion
            funding_status_str = row['funding_status'] if row['funding_status'] else 'unknown'
            try:
                funding_status = FundingStatus(funding_status_str)
            except ValueError:
                funding_status = FundingStatus.UNKNOWN
            
            # Handle funding category conversion
            funding_category_str = row['funding_category'] if row['funding_category'] else 'other'
            try:
                funding_category = FundingCategory(funding_category_str)
            except ValueError:
                funding_category = FundingCategory.OTHER
            
            funding_list.append(Funding(
                id=row['id'],
                entity_id=row['entity_id'],
                amount=row['amount'],
                currency=row['currency'],
                announcement_date=datetime.fromisoformat(row['announcement_date']) if row['announcement_date'] else None,
                project_description=row['project_description'],
                source_url=row['source_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                # Enhanced fields
                program_name=row['program_name'],
                grant_id=row['grant_id'],
                funding_status=funding_status,
                funding_category=funding_category,
                funding_phase=row['funding_phase'],
                disbursement_date=datetime.fromisoformat(row['disbursement_date']) if row['disbursement_date'] else None,
                completion_date=datetime.fromisoformat(row['completion_date']) if row['completion_date'] else None,
                project_location=row['project_location'],
                matching_funds=row['matching_funds'],
                jobs_created=row['jobs_created'],
                confidence_score=row['confidence_score'] if row['confidence_score'] else 0.0,
                verification_status=row['verification_status'],
                notes=row['notes']
            ))
        return funding_list
    
    def get_capabilities_by_entity(self, entity_id: int) -> List[Capability]:
        """Get capabilities for entity."""
        query = "SELECT * FROM capabilities WHERE entity_id = ? ORDER BY confidence_score DESC"
        results = self.execute_query(query, (entity_id,))
        capabilities = []
        for row in results:
            capabilities.append(Capability(
                id=row['id'],
                entity_id=row['entity_id'],
                capability_type=CapabilityType(row['capability_type']),
                confidence_score=row['confidence_score'],
                evidence=row['evidence'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            ))
        return capabilities
    
    def get_relationships_by_entity(self, entity_id: int) -> List[Relationship]:
        """Get relationships for entity."""
        query = """
            SELECT * FROM relationships 
            WHERE entity_a_id = ? OR entity_b_id = ? 
            ORDER BY confidence_score DESC
        """
        results = self.execute_query(query, (entity_id, entity_id))
        relationships = []
        for row in results:
            relationships.append(Relationship(
                id=row['id'],
                entity_a_id=row['entity_a_id'],
                entity_b_id=row['entity_b_id'],
                relationship_type=RelationshipType(row['relationship_type']),
                confidence_score=row['confidence_score'],
                evidence=row['evidence'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            ))
        return relationships
    
    def get_review_queue(self, status: ReviewStatus = ReviewStatus.PENDING) -> List[ReviewItem]:
        """Get review queue items."""
        query = "SELECT * FROM review_queue WHERE status = ? ORDER BY confidence_score ASC"
        results = self.execute_query(query, (status.value,))
        review_items = []
        for row in results:
            review_items.append(ReviewItem(
                id=row['id'],
                entity_id=row['entity_id'],
                item_type=row.get('item_type', ''),
                item_data=row.get('item_data'),
                confidence_score=row['confidence_score'],
                status=ReviewStatus(row['status']),
                priority=ReviewPriority(row.get('priority', 'medium')),
                review_notes=row.get('review_notes'),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                funding_amount=row.get('funding_amount'),
                entity_name=row.get('entity_name'),
                source_url=row.get('source_url')
            ))
        return review_items
    
    def get_review_items_by_status(self, status: ReviewStatus) -> List[ReviewItem]:
        """Get review items by status."""
        return self.get_review_queue(status)
    
    def get_review_items(self, filters: Dict[str, Any], limit: int = 50) -> List[ReviewItem]:
        """Get review items with filters."""
        query = "SELECT * FROM review_queue WHERE 1=1"
        params = []
        
        if 'status' in filters:
            query += " AND status = ?"
            params.append(filters['status'].value)
        
        if 'priority' in filters:
            query += " AND priority = ?"
            params.append(filters['priority'].value)
        
        query += " ORDER BY confidence_score ASC LIMIT ?"
        params.append(limit)
        
        results = self.execute_query(query, params)
        review_items = []
        for row in results:
            review_items.append(ReviewItem(
                id=row['id'],
                entity_id=row['entity_id'],
                item_type=row.get('item_type', ''),
                item_data=row.get('item_data'),
                confidence_score=row['confidence_score'],
                status=ReviewStatus(row['status']),
                priority=ReviewPriority(row.get('priority', 'medium')),
                review_notes=row.get('review_notes'),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                funding_amount=row.get('funding_amount'),
                entity_name=row.get('entity_name'),
                source_url=row.get('source_url')
            ))
        return review_items
    
    def get_review_item_by_id(self, item_id: int) -> Optional[ReviewItem]:
        """Get review item by ID."""
        query = "SELECT * FROM review_queue WHERE id = ?"
        results = self.execute_query(query, (item_id,))
        if results:
            row = results[0]
            return ReviewItem(
                id=row['id'],
                entity_id=row['entity_id'],
                item_type=row.get('item_type', ''),
                item_data=row.get('item_data'),
                confidence_score=row['confidence_score'],
                status=ReviewStatus(row['status']),
                priority=ReviewPriority(row.get('priority', 'medium')),
                review_notes=row.get('review_notes'),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                funding_amount=row.get('funding_amount'),
                entity_name=row.get('entity_name'),
                source_url=row.get('source_url')
            )
        return None
    
    def update_review_item(self, item: ReviewItem) -> bool:
        """Update review item."""
        query = """
        UPDATE review_queue 
        SET status = ?, priority = ?, review_notes = ?, reviewed_at = ?
        WHERE id = ?
        """
        params = (
            item.status.value,
            item.priority.value,
            item.review_notes,
            item.reviewed_at.isoformat() if item.reviewed_at else None,
            item.id
        )
        return self.execute_query(query, params) is not None
