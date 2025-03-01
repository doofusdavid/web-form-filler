"""
Tests for the form submitter.
"""

import unittest
from unittest.mock import patch, MagicMock

from web_form_filler.form_submitter import FormSubmitter

class TestFormSubmitter(unittest.TestCase):
    """Tests for the FormSubmitter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.url = "https://example.com/form"
        
        # Sample form info
        self.form_info = {
            'action': '/submit',
            'method': 'post',
            'fields': [
                {
                    'name': 'name',
                    'type': 'text',
                    'required': True,
                    'placeholder': '',
                    'id': 'name',
                    'class': [],
                    'value': '',
                    'label': 'Name:',
                    'options': []
                },
                {
                    'name': 'email',
                    'type': 'email',
                    'required': True,
                    'placeholder': '',
                    'id': 'email',
                    'class': [],
                    'value': '',
                    'label': 'Email:',
                    'options': []
                }
            ]
        }
        
        # Sample form data
        self.form_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com'
        }
    
    @patch('requests.Session')
    def test_submit_form_post(self, mock_session):
        """Test submitting a form with POST method."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Thank you for your submission!'
        mock_response.url = 'https://example.com/thank-you'
        
        # Mock the session
        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Create the submitter
        submitter = FormSubmitter()
        
        # Submit the form
        result = submitter.submit_form(self.url, self.form_info, self.form_data)
        
        # Check that we got the expected result
        self.assertEqual(result['status_code'], 200)
        self.assertTrue(result['success'])
        self.assertEqual(result['response_text'], 'Thank you for your submission!')
        self.assertEqual(result['url'], 'https://example.com/thank-you')
        
        # Check that the session was used correctly
        mock_session_instance.post.assert_called_once_with(
            'https://example.com/submit',
            data=self.form_data,
            allow_redirects=True
        )
    
    @patch('requests.Session')
    def test_submit_form_get(self, mock_session):
        """Test submitting a form with GET method."""
        # Change the form method to GET
        self.form_info['method'] = 'get'
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Thank you for your submission!'
        mock_response.url = 'https://example.com/thank-you'
        
        # Mock the session
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Create the submitter
        submitter = FormSubmitter()
        
        # Submit the form
        result = submitter.submit_form(self.url, self.form_info, self.form_data)
        
        # Check that we got the expected result
        self.assertEqual(result['status_code'], 200)
        self.assertTrue(result['success'])
        
        # Check that the session was used correctly
        mock_session_instance.get.assert_called_once_with(
            'https://example.com/submit',
            params=self.form_data,
            allow_redirects=True
        )
    
    @patch('requests.Session')
    def test_submit_form_absolute_url(self, mock_session):
        """Test submitting a form with an absolute URL."""
        # Change the form action to an absolute URL
        self.form_info['action'] = 'https://api.example.com/submit'
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Thank you for your submission!'
        
        # Mock the session
        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Create the submitter
        submitter = FormSubmitter()
        
        # Submit the form
        result = submitter.submit_form(self.url, self.form_info, self.form_data)
        
        # Check that we got the expected result
        self.assertEqual(result['status_code'], 200)
        self.assertTrue(result['success'])
        
        # Check that the session was used correctly
        mock_session_instance.post.assert_called_once_with(
            'https://api.example.com/submit',
            data=self.form_data,
            allow_redirects=True
        )
    
    @patch('requests.Session')
    def test_submit_form_error(self, mock_session):
        """Test submitting a form that results in an error."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid form data'
        
        # Mock the session
        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Create the submitter
        submitter = FormSubmitter()
        
        # Submit the form
        result = submitter.submit_form(self.url, self.form_info, self.form_data)
        
        # Check that we got the expected result
        self.assertEqual(result['status_code'], 400)
        self.assertFalse(result['success'])
        self.assertEqual(result['response_text'], 'Invalid form data')
    
    @patch('requests.Session')
    def test_submit_form_with_ip_rotation(self, mock_session):
        """Test submitting a form with IP rotation."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Thank you for your submission!'
        
        # Mock the session
        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Mock the IP rotator
        mock_ip_rotator = MagicMock()
        mock_ip_rotator.apply_to_session.return_value = mock_session_instance
        
        # Create the submitter with the IP rotator
        submitter = FormSubmitter(ip_rotator=mock_ip_rotator)
        
        # Submit the form
        result = submitter.submit_form(self.url, self.form_info, self.form_data)
        
        # Check that we got the expected result
        self.assertEqual(result['status_code'], 200)
        self.assertTrue(result['success'])
        
        # Check that the IP rotator was used
        mock_ip_rotator.apply_to_session.assert_called_once()
    
    def test_is_submission_successful(self):
        """Test the _is_submission_successful method."""
        # Create the submitter
        submitter = FormSubmitter()
        
        # Test with success indicators
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Thank you for your submission!'
        self.assertTrue(submitter._is_submission_successful(mock_response))
        
        # Test with error indicators
        mock_response.text = 'Error: Invalid form data'
        self.assertFalse(submitter._is_submission_successful(mock_response))
        
        # Test with both success and error indicators
        mock_response.text = 'Thank you for your submission! Error: Please check your email'
        self.assertTrue(submitter._is_submission_successful(mock_response))
        
        # Test with neither success nor error indicators
        mock_response.text = 'Some random text'
        self.assertTrue(submitter._is_submission_successful(mock_response))
        
        # Test with error status code
        mock_response.status_code = 400
        mock_response.text = 'Some random text'
        self.assertFalse(submitter._is_submission_successful(mock_response))

if __name__ == '__main__':
    unittest.main()