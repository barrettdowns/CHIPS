# Capability Cluster Report: {{ capability_name }}

**Generated:** {{ generated_date }}  
**Capability Area:** {{ capability_name }}  
**Description:** {{ capability_description }}  
**Total Entities:** {{ entities|length }}

---

## Overview

This report provides an analysis of all entities with {{ capability_name }} capabilities in the CHIPS Act ecosystem. The analysis includes funding patterns, relationship networks, and capability confidence scores.

### Key Statistics

- **Total Entities:** {{ entities|length }}
- **Total Funding:** ${{ "%.2f"|format(total_funding) }}M
- **Average Confidence:** {{ avg_confidence|round(2) }}
- **High Confidence Entities:** {{ high_confidence_count }} ({{ (high_confidence_count / entities|length * 100)|round(1) }}%)

---

## Entity Analysis

{% if entities %}
| Entity | Type | Funding | Confidence | Capabilities |
|--------|------|---------|------------|--------------|
{% for entity in entities %}
| [{{ entity.name }}]({{ entity.name|replace(' ', '_') }}.md) | {{ entity.entity_type.value|title }} | ${{ "%.2f"|format(entity.total_funding) if entity.total_funding else '0.00' }}M | {{ entity.avg_confidence|round(2) }} | {{ entity.capability_count }} |
{% endfor %}
{% else %}
No entities found with {{ capability_name }} capabilities.
{% endif %}

---

## Funding Analysis

{% if funding_by_entity %}
### Funding Distribution

{% for entity_funding in funding_by_entity %}
- **{{ entity_funding.entity_name }}:** ${{ "%.2f"|format(entity_funding.total_amount) }}M
  {% for funding in entity_funding.funding_details %}
  - {{ funding.announcement_date.strftime('%Y-%m-%d') if funding.announcement_date else 'N/A' }}: ${{ "%.2f"|format(funding.amount) if funding.amount else 'N/A' }}M - {{ funding.project_description[:50] }}{% if funding.project_description|length > 50 %}...{% endif %}
  {% endfor %}

{% endfor %}
{% endif %}

### Funding Trends

{% if funding_timeline %}
{% for period in funding_timeline %}
- **{{ period.period }}:** ${{ "%.2f"|format(period.total_amount) }}M ({{ period.entity_count }} entities)
{% endfor %}
{% endif %}

---

## Capability Analysis

{% if capability_stats %}
### Capability Confidence Distribution

- **High Confidence (0.8+):** {{ capability_stats.high_confidence }} entities
- **Medium Confidence (0.6-0.8):** {{ capability_stats.medium_confidence }} entities  
- **Low Confidence (0.3-0.6):** {{ capability_stats.low_confidence }} entities
- **Below Threshold (<0.3):** {{ capability_stats.below_threshold }} entities

### Evidence Quality

{% for evidence_type in capability_stats.evidence_types %}
- **{{ evidence_type.type }}:** {{ evidence_type.count }} entities ({{ evidence_type.percentage|round(1) }}%)
{% endfor %}
{% endif %}

---

## Relationship Network

{% if relationships %}
### Entity Relationships

{% for relationship in relationships %}
- **{{ relationship.entity_a_name }}** ↔ **{{ relationship.entity_b_name }}**
  - Type: {{ relationship.relationship_type.value|replace('_', ' ')|title }}
  - Confidence: {{ relationship.confidence_score|round(2) }}
  - Evidence: {{ relationship.evidence[:100] }}{% if relationship.evidence|length > 100 %}...{% endif %}

{% endfor %}
{% endif %}

### Network Statistics

- **Total Relationships:** {{ relationship_count }}
- **Average Connections per Entity:** {{ avg_connections|round(1) }}
- **Most Connected Entity:** {{ most_connected_entity.name if most_connected_entity else 'N/A' }} ({{ most_connected_count }} connections)

---

## Key Insights

### Top Funded Entities

{% if top_funded_entities %}
{% for entity in top_funded_entities[:5] %}
{{ loop.index }}. **{{ entity.name }}** - ${{ "%.2f"|format(entity.total_funding) }}M
{% endfor %}
{% endif %}

### Highest Confidence Capabilities

{% if top_confidence_entities %}
{% for entity in top_confidence_entities[:5] %}
{{ loop.index }}. **{{ entity.name }}** - {{ entity.avg_confidence|round(2) }} confidence
{% endfor %}
{% endif %}

### Emerging Trends

{% if trends %}
{% for trend in trends %}
- **{{ trend.trend }}:** {{ trend.description }}
{% endfor %}
{% endif %}

---

## Data Sources

{% if data_sources %}
| Source Type | Count | Coverage |
|-------------|-------|----------|
{% for source in data_sources %}
| {{ source.source_type }} | {{ source.count }} | {{ source.coverage|round(1) }}% |
{% endfor %}
{% endif %}

---

## Recommendations

### For Further Analysis

1. **High Priority:** Investigate entities with high funding but low confidence scores
2. **Medium Priority:** Expand data collection for entities with insufficient evidence
3. **Low Priority:** Review flagged entities in the review queue

### For Collection Strategy

1. **Focus Areas:** {{ focus_areas|join(', ') }}
2. **Data Gaps:** {{ data_gaps|join(', ') }}
3. **Update Frequency:** {{ update_frequency }}

---

## Metadata

- **Report Generated:** {{ generated_date }}
- **Capability ID:** {{ capability_id }}
- **Total Entities Analyzed:** {{ entities|length }}
- **Total Funding Analyzed:** ${{ "%.2f"|format(total_funding) }}M
- **Data Sources Used:** {{ data_sources|length }}
- **Relationships Mapped:** {{ relationship_count }}
- **Review Items:** {{ review_items_count }}
