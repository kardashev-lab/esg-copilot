from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import json
import uuid
from typing import Dict, Any
from datetime import datetime
import psutil
import asyncio

logger = logging.getLogger(__name__)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Comprehensive monitoring and logging middleware"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "response_times": [],
            "status_codes": {},
            "endpoints": {}
        }

    async def dispatch(self, request: Request, call_next):
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(request, response, process_time)
            
            # Log response
            if self.log_responses:
                await self._log_response(request, response, request_id, process_time)
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            self.metrics["errors"] += 1
            
            # Log error
            logger.error(
                f"Request error",
                extra={
                    "req_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": process_time,
                    "client_ip": self._get_client_ip(request)
                }
            )
            raise

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body for logging (be careful with large files)
                if request.headers.get("content-type", "").startswith("application/json"):
                    body_bytes = await request.body()
                    if len(body_bytes) < 10000:  # Only log small payloads
                        body = body_bytes.decode("utf-8")
            except Exception:
                body = "<unable to read body>"
        
        logger.info(
            f"Request started",
            extra={
                "req_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "headers": dict(request.headers),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent"),
                "body": body,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def _log_response(self, request: Request, response: Response, request_id: str, process_time: float):
        """Log response details"""
        logger.info(
            f"Request completed",
            extra={
                "req_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
                "response_size": response.headers.get("content-length"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def _update_metrics(self, request: Request, response: Response, process_time: float):
        """Update internal metrics"""
        self.metrics["requests"] += 1
        self.metrics["response_times"].append(process_time)
        
        # Keep only last 1000 response times for memory efficiency
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Track status codes
        status_code = response.status_code
        self.metrics["status_codes"][status_code] = self.metrics["status_codes"].get(status_code, 0) + 1
        
        # Track endpoints
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in self.metrics["endpoints"]:
            self.metrics["endpoints"][endpoint] = {
                "count": 0,
                "total_time": 0,
                "errors": 0,
                "avg_time": 0
            }
        
        endpoint_metrics = self.metrics["endpoints"][endpoint]
        endpoint_metrics["count"] += 1
        endpoint_metrics["total_time"] += process_time
        endpoint_metrics["avg_time"] = endpoint_metrics["total_time"] / endpoint_metrics["count"]
        
        if status_code >= 400:
            endpoint_metrics["errors"] += 1

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        response_times = self.metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_requests": self.metrics["requests"],
            "total_errors": self.metrics["errors"],
            "error_rate": self.metrics["errors"] / max(self.metrics["requests"], 1),
            "avg_response_time": avg_response_time,
            "status_codes": self.metrics["status_codes"],
            "endpoints": self.metrics["endpoints"],
            "system_metrics": self._get_system_metrics()
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids())
            }
        except Exception:
            return {}


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured JSON logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Set up structured logging context
        extra_context = {
            "service": "reggie-ai-copilot-api",
            "environment": "production",  # This should come from settings
            "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.url.path
        }
        
        # Add context to all log messages during this request
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in extra_context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class HealthCheckMonitor:
    """System health monitoring"""
    
    def __init__(self):
        self.startup_time = datetime.utcnow()
        self.health_checks = {}

    async def register_health_check(self, name: str, check_func):
        """Register a health check function"""
        self.health_checks[name] = check_func

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": str(datetime.utcnow() - self.startup_time),
            "checks": {}
        }
        
        # Run all registered health checks
        overall_healthy = True
        for name, check_func in self.health_checks.items():
            try:
                check_result = await check_func()
                status["checks"][name] = {
                    "status": "healthy" if check_result else "unhealthy",
                    "details": check_result if isinstance(check_result, dict) else {}
                }
                if not check_result:
                    overall_healthy = False
            except Exception as e:
                status["checks"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                overall_healthy = False
        
        # Add system metrics
        try:
            status["system"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        except Exception as e:
            status["system"] = {"error": str(e)}
        
        status["status"] = "healthy" if overall_healthy else "unhealthy"
        return status

# Global health monitor instance
health_monitor = HealthCheckMonitor()
