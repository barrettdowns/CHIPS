# CHIPS Act Intelligence System Summary

**Generated:** {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}

## 📊 System Overview

### Database Statistics
- **Total Entities:** {{ db_stats.entities_by_type.values() | sum }}
- **Total Funding:** ${{ "%.0f"|format(db_stats.total_funding) }}M
- **Entity Types:**
  {% for entity_type, count in db_stats.entities_by_type.items() %}
  - {{ entity_type }}: {{ count }}
  {% endfor %}

### Quality Metrics
- **Data Quality Score:** {{ "%.2f"|format(quality_metrics.data_quality_score) }}
- **Approval Rate:** {{ "%.1f"|format(quality_metrics.approval_rate * 100) }}%
- **Average Confidence:** {{ "%.2f"|format(quality_metrics.average_confidence) }}
- **Pending Reviews:** {{ quality_metrics.pending_reviews }}

## 🎯 Capability Distribution

{% for capability, count in db_stats.capabilities.items() %}
- **{{ capability }}:** {{ count }} entities
{% endfor %}

## 📈 Top Entities by Funding

{% for entity in db_stats.top_entities_by_funding[:10] %}
- **{{ entity.name }}:** ${{ "%.0f"|format(entity.total_funding) }}M
{% endfor %}

## 🔍 Recent Activity

### Last Collection
- **Date:** {{ db_stats.last_collection_date.strftime('%Y-%m-%d %H:%M:%S') if db_stats.last_collection_date else 'Never' }}
- **Items Collected:** {{ db_stats.last_collection_count }}

### Review Queue Status
- **High Priority:** {{ quality_metrics.high_priority_reviews }}
- **Medium Priority:** {{ quality_metrics.medium_priority_reviews }}
- **Low Priority:** {{ quality_metrics.low_priority_reviews }}

## ⚙️ System Configuration

{% for key, value in system_config.items() %}
- **{{ key }}:** {{ value }}
{% endfor %}

## 🚨 Alerts & Recommendations

{% if quality_metrics.data_quality_score < 0.7 %}
⚠️ **Data Quality Alert:** Quality score below threshold ({{ "%.2f"|format(quality_metrics.data_quality_score) }})
{% endif %}

{% if quality_metrics.pending_reviews > 200 %}
⚠️ **Review Queue Alert:** {{ quality_metrics.pending_reviews }} items pending review
{% endif %}

{% if db_stats.last_collection_date and (generated_at - db_stats.last_collection_date).days > 7 %}
⚠️ **Stale Data Alert:** Last collection was {{ (generated_at - db_stats.last_collection_date).days }} days ago
{% endif %}

## 📋 Next Steps

1. **Review Queue Management:** Process {{ quality_metrics.pending_reviews }} pending items
2. **Data Quality Improvement:** Focus on entities with low confidence scores
3. **Collection Schedule:** Ensure regular data collection
4. **Report Generation:** Generate updated entity and cluster reports

---

*This report was generated automatically by the CHIPS Act Intelligence System*
