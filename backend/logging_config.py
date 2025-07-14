"""
Logging configuration for the News 4U RSS aggregator.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging format
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)

# Configure file handler for general logs
file_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)

# Configure file handler for error logs
error_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "errors.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_format)

# Configure file handler for API requests
api_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "api.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
api_handler.setLevel(logging.INFO)
api_handler.setFormatter(log_format)

def setup_logging():
    """Setup logging configuration for the application."""
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    loggers = {
        'uvicorn': logging.INFO,
        'uvicorn.access': logging.INFO,
        'fastapi': logging.INFO,
        'sqlalchemy': logging.WARNING,  # Reduce SQLAlchemy verbosity
        'httpx': logging.WARNING,  # Reduce HTTP client verbosity
        'newspaper': logging.WARNING,  # Reduce newspaper3k verbosity
        'trafilatura': logging.WARNING,  # Reduce trafilatura verbosity
    }
    
    for logger_name, level in loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Create application-specific loggers
    app_logger = logging.getLogger('news4u')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(error_handler)
    
    api_logger = logging.getLogger('news4u.api')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(console_handler)
    api_logger.addHandler(api_handler)
    
    service_logger = logging.getLogger('news4u.services')
    service_logger.setLevel(logging.INFO)
    service_logger.addHandler(console_handler)
    service_logger.addHandler(file_handler)
    service_logger.addHandler(error_handler)
    
    db_logger = logging.getLogger('news4u.database')
    db_logger.setLevel(logging.INFO)
    db_logger.addHandler(console_handler)
    db_logger.addHandler(file_handler)
    db_logger.addHandler(error_handler)
    
    return {
        'app': app_logger,
        'api': api_logger,
        'services': service_logger,
        'database': db_logger
    }

def log_request(request, response=None, error=None):
    """Log API request details."""
    logger = logging.getLogger('news4u.api')
    
    log_data = {
        'method': request.method,
        'url': str(request.url),
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'unknown'),
        'timestamp': datetime.now().isoformat()
    }
    
    if response:
        log_data['status_code'] = response.status_code
        log_data['response_time'] = getattr(response, 'response_time', 'unknown')
        logger.info(f"API Request: {log_data}")
    elif error:
        log_data['error'] = str(error)
        logger.error(f"API Request Error: {log_data}")
    else:
        logger.info(f"API Request: {log_data}")

def log_content_extraction(url, success, content_length=0, embedded_images=0, standalone_images=0, error=None):
    """Log content extraction attempts."""
    logger = logging.getLogger('news4u.services')
    
    log_data = {
        'url': url,
        'success': success,
        'content_length': content_length,
        'embedded_images': embedded_images,
        'standalone_images': standalone_images,
        'timestamp': datetime.now().isoformat()
    }
    
    if error:
        log_data['error'] = str(error)
        logger.error(f"Content Extraction Failed: {log_data}")
    else:
        logger.info(f"Content Extraction Success: {log_data}")

def log_feed_fetch(feed_name, success, articles_found=0, articles_processed=0, error=None):
    """Log RSS feed fetch attempts."""
    logger = logging.getLogger('news4u.services')
    
    log_data = {
        'feed_name': feed_name,
        'success': success,
        'articles_found': articles_found,
        'articles_processed': articles_processed,
        'timestamp': datetime.now().isoformat()
    }
    
    if error:
        log_data['error'] = str(error)
        logger.error(f"Feed Fetch Failed: {log_data}")
    else:
        logger.info(f"Feed Fetch Success: {log_data}")

def log_database_operation(operation, table, success, rows_affected=0, error=None):
    """Log database operations."""
    logger = logging.getLogger('news4u.database')
    
    log_data = {
        'operation': operation,
        'table': table,
        'success': success,
        'rows_affected': rows_affected,
        'timestamp': datetime.now().isoformat()
    }
    
    if error:
        log_data['error'] = str(error)
        logger.error(f"Database Operation Failed: {log_data}")
    else:
        logger.info(f"Database Operation Success: {log_data}")

# Initialize logging when module is imported
loggers = setup_logging() 