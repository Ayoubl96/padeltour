import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging_config import get_logger
import re

logger = get_logger("padeltour.middleware")


class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware with detailed status code tracking and response metrics
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
        
        # Clean endpoint for better grouping in dashboards
        clean_endpoint = self._normalize_endpoint(path)
        
        # Log incoming request with enhanced structured data
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
                    "status_code": 500,
                    "status_category": "server_error",
                    "status_class": "5xx",
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
            
            # Enhanced status code categorization
            status_category = self._get_status_category(status_code)
            status_class = self._get_status_class(status_code)
            
            # Determine log level and message
            log_level = self._get_log_level(status_code)
            log_message = f"Completed {method} request to {path} - {status_code} ({duration_ms}ms)"
            
            # Enhanced log data with detailed status information
            log_extra = {
                "request_id": request_id,
                "method": method,
                "endpoint": clean_endpoint,
                "path": path,
                "status_code": status_code,
                "status_category": status_category,  # success, client_error, server_error, etc.
                "status_class": status_class,        # 2xx, 4xx, 5xx
                "duration_ms": duration_ms,
                "response_size_bytes": response_size,
                "client_ip": client_ip,
                "event_type": "request_complete",
                "timestamp": time.time(),
                
                # Performance and health indicators
                "is_success": status_code < 400,
                "is_client_error": 400 <= status_code < 500,
                "is_server_error": status_code >= 500,
                "is_slow": duration_ms > 1000,      # > 1 second
                "is_very_slow": duration_ms > 5000, # > 5 seconds
            }
            
            if error_message:
                log_extra["error"] = error_message
            
            # Log with appropriate level
            if log_level == "info":
                logger.info(log_message, extra=log_extra)
            elif log_level == "warning":
                logger.warning(log_message, extra=log_extra)
            else:
                logger.error(log_message, extra=log_extra)
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for better dashboard grouping
        Replace dynamic segments with placeholders
        """
        # Replace UUIDs with placeholder
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        
        # Replace numeric IDs with placeholder
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace other common dynamic segments
        path = re.sub(r'/[a-f0-9]{24}', '/{objectid}', path)  # MongoDB ObjectId
        
        return path
    
    def _get_status_category(self, status_code: int) -> str:
        """
        Categorize HTTP status codes for better dashboard grouping
        """
        if status_code < 300:
            return "success"
        elif status_code < 400:
            return "redirect"
        elif status_code < 500:
            return "client_error"
        else:
            return "server_error"
    
    def _get_status_class(self, status_code: int) -> str:
        """
        Get status code class (2xx, 4xx, etc.) for dashboard grouping
        """
        return f"{status_code // 100}xx"
    
    def _get_log_level(self, status_code: int) -> str:
        """
        Determine appropriate log level based on status code
        """
        if status_code < 400:
            return "info"
        elif status_code < 500:
            return "warning"  # Client errors as warnings
        else:
            return "error"    # Server errors as errors


class StatusCodeMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware specifically for collecting detailed status code metrics
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.status_code_counts = {}
        
    async def dispatch(self, request: Request, call_next):
        self.request_count += 1
        
        # Log periodic metrics every 100 requests
        if self.request_count % 100 == 0:
            logger.info(
                f"Status code metrics checkpoint: {self.request_count} total requests",
                extra={
                    "event_type": "status_metrics_checkpoint",
                    "total_requests": self.request_count,
                    "status_code_distribution": dict(self.status_code_counts),
                    "timestamp": time.time()
                }
            )
        
        try:
            response = await call_next(request)
            
            # Count status codes
            status_code = response.status_code
            status_class = f"{status_code // 100}xx"
            
            self.status_code_counts[status_code] = self.status_code_counts.get(status_code, 0) + 1
            
            # Log detailed status code info for specific codes
            if status_code >= 400:
                logger.warning(
                    f"HTTP {status_code} response on {request.method} {request.url.path}",
                    extra={
                        "event_type": "http_error_detail",
                        "status_code": status_code,
                        "status_class": status_class,
                        "method": request.method,
                        "endpoint": request.url.path,
                        "timestamp": time.time()
                    }
                )
            
            return response
            
        except Exception as e:
            # Count 5xx errors from exceptions
            self.status_code_counts[500] = self.status_code_counts.get(500, 0) + 1
            raise 