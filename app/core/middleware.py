import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging_config import get_logger

logger = get_logger("padeltour.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
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
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log incoming request
        logger.info(
            f"Incoming {method} request to {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "endpoint": url,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "event_type": "request_start"
            }
        )
        
        # Add request ID to request state for use in route handlers
        request.state.request_id = request_id
        
        response = None
        status_code = 500
        error_message = None
        
        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            # Log any exceptions that occur
            error_message = str(e)
            logger.error(
                f"Error processing {method} request to {url}: {error_message}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": url,
                    "status_code": 500,
                    "error": error_message,
                    "event_type": "request_error"
                },
                exc_info=True
            )
            # Re-raise the exception
            raise
        
        finally:
            # Calculate duration
            duration = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
            
            # Log response
            log_level = "info" if status_code < 400 else "error"
            log_message = f"Completed {method} request to {url} - {status_code}"
            
            log_extra = {
                "request_id": request_id,
                "method": method,
                "endpoint": url,
                "status_code": status_code,
                "duration_ms": duration,
                "client_ip": client_ip,
                "event_type": "request_complete",
                # Add debugging fields
                "has_response": response is not None,
                "processing_time": round(time.time() - start_time, 3)
            }
            
            if error_message:
                log_extra["error"] = error_message
                log_extra["had_exception"] = True
            else:
                log_extra["had_exception"] = False
                
            # Always log completion (even for errors) with consistent level for request_complete events
            logger.info(log_message, extra=log_extra)
            
            # Also log errors separately with ERROR level for alerting
            if status_code >= 400:
                logger.error(f"HTTP {status_code} error: {method} {url}", extra={
                    **log_extra,
                    "event_type": "http_error"
                })
        
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request context to all log messages within a request
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