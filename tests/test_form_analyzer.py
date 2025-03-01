"""
Tests for the form analyzer.
"""

import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from web_form_filler.form_analyzer import FormAnalyzer

class TestFormAnalyzer(unittest.TestCase):
    """Tests for the FormAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.url = "https://example.com/form"
        
        # Sample HTML with a form
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Form</title>
        </head>
        <body>
            <h1>Test Form</h1>
            <form action="/submit" method="post">
                <div>
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div>
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div>
                    <label for="phone">Phone:</label>
                    <input type="tel" id="phone" name="phone">
                </div>
                <div>
                    <label for="message">Message:</label>
                    <textarea id="message" name="message"></textarea>
                </div>
                <div>
                    <label for="topic">Topic:</label>
                    <select id="topic" name="topic">
                        <option value="general">General Inquiry</option>
                        <option value="support">Support</option>
                        <option value="feedback">Feedback</option>
                    </select>
                </div>
                <div style="display:none">
                    <input type="text" name="honeypot" value="">
                </div>
                <input type="hidden" name="form_id" value="contact_form">
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
        """
    
    @patch('requests.Session')
    def test_analyze(self, mock_session):
        """Test the analyze method."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        
        # Mock the session
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Create the analyzer
        analyzer = FormAnalyzer(self.url)
        
        # Analyze the form
        form_data = analyzer.analyze()
        
        # Check that we got the expected results
        self.assertEqual(len(form_data), 1)
        form_info = form_data[0]
        
        # Check form properties
        self.assertEqual(form_info['action'], 'https://example.com/submit')
        self.assertEqual(form_info['method'], 'post')
        
        # Check fields
        self.assertEqual(len(form_info['fields']), 7)  # 5 visible fields + honeypot + hidden
        
        # Check field types
        field_types = {field['name']: field['type'] for field in form_info['fields']}
        self.assertEqual(field_types['name'], 'text')
        self.assertEqual(field_types['email'], 'email')
        self.assertEqual(field_types['phone'], 'tel')
        self.assertEqual(field_types['message'], 'textarea')
        self.assertEqual(field_types['topic'], 'select')
        
        # Check honeypot fields
        self.assertEqual(len(form_info['honeypot_fields']), 1)
        self.assertIn('honeypot', form_info['honeypot_fields'])
    
    def test_extract_fields(self):
        """Test the _extract_fields method."""
        # Parse the HTML
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        form = soup.find('form')
        
        # Create the analyzer
        analyzer = FormAnalyzer(self.url)
        
        # Extract fields
        fields = analyzer._extract_fields(form)
        
        # Check that we got the expected fields
        self.assertEqual(len(fields), 7)
        
        # Check field names
        field_names = [field['name'] for field in fields]
        self.assertIn('name', field_names)
        self.assertIn('email', field_names)
        self.assertIn('phone', field_names)
        self.assertIn('message', field_names)
        self.assertIn('topic', field_names)
        self.assertIn('honeypot', field_names)
        self.assertIn('form_id', field_names)
        
        # Check required fields
        required_fields = [field['name'] for field in fields if field['required']]
        self.assertIn('name', required_fields)
        self.assertIn('email', required_fields)
        self.assertNotIn('phone', required_fields)
        
        # Check select options
        topic_field = next(field for field in fields if field['name'] == 'topic')
        self.assertEqual(len(topic_field['options']), 3)
        option_values = [option['value'] for option in topic_field['options']]
        self.assertIn('general', option_values)
        self.assertIn('support', option_values)
        self.assertIn('feedback', option_values)
    
    def test_detect_honeypot_fields(self):
        """Test the _detect_honeypot_fields method."""
        # Parse the HTML
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        form = soup.find('form')
        
        # Create the analyzer
        analyzer = FormAnalyzer(self.url)
        
        # Detect honeypot fields
        honeypot_fields = analyzer._detect_honeypot_fields(form)
        
        # Check that we got the expected honeypot fields
        self.assertEqual(len(honeypot_fields), 1)
        self.assertIn('honeypot', honeypot_fields)
        self.assertNotIn('form_id', honeypot_fields)  # Hidden but not a honeypot

if __name__ == '__main__':
    unittest.main()