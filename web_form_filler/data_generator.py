"""
Data Generator - Generates realistic data for form fields using Ollama.
"""

import re
import random
import json
import requests

from .utils.logger import setup_logger

logger = setup_logger()

class DataGenerator:
    """Generates realistic data for form fields using Ollama."""
    
    def __init__(self, model_name):
        """Initialize the DataGenerator with the Ollama model name.
        
        Args:
            model_name (str): The name of the Ollama model to use.
        """
        self.model_name = model_name
        self.ollama_api_url = "http://localhost:11434/api/generate"
        
    def generate_field_data(self, field_info):
        """Generate data for a single field based on its metadata.
        
        Args:
            field_info (dict): Metadata about the field.
            
        Returns:
            str: The generated data for the field.
        """
        # Construct a prompt for Ollama based on field metadata
        prompt = self._construct_prompt(field_info)
        
        # Call Ollama API
        response = self._call_ollama(prompt)
        
        # Process and return the response
        return self._process_response(response, field_info)
    
    def _batch_generate_field_data(self, fields):
        """Generate data for multiple fields in a single API call.
        
        Args:
            fields (list): List of field metadata dictionaries.
            
        Returns:
            dict: A dictionary mapping field names to generated values.
        """
        # Construct a combined prompt for all fields
        prompts = []
        for field in fields:
            field_name = field['name']
            field_type = field['type']
            label = field['label'] or field['placeholder'] or field_name
            
            # Clean up the label/name for better context
            clean_name = re.sub(r'[_\-]', ' ', field_name).strip()
            clean_label = re.sub(r'[_\-]', ' ', label).strip()
            
            field_prompt = f"Field '{clean_name}' ({clean_label}, type: {field_type})"
            
            # Add type-specific instructions
            if field_type == 'email':
                field_prompt += " - Provide a valid email address"
            elif field_type == 'tel':
                field_prompt += " - Provide a valid US phone number"
            elif field_type == 'date':
                field_prompt += " - Provide a date in YYYY-MM-DD format"
            elif field_type == 'select' and field['options']:
                options_text = ", ".join([f"'{opt['text']}'" for opt in field['options']])
                field_prompt += f" - Choose from: {options_text}"
            elif field_type == 'textarea':
                field_prompt += " - Provide a detailed paragraph (2-3 sentences) relevant to reporting DEI practices"
            
            prompts.append(field_prompt)
        
        # Construct the full prompt
        combined_prompt = f"""
        Generate realistic values for multiple form fields. This is for a reporting form related to DEI practices at schools.
        Provide values in a JSON format with field names as keys. Values should be appropriate for each field type.

        Fields to generate:
        {chr(10).join('- ' + p for p in prompts)}

        Examples of good responses:
        {{
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "555-123-4567",
            "message": "I observed inappropriate DEI training materials being used in the classroom."
        }}

        Respond with ONLY a valid JSON object containing the generated values.
        """
        
        try:
            # Call Ollama API once for all fields
            response = self._call_ollama(combined_prompt)
            
            # Parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If response isn't valid JSON, fall back to individual generation
                logger.error("Failed to parse batch response as JSON, falling back to individual generation")
                return {field['name']: self._fallback_generation(self._construct_prompt(field))
                       for field in fields}
                
        except Exception as e:
            logger.error(f"Error in batch generation: {e}")
            # Fall back to individual generation
            return {field['name']: self._fallback_generation(self._construct_prompt(field))
                   for field in fields}

    def generate_form_data(self, form_info, honeypot_fields=None):
        """Generate data for all fields in a form.
        
        Args:
            form_info (dict): Metadata about the form.
            honeypot_fields (list, optional): List of honeypot field names to skip or leave empty.
            
        Returns:
            dict: A dictionary mapping field names to generated values.
        """
        form_data = {}
        honeypot_fields = honeypot_fields or []
        
        logger.info(f"Generating data for {len(form_info['fields'])} fields")
        
        # Separate honeypot fields from regular fields
        regular_fields = [field for field in form_info['fields']
                         if field['name'] not in honeypot_fields]
        
        if regular_fields:
            # Generate data for all regular fields in one batch
            logger.info("Generating batch data for regular fields")
            batch_data = self._batch_generate_field_data(regular_fields)
            
            # Process each field's data with type-specific processing
            for field in regular_fields:
                field_name = field['name']
                raw_value = batch_data.get(field_name, '')
                processed_value = self._process_response(raw_value, field)
                form_data[field_name] = processed_value
                logger.debug(f"Generated value for {field_name}: {processed_value}")
        
        # Handle honeypot fields
        for field_name in honeypot_fields:
            logger.info(f"Skipping honeypot field: {field_name}")
            form_data[field_name] = ""
            
        return form_data
    
    def _construct_prompt(self, field_info):
        """Construct a prompt for Ollama based on field metadata.
        
        Args:
            field_info (dict): Metadata about the field.
            
        Returns:
            str: The prompt to send to Ollama.
        """
        field_name = field_info['name']
        field_type = field_info['type']
        label = field_info['label'] or field_info['placeholder'] or field_name
        
        # Clean up the label/name for better context
        clean_name = re.sub(r'[_\-]', ' ', field_name).strip()
        clean_label = re.sub(r'[_\-]', ' ', label).strip()
        
        # Construct a prompt based on field type and label
        prompt = f"""
        Generate a realistic value for a form field with the following properties:
        - Field name: {clean_name}
        - Field label: {clean_label}
        - Field type: {field_type}
        
        This is for a reporting form related to DEI practices at schools. 
        Provide ONLY the value, with no additional explanation or context.
        
        Examples of good responses:
        - For a name field: "John Smith"
        - For an email field: "john.smith@example.com"
        - For a phone field: "555-123-4567"
        - For a message field: "I observed inappropriate DEI training materials being used in the classroom."
        
        DO NOT include any explanations, just provide the value itself.
        """
        
        # Add type-specific instructions
        if field_type == 'email':
            prompt += "\nProvide a valid email address."
        elif field_type == 'tel':
            prompt += "\nProvide a valid US phone number."
        elif field_type == 'date':
            prompt += "\nProvide a date in YYYY-MM-DD format."
        elif field_type == 'select':
            # If we have options, ask to choose one
            if field_info['options']:
                options_text = ", ".join([f"'{opt['text']}'" for opt in field_info['options']])
                prompt += f"\nChoose one of the following options: {options_text}"
        elif field_type == 'textarea':
            prompt += "\nProvide a detailed paragraph (2-3 sentences) relevant to reporting DEI practices."
        
        return prompt
    
    def _call_ollama(self, prompt):
        """Call the Ollama API with the given prompt.
        
        Args:
            prompt (str): The prompt to send to Ollama.
            
        Returns:
            str: The response from Ollama.
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 100
                }
            }
            
            response = requests.post(self.ollama_api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            # Fallback to simple generation if Ollama fails
            return self._fallback_generation(prompt)
    
    def _fallback_generation(self, prompt):
        """Generate fallback data if Ollama API call fails.
        
        Args:
            prompt (str): The original prompt.
            
        Returns:
            str: Fallback generated data.
        """
        logger.warning("Using fallback data generation")
        
        # Extract field type from prompt
        field_type_match = re.search(r'Field type: (\w+)', prompt)
        field_type = field_type_match.group(1) if field_type_match else 'text'
        
        # Generate fallback data based on field type
        if 'email' in field_type:
            names = ['john.doe', 'jane.smith', 'robert.johnson', 'emily.davis', 'michael.wilson']
            domains = ['example.com', 'gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com']
            return f"{random.choice(names)}@{random.choice(domains)}"
            
        elif 'tel' in field_type or 'phone' in field_type:
            return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            
        elif 'date' in field_type:
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            return f"{year}-{month:02d}-{day:02d}"
            
        elif 'textarea' in field_type or 'message' in field_type:
            messages = [
                "I observed inappropriate DEI training materials being used in the classroom.",
                "The school is implementing mandatory DEI training that seems politically biased.",
                "Teachers are being required to attend DEI workshops that promote divisive concepts.",
                "Students are being separated by race for certain activities under DEI initiatives."
            ]
            return random.choice(messages)
            
        elif 'name' in field_type:
            first_names = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'Robert', 'Jennifer']
            last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson']
            return f"{random.choice(first_names)} {random.choice(last_names)}"
            
        else:
            # Generic text
            words = ['concern', 'report', 'issue', 'observation', 'incident', 'problem', 'situation', 'matter']
            return f"This is a {random.choice(words)} regarding DEI practices."
    
    def _process_response(self, response, field_info):
        """Process the Ollama response based on field type.
        
        Args:
            response (str): The raw response from Ollama.
            field_info (dict): Metadata about the field.
            
        Returns:
            str: The processed response.
        """
        # Clean up the response
        response = response.strip()
        
        # Remove any markdown formatting
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
        response = re.sub(r'`(.*?)`', r'\1', response)
        
        # Process based on field type
        field_type = field_info['type']
        
        if field_type == 'email':
            # Ensure it's a valid email
            if '@' not in response:
                domains = ['example.com', 'gmail.com', 'outlook.com', 'yahoo.com']
                clean_text = re.sub(r'[^a-zA-Z0-9]', '', response).lower()
                response = f"{clean_text}@{random.choice(domains)}"
                
        elif field_type == 'tel':
            # Ensure it's a valid phone number
            digits = re.sub(r'\D', '', response)
            if not digits or len(digits) < 10:
                digits = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            
            # Format as XXX-XXX-XXXX
            if len(digits) >= 10:
                response = f"{digits[:3]}-{digits[3:6]}-{digits[6:10]}"
            
        elif field_type == 'date':
            # Ensure it's a valid date
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', response)
            if not date_match:
                year = random.randint(2020, 2024)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                response = f"{year}-{month:02d}-{day:02d}"
            else:
                response = date_match.group(0)
                
        elif field_type == 'select':
            # If we have options, ensure the response matches one of them
            if field_info['options']:
                # Try to find the closest match
                options = field_info['options']
                option_values = [opt['value'] for opt in options]
                option_texts = [opt['text'] for opt in options]
                
                # Check if response exactly matches any option value or text
                if response in option_values:
                    return response
                if response in option_texts:
                    # Find the corresponding value
                    index = option_texts.index(response)
                    return options[index]['value']
                
                # If no exact match, return the first option value
                response = options[0]['value']
        
        # Truncate long responses for text fields
        if field_type in ['text', 'textarea']:
            max_length = 1000 if field_type == 'textarea' else 100
            response = response[:max_length]
        
        return response