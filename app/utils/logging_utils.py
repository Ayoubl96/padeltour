from typing import Optional, Any, Dict
from fastapi import Request
from app.core.logging_config import get_logger


def log_user_action(
    logger_name: str,
    action: str, 
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Log user actions with consistent formatting
    """
    logger = get_logger(logger_name)
    
    log_data = {
        "event_type": "user_action",
        "action": action,
    }
    
    if user_id:
        log_data["user_id"] = user_id
        
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
        log_data["client_ip"] = request.client.host if request.client else "unknown"
        
    if extra_data:
        log_data.update(extra_data)
    
    logger.info(f"User action: {action}", extra=log_data)


def log_business_event(
    logger_name: str,
    event: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
):
    """
    Log business events (tournaments, registrations, etc.)
    """
    logger = get_logger(logger_name)
    
    log_data = {
        "event_type": "business_event",
        "business_event": event,
    }
    
    if user_id:
        log_data["user_id"] = user_id
        
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
        
    if details:
        log_data.update(details)
    
    logger.info(f"Business event: {event}", extra=log_data)


def log_error(
    logger_name: str,
    error_message: str,
    error_type: str = "application_error",
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    exception: Optional[Exception] = None
):
    """
    Log errors with consistent formatting
    """
    logger = get_logger(logger_name)
    
    log_data = {
        "event_type": "error",
        "error_type": error_type,
    }
    
    if user_id:
        log_data["user_id"] = user_id
        
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
        
    if exception:
        log_data["exception_type"] = type(exception).__name__
        logger.error(error_message, extra=log_data, exc_info=True)
    else:
        logger.error(error_message, extra=log_data)


def log_database_operation(
    logger_name: str,
    operation: str,
    table: str,
    record_id: Optional[int] = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
):
    """
    Log database operations
    """
    logger = get_logger(logger_name)
    
    log_data = {
        "event_type": "database_operation",
        "operation": operation,
        "table": table,
    }
    
    if record_id:
        log_data["record_id"] = record_id
        
    if user_id:
        log_data["user_id"] = user_id
        
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
    
    logger.info(f"Database {operation} on {table}", extra=log_data)


def log_external_api_call(
    logger_name: str,
    api_name: str,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
):
    """
    Log external API calls
    """
    logger = get_logger(logger_name)
    
    log_data = {
        "event_type": "external_api_call",
        "api_name": api_name,
        "api_endpoint": endpoint,
        "api_method": method,
    }
    
    if status_code:
        log_data["api_status_code"] = status_code
        
    if duration_ms:
        log_data["api_duration_ms"] = duration_ms
        
    if user_id:
        log_data["user_id"] = user_id
        
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
    
    message = f"External API call to {api_name} {method} {endpoint}"
    if status_code:
        message += f" - {status_code}"
        
    logger.info(message, extra=log_data) 