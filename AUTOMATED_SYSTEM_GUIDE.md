# 🤖 Automated CHIPS Intelligence System - Usage Guide

## 🚀 **Quick Start**

### **Phase 1: Automated Batch Collection (IMPLEMENTED)**
```bash
# Run full automated cycle (collect, process, quality control, report)
python scripts/auto_collect.py

# Run with specific sources only
python scripts/auto_collect.py --sources chips_gov sec_edgar university_press news_aggregator usaspending

# Quick collection (fewer pages, faster)
python scripts/auto_collect.py --quick

# Limit entities for testing
python scripts/auto_collect.py --max-entities 20
```

### **Phase 2: Smart Scheduling (AVAILABLE)**
```bash
# Start automated system (runs continuously)
python scripts/master_control.py --start-automated

# Run daily cycle manually
python scripts/master_control.py --run-daily

# Run weekly comprehensive cycle
python scripts/master_control.py --run-weekly

# Check scheduler status
python scripts/smart_scheduler.py --status
```

### **Phase 3: Quality Control (IMPLEMENTED)**
```bash
# Process review queue automatically
python scripts/quality_control.py --process

# Show items needing manual review
python scripts/quality_control.py --manual-review

# Approve/reject items manually
python scripts/quality_control.py --approve 123
python scripts/quality_control.py --reject 456

# Show quality metrics
python scripts/quality_control.py --metrics
```

## 📋 **System Commands**

### **Automated Collection (CURRENT)**
```bash
# Run batch collection from all sources
python scripts/auto_collect.py

# Quick collection (fewer pages)
python scripts/auto_collect.py --quick

# Specific sources only
python scripts/auto_collect.py --sources chips_gov sec_edgar university_press news_aggregator usaspending

# Skip processing/reports
python scripts/auto_collect.py --skip-processing --skip-reports

# Limit entities
python scripts/auto_collect.py --max-entities 20
```

### **Master Control System (AVAILABLE)**
```bash
# Full intelligence cycle
python scripts/master_control.py --run-full

# Daily cycle (uses current pattern)
python scripts/master_control.py --run-daily

# Weekly comprehensive cycle
python scripts/master_control.py --run-weekly

# Start fully automated system
python scripts/master_control.py --start-automated

# System status
python scripts/master_control.py --status

# Health check
python scripts/master_control.py --health-check

# Create backup
python scripts/master_control.py --backup
```

### **Smart Scheduler (AVAILABLE)**
```bash
# Run scheduler continuously
python scripts/smart_scheduler.py --run

# Manual collection with pattern
python scripts/smart_scheduler.py --manual comprehensive
python scripts/smart_scheduler.py --manual focused
python scripts/smart_scheduler.py --manual news_focused
python scripts/smart_scheduler.py --manual academic

# Test current pattern
python scripts/smart_scheduler.py --test

# Show status
python scripts/smart_scheduler.py --status
```

### **Quality Control (IMPLEMENTED)**
```bash
# Process review queue
python scripts/quality_control.py --process

# Manual review interface
python scripts/quality_control.py --manual-review
python scripts/quality_control.py --manual-review --priority HIGH

# Approve/reject items
python scripts/quality_control.py --approve 123
python scripts/quality_control.py --reject 456

# Quality metrics
python scripts/quality_control.py --metrics
```

## 🔄 **Automated Workflows**

### **Current Implementation Status**
✅ **Phase 1: Automated Batch Collection** - FULLY IMPLEMENTED
- Collects from 5 sources: CHIPS.gov, SEC EDGAR, University Press, News Aggregator, USASpending.gov
- Processes 143 entities automatically
- Generates 141 entity reports + 6 cluster reports
- Zero double-counting with deduplication logic

🔄 **Phase 2: Smart Scheduling** - AVAILABLE BUT NOT ACTIVE
- Collection patterns: Comprehensive, Focused, News Focused, Academic
- Automated scheduling with pattern rotation
- Random delays and user agent rotation
- Time-based collection cycles

✅ **Phase 3: Quality Control** - IMPLEMENTED
- AI-powered capability classification
- Confidence scoring (0.0-1.0)
- Automated review queue management
- Manual review interface for edge cases

### **Collection Patterns (Available)**
- **Comprehensive:** All sources, 10 pages, 90 days
- **Focused:** CHIPS.gov + SEC, 15 pages, 120 days  
- **News Focused:** News sources, 8 pages, 60 days
- **Academic:** CHIPS.gov + universities, 12 pages, 90 days

### **Quality Control Flow (Active)**
1. **Auto-approve:** Confidence ≥ 85%
2. **Auto-reject:** Confidence ≤ 30%
3. **Manual review:** Confidence 30-85% or high-value funding
4. **Priority scoring:** Based on funding amount, confidence, source reliability

## 📊 **Monitoring & Status**

### **System Status**
```bash
python scripts/master_control.py --status
```
Shows:
- Database statistics (143 entities, 216 funding records, $1.56B total)
- Quality metrics
- Scheduler status
- System configuration

### **Quality Metrics**
```bash
python scripts/quality_control.py --metrics
```
Shows:
- Pending reviews count
- Approval rate
- Average confidence score
- Data quality score

### **Health Check**
```bash
python scripts/master_control.py --health-check
```
Checks:
- Database connectivity
- Data quality thresholds
- Review queue size
- System health

## 🎯 **Use Cases**

### **Daily Operations (CURRENT)**
```bash
# Run automated collection
python scripts/auto_collect.py

# Generate reports
python scripts/generate_reports.py --all

# Check system status
python scripts/run_collection.py stats
```

### **Manual Collection**
```bash
# Run collection when needed
python scripts/auto_collect.py --quick

# Specific sources
python scripts/auto_collect.py --sources chips_gov sec_edgar
```

### **Quality Review**
```bash
# Process review queue
python scripts/quality_control.py --process

# Review high-priority items
python scripts/quality_control.py --manual-review --priority HIGH
```

### **System Maintenance**
```bash
# Check system health
python scripts/master_control.py --health-check

# Create backup
python scripts/master_control.py --backup

# View system status
python scripts/master_control.py --status
```

## ⚙️ **Configuration**

### **Collection Sources (Active)**
- **CHIPS.gov:** Government announcements and funding
- **SEC EDGAR:** Corporate filings and disclosures
- **University Press:** Academic research and partnerships
- **News Aggregator:** Industry news and developments
- **USASpending.gov:** Federal contract and grant data

### **Quality Thresholds (Active)**
- **Confidence thresholds:** 30% (reject), 85% (approve)
- **Auto-approve/reject limits:** Based on confidence scores
- **Priority weights:** Funding amount, confidence, source reliability
- **Review criteria:** Low confidence, high-value funding, edge cases

### **Scheduling (Available)**
- **Collection times:** Configurable intervals
- **Pattern rotation frequency:** Every 7 days
- **Random delay ranges:** 2-10 seconds between requests
- **Schedule intervals:** Daily, weekly, custom

## 🚨 **Troubleshooting**

### **Common Issues**

**Collection Errors:**
```bash
# Check system status
python scripts/master_control.py --status

# Run health check
python scripts/master_control.py --health-check

# Test collection
python scripts/auto_collect.py --quick
```

**Quality Control Issues:**
```bash
# Check review queue
python scripts/quality_control.py --manual-review

# Process queue
python scripts/quality_control.py --process

# View metrics
python scripts/quality_control.py --metrics
```

**Scheduling Problems:**
```bash
# Check scheduler status
python scripts/smart_scheduler.py --status

# Test manual collection
python scripts/smart_scheduler.py --test

# Restart scheduler
python scripts/smart_scheduler.py --run
```

## 📈 **Performance Tips**

### **Optimization**
- Use `--quick` for faster collection
- Process review queue regularly
- Monitor quality metrics
- Create regular backups

### **Scaling**
- Adjust collection patterns based on needs
- Modify quality thresholds for your use case
- Schedule collections during off-peak hours
- Use multiple collection patterns

## 🔒 **Security & OPSEC**

### **VPN Integration**
- System checks VPN status before collection
- Random delays between requests
- User agent rotation
- Session isolation

### **Rate Limiting**
- Built-in delays between sources
- Respectful request patterns
- Error handling and retries
- Source-specific rate limits

## 🎉 **Current System Status**

### **✅ FULLY OPERATIONAL:**
- **143 entities** collected and profiled
- **216 funding records** with zero double-counting
- **$1.56B total funding** accurately tracked
- **141 entity reports** + 6 cluster reports generated
- **5 data sources** actively collecting
- **AI-powered classification** with 47 capabilities identified
- **Professional report templates** with compliance screening

### **🚀 READY TO USE:**
```bash
# Start with automated collection
python scripts/auto_collect.py

# Generate all reports
python scripts/generate_reports.py --all

# View in Streamlit app
streamlit run streamlit_app.py
```

The automated system is now fully operational with comprehensive intelligence collection, AI-powered analysis, and professional reporting capabilities!