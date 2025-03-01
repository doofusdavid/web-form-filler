"""
PIA VPN Rotator - Provides IP rotation via Private Internet Access VPN.
"""

import time
import subprocess
import random
import requests
from .base import BaseIPRotator
from ..utils.logger import setup_logger

logger = setup_logger()

class PIAVPNRotator(BaseIPRotator):
    """Provides IP rotation via Private Internet Access VPN."""
    
    def __init__(self, pia_username, pia_password, server_list=None):
        """Initialize the PIA VPN rotator.
        
        Args:
            pia_username (str): The PIA VPN username.
            pia_password (str): The PIA VPN password.
            server_list (list, optional): List of PIA server regions to rotate through.
        """
        self.pia_username = pia_username
        self.pia_password = pia_password
        self.server_list = server_list or self._get_default_servers()
        self.current_server_index = 0
        
        # Validate PIA credentials
        if not self.pia_username or not self.pia_password:
            raise ValueError("PIA username and password are required")
            
        logger.info(f"Initialized PIA VPN rotator with {len(self.server_list)} servers")
        
        # Check if PIA client is installed
        self._check_pia_client()
        
    def apply_to_session(self, session):
        """Apply VPN to the session.
        
        Args:
            session (requests.Session): The session to use with the VPN.
            
        Returns:
            requests.Session: The session (no direct modification needed).
        """
        # Rotate IP before returning the session
        self.rotate_ip()
        
        # Test the VPN connection
        self._test_vpn_connection(session)
        
        return session
        
    def rotate_ip(self):
        """Connect to a different PIA VPN server."""
        # Get the current connection status
        current_status = self._get_connection_status()
        
        # Disconnect from current VPN if connected
        if current_status == "connected":
            self._disconnect_vpn()
        
        # Get the next server
        server = self.server_list[self.current_server_index]
        self.current_server_index = (self.current_server_index + 1) % len(self.server_list)
        
        logger.info(f"Rotating to PIA VPN server: {server}")
        
        # Connect to the new server
        self._connect_vpn(server)
        
        # Wait for connection to establish
        time.sleep(5)
        
        # Verify connection
        new_status = self._get_connection_status()
        if new_status != "connected":
            logger.warning(f"Failed to connect to PIA VPN server {server}. Status: {new_status}")
            # Try one more time with a different server
            self.current_server_index = (self.current_server_index + 1) % len(self.server_list)
            server = self.server_list[self.current_server_index]
            logger.info(f"Trying another PIA VPN server: {server}")
            self._connect_vpn(server)
            time.sleep(5)
            
    def _check_pia_client(self):
        """Check if the PIA client is installed and accessible."""
        try:
            result = subprocess.run(['piactl', 'version'], 
                                   capture_output=True, 
                                   text=True, 
                                   check=False)
            
            if result.returncode == 0:
                logger.info(f"PIA client found: {result.stdout.strip()}")
            else:
                logger.error(f"PIA client error: {result.stderr.strip()}")
                raise RuntimeError("PIA client is not working properly")
                
        except FileNotFoundError:
            logger.error("PIA client (piactl) not found")
            raise RuntimeError("PIA client (piactl) not found. Please install the PIA VPN client.")
            
    def _get_connection_status(self):
        """Get the current PIA VPN connection status.
        
        Returns:
            str: The connection status (connected, disconnected, connecting, etc.).
        """
        try:
            result = subprocess.run(['piactl', 'get', 'connectionstate'], 
                                   capture_output=True, 
                                   text=True, 
                                   check=False)
            
            if result.returncode == 0:
                return result.stdout.strip().lower()
            else:
                logger.error(f"Error getting PIA connection state: {result.stderr.strip()}")
                return "unknown"
                
        except Exception as e:
            logger.error(f"Error getting PIA connection state: {e}")
            return "unknown"
            
    def _disconnect_vpn(self):
        """Disconnect from the current VPN server."""
        try:
            logger.info("Disconnecting from PIA VPN")
            subprocess.run(['piactl', 'disconnect'], check=True)
            time.sleep(2)  # Wait for disconnection
            
            # Verify disconnection
            status = self._get_connection_status()
            if status != "disconnected":
                logger.warning(f"Failed to disconnect from PIA VPN. Status: {status}")
                
        except Exception as e:
            logger.error(f"Error disconnecting from PIA VPN: {e}")
            
    def _connect_vpn(self, server):
        """Connect to the specified VPN server.
        
        Args:
            server (str): The PIA server region to connect to.
        """
        try:
            # Set the region
            logger.info(f"Setting PIA VPN region to {server}")
            subprocess.run(['piactl', 'set', 'region', server], check=True)
            
            # Connect
            logger.info("Connecting to PIA VPN")
            subprocess.run(['piactl', 'connect'], check=True)
            
        except Exception as e:
            logger.error(f"Error connecting to PIA VPN server {server}: {e}")
            
    def _test_vpn_connection(self, session):
        """Test the VPN connection.
        
        Args:
            session (requests.Session): The session to test with.
        """
        try:
            # Try to connect to a test URL
            response = session.get("https://httpbin.org/ip", timeout=10)
            response.raise_for_status()
            
            # Log the IP address
            ip_data = response.json()
            if 'origin' in ip_data:
                logger.info(f"Successfully connected through PIA VPN. IP: {ip_data['origin']}")
            else:
                logger.warning("Connected through PIA VPN, but couldn't determine IP address")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing PIA VPN connection: {e}")
            logger.warning("Continuing anyway, but VPN may not be working correctly")
            
    def _get_default_servers(self):
        """Get a default list of PIA servers.
        
        Returns:
            list: A list of PIA server region IDs.
        """
        return [
            'us_atlanta', 'us_chicago', 'us_denver', 'us_houston',
            'us_las_vegas', 'us_miami', 'us_new_york', 'us_seattle',
            'us_washington_dc', 'us_west', 'us_east', 'us_silicon_valley',
            'ca_toronto', 'ca_vancouver', 'uk_london', 'uk_manchester',
            'australia_melbourne', 'australia_sydney', 'netherlands',
            'germany', 'france', 'switzerland', 'sweden', 'japan'
        ]