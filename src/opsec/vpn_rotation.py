"""
OPSEC utilities for VPN management and request rotation.
"""

import subprocess
import time
import random
from typing import Optional, List
from loguru import logger


class VPNManager:
    """Manage VPN connections for OPSEC."""
    
    def __init__(self, vpn_type: str = "nordlayer"):
        self.vpn_type = vpn_type
        self.connection_status = None
        self.last_check = None
    
    def check_connection(self) -> bool:
        """Check VPN connection status."""
        try:
            if self.vpn_type == "nordlayer":
                result = subprocess.run(
                    ["nordlayer", "status"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif self.vpn_type == "nordvpn":
                result = subprocess.run(
                    ["nordvpn", "status"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    output = result.stdout.lower()
                    connected = any(indicator in output for indicator in [
                        'status: connected',
                        'connected',
                        'active'
                    ])
                    self.connection_status = connected
                    self.last_check = time.time()
                    return connected
                else:
                    logger.warning(f"NordVPN status check failed: {result.stderr}")
                    return False
            else:
                logger.warning(f"Unsupported VPN type: {self.vpn_type}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("VPN status check timed out")
            return False
        except Exception as e:
            logger.error(f"VPN status check error: {e}")
            return False
    
    def connect(self, country: Optional[str] = None) -> bool:
        """Connect to VPN."""
        try:
            if self.vpn_type == "nordvpn":
                cmd = ["nordvpn", "connect"]
                if country:
                    cmd.append(country)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.info(f"VPN connected to {country or 'default location'}")
                    return True
                else:
                    logger.error(f"VPN connection failed: {result.stderr}")
                    return False
            else:
                logger.warning(f"Unsupported VPN type: {self.vpn_type}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("VPN connection timed out")
            return False
        except Exception as e:
            logger.error(f"VPN connection error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from VPN."""
        try:
            if self.vpn_type == "nordvpn":
                result = subprocess.run(
                    ["nordvpn", "disconnect"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    logger.info("VPN disconnected")
                    return True
                else:
                    logger.error(f"VPN disconnection failed: {result.stderr}")
                    return False
            else:
                logger.warning(f"Unsupported VPN type: {self.vpn_type}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("VPN disconnection timed out")
            return False
        except Exception as e:
            logger.error(f"VPN disconnection error: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get detailed connection information."""
        try:
            if self.vpn_type == "nordvpn":
                result = subprocess.run(
                    ["nordvpn", "status"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    info = {
                        'status': 'connected' if 'Status: Connected' in output else 'disconnected',
                        'server': None,
                        'country': None,
                        'city': None,
                        'ip': None
                    }
                    
                    # Parse output for connection details
                    lines = output.split('\n')
                    for line in lines:
                        if 'Server:' in line:
                            info['server'] = line.split('Server:')[1].strip()
                        elif 'Country:' in line:
                            info['country'] = line.split('Country:')[1].strip()
                        elif 'City:' in line:
                            info['city'] = line.split('City:')[1].strip()
                        elif 'Your new IP:' in line:
                            info['ip'] = line.split('Your new IP:')[1].strip()
                    
                    return info
                else:
                    return {'status': 'error', 'message': result.stderr}
            else:
                return {'status': 'unsupported', 'vpn_type': self.vpn_type}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class RequestRotator:
    """Rotate requests to avoid detection."""
    
    def __init__(self, delay_range: tuple = (2, 10), user_agents: Optional[List[str]] = None):
        self.delay_range = delay_range
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        self.current_ua_index = 0
    
    def get_delay(self) -> float:
        """Get random delay between requests."""
        return random.uniform(self.delay_range[0], self.delay_range[1])
    
    def get_user_agent(self) -> str:
        """Get next user agent in rotation."""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return ua
    
    def wait(self):
        """Wait for random delay."""
        delay = self.get_delay()
        logger.debug(f"Waiting {delay:.2f} seconds")
        time.sleep(delay)


class OPSECValidator:
    """Validate OPSEC compliance before operations."""
    
    def __init__(self, vpn_manager: VPNManager, request_rotator: RequestRotator):
        self.vpn_manager = vpn_manager
        self.request_rotator = request_rotator
    
    def validate_before_request(self) -> bool:
        """Validate OPSEC compliance before making request."""
        # Check VPN connection
        if not self.vpn_manager.check_connection():
            logger.warning("VPN not connected, skipping request")
            return False
        
        # Apply request rotation delay
        self.request_rotator.wait()
        
        return True
    
    def get_request_headers(self) -> dict:
        """Get headers with rotated user agent."""
        return {
            'User-Agent': self.request_rotator.get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
