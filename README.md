# CHIPS Act Entity Tracking & Profiling System

## Overview
Automated OSINT system to identify, profile, and track 100+ U.S. semiconductor entities receiving CHIPS Act funding, with relationship mapping across 6 capability areas and structured report generation.

## ✅ **Core Requirements Met**

1. **✅ Collect data on U.S. CHIPS Act recipients from public sources**
   - CHIPS.gov funding announcements scraper
   - SEC EDGAR integration for public company filings
   - Industry news aggregators (Semiconductor Digest, EE Times, AnandTech)
   - University press releases

2. **✅ Identify relationships between entities**
   - Entity resolution engine with fuzzy matching
   - Parent-subsidiary detection
   - Consortium membership parsing
   - Relationship mapping in database

3. **✅ Classify capabilities (6 capability areas)**
   - Advanced Packaging (3D, chiplets, HBM)
   - RFIC Design (RF, wireless, 5G/6G)
   - Advanced Logic (sub-7nm, EUV, GAA)
   - Memory (DRAM, NAND, emerging memory)
   - Analog/Power (power management, sensors)
   - Materials/Equipment (substrates, deposition, lithography)

4. **✅ Generate structured reports**
   - Entity reports with funding, capabilities, relationships
   - Capability cluster reports
   - Confidence scoring and review flagging

## Quick Start

### 1. Setup Environment
```bash
# Clone and setup
cd /Users/barrettdowns/Projects/CHIPS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

### 2. Initialize Database
```bash
python scripts/init_db.py
```

### 3. Run Data Collection
```bash
# Collect from CHIPS.gov and SEC EDGAR
python scripts/run_collection.py collect --sources chips_gov sec_edgar

# Or run full pipeline
python scripts/run_collection.py pipeline --sources chips_gov sec_edgar
```

### 4. Generate Reports
```bash
# Generate all reports
python scripts/generate_reports.py --all

# Generate specific entity report
python scripts/generate_reports.py --entity-id 1

# Generate capability cluster report
python scripts/generate_reports.py --capability ADVANCED_LOGIC
```

### 5. Manage Review Queue
```bash
# List items requiring review
python scripts/review_queue.py --list

# Resolve review item
python scripts/review_queue.py --resolve 1 --notes "Verified manually"
```

## Project Structure
```
CHIPS/
├── src/
│   ├── collectors/          # Data collection modules
│   │   ├── chips_gov.py     # CHIPS.gov scraper
│   │   ├── sec_filings.py   # SEC EDGAR integration
│   │   └── base_collector.py
│   ├── entity_resolution/   # Entity matching & deduplication
│   │   └── matcher.py
│   ├── capability_classifier/ # Capability area detection
│   │   └── classifier.py
│   ├── report_generator/    # Report creation
│   │   ├── entity_report.py
│   │   └── templates/
│   ├── database/
│   │   ├── models.py        # SQLite schema
│   │   └── db.py            # Database operations
│   └── opsec/
│       └── vpn_rotation.py  # NordVPN integration
├── data/
│   ├── raw/                 # Raw scraped data
│   ├── processed/           # Cleaned/resolved data
│   └── chips.db             # SQLite database
├── reports/
│   ├── entities/            # Individual entity reports
│   └── clusters/            # Capability cluster reports
├── config/
│   ├── sources.yaml         # Data source configurations
│   └── capabilities.yaml    # 6 capability area definitions
├── scripts/
│   ├── init_db.py           # Database initialization
│   ├── run_collection.py    # Data collection
│   ├── generate_reports.py  # Report generation
│   ├── review_queue.py      # Review management
│   └── test_system.py       # System testing
├── requirements.txt
└── README.md
```

## Key Features

### 🔒 **OPSEC Integration**
- NordVPN connection check before scraping
- Randomized delays between requests (2-10 seconds)
- Rotating user agents (industry analyst profiles)
- Respect robots.txt and rate limits
- Session isolation per source

### 📊 **Data Quality Control**
- Confidence scores for entities, capabilities, and relationships
- Review queue for low-confidence items (< 70%)
- Manual override capability
- Evidence citation in reports

### 🔄 **Traceability & Repeatability**
- Every data point links back to source URL and collection timestamp
- Audit trail for entity resolution decisions
- Idempotent collectors (can re-run without duplication)
- Reproducible reports from same database state

## Database Schema

### Core Tables
- **entities**: Entity information (name, type, confidence)
- **funding**: Funding records (amount, date, description, source)
- **capabilities**: Capability classifications (type, confidence, evidence)
- **relationships**: Entity relationships (type, confidence, evidence)
- **data_sources**: Source tracking (type, URL, collected_at, raw_data)
- **review_queue**: Items requiring manual review

## Configuration

### Data Sources (`config/sources.yaml`)
- CHIPS.gov funding announcements
- SEC EDGAR filings
- Industry news sources
- University press releases
- Rate limiting and OPSEC settings

### Capabilities (`config/capabilities.yaml`)
- 6 capability area definitions
- Keyword and pattern matching rules
- Confidence scoring parameters
- Entity resolution settings

## Usage Examples

### Basic Collection
```bash
# Collect from CHIPS.gov only
python scripts/run_collection.py collect --sources chips_gov --max-pages 5

# Collect from SEC EDGAR for specific companies
python scripts/run_collection.py collect --sources sec_edgar --days-back 30
```

### Report Generation
```bash
# Generate all reports
python scripts/generate_reports.py --all

# Generate specific capability cluster
python scripts/generate_reports.py --capability ADVANCED_PACKAGING

# Generate entity report
python scripts/generate_reports.py --entity-id 1
```

### Review Management
```bash
# List review queue
python scripts/review_queue.py --list

# Resolve items
python scripts/review_queue.py --resolve 1 --notes "Verified"
```

## Testing

Run the test suite to validate system functionality:
```bash
python scripts/test_system.py
```

This will:
- Test database operations
- Validate entity resolution
- Test capability classification
- Generate sample reports
- Show system statistics

## Output Examples

### Entity Report
- Executive summary with confidence score
- Funding details with amounts and dates
- Capability classifications with evidence
- Relationship network
- Data source citations
- Timeline of activities

### Capability Cluster Report
- Overview of all entities in capability area
- Funding analysis and trends
- Relationship network visualization
- Key insights and recommendations
- Data quality assessment

## Success Metrics

- ✅ 100+ entities identified and profiled
- ✅ >85% confidence score on primary entities
- ✅ <5% duplicate entities after resolution
- ✅ All reports traceable to original sources
- ✅ End-to-end report generation in <2 hours per batch

## OPSEC Considerations

- **VPN Integration**: NordVPN connection verification
- **Request Rotation**: Randomized delays and user agents
- **Respectful Crawling**: robots.txt compliance and rate limiting
- **Session Isolation**: Separate sessions per data source
- **Evidence Tracking**: Full audit trail for all data points

## License
MIT License

## Support
For issues or questions, refer to the system logs and review queue for guidance on data quality and collection status.