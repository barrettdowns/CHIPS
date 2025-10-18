"""
AI-Enhanced Capability Classifier - Drop-in Replacement
Completely isolated module that can replace the existing classifier without affecting other code.
"""

import openai
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Import only what we need from existing system
from src.database.models import Capability, CapabilityType, Entity


@dataclass
class AIClassificationResult:
    """Result from AI classification."""
    capability_type: CapabilityType
    confidence_score: float
    evidence: str
    technical_details: Dict[str, Any]
    ai_insights: List[str]


class AICapabilityClassifier:
    """
    AI-powered capability classifier using OpenAI API.
    Drop-in replacement for the existing CapabilityClassifier.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
        # Capability definitions for AI context
        self.capability_definitions = {
            CapabilityType.THREE_D_PACKAGING: {
                "name": "3D Packaging",
                "description": "3D packaging technologies, chiplets, HBM (High Bandwidth Memory), advanced interconnects, system-in-package (SiP), fan-out wafer-level packaging (FOWLP), through-silicon vias (TSV), heterogeneous integration",
                "technical_indicators": ["3D packaging", "chiplets", "HBM", "interconnects", "SiP", "FOWLP", "TSV", "advanced packaging", "heterogeneous integration", "system-in-package"]
            },
            CapabilityType.HETEROGENEOUS_PACKAGING: {
                "name": "Heterogeneous Packaging",
                "description": "Mixed-technology integration, system-in-package, heterogeneous integration, multi-chip modules, hybrid integration, technology integration, mixed-signal integration",
                "technical_indicators": ["heterogeneous packaging", "heterogeneous integration", "mixed-technology", "system-in-package", "SIP", "multi-chip module", "MCM", "hybrid integration", "technology integration"]
            },
            CapabilityType.MULTI_PROJECT_WAFER: {
                "name": "Multi Project Wafer",
                "description": "MPW services, shared wafer runs, prototyping, low-volume production, wafer sharing, multi-project, prototype wafer, test wafer, engineering wafer",
                "technical_indicators": ["multi project wafer", "MPW", "shared wafer", "prototyping", "low-volume production", "wafer sharing", "multi-project", "prototype wafer", "test wafer", "engineering wafer"]
            },
            CapabilityType.RFIC_DESIGN: {
                "name": "Radio Frequency Integrated Circuit (RFIC) Design", 
                "description": "RF integrated circuits, wireless communications, 5G/6G technologies, millimeter wave, analog RF, power amplifiers, low-noise amplifiers, mixers, oscillators, RF front-end",
                "technical_indicators": ["RF", "wireless", "5G", "6G", "millimeter wave", "analog RF", "power amplifier", "LNA", "mixer", "oscillator", "RFIC", "RF front-end", "wireless communications"]
            },
            CapabilityType.MMIC_CHIPS: {
                "name": "Monolithic Microwave Integrated Circuit (MMIC) Chips",
                "description": "Microwave integrated circuits, high-frequency RF, MMIC design, microwave amplifier, microwave mixer, microwave oscillator, microwave filter, GaAs MMIC, GaN MMIC",
                "technical_indicators": ["MMIC", "monolithic microwave integrated circuit", "microwave integrated circuit", "high-frequency RF", "microwave design", "RF microwave", "microwave amplifier", "microwave mixer", "GaAs MMIC", "GaN MMIC"]
            },
            CapabilityType.RAD_HARD_CHIPS: {
                "name": "Radiation Hardened (RAD-HARD) Chips",
                "description": "Radiation-hardened electronics, space-grade, aerospace, nuclear applications, radiation tolerance, radiation resistance, space electronics, satellite electronics, nuclear electronics, radiation effects, single event upset, SEU, total ionizing dose, TID",
                "technical_indicators": ["radiation hardened", "RAD-HARD", "RADHARD", "space-grade", "aerospace electronics", "radiation tolerance", "radiation resistance", "space electronics", "satellite electronics", "nuclear electronics", "radiation effects", "SEU", "TID"]
            }
        }
        
        logger.info("AI Capability Classifier initialized")
    
    def classify_entity(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Capability]:
        """
        Classify entity capabilities using AI analysis.
        Drop-in replacement for existing classify_entity method.
        """
        logger.info(f"AI classifying capabilities for {entity.name}")
        
        try:
            # Build content from entity's own data
            entity_content_parts = []
            if entity.name:
                entity_content_parts.append(f"Entity Name: {entity.name}")
            if entity.description:
                entity_content_parts.append(f"Description: {entity.description}")
            if entity.industry:
                entity_content_parts.append(f"Industry: {entity.industry}")
            if entity.entity_type:
                entity_content_parts.append(f"Entity Type: {entity.entity_type.value}")
            
            # Combine with external content sources
            external_content = self._combine_content_sources(content_sources)
            if external_content:
                entity_content_parts.append(f"Additional Content: {external_content}")
            
            combined_content = " ".join(entity_content_parts)
            
            if not combined_content.strip():
                logger.warning(f"No content available for {entity.name}")
                return []
            
            # Perform AI analysis
            ai_results = self._analyze_capabilities_with_ai(entity, combined_content, content_sources)
            
            # Convert AI results to Capability objects
            capabilities = self._convert_ai_results_to_capabilities(entity, ai_results)
            
            logger.info(f"AI classified {len(capabilities)} capabilities for {entity.name}")
            return capabilities
            
        except Exception as e:
            logger.error(f"AI classification failed for {entity.name}: {e}")
            return []
    
    def _analyze_capabilities_with_ai(self, entity: Entity, content: str, content_sources: List[Dict[str, Any]]) -> List[AIClassificationResult]:
        """Perform AI analysis of entity capabilities."""
        
        # Prepare context for AI
        context = self._prepare_analysis_context(entity, content, content_sources)
        
        # Create AI prompt
        prompt = self._create_capability_analysis_prompt(context)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a semiconductor industry expert analyzing CHIPS Act funding recipients for their technical capabilities. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=2000
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content
        analysis_results = self._parse_ai_response(ai_response)
        
        return analysis_results
    
    def _prepare_analysis_context(self, entity: Entity, content: str, content_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare context for AI analysis."""
        
        # Extract funding information
        funding_info = []
        total_funding = 0
        for source in content_sources:
            if source.get('funding_amount'):
                funding_info.append({
                    'amount': source['funding_amount'],
                    'description': source.get('project_description', ''),
                    'date': source.get('collected_at', '')
                })
                total_funding += source['funding_amount']
        
        # Extract technical details
        technical_indicators = self._extract_technical_indicators(content)
        
        # Extract project descriptions
        project_descriptions = []
        for source in content_sources:
            desc = source.get('project_description', '')
            if desc:
                project_descriptions.append(desc)
        
        return {
            'entity_name': entity.name,
            'entity_description': entity.description,
            'entity_type': entity.entity_type.value,
            'content': content[:4000],  # Limit content length
            'content_for_analysis': content[:4000],  # For new prompt format
            'funding_info': funding_info,
            'total_funding': total_funding,
            'technical_indicators': technical_indicators,
            'project_descriptions': project_descriptions,
            'source_count': len(content_sources),
            'capability_definitions': self.capability_definitions
        }
    
    def _create_capability_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for AI capability analysis."""
        
        prompt = f"""
You are an expert semiconductor industry analyst. Analyze the following entity and determine which of the 6 official CHIPS Act capability areas it operates in.

**Entity Information:**
Name: {context['entity_name']}
Description: {context.get('entity_description', 'Not available')}

**Content for Analysis:**
{context['content_for_analysis']}

**Official CHIPS Act Capability Areas to Identify:**
1. **3D Packaging** - Integration of multiple dies stacked vertically or horizontally within a single package to increase density and performance. Includes 3D integration, die stacking, TSV technology, 3D ICs, wafer-level packaging (WLP), system-in-package (SiP), advanced interposers, fan-out wafer-level packaging (FOWLP).

2. **Heterogeneous Packaging** - Combining different types of components (logic, memory, analog, photonics, etc.) in one package. Includes chiplet architectures, heterogeneous integration, 2.5D integration, multi-die packaging, hybrid bonding, advanced substrate technology, co-packaged optics (CPO), embedded bridge technology.

3. **Multi Project Wafer (MPW)** - Shared fabrication runs where multiple designs from different organizations are manufactured on a single wafer to reduce cost. Includes MPW runs, shuttle runs, prototype fabrication services, foundry multiproject services, silicon shuttle programs, low-volume prototyping, test chip fabrication.

4. **Radio Frequency Integrated Circuit (RFIC) Design** - Design and development of integrated circuits operating at radio frequencies (typically MHz–GHz range). Includes RF front-end design, mmWave circuit design, RF transceiver design, power amplifier/low-noise amplifier design, RF SoC design, wireless communication ICs, CMOS RF design, antenna-on-chip integration.

5. **Monolithic Microwave Integrated Circuit (MMIC) Chips** - High-frequency integrated circuits (typically >30 GHz) for radar, satellite, and defense applications. Includes microwave ICs, millimeter-wave ICs, GaAs/GaN/InP-based MMICs, monolithic RF amplifiers, T/R module components, microwave power amplifiers, radar front-end chips, space/defense microwave components.

6. **Radiation Hardened (RAD-HARD) Chips** - Semiconductor devices designed to operate reliably in high-radiation environments (space, nuclear, defense). Includes rad-tolerant electronics, space-grade semiconductors, hardened-by-design chips, TID resistance, single event upset mitigation, spaceborne microelectronics, NASA/DoD qualified components.

**Instructions:**
- Be generous in your analysis - if a company works with integrated circuits, semiconductors, or related technologies, they likely have relevant capabilities
- Consider both explicit mentions and implied capabilities from the company's focus area
- Use confidence scores from 0.3 to 1.0 (be more inclusive than restrictive)
- If a company designs/manufactures integrated circuits, they likely have RFIC Design capability
- If they work with packaging technologies, they likely have 3D Packaging or Heterogeneous Packaging capability

Respond with JSON only:
{{
    "capabilities": [
        {{
            "capability_type": "Radio Frequency Integrated Circuit (RFIC) Design",
            "confidence_score": 0.8,
            "evidence": "Company specializes in integrated circuit design and manufacturing",
            "technical_details": {{"technologies": ["integrated circuits", "semiconductor solutions"]}},
            "ai_insights": ["Core competency in IC design and manufacturing"]
        }}
    ]
}}

If no capabilities are identified, return: {{"capabilities": []}}
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> List[AIClassificationResult]:
        """Parse AI response into structured results."""
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            # Convert to AIClassificationResult objects
            results = []
            
            # Handle different response formats
            if isinstance(parsed_data, list):
                # Direct array format: [...]
                capabilities = parsed_data
            elif isinstance(parsed_data, dict):
                # Object format: {"capabilities": [...]}
                capabilities = parsed_data.get('capabilities', [])
            else:
                capabilities = []
            
            for cap_data in capabilities:
                try:
                    # Map legacy capability names to new ones
                    capability_type_name = self._map_legacy_capability_name(cap_data['capability_type'])
                    capability_type = CapabilityType[capability_type_name]
                    confidence_score = float(cap_data.get('confidence_score', 0.5))
                    evidence = cap_data.get('evidence', '')
                    technical_details = cap_data.get('technical_details', {})
                    ai_insights = cap_data.get('ai_insights', [])
                    
                    result = AIClassificationResult(
                        capability_type=capability_type,
                        confidence_score=confidence_score,
                        evidence=evidence,
                        technical_details=technical_details,
                        ai_insights=ai_insights
                    )
                    
                    results.append(result)
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse capability data: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"AI Response: {ai_response}")
            return []
    
    def _map_legacy_capability_name(self, legacy_name: str) -> str:
        """Map legacy capability names to new capability enum names."""
        mapping = {
            # Direct matches
            'RFIC_DESIGN': 'RFIC_DESIGN',
            'HETEROGENEOUS_PACKAGING': 'HETEROGENEOUS_PACKAGING',
            'MULTI_PROJECT_WAFER': 'MULTI_PROJECT_WAFER',
            'MMIC_CHIPS': 'MMIC_CHIPS',
            'RAD_HARD_CHIPS': 'RAD_HARD_CHIPS',
            'THREE_D_PACKAGING': 'THREE_D_PACKAGING',
            
            # 3D Packaging mappings
            'ADVANCED_PACKAGING': 'THREE_D_PACKAGING',
            'MEMORY': 'THREE_D_PACKAGING',
            'MEMORY_MANUFACTURING': 'THREE_D_PACKAGING',
            'DIE_STACKING': 'THREE_D_PACKAGING',
            'TSV_TECHNOLOGY': 'THREE_D_PACKAGING',
            'WAFER_LEVEL_PACKAGING': 'THREE_D_PACKAGING',
            'FOWLP': 'THREE_D_PACKAGING',
            'SYSTEM_IN_PACKAGE': 'THREE_D_PACKAGING',
            'ADVANCED_INTERPOSERS': 'THREE_D_PACKAGING',
            
            # Heterogeneous Packaging mappings
            'CHIPLET_ARCHITECTURES': 'HETEROGENEOUS_PACKAGING',
            'HETEROGENEOUS_INTEGRATION': 'HETEROGENEOUS_PACKAGING',
            'MULTI_DIE_PACKAGING': 'HETEROGENEOUS_PACKAGING',
            'HYBRID_BONDING': 'HETEROGENEOUS_PACKAGING',
            'CO_PACKAGED_OPTICS': 'HETEROGENEOUS_PACKAGING',
            'EMBEDDED_BRIDGE': 'HETEROGENEOUS_PACKAGING',
            'PHOTONICS_INTEGRATION': 'HETEROGENEOUS_PACKAGING',
            'SEMICONDUCTOR_LASER_TECHNOLOGIES': 'HETEROGENEOUS_PACKAGING',
            'ADVANCED_OPTICAL_TECHNOLOGIES': 'HETEROGENEOUS_PACKAGING',
            'OPTOELECTRONICS': 'HETEROGENEOUS_PACKAGING',
            
            # Multi Project Wafer mappings
            'MPW_RUNS': 'MULTI_PROJECT_WAFER',
            'SHUTTLE_RUNS': 'MULTI_PROJECT_WAFER',
            'PROTOTYPE_FABRICATION': 'MULTI_PROJECT_WAFER',
            'FOUNDRY_SERVICES': 'MULTI_PROJECT_WAFER',
            'SILICON_SHUTTLE': 'MULTI_PROJECT_WAFER',
            'LOW_VOLUME_PROTOTYPING': 'MULTI_PROJECT_WAFER',
            'TEST_CHIP_FABRICATION': 'MULTI_PROJECT_WAFER',
            'THERMAL_PROCESSING': 'MULTI_PROJECT_WAFER',
            'PROCESS_OPTIMIZATION': 'MULTI_PROJECT_WAFER',
            'MATERIALS_EQUIPMENT': 'MULTI_PROJECT_WAFER',
            'TEST_AND_MEASUREMENT': 'MULTI_PROJECT_WAFER',
            'WAFER_PROCESSING': 'MULTI_PROJECT_WAFER',
            'SEMICONDUCTOR_EQUIPMENT': 'MULTI_PROJECT_WAFER',
            
            # RFIC Design mappings
            'RF_FRONT_END_DESIGN': 'RFIC_DESIGN',
            'MMWAVE_CIRCUIT_DESIGN': 'RFIC_DESIGN',
            'RF_TRANSCEIVER_DESIGN': 'RFIC_DESIGN',
            'POWER_AMPLIFIER_DESIGN': 'RFIC_DESIGN',
            'LOW_NOISE_AMPLIFIER': 'RFIC_DESIGN',
            'RF_SOC_DESIGN': 'RFIC_DESIGN',
            'WIRELESS_COMMUNICATION_ICS': 'RFIC_DESIGN',
            'CMOS_RF_DESIGN': 'RFIC_DESIGN',
            'ANTENNA_ON_CHIP': 'RFIC_DESIGN',
            'ELECTRONIC_DESIGN_AUTOMATION': 'RFIC_DESIGN',
            'ANALOG_AND_MIXED_SIGNAL': 'RFIC_DESIGN',
            'ANALOG_POWER': 'RFIC_DESIGN',
            'ADVANCED_LOGIC': 'RFIC_DESIGN',
            'RF_CIRCUIT_DESIGN': 'RFIC_DESIGN',
            'RADIO_FREQUENCY_INTEGRATED_CIRCUIT_RFIC_DESIGN': 'RFIC_DESIGN',
            'RADIO FREQUENCY INTEGRATED CIRCUIT (RFIC) DESIGN': 'RFIC_DESIGN',
            '3D PACKAGING': 'THREE_D_PACKAGING',
            'HETEROGENEOUS PACKAGING': 'HETEROGENEOUS_PACKAGING',
            'MULTI PROJECT WAFER (MPW)': 'MULTI_PROJECT_WAFER',
            'MULTI PROJECT WAFER': 'MULTI_PROJECT_WAFER',
            'MONOLITHIC MICROWAVE INTEGRATED CIRCUIT (MMIC) CHIPS': 'MMIC_CHIPS',
            'MONOLITHIC MICROWAVE INTEGRATED CIRCUIT (MMIC) CHIPS': 'MMIC_CHIPS',
            'RADIATION HARDENED (RAD-HARD) CHIPS': 'RAD_HARD_CHIPS',
            'RADIATION HARDENED (RAD-HARD) CHIPS': 'RAD_HARD_CHIPS',
            
            # MMIC Chips mappings
            'MICROWAVE_ICS': 'MMIC_CHIPS',
            'MILLIMETER_WAVE_ICS': 'MMIC_CHIPS',
            'GAAS_MMICS': 'MMIC_CHIPS',
            'GAN_MMICS': 'MMIC_CHIPS',
            'INP_MMICS': 'MMIC_CHIPS',
            'MONOLITHIC_RF_AMPLIFIERS': 'MMIC_CHIPS',
            'T_R_MODULE_COMPONENTS': 'MMIC_CHIPS',
            'MICROWAVE_POWER_AMPLIFIERS': 'MMIC_CHIPS',
            'RADAR_FRONT_END_CHIPS': 'MMIC_CHIPS',
            'HIGH_FREQUENCY_RADAR': 'MMIC_CHIPS',
            'SPACE_MICROWAVE_COMPONENTS': 'MMIC_CHIPS',
            'DEFENSE_MICROWAVE': 'MMIC_CHIPS',
            'LOW_SIGNAL_LOSS_TECHNOLOGIES': 'MMIC_CHIPS',
            'HIGH_FREQUENCY_CIRCUITS': 'MMIC_CHIPS',
            
            # Radiation Hardened mappings
            'RAD_TOLERANT_ELECTRONICS': 'RAD_HARD_CHIPS',
            'SPACE_GRADE_SEMICONDUCTORS': 'RAD_HARD_CHIPS',
            'HARDENED_BY_DESIGN': 'RAD_HARD_CHIPS',
            'HARDENED_BY_PROCESS': 'RAD_HARD_CHIPS',
            'TOTAL_IONIZING_DOSE_RESISTANCE': 'RAD_HARD_CHIPS',
            'SINGLE_EVENT_UPSET_MITIGATION': 'RAD_HARD_CHIPS',
            'SPACEBORNE_MICROELECTRONICS': 'RAD_HARD_CHIPS',
            'RHBD_ASICS': 'RAD_HARD_CHIPS',
            'RHBP_FPGAS': 'RAD_HARD_CHIPS',
            'NASA_QUALIFIED_COMPONENTS': 'RAD_HARD_CHIPS',
            'DOD_QUALIFIED_COMPONENTS': 'RAD_HARD_CHIPS',
            'RADIATION_CHARACTERIZATION': 'RAD_HARD_CHIPS',
            'RADIATION_TESTING': 'RAD_HARD_CHIPS',
            'SPACE_ELECTRONICS': 'RAD_HARD_CHIPS',
            'AEROSPACE_ELECTRONICS': 'RAD_HARD_CHIPS',
        }
        
        # Try exact match first
        mapped_name = mapping.get(legacy_name, None)
        
        # If no exact match, try case-insensitive and normalized matching
        if mapped_name is None:
            legacy_normalized = legacy_name.upper().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            for key, value in mapping.items():
                key_normalized = key.upper().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                if legacy_normalized == key_normalized:
                    mapped_name = value
                    break
        
        # If still no match, return original
        if mapped_name is None:
            mapped_name = legacy_name
            
        logger.info(f"Mapped legacy capability '{legacy_name}' to '{mapped_name}'")
        return mapped_name
    
    def _convert_ai_results_to_capabilities(self, entity: Entity, ai_results: List[AIClassificationResult]) -> List[Capability]:
        """Convert AI analysis results to Capability objects."""
        capabilities = []
        
        for result in ai_results:
            # Only include capabilities above minimum threshold
            if result.confidence_score >= 0.3:
                capability = Capability(
                    entity_id=entity.id,
                    capability_type=result.capability_type,
                    confidence_score=result.confidence_score,
                    evidence=result.evidence + f" [AI Enhanced: {', '.join(result.ai_insights[:2])}]"
                )
                
                capabilities.append(capability)
        
        return capabilities
    
    def _extract_technical_indicators(self, content: str) -> List[str]:
        """Extract technical indicators from content."""
        technical_patterns = [
            r'\d+nm',  # Process nodes
            r'EUV|extreme ultraviolet',
            r'GAA|gate-all-around',
            r'DRAM|NAND|MRAM|ReRAM|PCM',
            r'RF|wireless|5G|6G',
            r'packaging|chiplets|HBM',
            r'power management|PMIC',
            r'lithography|deposition|etching',
            r'CPU|GPU|processor',
            r'memory|storage',
            r'analog|digital|mixed-signal',
            r'sensor|transducer',
            r'equipment|tool|machine'
        ]
        
        indicators = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            indicators.extend(matches)
        
        return list(set(indicators))  # Remove duplicates
    
    def _combine_content_sources(self, content_sources: List[Dict[str, Any]]) -> str:
        """Combine content from multiple sources."""
        combined = []
        
        for source in content_sources:
            content = source.get('content', '')
            if content:
                combined.append(content)
            
            project_desc = source.get('project_description', '')
            if project_desc:
                combined.append(project_desc)
            
            funding_info = source.get('funding_info', {})
            if funding_info:
                project_desc = funding_info.get('project_description', '')
                if project_desc:
                    combined.append(project_desc)
        
        return ' '.join(combined)
    
    def classify_all_entities(self, entities: List[Entity], content_sources: List[Dict[str, Any]]) -> Dict[int, List[Capability]]:
        """
        Classify capabilities for all entities.
        Drop-in replacement for existing classify_all_entities method.
        """
        entity_capabilities = {}
        
        for entity in entities:
            logger.info(f"AI classifying capabilities for {entity.name}")
            
            # Get content sources relevant to this entity
            entity_sources = self._get_entity_sources(entity, content_sources)
            
            # Classify capabilities
            capabilities = self.classify_entity(entity, entity_sources)
            entity_capabilities[entity.id] = capabilities
            
            logger.info(f"Found {len(capabilities)} capabilities for {entity.name}")
        
        return entity_capabilities
    
    def _get_entity_sources(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get content sources relevant to specific entity."""
        relevant_sources = []
        entity_name_lower = entity.name.lower()
        
        for source in content_sources:
            content = source.get('content', '').lower()
            entities = source.get('entities', [])
            
            # Check if entity name appears in content
            if entity_name_lower in content:
                relevant_sources.append(source)
                continue
            
            # Check if entity is in entities list
            if any(entity_name_lower in entity_name.lower() for entity_name in entities):
                relevant_sources.append(source)
                continue
            
            # Check project description
            project_desc = source.get('project_description', '').lower()
            if entity_name_lower in project_desc:
                relevant_sources.append(source)
                continue
        
        return relevant_sources
    
    def get_capability_summary(self, capability_type: CapabilityType) -> Dict[str, Any]:
        """Get summary for a specific capability type."""
        capability_def = self.capability_definitions.get(capability_type, {})
        
        return {
            'id': capability_type.value,
            'name': capability_def.get('name', capability_type.name),
            'description': capability_def.get('description', ''),
            'technical_indicators': capability_def.get('technical_indicators', [])
        }
    
    def get_all_capabilities_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary for all capabilities."""
        summary = {}
        
        for capability_type, capability_def in self.capability_definitions.items():
            summary[str(capability_type.value)] = {
                'name': capability_def.get('name', ''),
                'description': capability_def.get('description', ''),
                'technical_indicators': capability_def.get('technical_indicators', [])
            }
        
        return summary
