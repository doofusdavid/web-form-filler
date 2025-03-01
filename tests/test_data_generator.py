"""
Tests for the data generator.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from web_form_filler.data_generator import DataGenerator

class TestDataGenerator(unittest.TestCase):
    """Tests for the DataGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model_name = "deepseek-r1"
        
        # Sample form info
        self.form_info = {
            'action': 'https://example.com/submit',
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
                },
                {
                    'name': 'phone',
                    'type': 'tel',
                    'required': False,
                    'placeholder': '',
                    'id': 'phone',
                    'class': [],
                    'value': '',
                    'label': 'Phone:',
                    'options': []
                },
                {
                    'name': 'message',
                    'type': 'textarea',
                    'required': False,
                    'placeholder': '',
                    'id': 'message',
                    'class': [],
                    'value': '',
                    'label': 'Message:',
                    'options': []
                },
                {
                    'name': 'topic',
                    'type': 'select',
                    'required': False,
                    'placeholder': '',
                    'id': 'topic',
                    'class': [],
                    'value': '',
                    'label': 'Topic:',
                    'options': [
                        {'value': 'general', 'text': 'General Inquiry'},
                        {'value': 'support', 'text': 'Support'},
                        {'value': 'feedback', 'text': 'Feedback'}
                    ]
                },
                {
                    'name': 'honeypot',
                    'type': 'text',
                    'required': False,
                    'placeholder': '',
                    'id': '',
                    'class': [],
                    'value': '',
                    'label': '',
                    'options': []
                }
            ],
            'honeypot_fields': ['honeypot']
        }
    
    @patch('requests.post')
    def test_generate_field_data(self, mock_post):
        """Test the generate_field_data method."""
        # Mock the Ollama API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'John Doe'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create the generator
        generator = DataGenerator(self.model_name)
        
        # Generate data for a field
        field_info = self.form_info['fields'][0]  # name field
        data = generator.generate_field_data(field_info)
        
        # Check that we got the expected data
        self.assertEqual(data, 'John Doe')
        
        # Check that the Ollama API was called with the expected parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], 'http://localhost:11434/api/generate')
        
        # Check the payload
        payload = kwargs['json']
        self.assertEqual(payload['model'], self.model_name)
        self.assertIn('name', payload['prompt'])
        self.assertIn('Name:', payload['prompt'])
        self.assertIn('text', payload['prompt'])
    
    @patch('requests.post')
    def test_batch_generate_field_data(self, mock_post):
        """Test the _batch_generate_field_data method."""
        # Mock successful JSON response from Ollama
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': json.dumps({
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '555-123-4567',
                'message': 'I observed inappropriate DEI training materials being used in the classroom.',
                'topic': 'general'
            })
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        generator = DataGenerator(self.model_name)
        
        # Get non-honeypot fields
        fields = [f for f in self.form_info['fields'] if f['name'] != 'honeypot']
        result = generator._batch_generate_field_data(fields)
        
        # Verify the result contains all expected fields
        self.assertIn('name', result)
        self.assertIn('email', result)
        self.assertIn('phone', result)
        self.assertIn('message', result)
        self.assertIn('topic', result)
        
        # Verify Ollama was called once with all fields in prompt
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        prompt = kwargs['json']['prompt']
        self.assertIn('name', prompt)
        self.assertIn('email', prompt)
        self.assertIn('phone', prompt)
        self.assertIn('message', prompt)
        self.assertIn('topic', prompt)

    @patch('requests.post')
    def test_generate_form_data(self, mock_post):
        """Test the generate_form_data method."""
        # Mock successful JSON response from Ollama
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': json.dumps({
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '555-123-4567',
                'message': 'I observed inappropriate DEI training materials being used in the classroom.',
                'topic': 'general'
            })
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create the generator
        generator = DataGenerator(self.model_name)
        
        # Generate data for the form
        form_data = generator.generate_form_data(self.form_info, self.form_info['honeypot_fields'])
        
        # Check that we got the expected data
        self.assertEqual(form_data['name'], 'John Doe')
        self.assertEqual(form_data['email'], 'john.doe@example.com')
        self.assertEqual(form_data['phone'], '555-123-4567')
        self.assertEqual(form_data['message'], 'I observed inappropriate DEI training materials being used in the classroom.')
        self.assertEqual(form_data['topic'], 'general')
        
        # Check that the honeypot field was left empty
        self.assertEqual(form_data['honeypot'], '')
        
        # Check that the Ollama API was called exactly once for all fields
        mock_post.assert_called_once()
    
    def test_process_response(self):
        """Test the _process_response method."""
        # Create the generator
        generator = DataGenerator(self.model_name)
        
        # Test email processing
        email_field = self.form_info['fields'][1]  # email field
        email_response = generator._process_response('john.doe', email_field)
        self.assertIn('@', email_response)
        
        # Test phone processing
        phone_field = self.form_info['fields'][2]  # phone field
        phone_response = generator._process_response('5551234567', phone_field)
        self.assertRegex(phone_response, r'\d{3}-\d{3}-\d{4}')
        
        # Test select field processing
        select_field = self.form_info['fields'][4]  # topic field
        select_response = generator._process_response('Support', select_field)
        self.assertEqual(select_response, 'support')
        
        # Test text field truncation
        text_field = self.form_info['fields'][0]  # name field
        long_text = 'a' * 200
        text_response = generator._process_response(long_text, text_field)
        self.assertEqual(len(text_response), 100)
        
        # Test textarea field truncation
        textarea_field = self.form_info['fields'][3]  # message field
        long_text = 'a' * 2000
        textarea_response = generator._process_response(long_text, textarea_field)
        self.assertEqual(len(textarea_response), 1000)

if __name__ == '__main__':
    unittest.main()