import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Any, Dict
import os
from app.core.grafana_config import setup_grafana_logging


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
            
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
            
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
            
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        elif hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)


class PlainFormatter(logging.Formatter):
    """
    Plain text formatter for development
    """
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        return f"[{timestamp}] {record.levelname} - {record.name}: {record.getMessage()}"


def setup_logging():
    """
    Setup logging configuration
    """
    # Get log level from environment variable, default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Use JSON formatting in production (Heroku), plain text in development
    use_json = os.getenv("DYNO") is not None  # DYNO env var exists in Heroku
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Set formatter based on environment
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = PlainFormatter()
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Setup Grafana Cloud logging if configured
    setup_grafana_logging()
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return logging.getLogger(name)


# Application logger
app_logger = get_logger("padeltour")


# Log context manager for adding extra fields
class LogContext:
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra = kwargs
    
    def info(self, message: str, **extra_kwargs):
        self.logger.info(message, extra={**self.extra, **extra_kwargs})
    
    def error(self, message: str, **extra_kwargs):
        self.logger.error(message, extra={**self.extra, **extra_kwargs})
    
    def warning(self, message: str, **extra_kwargs):
        self.logger.warning(message, extra={**self.extra, **extra_kwargs})
    
    def debug(self, message: str, **extra_kwargs):
        self.logger.debug(message, extra={**self.extra, **extra_kwargs}) 