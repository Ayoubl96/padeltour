import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging_config import get_logger
import json

logger = get_logger("padeltour.middleware")


class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware with better metrics for Grafana dashboard
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
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Clean endpoint for better grouping in dashboard
        clean_endpoint = self._clean_endpoint(path)
        
        # Log incoming request with structured data
        logger.info(
            f"Incoming {method} request to {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "endpoint": clean_endpoint,
                "full_url": url,
                "path": path,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "event_type": "request_start",
                "timestamp": time.time()
            }
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        response = None
        status_code = 500
        error_message = None
        response_size = 0
        
        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
            
            # Try to get response size if available
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                response_size = int(response.headers['content-length'])
            
        except Exception as e:
            error_message = str(e)
            logger.error(
                f"Error processing {method} request to {url}: {error_message}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": clean_endpoint,
                    "error": error_message,
                    "event_type": "request_error",
                    "timestamp": time.time()
                },
                exc_info=True
            )
            raise
        
        finally:
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Determine status category for better dashboard grouping
            status_category = self._get_status_category(status_code)
            
            # Enhanced completion log with metrics
            log_message = f"Completed {method} request to {path} - {status_code} ({duration_ms}ms)"
            
            log_extra = {
                "request_id": request_id,
                "method": method,
                "endpoint": clean_endpoint,
                "path": path,
                "status_code": status_code,
                "status_category": status_category,
                "duration_ms": duration_ms,
                "response_size_bytes": response_size,
                "client_ip": client_ip,
                "event_type": "request_complete",
                "timestamp": time.time(),
                # Add performance categories
                "is_slow": duration_ms > 1000,  # > 1 second
                "is_error": status_code >= 400,
                "is_server_error": status_code >= 500
            }
            
            if error_message:
                log_extra["error"] = error_message
            
            # Log with appropriate level
            if status_code >= 500:
                logger.error(log_message, extra=log_extra)
            elif status_code >= 400:
                logger.warning(log_message, extra=log_extra)
            else:
                logger.info(log_message, extra=log_extra)
        
        return response
    
    def _clean_endpoint(self, path: str) -> str:
        """
        Clean endpoint path for better dashboard grouping
        Replace dynamic segments with placeholders
        """
        # Common patterns to normalize
        import re
        
        # Replace UUIDs with placeholder
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        
        # Replace numeric IDs with placeholder
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Keep original if no substitutions made
        return path
    
    def _get_status_category(self, status_code: int) -> str:
        """
        Categorize HTTP status codes for dashboard
        """
        if status_code < 300:
            return "success"
        elif status_code < 400:
            return "redirect"
        elif status_code < 500:
            return "client_error"
        else:
            return "server_error"


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware specifically for collecting metrics data
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        
    async def dispatch(self, request: Request, call_next):
        self.request_count += 1
        
        # Log periodic metrics
        if self.request_count % 100 == 0:  # Every 100 requests
            logger.info(
                f"Metrics checkpoint: {self.request_count} total requests, {self.error_count} errors",
                extra={
                    "event_type": "metrics_checkpoint",
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                    "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0
                }
            )
        
        try:
            response = await call_next(request)
            
            # Count errors
            if response.status_code >= 400:
                self.error_count += 1
                
            return response
            
        except Exception as e:
            self.error_count += 1
            raise 