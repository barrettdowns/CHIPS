# CHIPS Act Entity Intelligence System - User Guide

## 🚀 Quick Start Commands

### 1. **Setup (First Time Only)**
```bash
cd /Users/barrettdowns/Projects/CHIPS
source venv/bin/activate
python scripts/init_db.py
```

### 2. **Check System Status**
```bash
python scripts/run_collection.py stats
```

### 3. **Generate Reports**
```bash
# Generate all reports
python scripts/generate_reports.py --all

# Generate specific entity report
python scripts/generate_reports.py --entity-id 1

# Generate capability cluster report
python scripts/generate_reports.py --capability RFIC_DESIGN
```

### 4. **View Reports**
```bash
# List all reports
ls -la reports/entities/
ls -la reports/clusters/

# View specific report
cat reports/entities/Intel_Corporation_report.md
cat reports/clusters/RFIC_DESIGN_cluster_report.md
```

## 📊 Data Collection Commands

### **Automated Batch Collection (Recommended)**
```bash
# Run full automated collection from all sources
python scripts/auto_collect.py

# Quick collection (fewer pages, faster)
python scripts/auto_collect.py --quick

# Specific sources only
python scripts/auto_collect.py --sources chips_gov sec_edgar university_press news_aggregator

# Limit to 20 entities for testing
python scripts/auto_collect.py --max-entities 20
```

### **Individual Source Collection**
```bash
# CHIPS.gov collection
python scripts/run_collection.py collect --sources chips_gov --max-pages 3

# SEC EDGAR collection
python scripts/run_collection.py collect --sources sec_edgar --days-back 30

# University press releases
python scripts/run_collection.py collect --sources university_press

# News aggregator
python scripts/run_collection.py collect --sources news_aggregator

# USASpending.gov API
python scripts/run_collection.py collect --sources usaspending
```

### **Full Pipeline (Recommended)**
```bash
# Run complete pipeline: collect → process → report
python scripts/run_collection.py pipeline --sources chips_gov sec_edgar university_press news_aggregator usaspending
```

## 🔍 Report Management

### **Entity Reports**
- **Location:** `reports/entities/[Entity_Name]_report.md`
- **Contains:** Professional template with funding details, capabilities, relationships, compliance screening
- **Generate:** `python scripts/generate_reports.py --entity-id [ID]`

### **Capability Cluster Reports**
- **Location:** `reports/clusters/[CAPABILITY_NAME]_cluster_report.md`
- **Contains:** All entities in capability area, funding analysis, trends
- **Generate:** `python scripts/generate_reports.py --capability [NAME]`

### **Official 6 Capabilities**
- `THREE_D_PACKAGING` - 3D packaging, chiplets, HBM, advanced interconnects
- `HETEROGENEOUS_PACKAGING` - Mixed-technology integration, system-in-package
- `MULTI_PROJECT_WAFER` - MPW services, shared wafer runs, prototyping
- `RFIC_DESIGN` - RF, wireless, 5G/6G, millimeter wave, analog RF
- `MMIC_CHIPS` - Microwave integrated circuits, high-frequency RF, MMIC design
- `RAD_HARD_CHIPS` - Radiation-hardened electronics, space-grade, aerospace

## 🤖 AI-Powered Features

### **AI Capability Classification**
```bash
# Classify capabilities for all entities using AI
python scripts/simple_classify_capabilities.py

# Test AI classifier on specific entity
python scripts/test_ai_classifier.py --entity-id 1
```

### **AI Company Enrichment**
```bash
# Enrich all entities with AI-powered company information
python scripts/batch_enrich_entities.py

# Quick recovery enrichment from existing reports
python scripts/quick_recovery_enrich.py
```

### **AI Relationship Mapping**
```bash
# Map relationships between entities using AI
python scripts/ai_relationship_mapper.py
```

## 🔧 Entity Management

### **Fix Entity Classifications**
```bash
# Fix entity types (Company, University, Consortium)
python scripts/fix_entity_types.py
```

### **Add Funding Columns**
```bash
# Add enhanced funding fields to database
python scripts/add_funding_columns.py
```

## 📁 File Locations

### **Database**
- **Location:** `data/chips.db`
- **Backup:** Copy this file to backup your data

### **Raw Data**
- **Location:** `data/raw/[source]_[timestamp].json`
- **Purpose:** Original scraped data for debugging

### **Reports**
- **Entities:** `reports/entities/` (141 professional reports)
- **Clusters:** `reports/clusters/` (6 capability cluster reports)

### **Configuration**
- **Sources:** `config/sources.yaml`
- **Capabilities:** `config/capabilities.yaml`
- **AI Classifier:** `config/ai_classifier.yaml`

## ⚠️ Important Notes

### **Rate Limiting**
- CHIPS.gov: 10 requests/minute (6 second delays)
- SEC EDGAR: 5 requests/minute (12 second delays)
- USASpending.gov: API rate limits respected
- Respect robots.txt and be courteous

### **OPSEC Features**
- VPN connection check (configurable)
- User-agent rotation
- Request delays and randomization
- Session isolation per source

### **Data Quality**
- Confidence scores: 0.0-1.0
- AI-powered classification with fallback to rule-based
- Comprehensive funding deduplication
- All data traceable to original sources

## 🧪 Testing

### **Run Test Suite**
```bash
python scripts/test_system.py
```

### **Test Individual Components**
```bash
# Test database
python scripts/init_db.py

# Test report generation
python scripts/generate_reports.py --all

# Test AI classifier
python scripts/test_ai_classifier.py --test-all --limit 5
```

## 📈 Monitoring Progress

### **Check Database Stats**
```bash
python scripts/run_collection.py stats
```

### **View Collection Logs**
- Logs appear in terminal with timestamps
- Look for "INFO" and "ERROR" messages
- Collection statistics shown at end

## 🌐 Streamlit Web Interface

### **Start Streamlit App**
```bash
streamlit run streamlit_app.py
```

### **Access at:** `http://localhost:8501`

**Features:**
- **Dashboard:** System status, entity count, funding totals
- **Entities:** View, filter, and manage all entities
- **Reports:** Generate and download reports
- **Settings:** Configure collection parameters

## 🚨 Troubleshooting

### **Common Issues**
1. **Import errors:** Make sure you're in the right directory and venv is activated
2. **Database errors:** Run `python scripts/init_db.py` to reset
3. **No data:** Check VPN connection and rate limits
4. **Empty reports:** Ensure entities exist in database
5. **AI classifier errors:** Check OpenAI API key in environment variables

### **Reset System**
```bash
# Reset database
rm data/chips.db
python scripts/init_db.py

# Clear reports
rm -rf reports/entities/* reports/clusters/*
```

## 📋 Daily Workflow

### **Morning Routine**
1. Check system status: `python scripts/run_collection.py stats`
2. Run collection: `python scripts/auto_collect.py --quick`
3. Generate reports: `python scripts/generate_reports.py --all`

### **Evening Routine**
1. Check new reports: `ls -la reports/entities/`
2. Review funding data in Streamlit app
3. Verify entity classifications

## 🎯 Success Metrics

- **Target:** 100+ entities profiled ✅ (Currently: 143 entities)
- **Quality:** >85% confidence on primary entities ✅
- **Coverage:** All 6 capability areas represented ✅
- **Timeliness:** Reports generated within 2 hours of collection ✅
- **Funding Accuracy:** Zero double-counting, comprehensive attribution ✅

## 💰 Current System Status

### **Entities Collected:** 143
### **Funding Records:** 216 (zero duplicates)
### **Total Funding:** $1.56B
### **Reports Generated:** 141 entity reports + 6 cluster reports
### **Capabilities Classified:** 47 capabilities across all entities
### **Data Sources:** 5 active collectors (CHIPS.gov, SEC EDGAR, University Press, News Aggregator, USASpending.gov)

---

**Remember:** This system is designed for automated operation with AI-powered intelligence. All reports use professional templates with comprehensive funding attribution and compliance screening!