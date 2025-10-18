"""
Report generation engine for CHIPS Act entity tracking.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from ..database.db import DatabaseOperations
from ..database.models import CapabilityType, ReviewStatus
from .format_converter import ReportFormatConverter
# Templates are loaded dynamically by Jinja2


class ReportGenerator:
    """Generate reports for entities and capability clusters."""
    
    def __init__(self, db_ops: DatabaseOperations, templates_dir: str = "src/report_generator/templates"):
        self.db_ops = db_ops
        self.templates_dir = Path(templates_dir)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.format_converter = ReportFormatConverter()
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )
    
    def generate_entity_report(self, entity_id: int) -> str:
        """Generate report for a specific entity."""
        logger.info(f"Generating report for entity {entity_id}")
        
        # Get entity summary
        summary = self.db_ops.get_entity_summary(entity_id)
        if not summary:
            logger.error(f"No data found for entity {entity_id}")
            return ""
        
        entity = summary['entity']
        
        # Prepare template data
        template_data = {
            'entity': entity,
            'funding': summary['funding'],
            'capabilities': summary['capabilities'],
            'relationships': summary['relationships'],
            'data_sources': summary['data_sources'],
            'total_funding': summary['total_funding'],
            'capability_count': summary['capability_count'],
            'relationship_count': summary['relationship_count'],
            'source_count': summary['source_count'],
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'capability_areas': [cap.capability_type.name.replace('_', ' ').title() for cap in summary['capabilities']],
            'review_items': self._get_review_items(entity_id),
            # New fields for professional template
            'funding_type': self._get_funding_type(summary['funding']),
            'funding_date': self._get_funding_date(summary['funding']),
            'project_location': self._get_project_location(summary['funding']),
            'academic_relationships': self._get_academic_relationships(summary['relationships']),
            'parent_subsidiary_relationships': self._get_parent_subsidiary_relationships(summary['relationships']),
            'supply_chain_relationships': self._get_supply_chain_relationships(summary['relationships']),
            'other_funding': self._get_other_funding(summary['funding']),
            'sources': summary['data_sources']
        }
        
        # Render template
        template = self.jinja_env.get_template('entity_report.md')
        report_content = template.render(**template_data)
        
        # Save report
        report_filename = f"{entity.name.replace(' ', '_')}_report.md"
        report_path = self.reports_dir / "entities" / report_filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Entity report saved to {report_path}")
        return str(report_path)
    
    def generate_entity_report_multiple_formats(self, entity_id: int, formats: List[str] = ['md', 'docx', 'txt']) -> Dict[str, str]:
        """Generate entity report in multiple formats."""
        logger.info(f"Generating entity report in formats: {formats}")
        
        # First generate the markdown report
        md_path = self.generate_entity_report(entity_id)
        if not md_path:
            return {}
        
        # Convert to other formats
        converted_paths = {'md': md_path}
        
        for format_type in formats:
            if format_type != 'md':
                try:
                    converted_path = self.format_converter.convert_report(md_path, format_type)
                    converted_paths[format_type] = converted_path
                    logger.info(f"Converted to {format_type}: {converted_path}")
                except Exception as e:
                    logger.error(f"Failed to convert to {format_type}: {e}")
        
        return converted_paths
    
    def generate_capability_cluster_report(self, capability_type: CapabilityType) -> str:
        """Generate report for a capability cluster."""
        logger.info(f"Generating cluster report for {capability_type.name}")
        
        # Get entities with this capability
        entities = self.db_ops.get_entities_by_capability(capability_type)
        if not entities:
            logger.warning(f"No entities found for capability {capability_type.name}")
            return ""
        
        # Prepare template data
        template_data = self._prepare_cluster_data(capability_type, entities)
        
        # Render template
        template = self.jinja_env.get_template('cluster_report.md')
        report_content = template.render(**template_data)
        
        # Save report
        report_filename = f"{capability_type.name}_cluster_report.md"
        report_path = self.reports_dir / "clusters" / report_filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Cluster report saved to {report_path}")
        return str(report_path)
    
    def generate_all_entity_reports(self) -> List[str]:
        """Generate reports for all entities."""
        logger.info("Generating reports for all entities")
        
        # Get all entities
        entities = self.db_ops.search_entities("")
        report_paths = []
        
        for entity in entities:
            try:
                report_path = self.generate_entity_report(entity.id)
                if report_path:
                    report_paths.append(report_path)
            except Exception as e:
                logger.error(f"Failed to generate report for entity {entity.id}: {e}")
        
        logger.info(f"Generated {len(report_paths)} entity reports")
        return report_paths
    
    def generate_all_cluster_reports(self) -> List[str]:
        """Generate reports for all capability clusters."""
        logger.info("Generating reports for all capability clusters")
        
        report_paths = []
        
        for capability_type in CapabilityType:
            try:
                report_path = self.generate_capability_cluster_report(capability_type)
                if report_path:
                    report_paths.append(report_path)
            except Exception as e:
                logger.error(f"Failed to generate cluster report for {capability_type.name}: {e}")
        
        logger.info(f"Generated {len(report_paths)} cluster reports")
        return report_paths
    
    def _prepare_cluster_data(self, capability_type: CapabilityType, entities: List) -> Dict[str, Any]:
        """Prepare data for cluster report template."""
        # Get capability summary
        capability_summary = self._get_capability_summary(capability_type)
        
        # Calculate statistics
        total_funding = 0
        total_confidence = 0
        high_confidence_count = 0
        
        entity_data = []
        funding_by_entity = []
        
        for entity in entities:
            # Get entity summary
            summary = self.db_ops.get_entity_summary(entity.id)
            if not summary:
                continue
            
            # Calculate entity statistics
            entity_funding = summary['total_funding']
            entity_capabilities = summary['capabilities']
            entity_confidence = sum(cap.confidence_score for cap in entity_capabilities) / len(entity_capabilities) if entity_capabilities else 0
            
            total_funding += entity_funding
            total_confidence += entity_confidence
            
            if entity_confidence >= 0.8:
                high_confidence_count += 1
            
            # Prepare entity data
            entity_info = {
                'name': entity.name,
                'entity_type': entity.entity_type,
                'total_funding': entity_funding,
                'avg_confidence': entity_confidence,
                'capability_count': len(entity_capabilities)
            }
            entity_data.append(entity_info)
            
            # Prepare funding data
            if summary['funding']:
                funding_by_entity.append({
                    'entity_name': entity.name,
                    'total_amount': entity_funding,
                    'funding_details': summary['funding']
                })
        
        avg_confidence = total_confidence / len(entities) if entities else 0
        
        # Get relationships
        relationships = self._get_cluster_relationships(entities)
        
        # Get capability statistics
        capability_stats = self._get_capability_statistics(capability_type, entities)
        
        # Get data sources
        data_sources = self._get_cluster_data_sources(entities)
        
        return {
            'capability_name': capability_summary['name'],
            'capability_description': capability_summary['description'],
            'capability_id': capability_type.value,
            'entities': entity_data,
            'total_funding': total_funding,
            'avg_confidence': avg_confidence,
            'high_confidence_count': high_confidence_count,
            'funding_by_entity': funding_by_entity,
            'relationships': relationships,
            'capability_stats': capability_stats,
            'data_sources': data_sources,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'relationship_count': len(relationships),
            'avg_connections': self._calculate_avg_connections(entities),
            'most_connected_entity': self._get_most_connected_entity(entities),
            'most_connected_count': self._get_most_connected_count(entities),
            'top_funded_entities': sorted(entity_data, key=lambda x: x['total_funding'], reverse=True)[:5],
            'top_confidence_entities': sorted(entity_data, key=lambda x: x['avg_confidence'], reverse=True)[:5],
            'trends': self._get_capability_trends(capability_type),
            'focus_areas': self._get_focus_areas(capability_type),
            'data_gaps': self._get_data_gaps(capability_type),
            'update_frequency': 'Monthly',
            'review_items_count': self._get_review_items_count(entities)
        }
    
    def _get_capability_summary(self, capability_type: CapabilityType) -> Dict[str, str]:
        """Get capability summary information."""
        summaries = {
            CapabilityType.THREE_D_PACKAGING: {
                'name': '3D Packaging',
                'description': '3D packaging, chiplets, HBM, advanced interconnects'
            },
            CapabilityType.HETEROGENEOUS_PACKAGING: {
                'name': 'Heterogeneous Packaging',
                'description': 'Mixed-technology integration, system-in-package, heterogeneous integration'
            },
            CapabilityType.MULTI_PROJECT_WAFER: {
                'name': 'Multi Project Wafer',
                'description': 'MPW services, shared wafer runs, prototyping, low-volume production'
            },
            CapabilityType.RFIC_DESIGN: {
                'name': 'Radio Frequency Integrated Circuit (RFIC) Design',
                'description': 'RF, wireless, 5G/6G, millimeter wave, analog RF'
            },
            CapabilityType.MMIC_CHIPS: {
                'name': 'Monolithic Microwave Integrated Circuit (MMIC) Chips',
                'description': 'Microwave integrated circuits, high-frequency RF, MMIC design'
            },
            CapabilityType.RAD_HARD_CHIPS: {
                'name': 'Radiation Hardened (RAD-HARD) Chips',
                'description': 'Radiation-hardened electronics, space-grade, aerospace, nuclear applications'
            }
        }
        
        return summaries.get(capability_type, {'name': capability_type.name, 'description': ''})
    
    def _get_cluster_relationships(self, entities: List) -> List[Dict[str, Any]]:
        """Get relationships for entities in cluster."""
        relationships = []
        
        for entity in entities:
            entity_rels = self.db_ops.db_manager.get_relationships_by_entity(entity.id)
            for rel in entity_rels:
                # Get connected entity name
                if rel.entity_a_id == entity.id:
                    connected_entity = self.db_ops.db_manager.get_entity_by_id(rel.entity_b_id)
                else:
                    connected_entity = self.db_ops.db_manager.get_entity_by_id(rel.entity_a_id)
                
                if connected_entity:
                    relationships.append({
                        'entity_a_name': entity.name,
                        'entity_b_name': connected_entity.name,
                        'relationship_type': rel.relationship_type,
                        'confidence_score': rel.confidence_score,
                        'evidence': rel.evidence
                    })
        
        return relationships
    
    def _get_capability_statistics(self, capability_type: CapabilityType, entities: List) -> Dict[str, Any]:
        """Get capability statistics for cluster."""
        stats = {
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'below_threshold': 0,
            'evidence_types': []
        }
        
        for entity in entities:
            capabilities = self.db_ops.db_manager.get_capabilities_by_entity(entity.id)
            capability_caps = [cap for cap in capabilities if cap.capability_type == capability_type]
            
            for cap in capability_caps:
                if cap.confidence_score >= 0.8:
                    stats['high_confidence'] += 1
                elif cap.confidence_score >= 0.6:
                    stats['medium_confidence'] += 1
                elif cap.confidence_score >= 0.3:
                    stats['low_confidence'] += 1
                else:
                    stats['below_threshold'] += 1
        
        return stats
    
    def _get_cluster_data_sources(self, entities: List) -> List[Dict[str, Any]]:
        """Get data sources for cluster."""
        source_counts = {}
        total_sources = 0
        
        for entity in entities:
            sources = self.db_ops.db_manager.execute_query(
                "SELECT source_type FROM data_sources WHERE entity_id = ?",
                (entity.id,)
            )
            
            for source in sources:
                source_type = source['source_type']
                source_counts[source_type] = source_counts.get(source_type, 0) + 1
                total_sources += 1
        
        data_sources = []
        for source_type, count in source_counts.items():
            data_sources.append({
                'source_type': source_type,
                'count': count,
                'coverage': (count / total_sources * 100) if total_sources > 0 else 0
            })
        
        return data_sources
    
    def _calculate_avg_connections(self, entities: List) -> float:
        """Calculate average connections per entity."""
        total_connections = 0
        
        for entity in entities:
            relationships = self.db_ops.db_manager.get_relationships_by_entity(entity.id)
            total_connections += len(relationships)
        
        return total_connections / len(entities) if entities else 0
    
    def _get_most_connected_entity(self, entities: List):
        """Get most connected entity in cluster."""
        max_connections = 0
        most_connected = None
        
        for entity in entities:
            relationships = self.db_ops.db_manager.get_relationships_by_entity(entity.id)
            if len(relationships) > max_connections:
                max_connections = len(relationships)
                most_connected = entity
        
        return most_connected
    
    def _get_most_connected_count(self, entities: List) -> int:
        """Get connection count for most connected entity."""
        most_connected = self._get_most_connected_entity(entities)
        if most_connected:
            relationships = self.db_ops.db_manager.get_relationships_by_entity(most_connected.id)
            return len(relationships)
        return 0
    
    def _get_capability_trends(self, capability_type: CapabilityType) -> List[Dict[str, str]]:
        """Get trends for capability area."""
        # This would be implemented based on historical data
        return [
            {
                'trend': 'Growing Investment',
                'description': 'Increased funding in this capability area over the past year'
            },
            {
                'trend': 'Technology Maturation',
                'description': 'Capability moving from research to production phase'
            }
        ]
    
    def _get_focus_areas(self, capability_type: CapabilityType) -> List[str]:
        """Get focus areas for capability."""
        focus_areas = {
            CapabilityType.THREE_D_PACKAGING: ['3D Integration', 'Chiplet Architecture', 'HBM Development'],
            CapabilityType.HETEROGENEOUS_PACKAGING: ['Mixed-Technology Integration', 'System-in-Package', 'Hybrid Integration'],
            CapabilityType.MULTI_PROJECT_WAFER: ['MPW Services', 'Prototyping', 'Low-Volume Production'],
            CapabilityType.RFIC_DESIGN: ['5G/6G Technologies', 'Millimeter Wave', 'Power Efficiency'],
            CapabilityType.MMIC_CHIPS: ['Microwave Design', 'High-Frequency RF', 'GaAs/GaN MMIC'],
            CapabilityType.RAD_HARD_CHIPS: ['Space-Grade Electronics', 'Radiation Tolerance', 'Aerospace Applications']
        }
        
        return focus_areas.get(capability_type, [])
    
    def _get_funding_type(self, funding: List) -> str:
        """Get funding type from funding data."""
        if not funding:
            return None
        
        # Look for program type indicators in project descriptions
        for fund in funding:
            if fund.project_description:
                desc_lower = fund.project_description.lower()
                if 'manufacturing' in desc_lower:
                    return 'Manufacturing'
                elif 'research' in desc_lower or 'r&d' in desc_lower:
                    return 'R&D'
                elif 'workforce' in desc_lower or 'training' in desc_lower:
                    return 'Workforce Development'
        
        return 'R&D'  # Default assumption
    
    def _get_funding_date(self, funding: List) -> str:
        """Get funding date from funding data."""
        if not funding:
            return None
        
        # Get the most recent funding date
        dates = [f.announcement_date for f in funding if f.announcement_date]
        if dates:
            return max(dates).strftime('%Y-%m-%d')
        
        return None
    
    def _get_project_location(self, funding: List) -> str:
        """Get project location from funding data."""
        if not funding:
            return None
        
        # Look for location indicators in project descriptions
        for fund in funding:
            if fund.project_description:
                # Simple location extraction (could be enhanced with NLP)
                desc = fund.project_description
                if 'california' in desc.lower():
                    return 'California'
                elif 'texas' in desc.lower():
                    return 'Texas'
                elif 'arizona' in desc.lower():
                    return 'Arizona'
                elif 'new york' in desc.lower():
                    return 'New York'
        
        return 'Not specified'
    
    def _get_academic_relationships(self, relationships: List) -> List:
        """Get academic relationships from relationships data."""
        if not relationships:
            return []
        
        academic_types = ['research_collaboration', 'partner']
        academic_keywords = ['university', 'college', 'institute', 'research', 'academic']
        
        academic_rels = []
        for rel in relationships:
            rel_type = rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type)
            if rel_type in academic_types:
                academic_rels.append(rel)
            elif rel.evidence:
                evidence_lower = rel.evidence.lower()
                if any(keyword in evidence_lower for keyword in academic_keywords):
                    academic_rels.append(rel)
        
        return academic_rels
    
    def _get_parent_subsidiary_relationships(self, relationships: List) -> List:
        """Get parent/subsidiary relationships from relationships data."""
        if not relationships:
            return []
        
        parent_subsidiary_types = ['parent_subsidiary']
        
        parent_subsidiary_rels = []
        for rel in relationships:
            rel_type = rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type)
            if rel_type in parent_subsidiary_types:
                parent_subsidiary_rels.append(rel)
        
        return parent_subsidiary_rels
    
    def _get_supply_chain_relationships(self, relationships: List) -> List:
        """Get supply chain relationships from relationships data."""
        if not relationships:
            return []
        
        supply_chain_types = ['supplier', 'customer', 'supply_chain']
        
        supply_chain_rels = []
        for rel in relationships:
            rel_type = rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type)
            if rel_type in supply_chain_types:
                supply_chain_rels.append(rel)
        
        return supply_chain_rels
    
    def _get_other_funding(self, funding: List) -> List:
        """Get other funding sources (non-CHIPS)."""
        if not funding:
            return []
        
        # For now, return empty as we're focusing on CHIPS Act funding
        # This could be enhanced to identify other funding sources
        return []
    
    def _get_data_gaps(self, capability_type: CapabilityType) -> List[str]:
        """Get data gaps for capability."""
        return [
            'Limited patent data',
            'Insufficient funding details',
            'Missing relationship information'
        ]
    
    def _get_review_items_count(self, entities: List) -> int:
        """Get count of review items for entities."""
        total_review_items = 0
        
        for entity in entities:
            review_items = self.db_ops.db_manager.get_review_queue()
            entity_review_items = [item for item in review_items if item.entity_id == entity.id]
            total_review_items += len(entity_review_items)
        
        return total_review_items
    
    def _get_review_items(self, entity_id: int) -> List[Dict[str, Any]]:
        """Get review items for entity."""
        review_items = self.db_ops.db_manager.get_review_queue()
        entity_review_items = [item for item in review_items if item.entity_id == entity_id]
        
        return [
            {
                'issue_type': item.issue_type,
                'confidence_score': item.confidence_score,
                'status': item.status,
                'notes': item.notes
            }
            for item in entity_review_items
        ]
