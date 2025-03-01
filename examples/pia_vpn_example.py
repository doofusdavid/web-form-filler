#!/usr/bin/env python3
"""
Example of using the web form filler with PIA VPN IP rotation.

This example demonstrates how to use the web form filler with PIA VPN for IP rotation.
"""

import sys
import os
import argparse

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_form_filler.form_analyzer import FormAnalyzer
from web_form_filler.data_generator import DataGenerator
from web_form_filler.form_submitter import FormSubmitter
from web_form_filler.ip_rotation.pia_vpn import PIAVPNRotator

def main():
    """Run the example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fill out a web form using PIA VPN for IP rotation.')
    parser.add_argument('--url', required=True, help='URL of the web form to fill out')
    parser.add_argument('--model', required=True, help='Ollama model to use for generating data')
    parser.add_argument('--count', type=int, default=3, help='Number of times to fill out the form')
    parser.add_argument('--pia-username', required=True, help='PIA VPN username')
    parser.add_argument('--pia-password', required=True, help='PIA VPN password')
    parser.add_argument('--servers', help='Comma-separated list of PIA server regions (e.g., "us_east,us_west,uk_london")')
    
    args = parser.parse_args()
    
    # Parse server list if provided
    server_list = None
    if args.servers:
        server_list = [s.strip() for s in args.servers.split(',')]
    
    # Initialize the IP rotator
    print(f"Initializing PIA VPN rotator with username: {args.pia_username}")
    try:
        ip_rotator = PIAVPNRotator(
            args.pia_username,
            args.pia_password,
            server_list
        )
    except Exception as e:
        print(f"Error initializing PIA VPN rotator: {e}")
        return 1
    
    # Analyze the form
    print(f"Analyzing form at {args.url}...")
    form_analyzer = FormAnalyzer(args.url)
    
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
    
    # Initialize the data generator
    print(f"Initializing data generator with model: {args.model}")
    data_generator = DataGenerator(args.model)
    
    # Initialize the form submitter with the IP rotator
    form_submitter = FormSubmitter(ip_rotator=ip_rotator)
    
    # Fill out and submit the form multiple times
    successful_submissions = 0
    for i in range(args.count):
        print(f"\nSubmission {i+1}/{args.count}:")
        
        # Generate form data
        print("Generating form data...")
        try:
            form_data = data_generator.generate_form_data(form_info, form_info['honeypot_fields'])
        except Exception as e:
            print(f"Error generating form data: {e}")
            continue
        
        # Submit the form
        print("Submitting form with IP rotation...")
        try:
            result = form_submitter.submit_form(args.url, form_info, form_data)
        except Exception as e:
            print(f"Error submitting form: {e}")
            continue
        
        if result['success']:
            print(f"Form submitted successfully (status code: {result['status_code']}).")
            successful_submissions += 1
        else:
            print(f"Form submission failed (status code: {result['status_code']}).")
    
    print(f"\nAll submissions completed. {successful_submissions}/{args.count} successful.")
    return 0

if __name__ == "__main__":
    sys.exit(main())