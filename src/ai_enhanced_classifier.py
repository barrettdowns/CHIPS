"""
AI-Enhanced Capability Classifier using OpenAI API.
Replaces rule-based classification with intelligent analysis.
"""

import openai
import json
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from enum import Enum

from .database.models import Entity, Capability, CapabilityType
from .capability_classifier.classifier import CapabilityClassifier


class AnalysisType(Enum):
    CAPABILITY_CLASSIFICATION = "capability_classification"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"
    TECHNICAL_INSIGHTS = "technical_insights"
    FUNDING_ANALYSIS = "funding_analysis"


@dataclass
class AIAnalysisResult:
    """Result from AI analysis."""
    analysis_type: AnalysisType
    confidence_score: float
    insights: List[str]
    evidence: str
    technical_details: Dict[str, Any]
    recommendations: List[str]


class AIEnhancedClassifier:
    """AI-powered capability classifier using OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.fallback_classifier = CapabilityClassifier()
        
        # Capability definitions for AI context
        self.capability_definitions = {
            CapabilityType.ADVANCED_PACKAGING: {
                "name": "Advanced Packaging",
                "description": "3D packaging technologies, chiplets, HBM (High Bandwidth Memory), advanced interconnects, system-in-package (SiP), fan-out wafer-level packaging (FOWLP), through-silicon vias (TSV)",
                "keywords": ["3D packaging", "chiplets", "HBM", "interconnects", "SiP", "FOWLP", "TSV", "advanced packaging", "heterogeneous integration"]
            },
            CapabilityType.RFIC_DESIGN: {
                "name": "RFIC Design", 
                "description": "RF integrated circuits, wireless communications, 5G/6G technologies, millimeter wave, analog RF, power amplifiers, low-noise amplifiers, mixers, oscillators",
                "keywords": ["RF", "wireless", "5G", "6G", "millimeter wave", "analog RF", "power amplifier", "LNA", "mixer", "oscillator", "RFIC"]
            },
            CapabilityType.ADVANCED_LOGIC: {
                "name": "Advanced Logic",
                "description": "Sub-7nm process technologies, EUV lithography, Gate-All-Around (GAA) transistors, advanced CMOS, logic design, CPU/GPU architectures, process scaling",
                "keywords": ["sub-7nm", "EUV", "GAA", "CMOS", "logic", "CPU", "GPU", "process node", "transistor", "lithography", "scaling"]
            },
            CapabilityType.MEMORY: {
                "name": "Memory",
                "description": "DRAM, NAND flash, emerging memory technologies (MRAM, ReRAM, PCM), memory controllers, high-speed memory interfaces, memory architecture",
                "keywords": ["DRAM", "NAND", "MRAM", "ReRAM", "PCM", "memory controller", "memory interface", "flash memory", "emerging memory"]
            },
            CapabilityType.ANALOG_POWER: {
                "name": "Analog/Power",
                "description": "Power management ICs, analog design, mixed-signal circuits, sensors, power conversion, voltage regulation, analog-to-digital converters",
                "keywords": ["power management", "analog", "mixed-signal", "sensor", "power conversion", "voltage regulation", "ADC", "DAC", "PMIC"]
            },
            CapabilityType.MATERIALS_EQUIPMENT: {
                "name": "Materials/Equipment",
                "description": "Semiconductor materials, fabrication equipment, lithography tools, deposition systems, etching equipment, substrates, process tools",
                "keywords": ["materials", "equipment", "lithography", "deposition", "etching", "substrate", "process tool", "fabrication", "semiconductor materials"]
            }
        }
    
    def classify_entity_capabilities(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Capability]:
        """Classify entity capabilities using AI analysis."""
        logger.info(f"AI classifying capabilities for {entity.name}")
        
        try:
            # Combine content for analysis
            combined_content = self._combine_content_sources(content_sources)
            if not combined_content:
                logger.warning(f"No content available for {entity.name}, using fallback")
                return self.fallback_classifier.classify_entity(entity, content_sources)
            
            # Perform AI analysis
            analysis_result = self._analyze_capabilities(entity, combined_content, content_sources)
            
            # Convert AI results to Capability objects
            capabilities = self._convert_ai_results_to_capabilities(entity, analysis_result)
            
            logger.info(f"AI classified {len(capabilities)} capabilities for {entity.name}")
            return capabilities
            
        except Exception as e:
            logger.error(f"AI classification failed for {entity.name}: {e}")
            logger.info("Falling back to rule-based classifier")
            return self.fallback_classifier.classify_entity(entity, content_sources)
    
    def _analyze_capabilities(self, entity: Entity, content: str, content_sources: List[Dict[str, Any]]) -> AIAnalysisResult:
        """Perform AI analysis of entity capabilities."""
        
        # Prepare context for AI
        context = self._prepare_analysis_context(entity, content, content_sources)
        
        # Create AI prompt
        prompt = self._create_capability_analysis_prompt(context)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a semiconductor industry expert analyzing CHIPS Act funding recipients for their technical capabilities."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=2000
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content
        analysis_result = self._parse_ai_response(ai_response)
        
        return analysis_result
    
    def _prepare_analysis_context(self, entity: Entity, content: str, content_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare context for AI analysis."""
        
        # Extract funding information
        funding_info = []
        for source in content_sources:
            if source.get('funding_amount'):
                funding_info.append({
                    'amount': source['funding_amount'],
                    'description': source.get('project_description', ''),
                    'date': source.get('collected_at', '')
                })
        
        # Extract technical details
        technical_indicators = self._extract_technical_indicators(content)
        
        return {
            'entity_name': entity.name,
            'entity_type': entity.entity_type.value,
            'content': content[:4000],  # Limit content length
            'funding_info': funding_info,
            'technical_indicators': technical_indicators,
            'source_count': len(content_sources),
            'capability_definitions': self.capability_definitions
        }
    
    def _create_capability_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for AI capability analysis."""
        
        capability_definitions_text = "\n".join([
            f"{cap_type.name}: {defn['description']}"
            for cap_type, defn in context['capability_definitions'].items()
        ])
        
        prompt = f"""
Analyze the following semiconductor entity for its technical capabilities:

ENTITY: {context['entity_name']} ({context['entity_type']})
FUNDING: {context['funding_info']}
TECHNICAL CONTEXT: {context['technical_indicators']}

CONTENT TO ANALYZE:
{context['content']}

CAPABILITY DEFINITIONS:
{capability_definitions_text}

Please analyze this entity and determine which semiconductor capability areas it operates in. Consider:

1. Direct technical mentions (process nodes, technologies, equipment)
2. Implied capabilities from funding descriptions
3. Industry context and relationships
4. Technical depth and specificity

Respond with a JSON object containing:
{{
    "capabilities": [
        {{
            "capability_type": "ADVANCED_LOGIC",
            "confidence_score": 0.85,
            "evidence": "Specific technical evidence from the content",
            "technical_details": {{
                "process_nodes": ["7nm", "5nm"],
                "technologies": ["EUV lithography", "GAA transistors"],
                "applications": ["CPU", "GPU"]
            }},
            "insights": ["Key insights about this capability"],
            "recommendations": ["Recommendations for further analysis"]
        }}
    ],
    "overall_confidence": 0.8,
    "analysis_notes": "Overall analysis notes"
}}

Focus on accuracy and provide specific technical evidence for each capability classification.
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> AIAnalysisResult:
        """Parse AI response into structured result."""
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            # Convert to AIAnalysisResult
            capabilities = parsed_data.get('capabilities', [])
            overall_confidence = parsed_data.get('overall_confidence', 0.5)
            
            insights = []
            evidence_parts = []
            technical_details = {}
            recommendations = []
            
            for cap in capabilities:
                insights.extend(cap.get('insights', []))
                evidence_parts.append(cap.get('evidence', ''))
                technical_details.update(cap.get('technical_details', {}))
                recommendations.extend(cap.get('recommendations', []))
            
            return AIAnalysisResult(
                analysis_type=AnalysisType.CAPABILITY_CLASSIFICATION,
                confidence_score=overall_confidence,
                insights=insights,
                evidence=' '.join(evidence_parts),
                technical_details=technical_details,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"AI Response: {ai_response}")
            
            # Return fallback result
            return AIAnalysisResult(
                analysis_type=AnalysisType.CAPABILITY_CLASSIFICATION,
                confidence_score=0.3,
                insights=["AI analysis failed, using fallback"],
                evidence="Analysis error",
                technical_details={},
                recommendations=["Manual review recommended"]
            )
    
    def _convert_ai_results_to_capabilities(self, entity: Entity, analysis_result: AIAnalysisResult) -> List[Capability]:
        """Convert AI analysis results to Capability objects."""
        capabilities = []
        
        # Parse the AI response again to get individual capabilities
        try:
            # This would need to be implemented based on the actual AI response structure
            # For now, return empty list - the AI response parsing needs to be completed
            pass
        except Exception as e:
            logger.error(f"Failed to convert AI results: {e}")
        
        return capabilities
    
    def _extract_technical_indicators(self, content: str) -> List[str]:
        """Extract technical indicators from content."""
        technical_patterns = [
            r'\d+nm',  # Process nodes
            r'EUV|extreme ultraviolet',
            r'GAA|gate-all-around',
            r'DRAM|NAND|MRAM|ReRAM',
            r'RF|wireless|5G|6G',
            r'packaging|chiplets|HBM',
            r'power management|PMIC',
            r'lithography|deposition|etching'
        ]
        
        import re
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
    
    def analyze_entity_relationships(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze entity relationships using AI."""
        logger.info(f"AI analyzing relationships for {entity.name}")
        
        try:
            combined_content = self._combine_content_sources(content_sources)
            if not combined_content:
                return []
            
            # Create relationship analysis prompt
            prompt = f"""
Analyze the following content for relationships between semiconductor entities:

ENTITY: {entity.name}
CONTENT: {combined_content[:3000]}

Identify relationships such as:
- Parent-subsidiary relationships
- Partnership agreements
- Consortium memberships
- Joint ventures
- Supplier-customer relationships
- Technology licensing agreements

Respond with JSON format:
{{
    "relationships": [
        {{
            "entity_name": "Partner Company Name",
            "relationship_type": "PARTNER",
            "confidence": 0.8,
            "evidence": "Specific evidence from content",
            "description": "Description of the relationship"
        }}
    ]
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a business intelligence analyst specializing in semiconductor industry relationships."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            relationships = self._parse_relationship_response(ai_response)
            
            logger.info(f"AI identified {len(relationships)} relationships for {entity.name}")
            return relationships
            
        except Exception as e:
            logger.error(f"AI relationship analysis failed for {entity.name}: {e}")
            return []
    
    def _parse_relationship_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI relationship analysis response."""
        try:
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = ai_response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            return parsed_data.get('relationships', [])
            
        except Exception as e:
            logger.error(f"Failed to parse relationship response: {e}")
            return []
    
    def generate_intelligence_summary(self, entity: Entity, capabilities: List[Capability], 
                                    relationships: List[Dict[str, Any]]) -> str:
        """Generate AI-powered intelligence summary for entity."""
        logger.info(f"Generating AI intelligence summary for {entity.name}")
        
        try:
            # Prepare summary context
            capability_summary = "\n".join([
                f"- {cap.capability_type.name}: {cap.confidence_score:.2f} confidence"
                for cap in capabilities
            ])
            
            relationship_summary = "\n".join([
                f"- {rel.get('entity_name', 'Unknown')}: {rel.get('relationship_type', 'Unknown')}"
                for rel in relationships
            ])
            
            prompt = f"""
Generate a comprehensive intelligence summary for this semiconductor entity:

ENTITY: {entity.name}
CAPABILITIES: {capability_summary}
RELATIONSHIPS: {relationship_summary}

Provide:
1. Executive summary of the entity's role in the semiconductor ecosystem
2. Key technical capabilities and their significance
3. Strategic relationships and their implications
4. Market positioning and competitive advantages
5. Potential risks or opportunities
6. Recommendations for further monitoring

Format as a professional intelligence report.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior intelligence analyst specializing in semiconductor industry analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            summary = response.choices[0].message.content
            logger.info(f"Generated intelligence summary for {entity.name}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate intelligence summary for {entity.name}: {e}")
            return f"Intelligence summary generation failed for {entity.name}: {e}"
