"""
SOCKS Proxy Rotator - Provides IP rotation via SOCKS proxy.
"""

import requests
from .base import BaseIPRotator
from ..utils.logger import setup_logger

logger = setup_logger()

class SOCKSProxyRotator(BaseIPRotator):
    """Provides IP rotation via SOCKS proxy."""
    
    def __init__(self, proxy_host, proxy_port, proxy_username=None, proxy_password=None):
        """Initialize the SOCKS proxy rotator.
        
        Args:
            proxy_host (str): The SOCKS proxy host.
            proxy_port (int): The SOCKS proxy port.
            proxy_username (str, optional): The SOCKS proxy username.
            proxy_password (str, optional): The SOCKS proxy password.
        """
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        
        # Validate proxy settings
        if not self.proxy_host or not self.proxy_port:
            raise ValueError("SOCKS proxy host and port are required")
            
        logger.info(f"Initialized SOCKS proxy rotator with host {proxy_host}:{proxy_port}")
        
    def apply_to_session(self, session):
        """Apply SOCKS proxy to the session.
        
        Args:
            session (requests.Session): The session to apply the proxy to.
            
        Returns:
            requests.Session: The modified session.
        """
        # Construct the proxy URL
        proxy_url = f"socks5://"
        
        if self.proxy_username and self.proxy_password:
            proxy_url += f"{self.proxy_username}:{self.proxy_password}@"
            
        proxy_url += f"{self.proxy_host}:{self.proxy_port}"
        
        # Apply the proxy to the session
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        logger.info(f"Applied SOCKS proxy to session: {self.proxy_host}:{self.proxy_port}")
        
        # Test the proxy connection
        self._test_proxy_connection(session)
        
        return session
    
    def _test_proxy_connection(self, session):
        """Test the proxy connection.
        
        Args:
            session (requests.Session): The session with the proxy applied.
        """
        try:
            # Try to connect to a test URL
            response = session.get("https://httpbin.org/ip", timeout=10)
            response.raise_for_status()
            
            # Log the IP address
            ip_data = response.json()
            if 'origin' in ip_data:
                logger.info(f"Successfully connected through SOCKS proxy. IP: {ip_data['origin']}")
            else:
                logger.warning("Connected through SOCKS proxy, but couldn't determine IP address")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing SOCKS proxy connection: {e}")
            logger.warning("Continuing anyway, but proxy may not be working correctly")