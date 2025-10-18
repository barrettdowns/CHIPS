"""
Cost-Effective AI Enhancement for CHIPS System
Hybrid approach: AI for edge cases and validation only
"""

import openai
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from dataclasses import dataclass

from .capability_classifier.classifier import CapabilityClassifier
from .database.models import Entity, Capability, CapabilityType


@dataclass
class CostTracker:
    """Track AI usage costs."""
    tokens_used: int = 0
    cost_estimate: float = 0.0
    requests_made: int = 0


class CostEffectiveAIEnhancer:
    """Cost-effective AI enhancement using hybrid approach."""
    
    def __init__(self, api_key: str, daily_budget: float = 5.0):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Most cost-effective model
        self.daily_budget = daily_budget
        self.cost_tracker = CostTracker()
        
        # Use existing classifier as primary
        self.primary_classifier = CapabilityClassifier()
        
        # AI enhancement thresholds
        self.ai_thresholds = {
            'low_confidence': 0.4,  # Use AI for low confidence classifications
            'conflicting_evidence': True,  # Use AI when evidence conflicts
            'new_entity_types': True,  # Use AI for unfamiliar entity types
            'complex_relationships': True  # Use AI for relationship analysis
        }
        
        logger.info(f"Cost-effective AI enhancer initialized with ${daily_budget} daily budget")
    
    def should_use_ai(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> bool:
        """Determine if AI analysis is cost-effective for this entity."""
        
        # Check daily budget
        if self.cost_tracker.cost_estimate >= self.daily_budget:
            logger.warning("Daily AI budget exceeded, using rule-based classification")
            return False
        
        # Use AI for high-value entities only
        funding_amount = self._get_funding_amount(content_sources)
        if funding_amount > 50:  # Only for entities with >$50M funding
            return True
        
        # Use AI for low-confidence rule-based results
        rule_based_capabilities = self.primary_classifier.classify_entity(entity, content_sources)
        if any(cap.confidence_score < self.ai_thresholds['low_confidence'] for cap in rule_based_capabilities):
            return True
        
        # Use AI for complex technical content
        if self._has_complex_technical_content(content_sources):
            return True
        
        return False
    
    def classify_entity_hybrid(self, entity: Entity, content_sources: List[Dict[str, Any]]) -> List[Capability]:
        """Hybrid classification: rule-based primary, AI enhancement for edge cases."""
        
        # Always start with rule-based classification
        rule_based_capabilities = self.primary_classifier.classify_entity(entity, content_sources)
        
        # Check if AI enhancement is cost-effective
        if not self.should_use_ai(entity, content_sources):
            logger.info(f"Using rule-based classification for {entity.name} (cost-effective)")
            return rule_based_capabilities
        
        # Use AI for enhancement
        logger.info(f"Using AI enhancement for {entity.name} (high-value entity)")
        try:
            ai_enhanced_capabilities = self._ai_enhance_classification(entity, content_sources, rule_based_capabilities)
            return ai_enhanced_capabilities
        except Exception as e:
            logger.error(f"AI enhancement failed for {entity.name}: {e}")
            return rule_based_capabilities
    
    def _ai_enhance_classification(self, entity: Entity, content_sources: List[Dict[str, Any]], 
                                 existing_capabilities: List[Capability]) -> List[Capability]:
        """Use AI to enhance existing classifications."""
        
        # Prepare focused prompt for specific issues
        combined_content = self._combine_content_sources(content_sources)
        
        # Create targeted prompt for low-confidence areas
        low_confidence_areas = [cap.capability_type.name for cap in existing_capabilities 
                               if cap.confidence_score < 0.6]
        
        prompt = f"""
Analyze this semiconductor entity for specific capability areas:

ENTITY: {entity.name}
FUNDING: ${self._get_funding_amount(content_sources)}M

CONTENT: {combined_content[:2000]}  # Limit content to control costs

FOCUS AREAS: {', '.join(low_confidence_areas) if low_confidence_areas else 'All capability areas'}

Respond with JSON only:
{{
    "capabilities": [
        {{
            "type": "ADVANCED_LOGIC",
            "confidence": 0.85,
            "evidence": "Brief evidence",
            "technical_details": "Key technical aspects"
        }}
    ],
    "cost_estimate": "Estimated tokens used"
}}

Keep response concise to minimize costs.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a semiconductor expert. Respond with JSON only. Be concise."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800  # Limit output to control costs
        )
        
        # Track costs
        self._track_costs(response)
        
        # Parse and merge results
        ai_results = self._parse_ai_response(response.choices[0].message.content)
        enhanced_capabilities = self._merge_classifications(existing_capabilities, ai_results)
        
        return enhanced_capabilities
    
    def _track_costs(self, response):
        """Track API usage costs."""
        # Estimate costs based on token usage
        # This is approximate - actual costs depend on input/output token counts
        estimated_tokens = 1000  # Conservative estimate
        estimated_cost = (estimated_tokens / 1_000_000) * 0.15  # Input cost
        
        self.cost_tracker.tokens_used += estimated_tokens
        self.cost_tracker.cost_estimate += estimated_cost
        self.cost_tracker.requests_made += 1
        
        logger.info(f"AI cost: ${estimated_cost:.4f} (Total: ${self.cost_tracker.cost_estimate:.2f})")
    
    def _parse_ai_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response with error handling."""
        try:
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = ai_response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            return parsed_data.get('capabilities', [])
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return []
    
    def _merge_classifications(self, existing: List[Capability], ai_results: List[Dict[str, Any]]) -> List[Capability]:
        """Merge rule-based and AI classifications."""
        enhanced_capabilities = []
        
        # Keep high-confidence rule-based results
        for cap in existing:
            if cap.confidence_score >= 0.7:
                enhanced_capabilities.append(cap)
        
        # Add AI-enhanced results
        for ai_cap in ai_results:
            capability_type = CapabilityType[ai_cap['type']]
            confidence = ai_cap.get('confidence', 0.5)
            
            # Only add if AI confidence is higher than existing
            existing_cap = next((c for c in existing if c.capability_type == capability_type), None)
            if not existing_cap or confidence > existing_cap.confidence_score:
                enhanced_capability = Capability(
                    entity_id=existing[0].entity_id if existing else None,
                    capability_type=capability_type,
                    confidence_score=confidence,
                    evidence=ai_cap.get('evidence', '') + ' [AI Enhanced]'
                )
                enhanced_capabilities.append(enhanced_capability)
        
        return enhanced_capabilities
    
    def _get_funding_amount(self, content_sources: List[Dict[str, Any]]) -> float:
        """Extract funding amount from content sources."""
        for source in content_sources:
            funding_amount = source.get('funding_amount')
            if funding_amount:
                return funding_amount
        return 0.0
    
    def _has_complex_technical_content(self, content_sources: List[Dict[str, Any]]) -> bool:
        """Check if content has complex technical details."""
        combined_content = self._combine_content_sources(content_sources)
        
        complex_indicators = [
            'process node', 'nm', 'EUV', 'GAA', 'transistor',
            'lithography', 'deposition', 'packaging', 'interconnect',
            'architecture', 'fabrication', 'manufacturing'
        ]
        
        content_lower = combined_content.lower()
        return sum(1 for indicator in complex_indicators if indicator in content_lower) >= 3
    
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
        
        return ' '.join(combined)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for monitoring."""
        return {
            'tokens_used': self.cost_tracker.tokens_used,
            'cost_estimate': self.cost_tracker.cost_estimate,
            'requests_made': self.cost_tracker.requests_made,
            'daily_budget': self.daily_budget,
            'budget_remaining': self.daily_budget - self.cost_tracker.cost_estimate,
            'budget_utilization': (self.cost_tracker.cost_estimate / self.daily_budget) * 100
        }
    
    def reset_daily_costs(self):
        """Reset daily cost tracking."""
        self.cost_tracker = CostTracker()
        logger.info("Daily AI costs reset")


class SmartAIOrchestrator:
    """Orchestrate AI usage based on cost and value."""
    
    def __init__(self, api_key: str, monthly_budget: float = 50.0):
        self.enhancer = CostEffectiveAIEnhancer(api_key, daily_budget=monthly_budget/30)
        self.usage_stats = {
            'ai_enhanced': 0,
            'rule_based': 0,
            'total_savings': 0.0
        }
    
    def process_entity_batch(self, entities: List[Entity], content_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process batch of entities with cost optimization."""
        
        results = {
            'processed': 0,
            'ai_enhanced': 0,
            'rule_based': 0,
            'total_cost': 0.0,
            'cost_per_entity': 0.0
        }
        
        for entity in entities:
            try:
                capabilities = self.enhancer.classify_entity_hybrid(entity, content_sources)
                
                # Track usage
                if self.enhancer.cost_tracker.requests_made > self.usage_stats['ai_enhanced']:
                    self.usage_stats['ai_enhanced'] += 1
                    results['ai_enhanced'] += 1
                else:
                    self.usage_stats['rule_based'] += 1
                    results['rule_based'] += 1
                
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Failed to process entity {entity.name}: {e}")
        
        results['total_cost'] = self.enhancer.cost_tracker.cost_estimate
        results['cost_per_entity'] = results['total_cost'] / results['processed'] if results['processed'] > 0 else 0
        
        return results
