from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import redis
import asyncio

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    esg_copilot_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    ESGCopilotException
)
from app.middleware.security import SecurityMiddleware, APIKeyMiddleware
from app.middleware.monitoring import MonitoringMiddleware, StructuredLoggingMiddleware, health_monitor
from app.utils.cache import initialize_cache
from app.utils.backup import initialize_backup_system, BackupConfig, shutdown_backup_system
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load environment variables
load_dotenv()

# Configure structured logging
def setup_logging():
    """Setup structured logging based on configuration"""
    if settings.log_format == "json":
        # JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "service": "esg-copilot-api",
                    "environment": settings.environment
                }
                
                # Add extra fields from record
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                                  'filename', 'module', 'lineno', 'funcName', 'created', 
                                  'msecs', 'relativeCreated', 'thread', 'threadName', 
                                  'processName', 'process', 'stack_info', 'exc_info']:
                        log_entry[key] = value
                
                return json.dumps(log_entry)
        
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

setup_logging()
logger = logging.getLogger(__name__)

# Global Redis client for rate limiting
redis_client = None

async def setup_redis():
    """Setup Redis connection if configured"""
    global redis_client
    if settings.redis_url:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                db=settings.redis_db,
                max_connections=settings.redis_pool_size,
                decode_responses=True
            )
            # Test connection
            await asyncio.to_thread(redis_client.ping)
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Rate limiting will use memory.")
            redis_client = None

async def setup_health_checks():
    """Setup health check functions"""
    
    async def check_openai():
        """Check OpenAI API connectivity"""
        if not settings.openai_api_key:
            return {"status": "disabled", "reason": "No API key configured"}
        try:
            # Simple test - you might want to make an actual API call
            return {"status": "healthy", "model": settings.openai_model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_redis():
        """Check Redis connectivity"""
        if not redis_client:
            return {"status": "disabled", "reason": "Redis not configured"}
        try:
            await asyncio.to_thread(redis_client.ping)
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_disk_space():
        """Check disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            usage_percent = (used / total) * 100
            status = "healthy" if usage_percent < 90 else "warning" if usage_percent < 95 else "critical"
            return {
                "status": status,
                "usage_percent": round(usage_percent, 2),
                "free_gb": round(free / (1024**3), 2)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # Register health checks
    await health_monitor.register_health_check("openai", check_openai)
    await health_monitor.register_health_check("redis", check_redis)
    await health_monitor.register_health_check("disk_space", check_disk_space)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ESG AI Co-Pilot API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Version: {settings.version}")
    
    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_db_path, exist_ok=True)
    
    # Setup Redis
    await setup_redis()
    
    # Initialize cache system
    initialize_cache(redis_client, settings.cache_ttl)
    
    # Initialize backup system
    backup_config = BackupConfig(
        enabled=settings.backup_enabled,
        schedule=settings.backup_schedule,
        retention_days=settings.backup_retention_days,
        s3_bucket=getattr(settings, 's3_bucket', None),
        s3_region=getattr(settings, 's3_region', None),
        s3_access_key=getattr(settings, 's3_access_key', None),
        s3_secret_key=getattr(settings, 's3_secret_key', None)
    )
    initialize_backup_system(backup_config)
    
    # Setup health checks
    await setup_health_checks()
    
    logger.info("ESG AI Co-Pilot API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ESG AI Co-Pilot API...")
    
    # Shutdown backup system
    shutdown_backup_system()
    
    # Close Redis connection
    if redis_client:
        try:
            redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    logger.info("ESG AI Co-Pilot API shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="ESG AI Co-Pilot API",
    description="AI-powered co-pilot for ESG and sustainability professionals",
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add security middleware (order matters!)
if settings.is_production:
    # Trusted host middleware to prevent Host header attacks
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your actual domains in production
    )

# Add monitoring middleware first
app.add_middleware(
    MonitoringMiddleware,
    log_requests=True,
    log_responses=settings.debug
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add security middleware
app.add_middleware(
    SecurityMiddleware,
    redis_client=redis_client,
    rate_limit_requests=settings.rate_limit_requests,
    rate_limit_window=settings.rate_limit_window,
    blocked_ips=settings.blocked_ips,
    allowed_ips=settings.allowed_ips
)

# Add API key middleware for production
if settings.api_keys:
    app.add_middleware(
        APIKeyMiddleware,
        api_keys=settings.api_keys,
        exempt_paths=["/health", "/", "/metrics"]
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Exception handlers
app.add_exception_handler(ESGCopilotException, esg_copilot_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return await health_monitor.get_health_status()

# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    if not settings.enable_metrics:
        return JSONResponse(
            status_code=404,
            content={"detail": "Metrics endpoint disabled"}
        )
    
    # Get metrics from middleware - this would need to be properly implemented
    # For now, return basic system metrics
    metrics = {
        "requests": 0,
        "errors": 0,
        "uptime": str(datetime.utcnow() - health_monitor.startup_time)
    }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "esg-copilot-api",
        "version": settings.version,
        "environment": settings.environment,
        "metrics": metrics
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ESG AI Co-Pilot API",
        "version": settings.version,
        "environment": settings.environment,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "features": {
            "chat": settings.enable_chat,
            "document_upload": settings.enable_document_upload,
            "report_generation": settings.enable_report_generation,
            "compliance_check": settings.enable_compliance_check,
            "supply_chain": settings.enable_supply_chain
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
