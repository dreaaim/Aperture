"""Logging utility functions."""

import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Optional logger name. If not provided, the root logger is returned.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
    
    return logger


# Create a default logger instance
default_logger = get_logger("aperture")
