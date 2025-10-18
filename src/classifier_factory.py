"""
Classifier Factory - Easy switching between rule-based and AI classifiers
"""

import yaml
from pathlib import Path
from loguru import logger
from typing import Optional

from src.capability_classifier.classifier import CapabilityClassifier
from src.ai_capability_classifier import AICapabilityClassifier


class ClassifierFactory:
    """Factory for creating capability classifiers."""
    
    def __init__(self, config_path: str = "config/ai_classifier.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return {'classifier_type': 'rule_based'}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {'classifier_type': 'rule_based'}
    
    def create_classifier(self, api_key: Optional[str] = None) -> CapabilityClassifier:
        """
        Create a capability classifier based on configuration.
        
        Args:
            api_key: OpenAI API key (required for AI classifier)
            
        Returns:
            CapabilityClassifier instance
        """
        classifier_type = self.config.get('classifier_type', 'rule_based')
        
        if classifier_type == 'ai':
            if not api_key:
                logger.error("API key required for AI classifier")
                logger.info("Falling back to rule-based classifier")
                return CapabilityClassifier()
            
            logger.info("Creating AI-powered capability classifier")
            return AICapabilityClassifier(api_key)
        
        else:
            logger.info("Creating rule-based capability classifier")
            return CapabilityClassifier()
    
    def get_classifier_info(self) -> dict:
        """Get information about the current classifier configuration."""
        classifier_type = self.config.get('classifier_type', 'rule_based')
        
        info = {
            'type': classifier_type,
            'description': self._get_classifier_description(classifier_type),
            'config_file': str(self.config_path),
            'ai_settings': self.config.get('ai_settings', {}),
            'cost_control': self.config.get('cost_control', {})
        }
        
        return info
    
    def _get_classifier_description(self, classifier_type: str) -> str:
        """Get description for classifier type."""
        descriptions = {
            'rule_based': 'Rule-based classifier using keyword matching and patterns',
            'ai': 'AI-powered classifier using OpenAI GPT models'
        }
        
        return descriptions.get(classifier_type, 'Unknown classifier type')
    
    def switch_to_ai(self, api_key: str) -> bool:
        """Switch to AI classifier."""
        try:
            self.config['classifier_type'] = 'ai'
            self._save_config()
            logger.info("Switched to AI classifier")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to AI classifier: {e}")
            return False
    
    def switch_to_rule_based(self) -> bool:
        """Switch to rule-based classifier."""
        try:
            self.config['classifier_type'] = 'rule_based'
            self._save_config()
            logger.info("Switched to rule-based classifier")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to rule-based classifier: {e}")
            return False
    
    def _save_config(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)


# Convenience functions for easy usage
def get_classifier(api_key: Optional[str] = None) -> CapabilityClassifier:
    """Get a capability classifier instance."""
    factory = ClassifierFactory()
    return factory.create_classifier(api_key)


def switch_to_ai_classifier(api_key: str) -> bool:
    """Switch to AI classifier."""
    factory = ClassifierFactory()
    return factory.switch_to_ai(api_key)


def switch_to_rule_based_classifier() -> bool:
    """Switch to rule-based classifier."""
    factory = ClassifierFactory()
    return factory.switch_to_rule_based()


def get_classifier_status() -> dict:
    """Get current classifier status."""
    factory = ClassifierFactory()
    return factory.get_classifier_info()
