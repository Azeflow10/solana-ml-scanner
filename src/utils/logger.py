"""
Logging utilities
"""

import logging
import sys
from pathlib import Path
from typing import Optional

_logger_configured = False

def setup_logger(
    name: str = "solana_scanner",
    level: int = logging.INFO,
    log_file: Optional[str] = "logs/scanner.log"
) -> logging.Logger:
    """Setup logger with console and file handlers"""
    global _logger_configured
    
    # Get root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _logger_configured = True
    
    # Return a named logger
    logger = logging.getLogger(name)
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
