"""
Form Analyzer - Analyzes web forms to extract field information and detect honeypot fields.
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .utils.logger import setup_logger

logger = setup_logger()

class FormAnalyzer:
    """Analyzes web forms to extract field information and detect honeypot fields."""
    
    def __init__(self, url):
        """Initialize the FormAnalyzer with the URL of the web form.
        
        Args:
            url (str): The URL of the web form to analyze.
        """
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def analyze(self):
        """Analyze the form and return field metadata.
        
        Returns:
            list: A list of dictionaries containing form metadata and fields.
        """
        logger.info(f"Fetching page from {self.url}")
        try:
            response = self.session.get(self.url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            raise
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all forms on the page
        forms = soup.find_all('form')
        logger.info(f"Found {len(forms)} forms on the page")
        
        if not forms:
            logger.warning("No forms found on the page")
            return []
        
        # Extract form metadata and fields
        form_data = []
        for i, form in enumerate(forms):
            logger.info(f"Analyzing form #{i+1}")
            
            # Get form action (submission URL)
            action = form.get('action', '')
            if action:
                # Handle relative URLs
                action = urljoin(self.url, action)
            else:
                # If no action is specified, the form submits to the current URL
                action = self.url
                
            # Get form method
            method = form.get('method', 'post').lower()
            
            # Extract fields
            fields = self._extract_fields(form)
            
            # Detect honeypot fields
            honeypot_fields = self._detect_honeypot_fields(form)
            
            form_info = {
                'action': action,
                'method': method,
                'fields': fields,
                'honeypot_fields': honeypot_fields
            }
            form_data.append(form_info)
            
            logger.info(f"Form #{i+1}: {len(fields)} fields, {len(honeypot_fields)} potential honeypot fields")
            
        return form_data
    
    def _extract_fields(self, form):
        """Extract field metadata from the form.
        
        Args:
            form (BeautifulSoup.element.Tag): The form element to extract fields from.
            
        Returns:
            list: A list of dictionaries containing field metadata.
        """
        fields = []
        
        # Process all input, textarea, and select elements
        for input_field in form.find_all(['input', 'textarea', 'select']):
            field_name = input_field.get('name')
            
            # Skip fields without a name
            if not field_name:
                continue
                
            field_type = input_field.get('type', 'text').lower() if input_field.name == 'input' else input_field.name
            
            field_info = {
                'name': field_name,
                'type': field_type,
                'required': input_field.has_attr('required'),
                'placeholder': input_field.get('placeholder', ''),
                'id': input_field.get('id', ''),
                'class': input_field.get('class', []),
                'value': input_field.get('value', ''),
                'label': self._find_label_for_field(input_field),
                'options': self._extract_options(input_field)
            }
            
            fields.append(field_info)
            
        return fields
    
    def _find_label_for_field(self, field):
        """Find the label text for a form field.
        
        Args:
            field (BeautifulSoup.element.Tag): The field element to find a label for.
            
        Returns:
            str: The label text, or an empty string if no label is found.
        """
        # Check for a label with a for attribute matching the field's id
        field_id = field.get('id')
        if field_id:
            label = field.find_parent().find('label', attrs={'for': field_id})
            if label:
                return label.get_text(strip=True)
        
        # Check if the field is inside a label
        parent_label = field.find_parent('label')
        if parent_label:
            # Get the label text excluding the field itself
            field_html = str(field)
            label_html = str(parent_label)
            label_text = BeautifulSoup(label_html.replace(field_html, ''), 'html.parser').get_text(strip=True)
            return label_text
            
        return ''
    
    def _extract_options(self, field):
        """Extract options from select fields or radio/checkbox groups.
        
        Args:
            field (BeautifulSoup.element.Tag): The field element to extract options from.
            
        Returns:
            list: A list of option values, or an empty list if the field has no options.
        """
        options = []
        
        # Handle select fields
        if field.name == 'select':
            for option in field.find_all('option'):
                value = option.get('value', '')
                text = option.get_text(strip=True)
                if value:  # Skip options without a value
                    options.append({
                        'value': value,
                        'text': text
                    })
        
        # Handle radio/checkbox groups (not implemented yet)
        # This would require finding all inputs with the same name
        
        return options
    
    def _detect_honeypot_fields(self, form):
        """Detect potential honeypot fields.
        
        Args:
            form (BeautifulSoup.element.Tag): The form element to analyze.
            
        Returns:
            list: A list of field names that are likely honeypot fields.
        """
        honeypot_fields = []
        
        # Check for hidden fields
        hidden_fields = form.find_all('input', type='hidden')
        for field in hidden_fields:
            field_name = field.get('name', '')
            if not field_name:
                continue
                
            # Exclude common hidden fields like CSRF tokens
            if not any(token in field_name.lower() for token in ['csrf', 'token', '_token', 'authenticity']):
                honeypot_fields.append(field_name)
        
        # Check for fields hidden via CSS
        for input_field in form.find_all(['input', 'textarea']):
            field_name = input_field.get('name', '')
            if not field_name:
                continue
                
            # Check for inline style with display:none or visibility:hidden
            style = input_field.get('style', '')
            if 'display:none' in style or 'visibility:hidden' in style:
                honeypot_fields.append(field_name)
                
            # Check for suspicious class names
            classes = input_field.get('class', [])
            if isinstance(classes, str):
                classes = classes.split()
                
            suspicious_classes = ['hidden', 'hide', 'invisible', 'visually-hidden', 'sr-only']
            if any(cls in suspicious_classes for cls in classes):
                honeypot_fields.append(field_name)
                
            # Check for suspicious field names
            suspicious_names = ['url', 'website', 'email2', 'phone2', 'address2', 'honey', 'pot']
            if any(name in field_name.lower() for name in suspicious_names):
                honeypot_fields.append(field_name)
        
        return list(set(honeypot_fields))  # Remove duplicates