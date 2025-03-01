"""
Form Submitter - Submits web forms with generated data.
"""

import time
import random
import requests
from urllib.parse import urljoin, urlparse

from .utils.logger import setup_logger

logger = setup_logger()

class FormSubmitter:
    """Submits web forms with generated data."""
    
    def __init__(self, ip_rotator=None):
        """Initialize the FormSubmitter.
        
        Args:
            ip_rotator (BaseIPRotator, optional): An IP rotator to use for submissions.
        """
        self.ip_rotator = ip_rotator
        
    def submit_form(self, url, form_info, form_data):
        """Submit the form with the generated data.
        
        Args:
            url (str): The URL of the page containing the form.
            form_info (dict): Metadata about the form.
            form_data (dict): The data to submit.
            
        Returns:
            dict: A dictionary containing the submission result.
        """
        # Create a new session with the rotated IP if available
        session = self._create_session()
        
        # Add common headers to mimic a browser
        session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': url,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Determine the submission URL
        submit_url = self._get_submit_url(url, form_info['action'])
        
        # Log submission details
        logger.info(f"Submitting form to: {submit_url}")
        logger.info(f"Method: {form_info['method']}")
        logger.debug(f"Form data: {form_data}")
        
        # Submit the form
        try:
            if form_info['method'] == 'post':
                response = session.post(submit_url, data=form_data, allow_redirects=True)
            else:
                response = session.get(submit_url, params=form_data, allow_redirects=True)
                
            # Check for common form submission success indicators
            success = self._is_submission_successful(response)
            
            return {
                'status_code': response.status_code,
                'success': success,
                'response_text': response.text,
                'url': response.url
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting form: {e}")
            return {
                'status_code': 0,
                'success': False,
                'response_text': str(e),
                'url': submit_url
            }
    
    def _create_session(self):
        """Create a new session with the rotated IP if available.
        
        Returns:
            requests.Session: A configured session object.
        """
        session = requests.Session()
        
        if self.ip_rotator:
            logger.info("Applying IP rotation to session")
            try:
                session = self.ip_rotator.apply_to_session(session)
            except Exception as e:
                logger.error(f"Error applying IP rotation: {e}")
                
        return session
    
    def _get_submit_url(self, base_url, action):
        """Determine the submission URL based on the form action.
        
        Args:
            base_url (str): The URL of the page containing the form.
            action (str): The form action attribute.
            
        Returns:
            str: The full submission URL.
        """
        if not action:
            # If no action is specified, the form submits to the current URL
            return base_url
            
        # Handle absolute URLs
        if action.startswith(('http://', 'https://')):
            return action
            
        # Handle relative URLs
        return urljoin(base_url, action)
    
    def _is_submission_successful(self, response):
        """Determine if the form submission was successful.
        
        Args:
            response (requests.Response): The response from the form submission.
            
        Returns:
            bool: True if the submission appears successful, False otherwise.
        """
        # Check status code
        if not (200 <= response.status_code < 400):
            return False
            
        # Check for common success indicators in the response text
        success_indicators = [
            'success', 'thank you', 'thanks', 'received', 'submitted',
            'confirmed', 'complete', 'done', 'finished'
        ]
        
        # Check for common error indicators
        error_indicators = [
            'error', 'invalid', 'failed', 'incorrect', 'wrong',
            'problem', 'not valid', 'try again'
        ]
        
        response_text_lower = response.text.lower()
        
        # Check for success indicators
        has_success = any(indicator in response_text_lower for indicator in success_indicators)
        
        # Check for error indicators
        has_error = any(indicator in response_text_lower for indicator in error_indicators)
        
        # If we have both success and error indicators, rely on status code
        if has_success and has_error:
            return 200 <= response.status_code < 300
            
        # If we have success indicators and no error indicators, consider it successful
        if has_success and not has_error:
            return True
            
        # If we have error indicators and no success indicators, consider it failed
        if has_error and not has_success:
            return False
            
        # If we have neither, rely on status code
        return 200 <= response.status_code < 300
    
    def _get_random_user_agent(self):
        """Get a random user agent string to mimic different browsers.
        
        Returns:
            str: A random user agent string.
        """
        user_agents = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        return random.choice(user_agents)