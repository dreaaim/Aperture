"""Logging utility functions.

This module provides utility functions for configuring and obtaining logger instances.

The `get_logger` function creates and configures a logger with:
- A console handler that outputs to stdout
- A standard log format including timestamp, logger name, level, and message
- INFO level logging by default

This module also provides a default logger instance named "aperture" that can be used throughout the application.

Example:
    from app.utils.logger import get_logger, default_logger
    
    # Use the default logger
    default_logger.info("This is an info message")
    default_logger.error("This is an error message")
    
    # Create a named logger
    logger = get_logger("my_module")
    logger.info("This is a message from my module")

    Output:
    2023-10-01 12:00:00,000 - aperture - INFO - This is an info message
    2023-10-01 12:00:00,000 - aperture - ERROR - This is an error message
    2023-10-01 12:00:00,000 - my_module - INFO - This is a message from my module
"""

import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    This function creates and configures a logger instance with a console handler
    that outputs to stdout with a standard log format.
    
    Args:
        name: Optional logger name. If not provided, the root logger is returned.
        Using a descriptive name helps identify the source of log messages.
        
    Returns:
        A configured logger instance with a console handler.
        
    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger("my_module")
        >>> logger.info("This is a log message")
        2023-10-01 12:00:00,000 - my_module - INFO - This is a log message
        
        >>> root_logger = get_logger()
        >>> root_logger.info("This is a root log message")
        2023-10-01 12:00:00,000 - root - INFO - This is a root log message
    """
    # Get or create logger with the specified name
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured before
    # This prevents duplicate handlers if the function is called multiple times
    if not logger.handlers:
        # Create console handler that outputs to stdout
        # Using stdout instead of stderr makes log messages easier to read in some environments
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Set handler level to INFO
        console_handler.setLevel(logging.INFO)
        
        # Create formatter with timestamp, logger name, level, and message
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set formatter for the handler
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Set logger level to INFO
        logger.setLevel(logging.INFO)
    
    return logger


# Create a default logger instance with name "aperture"
# This logger can be imported and used throughout the application
# Example: from app.utils.logger import default_logger
#          default_logger.info("Application started")
default_logger = get_logger("aperture")
