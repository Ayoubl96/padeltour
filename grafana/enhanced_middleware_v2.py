import time
import uuid
import json
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging_config import get_logger

logger = get_logger("padeltour.enhanced_middleware")


class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware to log all HTTP requests and responses with detailed metrics
    Provides additional fields for comprehensive monitoring and analytics
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        content_type = request.headers.get("content-type", "")
        content_length = request.headers.get("content-length", "0")
        
        # Extract additional headers for monitoring
        x_forwarded_for = request.headers.get("x-forwarded-for", "")
        authorization = "present" if request.headers.get("authorization") else "none"
        
        # Log incoming request with enhanced details
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "endpoint": path,
                "url": url,
                "query_params": query_params,
                "client_ip": client_ip,
                "x_forwarded_for": x_forwarded_for,
                "user_agent": user_agent,
                "content_type": content_type,
                "content_length": int(content_length) if content_length.isdigit() else 0,
                "authorization": authorization,
                "event_type": "request_start",
                "timestamp": time.time()
            }
        )
        
        # Add request ID to request state for use in route handlers
        request.state.request_id = request_id
        
        response = None
        status_code = 500
        error_message = None
        response_size = 0
        
        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
            
            # Try to get response size
            if hasattr(response, 'headers'):
                content_length_header = response.headers.get("content-length")
                if content_length_header:
                    response_size = int(content_length_header)
            
        except Exception as e:
            # Log any exceptions that occur
            error_message = str(e)
            error_type = type(e).__name__
            
            logger.error(
                f"Request failed: {method} {path} - {error_type}: {error_message}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": path,
                    "status_code": 500,
                    "error": error_message,
                    "error_type": error_type,
                    "event_type": "request_error",
                    "client_ip": client_ip,
                    "timestamp": time.time()
                },
                exc_info=True
            )
            # Re-raise the exception
            raise
        
        finally:
            # Calculate duration
            end_time = time.time()
            duration_ms = round((end_time - start_time) * 1000, 2)
            
            # Determine status code category
            status_category = self._get_status_category(status_code)
            
            # Log response completion
            log_message = f"Request completed: {method} {path} - {status_code}"
            
            # Enhanced log data
            log_extra = {
                "request_id": request_id,
                "method": method,
                "endpoint": path,
                "url": url,
                "status_code": status_code,
                "status_category": status_category,
                "duration_ms": duration_ms,
                "response_size": response_size,
                "client_ip": client_ip,
                "x_forwarded_for": x_forwarded_for,
                "user_agent": user_agent,
                "event_type": "request_complete",
                "timestamp": end_time,
                # Performance metrics
                "is_slow": duration_ms > 1000,  # Flag slow requests (>1s)
                "is_error": status_code >= 400,
                "is_server_error": status_code >= 500,
                "is_client_error": 400 <= status_code < 500,
                "is_success": 200 <= status_code < 300,
                "is_redirect": 300 <= status_code < 400,
            }
            
            if error_message:
                log_extra["error"] = error_message
                log_extra["had_exception"] = True
            else:
                log_extra["had_exception"] = False
            
            # Always log completion (use INFO level for consistent querying)
            logger.info(log_message, extra=log_extra)
            
            # Log specific event types for different status codes
            if status_code >= 500:
                logger.error(f"Server error: {method} {path} - {status_code}", extra={
                    **log_extra,
                    "event_type": "server_error"
                })
            elif status_code >= 400:
                logger.warning(f"Client error: {method} {path} - {status_code}", extra={
                    **log_extra,
                    "event_type": "client_error"
                })
            elif status_code >= 300:
                logger.info(f"Redirect: {method} {path} - {status_code}", extra={
                    **log_extra,
                    "event_type": "redirect"
                })
            else:
                logger.info(f"Success: {method} {path} - {status_code}", extra={
                    **log_extra,
                    "event_type": "success"
                })
            
            # Log slow requests separately for monitoring
            if duration_ms > 1000:
                logger.warning(f"Slow request detected: {method} {path} took {duration_ms}ms", extra={
                    **log_extra,
                    "event_type": "slow_request"
                })
            
            # Log high traffic endpoints
            self._log_endpoint_metrics(path, method, status_code, duration_ms, request_id)
        
        return response
    
    def _get_status_category(self, status_code: int) -> str:
        """Categorize HTTP status codes"""
        if 200 <= status_code < 300:
            return "2xx_success"
        elif 300 <= status_code < 400:
            return "3xx_redirect"
        elif 400 <= status_code < 500:
            return "4xx_client_error"
        elif 500 <= status_code < 600:
            return "5xx_server_error"
        else:
            return "unknown"
    
    def _log_endpoint_metrics(self, endpoint: str, method: str, status_code: int, duration_ms: float, request_id: str):
        """Log specific endpoint metrics for analytics"""
        # Log endpoint-specific metrics
        logger.info(
            f"Endpoint metrics: {method} {endpoint}",
            extra={
                "request_id": request_id,
                "event_type": "endpoint_metrics",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "endpoint_method": f"{method}_{endpoint}",
                "timestamp": time.time()
            }
        )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware to add request context to all log messages within a request
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get request ID from logging middleware
        request_id = getattr(request.state, 'request_id', None)
        
        # Add request context to logger
        if request_id:
            # You can access this in your route handlers via request.state.request_id
            pass
            
        response = await call_next(request)
        return response


# Helper function to log custom business events with enhanced context
def log_enhanced_business_event(
    event_name: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    tournament_id: Optional[int] = None,
    match_id: Optional[int] = None,
    additional_data: Optional[dict] = None,
    request: Optional[Request] = None
):
    """
    Log business events with enhanced context for better analytics
    """
    log_data = {
        "event_type": "business_event",
        "business_event": event_name,
        "timestamp": time.time()
    }
    
    # Add IDs if provided
    if user_id:
        log_data["user_id"] = user_id
    if company_id:
        log_data["company_id"] = company_id
    if tournament_id:
        log_data["tournament_id"] = tournament_id
    if match_id:
        log_data["match_id"] = match_id
    
    # Add request context
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
        log_data["client_ip"] = request.client.host if request.client else "unknown"
        log_data["endpoint"] = request.url.path
        log_data["method"] = request.method
    
    # Add additional data
    if additional_data:
        log_data.update(additional_data)
    
    logger.info(f"Business event: {event_name}", extra=log_data)


# Helper function to log performance metrics
def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    additional_context: Optional[dict] = None,
    request: Optional[Request] = None
):
    """
    Log performance metrics for monitoring
    """
    log_data = {
        "event_type": "performance_metric",
        "metric_name": metric_name,
        "metric_value": value,
        "metric_unit": unit,
        "timestamp": time.time()
    }
    
    if request:
        log_data["request_id"] = getattr(request.state, 'request_id', None)
        log_data["endpoint"] = request.url.path
        log_data["method"] = request.method
    
    if additional_context:
        log_data.update(additional_context)
    
    logger.info(f"Performance metric: {metric_name} = {value}{unit}", extra=log_data) 