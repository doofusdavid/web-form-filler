"""
Logger - Logging utility for the web form filler.
"""

import os
import sys
import logging
from datetime import datetime

# Global logger instance
_logger = None

def setup_logger(level=logging.INFO):
    """Set up and configure the logger.
    
    Args:
        level (int, optional): The logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: The configured logger.
    """
    global _logger
    
    # Return existing logger if already set up
    if _logger is not None:
        return _logger
        
    # Create logger
    _logger = logging.getLogger('web_form_filler')
    _logger.setLevel(level)
    _logger.propagate = False
    
    # Clear any existing handlers
    if _logger.handlers:
        _logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    _logger.addHandler(console_handler)
    
    # Create file handler for logging to a file
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join('logs', f'web_form_filler_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Add file handler to logger
        _logger.addHandler(file_handler)
        
        _logger.info(f"Logging to file: {log_file}")
        
    except Exception as e:
        _logger.warning(f"Could not set up file logging: {e}")
    
    return _logger

def get_logger():
    """Get the logger instance.
    
    Returns:
        logging.Logger: The logger instance.
    """
    global _logger
    
    if _logger is None:
        return setup_logger()
        
    return _logger