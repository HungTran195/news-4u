"""
Logging configuration for the news aggregation system.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Log message format
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logging levels for third-party libraries
    for logger_name, level in LOGGING_LEVELS.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def log_request(request, response=None, error=None):
    """
    Log HTTP request details.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object (optional)
        error: Exception object (optional)
    """
    logger = logging.getLogger("http")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }
    
    if response:
        log_data.update({
            "status_code": response.status_code,
            "response_time": getattr(response, "response_time", None)
        })
    
    if error:
        log_data.update({
            "error": str(error),
            "error_type": type(error).__name__
        })
    
    if error:
        logger.error(f"Request failed: {json.dumps(log_data)}")
    else:
        logger.info(f"Request completed: {json.dumps(log_data)}")


def log_content_extraction(url, success, content_length=0, embedded_images=0, standalone_images=0, error=None):
    """
    Log content extraction results.
    
    Args:
        url: URL being extracted
        success: Whether extraction was successful
        content_length: Length of extracted content
        embedded_images: Number of embedded images found
        standalone_images: Number of standalone images found
        error: Exception object (optional)
    """
    logger = logging.getLogger("content_extraction")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "success": success,
        "content_length": content_length,
        "embedded_images": embedded_images,
        "standalone_images": standalone_images
    }
    
    if error:
        log_data.update({
            "error": str(error),
            "error_type": type(error).__name__
        })
    
    if success:
        logger.info(f"Content extraction successful: {json.dumps(log_data)}")
    else:
        logger.error(f"Content extraction failed: {json.dumps(log_data)}")


def log_feed_fetch(feed_name, success, articles_found=0, articles_processed=0, error=None):
    """
    Log RSS feed fetch results.
    
    Args:
        feed_name: Name of the RSS feed
        success: Whether fetch was successful
        articles_found: Number of articles found in feed
        articles_processed: Number of articles successfully processed
        error: Exception object (optional)
    """
    logger = logging.getLogger("feed_fetch")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "feed_name": feed_name,
        "success": success,
        "articles_found": articles_found,
        "articles_processed": articles_processed
    }
    
    if error:
        log_data.update({
            "error": str(error),
            "error_type": type(error).__name__
        })
    
    if success:
        logger.info(f"Feed fetch successful: {json.dumps(log_data)}")
    else:
        logger.error(f"Feed fetch failed: {json.dumps(log_data)}")


def log_database_operation(operation, table, success, rows_affected=0, error=None):
    """
    Log database operation results.
    
    Args:
        operation: Type of operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        success: Whether operation was successful
        rows_affected: Number of rows affected
        error: Exception object (optional)
    """
    logger = logging.getLogger("database")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "table": table,
        "success": success,
        "rows_affected": rows_affected
    }
    
    if error:
        log_data.update({
            "error": str(error),
            "error_type": type(error).__name__
        })
    
    if success:
        logger.info(f"Database operation successful: {json.dumps(log_data)}")
    else:
        logger.error(f"Database operation failed: {json.dumps(log_data)}") 