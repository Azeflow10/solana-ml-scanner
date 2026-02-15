"""
Logging utilities with Windows emoji support
"""

import codecs
import io
import logging
import sys
from pathlib import Path
from typing import Optional

_logger_configured = False
_stdout_reconfigured = False

def setup_logger(
    name: str = "solana_scanner",
    level: int = logging.INFO,
    log_file: Optional[str] = "logs/scanner.log"
) -> logging.Logger:
    """
    Setup logger with Windows-compatible encoding
    
    This function configures the logging system to handle UTF-8 emojis on Windows.
    
    **Important:** On Windows, this function modifies sys.stdout globally to use UTF-8
    encoding with error replacement. This affects all print statements and stdout writes
    application-wide, not just logging. This is necessary to prevent UnicodeEncodeError
    when logging emojis on Windows (which uses CP1252 encoding by default).
    
    Args:
        name: Logger name
        level: Logging level (default: logging.INFO)
        log_file: Optional log file path (default: "logs/scanner.log")
    
    Returns:
        Configured logger instance
    """
    global _logger_configured, _stdout_reconfigured
    
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
    
    # Console handler with UTF-8 encoding
    try:
        # Force UTF-8 encoding for console output on Windows
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Try to reconfigure stdout to use UTF-8 (only once)
        if sys.platform == 'win32' and not _stdout_reconfigured:
            try:
                # Reconfigure stdout with UTF-8 and error handling
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                _stdout_reconfigured = True
            except (AttributeError, io.UnsupportedOperation):
                # Fallback for older Python or unsupported operations
                # Use a custom stream handler that handles encoding errors
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
                _stdout_reconfigured = True
        
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
        
    except Exception as e:
        # Fallback: create handler without special encoding
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
        print(f"Warning: Could not set UTF-8 encoding for console: {e}")
    
    # File handler (always UTF-8)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not create log file handler: {e}")
    
    _logger_configured = True
    
    # Return a named logger
    logger = logging.getLogger(name)
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
