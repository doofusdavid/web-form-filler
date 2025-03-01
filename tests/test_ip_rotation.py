"""
Tests for the IP rotation module.
"""

import unittest
from unittest.mock import patch, MagicMock, call

from web_form_filler.ip_rotation.base import BaseIPRotator
from web_form_filler.ip_rotation.socks_proxy import SOCKSProxyRotator
from web_form_filler.ip_rotation.pia_vpn import PIAVPNRotator

class TestSOCKSProxyRotator(unittest.TestCase):
    """Tests for the SOCKSProxyRotator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 1080
        self.proxy_username = "user"
        self.proxy_password = "pass"
    
    def test_init(self):
        """Test initialization."""
        # Test with required parameters
        rotator = SOCKSProxyRotator(self.proxy_host, self.proxy_port)
        self.assertEqual(rotator.proxy_host, self.proxy_host)
        self.assertEqual(rotator.proxy_port, self.proxy_port)
        self.assertIsNone(rotator.proxy_username)
        self.assertIsNone(rotator.proxy_password)
        
        # Test with all parameters
        rotator = SOCKSProxyRotator(
            self.proxy_host, 
            self.proxy_port, 
            self.proxy_username, 
            self.proxy_password
        )
        self.assertEqual(rotator.proxy_host, self.proxy_host)
        self.assertEqual(rotator.proxy_port, self.proxy_port)
        self.assertEqual(rotator.proxy_username, self.proxy_username)
        self.assertEqual(rotator.proxy_password, self.proxy_password)
        
        # Test with invalid parameters
        with self.assertRaises(ValueError):
            SOCKSProxyRotator(None, self.proxy_port)
        with self.assertRaises(ValueError):
            SOCKSProxyRotator(self.proxy_host, None)
    
    @patch('requests.Session')
    def test_apply_to_session(self, mock_session):
        """Test applying the proxy to a session."""
        # Mock the session
        mock_session_instance = MagicMock()
        
        # Create the rotator
        rotator = SOCKSProxyRotator(
            self.proxy_host, 
            self.proxy_port, 
            self.proxy_username, 
            self.proxy_password
        )
        
        # Apply to session
        result = rotator.apply_to_session(mock_session_instance)
        
        # Check that the session was modified correctly
        self.assertEqual(result, mock_session_instance)
        self.assertEqual(
            result.proxies,
            {
                'http': f'socks5://{self.proxy_username}:{self.proxy_password}@{self.proxy_host}:{self.proxy_port}',
                'https': f'socks5://{self.proxy_username}:{self.proxy_password}@{self.proxy_host}:{self.proxy_port}'
            }
        )
        
        # Test without username/password
        rotator = SOCKSProxyRotator(self.proxy_host, self.proxy_port)
        result = rotator.apply_to_session(mock_session_instance)
        self.assertEqual(
            result.proxies,
            {
                'http': f'socks5://{self.proxy_host}:{self.proxy_port}',
                'https': f'socks5://{self.proxy_host}:{self.proxy_port}'
            }
        )
    
    @patch('requests.get')
    def test_test_proxy_connection(self, mock_get):
        """Test the _test_proxy_connection method."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {'origin': '1.2.3.4'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Create the rotator
        rotator = SOCKSProxyRotator(self.proxy_host, self.proxy_port)
        
        # Mock the session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        
        # Test the connection
        rotator._test_proxy_connection(mock_session)
        
        # Check that the session was used correctly
        mock_session.get.assert_called_once_with("https://httpbin.org/ip", timeout=10)
        
        # Test with error
        mock_session.get.side_effect = Exception("Connection error")
        rotator._test_proxy_connection(mock_session)  # Should not raise an exception

class TestPIAVPNRotator(unittest.TestCase):
    """Tests for the PIAVPNRotator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pia_username = "user"
        self.pia_password = "pass"
        self.server_list = ["us_east", "us_west", "uk_london"]
    
    @patch('subprocess.run')
    def test_init(self, mock_run):
        """Test initialization."""
        # Mock the subprocess.run call to check PIA client
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "PIA Client v2.0"
        
        # Test with required parameters
        rotator = PIAVPNRotator(self.pia_username, self.pia_password)
        self.assertEqual(rotator.pia_username, self.pia_username)
        self.assertEqual(rotator.pia_password, self.pia_password)
        self.assertGreater(len(rotator.server_list), 0)
        
        # Test with all parameters
        rotator = PIAVPNRotator(
            self.pia_username, 
            self.pia_password, 
            self.server_list
        )
        self.assertEqual(rotator.pia_username, self.pia_username)
        self.assertEqual(rotator.pia_password, self.pia_password)
        self.assertEqual(rotator.server_list, self.server_list)
        
        # Test with invalid parameters
        with self.assertRaises(ValueError):
            PIAVPNRotator(None, self.pia_password)
        with self.assertRaises(ValueError):
            PIAVPNRotator(self.pia_username, None)
        
        # Test with PIA client not found
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'piactl'")
        with self.assertRaises(RuntimeError):
            PIAVPNRotator(self.pia_username, self.pia_password)
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_rotate_ip(self, mock_sleep, mock_run):
        """Test the rotate_ip method."""
        # Mock the subprocess.run calls
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "connected"
        
        # Create the rotator
        rotator = PIAVPNRotator(
            self.pia_username, 
            self.pia_password, 
            self.server_list
        )
        
        # Mock the _get_connection_status method
        rotator._get_connection_status = MagicMock(return_value="connected")
        
        # Rotate IP
        rotator.rotate_ip()
        
        # Check that the subprocess.run was called correctly
        expected_calls = [
            call(['piactl', 'version'], capture_output=True, text=True, check=False),
            call(['piactl', 'disconnect'], check=True),
            call(['piactl', 'set', 'region', self.server_list[0]], check=True),
            call(['piactl', 'connect'], check=True)
        ]
        mock_run.assert_has_calls(expected_calls)
        
        # Check that time.sleep was called
        mock_sleep.assert_called()
        
        # Test with disconnected status
        rotator._get_connection_status = MagicMock(return_value="disconnected")
        rotator.rotate_ip()
        
        # Check that disconnect was not called again
        expected_calls = [
            call(['piactl', 'set', 'region', self.server_list[1]], check=True),
            call(['piactl', 'connect'], check=True)
        ]
        mock_run.assert_has_calls(expected_calls, any_order=True)
    
    @patch('subprocess.run')
    def test_apply_to_session(self, mock_run):
        """Test the apply_to_session method."""
        # Mock the subprocess.run calls
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "connected"
        
        # Create the rotator
        rotator = PIAVPNRotator(
            self.pia_username, 
            self.pia_password, 
            self.server_list
        )
        
        # Mock the rotate_ip method
        rotator.rotate_ip = MagicMock()
        
        # Mock the _test_vpn_connection method
        rotator._test_vpn_connection = MagicMock()
        
        # Mock the session
        mock_session = MagicMock()
        
        # Apply to session
        result = rotator.apply_to_session(mock_session)
        
        # Check that rotate_ip was called
        rotator.rotate_ip.assert_called_once()
        
        # Check that _test_vpn_connection was called
        rotator._test_vpn_connection.assert_called_once_with(mock_session)
        
        # Check that the session was returned unchanged
        self.assertEqual(result, mock_session)

if __name__ == '__main__':
    unittest.main()