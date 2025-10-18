"""
Base collector class with OPSEC features for CHIPS Act entity tracking.
"""

import time
import random
import subprocess
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
from loguru import logger
import yaml
from pathlib import Path


class OPSECManager:
    """OPSEC management for secure data collection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.opsec_config = config.get('opsec', {})
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with OPSEC features."""
        # Set default headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Rotate user agent if enabled
        if self.opsec_config.get('user_agent_rotation', True):
            self._rotate_user_agent()
    
    def _rotate_user_agent(self):
        """Rotate user agent to appear as different browsers."""
        try:
            ua = self.user_agent.random
            self.session.headers['User-Agent'] = ua
            logger.info(f"🔄 Rotated User-Agent")
        except Exception as e:
            logger.warning(f"Failed to rotate User-Agent: {e}")
            # Fallback to a common user agent
            self.session.headers['User-Agent'] = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
    
    def check_vpn_connection(self) -> bool:
        """Check if VPN is connected."""
        if not self.opsec_config.get('vpn_check_enabled', True):
            return True
        
        try:
            vpn_command = self.opsec_config.get('vpn_command', 'nordvpn status')
            result = subprocess.run(
                vpn_command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                # Check for common VPN status indicators
                vpn_connected = any(indicator in output for indicator in [
                    'connected', 'active', 'status: connected'
                ])
                logger.info(f"VPN Status: {'Connected' if vpn_connected else 'Not Connected'}")
                return vpn_connected
            else:
                logger.warning(f"VPN check failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("VPN check timed out")
            return False
        except Exception as e:
            logger.error(f"VPN check error: {e}")
            return False
    
    def get_request_delay(self) -> float:
        """Get random delay between requests."""
        delay_range = self.opsec_config.get('request_delay_range', [2, 10])
        return random.uniform(delay_range[0], delay_range[1])
    
    def make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with OPSEC features."""
        # Check VPN connection
        if not self.check_vpn_connection():
            logger.warning("VPN not connected, skipping request")
            return None
        
        # Add random delay
        delay = self.get_request_delay()
        logger.info(f"⏳ Waiting {delay:.1f}s before request")
        time.sleep(delay)
        
        # Rotate user agent
        self._rotate_user_agent()
        
        # Make request with timeout
        timeout = kwargs.pop('timeout', 30)
        try:
            response = self.session.get(url, timeout=timeout, **kwargs)
            logger.info(f"✅ Request successful (status {response.status_code})")
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def respect_robots_txt(self, url: str) -> bool:
        """Check robots.txt compliance."""
        if not self.opsec_config.get('respect_robots_txt', True):
            return True
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                # Simple robots.txt check - in production, use robotparser
                robots_content = response.text.lower()
                if 'disallow:' in robots_content:
                    logger.info(f"Robots.txt found for {parsed_url.netloc}")
                    # For now, we'll be respectful and continue
                    # In production, implement proper robots.txt parsing
                return True
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
        
        return True


class BaseCollector(ABC):
    """Base class for data collectors with OPSEC features."""
    
    def __init__(self, config_path: str = "config/sources.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.opsec_manager = OPSECManager(self.config)
        self.collection_config = self.config.get('collection', {})
        self.data_dir = Path("data/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Collection statistics
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'items_collected': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}
    
    def _get_source_config(self, source_name: str) -> Dict[str, Any]:
        """Get configuration for specific source."""
        sources = self.config.get('sources', {})
        return sources.get(source_name, {})
    
    def _make_request(self, url: str, source_config: Dict[str, Any], **kwargs) -> Optional[requests.Response]:
        """Make request with source-specific configuration."""
        # Get rate limiting from source config
        rate_limit = source_config.get('rate_limit', {})
        requests_per_minute = rate_limit.get('requests_per_minute', 10)
        delay_between_requests = rate_limit.get('delay_between_requests', 6)
        
        # Check if we need to wait
        if self.stats['requests_made'] > 0:
            time.sleep(delay_between_requests)
        
        # Update headers from source config
        headers = kwargs.get('headers', {})
        source_headers = source_config.get('headers', {})
        headers.update(source_headers)
        kwargs['headers'] = headers
        
        # Make request
        self.stats['requests_made'] += 1
        response = self.opsec_manager.make_request(url, **kwargs)
        
        if response and response.status_code == 200:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        return response
    
    def _save_raw_data(self, data: Any, filename: str) -> str:
        """Save raw data to file."""
        file_path = self.data_dir / filename
        try:
            if isinstance(data, (dict, list)):
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
            
            logger.info(f"💾 Saved raw data to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save raw data to {file_path}: {e}")
            return ""
    
    def _extract_text_content(self, html: str, selectors: Dict[str, str]) -> Dict[str, str]:
        """Extract text content using CSS selectors."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            extracted = {}
            for key, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    # Join multiple elements if found
                    extracted[key] = ' '.join([elem.get_text(strip=True) for elem in elements])
                else:
                    extracted[key] = ""
            
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract content: {e}")
            return {}
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize URL by joining with base URL if relative."""
        return urljoin(base_url, url)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _retry_request(self, url: str, source_config: Dict[str, Any], 
                      max_retries: int = 3, **kwargs) -> Optional[requests.Response]:
        """Retry request with exponential backoff."""
        retry_attempts = self.collection_config.get('retry_attempts', 3)
        retry_delay = self.collection_config.get('retry_delay', 5)
        
        for attempt in range(max_retries):
            response = self._make_request(url, source_config, **kwargs)
            if response and response.status_code == 200:
                return response
            
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"Request failed, retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        logger.error(f"All retry attempts failed for {url}")
        return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'duration_seconds': duration,
            'success_rate': (
                self.stats['successful_requests'] / self.stats['requests_made'] 
                if self.stats['requests_made'] > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset collection statistics."""
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'items_collected': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
    
    @abstractmethod
    def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data from source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get source name. Must be implemented by subclasses."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if collector is enabled."""
        source_config = self._get_source_config(self.get_source_name())
        return source_config.get('enabled', True)
    
    def run_collection(self, **kwargs) -> List[Dict[str, Any]]:
        """Run collection with error handling and statistics."""
        if not self.is_enabled():
            logger.info(f"Collector {self.get_source_name()} is disabled")
            return []
        
        logger.info(f"Starting collection from {self.get_source_name()}")
        self.reset_stats()
        
        try:
            results = self.collect(**kwargs)
            self.stats['items_collected'] = len(results)
            
            stats = self.get_collection_stats()
            logger.info(f"Collection completed: {stats['items_collected']} items, "
                       f"{stats['successful_requests']}/{stats['requests_made']} requests successful")
            
            return results
        except Exception as e:
            logger.error(f"Collection failed for {self.get_source_name()}: {e}")
            return []
