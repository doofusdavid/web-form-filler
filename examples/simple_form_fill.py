#!/usr/bin/env python3
"""
Simple example of using the web form filler.

This example demonstrates how to use the web form filler to fill out a simple contact form.
"""

import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_form_filler.form_analyzer import FormAnalyzer
from web_form_filler.data_generator import DataGenerator
from web_form_filler.form_submitter import FormSubmitter

def main():
    """Run the example."""
    # URL of the form to fill out
    url = "https://example.com/contact"
    
    # Ollama model to use
    model = "llama2"
    
    # Number of times to fill out the form
    count = 3
    
    print(f"Analyzing form at {url}...")
    form_analyzer = FormAnalyzer(url)
    
    try:
        form_data = form_analyzer.analyze()
    except Exception as e:
        print(f"Error analyzing form: {e}")
        return 1
    
    if not form_data:
        print("No forms found on the page.")
        return 1
    
    # Use the first form
    form_info = form_data[0]
    
    print(f"Found form with {len(form_info['fields'])} fields.")
    print(f"Form action: {form_info['action']}")
    print(f"Form method: {form_info['method']}")
    
    # Print field information
    print("\nFields:")
    for field in form_info['fields']:
        print(f"  {field['name']} ({field['type']}): {field['label']}")
    
    # Print honeypot fields
    if form_info['honeypot_fields']:
        print(f"\nDetected {len(form_info['honeypot_fields'])} potential honeypot fields:")
        for field in form_info['honeypot_fields']:
            print(f"  {field}")
    
    # Initialize the data generator
    print(f"\nInitializing data generator with model: {model}")
    data_generator = DataGenerator(model)
    
    # Initialize the form submitter
    form_submitter = FormSubmitter()
    
    # Fill out and submit the form multiple times
    successful_submissions = 0
    for i in range(count):
        print(f"\nSubmission {i+1}/{count}:")
        
        # Generate form data
        print("Generating form data...")
        try:
            form_data = data_generator.generate_form_data(form_info, form_info['honeypot_fields'])
        except Exception as e:
            print(f"Error generating form data: {e}")
            continue
        
        # Print the generated data
        print("Generated data:")
        for key, value in form_data.items():
            print(f"  {key}: {value}")
        
        # Submit the form
        print("Submitting form...")
        try:
            result = form_submitter.submit_form(url, form_info, form_data)
        except Exception as e:
            print(f"Error submitting form: {e}")
            continue
        
        if result['success']:
            print(f"Form submitted successfully (status code: {result['status_code']}).")
            successful_submissions += 1
        else:
            print(f"Form submission failed (status code: {result['status_code']}).")
    
    print(f"\nAll submissions completed. {successful_submissions}/{count} successful.")
    return 0

if __name__ == "__main__":
    sys.exit(main())