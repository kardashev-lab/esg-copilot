from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import redis
from collections import defaultdict
from typing import Dict, Optional
import ipaddress
import re
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware with multiple protection layers"""
    
    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 3600,  # 1 hour
        blocked_ips: Optional[list] = None,
        allowed_ips: Optional[list] = None
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.blocked_ips = set(blocked_ips or [])
        self.allowed_ips = set(allowed_ips or [])
        
        # In-memory fallback if Redis is not available
        self.memory_store: Dict[str, Dict] = defaultdict(dict)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check IP allowlist/blocklist
        if not self._is_ip_allowed(client_ip):
            logger.warning(f"Blocked request from IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # Check rate limiting
        if not await self._check_rate_limit(client_ip, request.url.path):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": 3600
                }
            )
        
        # Check for suspicious patterns
        if self._detect_suspicious_activity(request):
            logger.warning(f"Suspicious activity detected from IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Suspicious activity detected"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (for proxy/load balancer scenarios)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"

    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed based on allowlist/blocklist"""
        if ip == "unknown":
            return False
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Check if IP is in blocklist
            if self.blocked_ips:
                for blocked_ip in self.blocked_ips:
                    if ip_obj in ipaddress.ip_network(blocked_ip, strict=False):
                        return False
            
            # If allowlist is set, only allow IPs in the allowlist
            if self.allowed_ips:
                for allowed_ip in self.allowed_ips:
                    if ip_obj in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                return False
            
            return True
        except ValueError:
            # Invalid IP address
            return False

    async def _check_rate_limit(self, ip: str, path: str) -> bool:
        """Check rate limiting for IP"""
        current_time = int(time.time())
        key = f"rate_limit:{ip}"
        
        try:
            if self.redis_client:
                # Use Redis for rate limiting
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, current_time - self.rate_limit_window)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, self.rate_limit_window)
                results = pipe.execute()
                request_count = results[1]
            else:
                # Use in-memory store as fallback
                self._cleanup_memory_store()
                if key not in self.memory_store:
                    self.memory_store[key] = {"requests": [], "last_request": current_time}
                
                # Remove old requests
                self.memory_store[key]["requests"] = [
                    req_time for req_time in self.memory_store[key]["requests"]
                    if req_time > current_time - self.rate_limit_window
                ]
                
                # Add current request
                self.memory_store[key]["requests"].append(current_time)
                self.memory_store[key]["last_request"] = current_time
                request_count = len(self.memory_store[key]["requests"])
            
            return request_count <= self.rate_limit_requests
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return True

    def _cleanup_memory_store(self):
        """Clean up old entries from memory store"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            keys_to_remove = []
            for key, data in self.memory_store.items():
                if current_time - data.get("last_request", 0) > self.rate_limit_window:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.memory_store[key]
            
            self.last_cleanup = current_time

    def _detect_suspicious_activity(self, request: Request) -> bool:
        """Detect suspicious activity patterns"""
        # Check for common attack patterns in URL
        suspicious_patterns = [
            r"\.\.\/",  # Directory traversal
            r"<script",  # XSS attempt
            r"union.*select",  # SQL injection
            r"eval\(",  # Code injection
            r"exec\(",  # Code execution
        ]
        
        url_path = request.url.path.lower()
        query_string = str(request.url.query).lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url_path + query_string, re.IGNORECASE):
                return True
        
        # Check for suspicious headers
        user_agent = request.headers.get("User-Agent", "").lower()
        if not user_agent or "bot" in user_agent or "crawler" in user_agent:
            # Allow legitimate bots but log for monitoring
            logger.info(f"Bot/crawler detected: {user_agent}")
        
        # Check for unusually large headers
        for header_name, header_value in request.headers.items():
            if len(header_value) > 4096:  # 4KB limit
                return True
        
        return False

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # HSTS (only add if HTTPS)
        if response.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server information
        response.headers.pop("Server", None)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key authentication middleware for production"""
    
    def __init__(self, app, api_keys: Optional[list] = None, exempt_paths: Optional[list] = None):
        super().__init__(app)
        self.api_keys = set(api_keys or [])
        self.exempt_paths = set(exempt_paths or ["/health", "/", "/docs", "/redoc", "/openapi.json"])

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "API key required"}
            )
        
        # Validate API key
        if self.api_keys and api_key not in self.api_keys:
            logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"}
            )
        
        return await call_next(request)
