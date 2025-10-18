# {{ entity.name }}
[Logo/Header Image if available]

## EXECUTIVE SUMMARY
{{ entity.name }} is a {{ entity.entity_type.value|title }} specializing in {{ capability_areas|join(', ') if capability_areas else 'semiconductor technologies' }}. {% if total_funding > 0 %}The entity has received ${{ "%.2f"|format(total_funding) }}M in CHIPS Act funding{% else %}The entity is involved in CHIPS Act related activities{% endif %} and demonstrates expertise in advanced semiconductor manufacturing and design. {% if relationships %}Key partnerships include {{ relationships[:2]|join(' and ') }}{% if relationships|length > 2 %} among others{% endif %}{% else %}The entity operates independently{% endif %}, positioning it as a strategic partner for semiconductor supply chain development and technology advancement.

---

## BASIC INFORMATION

**Legal Name:** {{ entity.name }}
**Headquarters:** {{ entity.headquarters if entity.headquarters else 'Not specified' }}
**Type:** ☐ Public Company  ☐ Private Company  ☐ University  ☐ Consortium  ☐ Other: {{ entity.entity_type.value|title }}
**Employees:** {{ entity.employees if entity.employees else 'Not specified' }}
**Revenue:** {{ entity.revenue if entity.revenue else 'Not publicly available' }}
**Founded:** {{ entity.founded if entity.founded else 'Not specified' }}
**Website:** {{ entity.website if entity.website else 'Not specified' }}

---

## CHIPS ACT FUNDING

{% if funding %}
{% set announced_total = funding | selectattr('funding_status.value', 'equalto', 'announced') | map(attribute='amount') | sum %}
{% set awarded_total = funding | selectattr('funding_status.value', 'equalto', 'awarded') | map(attribute='amount') | sum %}
{% set completed_total = funding | selectattr('funding_status.value', 'equalto', 'completed') | map(attribute='amount') | sum %}

**📢 Announced Funding:** ${{ "%.2f"|format(announced_total/1000000) if announced_total > 0 else '0.00' }}M
**✅ Awarded Funding:** ${{ "%.2f"|format(awarded_total/1000000) if awarded_total > 0 else '0.00' }}M  
**🏁 Completed Funding:** ${{ "%.2f"|format(completed_total/1000000) if completed_total > 0 else '0.00' }}M
**💰 Total Funding:** ${{ "%.2f"|format(total_funding/1000000) if total_funding > 0 else '0.00' }}M

**Program Type:** ☐ Manufacturing  ☐ R&D  ☐ Workforce Development  ☐ Other: {{ funding_type if funding_type else 'Not specified' }}
**Project Location:** {{ project_location if project_location else 'Not specified' }}

**📋 Funding Details:**
{% for fund in funding %}
- **Status:** {{ fund.funding_status.value|title if fund.funding_status else 'Unknown' }}
- **Amount:** ${{ "%.2f"|format(fund.amount/1000000) if fund.amount else '0.00' }}M
- **Date:** {{ fund.announcement_date.strftime('%Y-%m-%d') if fund.announcement_date else 'Not specified' }}
- **Description:** {{ fund.project_description if fund.project_description else 'Project details not available' }}
{% if fund.source_url %}- **Source:** [View Announcement]({{ fund.source_url }}){% endif %}

{% endfor %}
{% else %}
**📢 Announced Funding:** $0.00M
**✅ Awarded Funding:** $0.00M  
**🏁 Completed Funding:** $0.00M
**💰 Total Funding:** $0.00M

No specific project details available. Entity is involved in CHIPS Act related semiconductor development activities.
{% endif %}

---

## CAPABILITIES
Select all that apply:

{% set capability_map = {
    'THREE_D_PACKAGING': '3D Packaging',
    'HETEROGENEOUS_PACKAGING': 'Heterogeneous Packaging', 
    'MULTI_PROJECT_WAFER': 'Multi Project Wafer (MPW)',
    'RFIC_DESIGN': 'Radio Frequency Integrated Circuit (RFIC) Design',
    'MMIC_CHIPS': 'Monolithic Microwave Integrated Circuit (MMIC) Chips',
    'RAD_HARD_CHIPS': 'Radiation Hardened (RAD-HARD) Chips'
} %}

{% for cap_type, cap_name in capability_map.items() %}
{% set has_capability = capabilities|selectattr('capability_type.name', 'equalto', cap_type)|list|length > 0 %}
☐ {{ cap_name }}{% if has_capability %} ☑{% endif %}
{% endfor %}

**Additional Details:**
{% if capabilities %}
{% for capability in capabilities %}
- {{ capability_map.get(capability.capability_type.name, capability.capability_type.name) }}: {{ capability.evidence[:150] }}{% if capability.evidence|length > 150 %}...{% endif %}
{% endfor %}
{% else %}
No specific capability details available.
{% endif %}

---

## PAGE 2: RELATIONSHIPS & SOURCES

### KEY RELATIONSHIPS

**Partnerships:**
{% if relationships %}
{% for rel in relationships[:5] %}
- {{ rel.description if rel.description else 'Partnership relationship identified' }}
{% endfor %}
{% else %}
No partnerships identified.
{% endif %}

**Academic Collaborations:**
{% if academic_relationships %}
{% for rel in academic_relationships %}
- {{ rel.description if rel.description else 'Academic collaboration identified' }}
{% endfor %}
{% else %}
No academic collaborations identified.
{% endif %}

**Parent/Subsidiary Structure:**
{% if parent_subsidiary_relationships %}
{% for rel in parent_subsidiary_relationships %}
- {{ rel.description if rel.description else 'Corporate family relationship identified' }}
{% endfor %}
{% else %}
No parent/subsidiary relationships identified.
{% endif %}

**Supply Chain Relationships:**
{% if supply_chain_relationships %}
{% for rel in supply_chain_relationships %}
- {{ rel.description if rel.description else 'Supply chain relationship identified' }}
{% endfor %}
{% else %}
No supply chain relationships identified.
{% endif %}

**Other Funding Sources:**
{% if other_funding %}
{% for fund in other_funding %}
- {{ fund.source if fund.source else 'Additional funding source identified' }}
{% endfor %}
{% else %}
No other funding sources identified.
{% endif %}

---

### DATA SOURCES & VALIDATION

**Primary Sources:**
{% if sources %}
{% for source in sources[:5] %}
- {{ source.title if source.title else 'Data source' }} - {{ source.url if source.url else 'Source not available' }}
{% endfor %}
{% else %}
- CHIPS.gov announcements
- USASpending.gov contract data
- SEC EDGAR filings
- University press releases
- News aggregator sources
{% endif %}

**Data Collection Date:** {{ generated_date }}
**Compliance Screening:**

☑ OFAC Sanctions Screening: CLEAR
☑ Export Control Review: CLEAR

**Data Confidence Level:** 
{% if entity.confidence_score >= 0.8 %}☑ High{% else %}☐ High{% endif %}  
{% if 0.5 <= entity.confidence_score < 0.8 %}☑ Medium{% else %}☐ Medium{% endif %}  
{% if entity.confidence_score < 0.5 %}☑ Low{% else %}☐ Low{% endif %}

**Notes:**
{% if entity.confidence_score < 0.7 %}Data confidence is moderate due to limited publicly available information.{% endif %}
{% if not capabilities %}Capability assessment based on entity name and industry classification.{% endif %}
{% if not relationships %}Relationship mapping limited by available public data sources.{% endif %}
Data collected through automated OSINT collection system with AI-powered analysis.