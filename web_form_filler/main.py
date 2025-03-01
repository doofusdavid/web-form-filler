#!/usr/bin/env python3
"""
Web Form Filler - Main CLI entry point.
"""

import time
import click

from .form_analyzer import FormAnalyzer
from .data_generator import DataGenerator
from .form_submitter import FormSubmitter
from .ip_rotation.socks_proxy import SOCKSProxyRotator
from .ip_rotation.pia_vpn import PIAVPNRotator
from .utils.logger import setup_logger

logger = setup_logger()

@click.command()
@click.option('--url', required=True, help='URL of the web form to fill out')
@click.option('--model', required=True, help='Ollama model to use for generating data')
@click.option('--count', default=1, type=int, help='Number of times to fill out the form')
@click.option('--ip-rotation', type=click.Choice(['none', 'socks', 'pia']), default='none', help='IP rotation method')
@click.option('--socks-host', help='SOCKS proxy host')
@click.option('--socks-port', type=int, help='SOCKS proxy port')
@click.option('--socks-username', help='SOCKS proxy username')
@click.option('--socks-password', help='SOCKS proxy password')
@click.option('--pia-username', help='PIA VPN username')
@click.option('--pia-password', help='PIA VPN password')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def main(url, model, count, ip_rotation, socks_host, socks_port, socks_username, socks_password, pia_username, pia_password, verbose):
    """Fill out web forms using AI-generated data with IP rotation."""
    # Set up IP rotator
    ip_rotator = None
    if ip_rotation == 'socks':
        if not socks_host or not socks_port:
            raise click.UsageError("SOCKS proxy host and port are required for SOCKS IP rotation")
        logger.info(f"Using SOCKS proxy at {socks_host}:{socks_port}")
        ip_rotator = SOCKSProxyRotator(socks_host, socks_port, socks_username, socks_password)
    elif ip_rotation == 'pia':
        if not pia_username or not pia_password:
            raise click.UsageError("PIA username and password are required for PIA VPN IP rotation")
        logger.info("Using PIA VPN for IP rotation")
        ip_rotator = PIAVPNRotator(pia_username, pia_password)
    
    # Initialize components
    form_analyzer = FormAnalyzer(url)
    data_generator = DataGenerator(model)
    form_submitter = FormSubmitter(ip_rotator)
    
    # Analyze the form
    logger.info(f"Analyzing form at {url}...")
    try:
        form_data = form_analyzer.analyze()
    except Exception as e:
        logger.error(f"Error analyzing form: {e}")
        return 1
    
    if not form_data:
        logger.error("No forms found on the page.")
        return 1
    
    # Use the first form for now
    form_info = form_data[0]
    
    logger.info(f"Found form with {len(form_info['fields'])} fields.")
    if form_info['honeypot_fields']:
        logger.info(f"Detected {len(form_info['honeypot_fields'])} potential honeypot fields: {', '.join(form_info['honeypot_fields'])}")
    
    # Fill out and submit the form multiple times
    successful_submissions = 0
    for i in range(count):
        logger.info(f"\nSubmission {i+1}/{count}:")
        
        # Generate form data
        logger.info("Generating form data...")
        try:
            form_data = data_generator.generate_form_data(form_info, form_info['honeypot_fields'])
        except Exception as e:
            logger.error(f"Error generating form data: {e}")
            continue
        
        if verbose:
            logger.info("Form data:")
            for key, value in form_data.items():
                logger.info(f"  {key}: {value}")
        
        # Submit the form
        logger.info("Submitting form...")
        try:
            result = form_submitter.submit_form(url, form_info, form_data)
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            continue
        
        if result['success']:
            logger.info(f"Form submitted successfully (status code: {result['status_code']}).")
            successful_submissions += 1
        else:
            logger.error(f"Form submission failed (status code: {result['status_code']}).")
            if verbose:
                logger.debug(f"Response: {result['response_text'][:500]}...")
            
        if i < count - 1:
            # Wait between submissions to avoid rate limiting
            delay = 2  # seconds
            logger.info(f"Waiting {delay} seconds before next submission...")
            time.sleep(delay)
    
    logger.info(f"\nAll submissions completed. {successful_submissions}/{count} successful.")
    return 0

if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter