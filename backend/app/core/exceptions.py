"""
Custom exceptions and error handling for the ESG AI Co-Pilot API
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ESGCopilotException(Exception):
    """Base exception for ESG Co-Pilot application"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ValidationException(ESGCopilotException):
    """Raised when validation fails"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
            status_code=400
        )


class AuthenticationException(ESGCopilotException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationException(ESGCopilotException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )


class ResourceNotFoundException(ESGCopilotException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=404
        )


class RateLimitException(ESGCopilotException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, retry_after: int = 3600):
        super().__init__(
            message="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            status_code=429
        )


class ExternalServiceException(ESGCopilotException):
    """Raised when an external service fails"""
    
    def __init__(self, service_name: str, message: str = None):
        super().__init__(
            message=message or f"{service_name} service unavailable",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name},
            status_code=503
        )


class FileProcessingException(ESGCopilotException):
    """Raised when file processing fails"""
    
    def __init__(self, filename: str, message: str = None):
        super().__init__(
            message=message or f"Failed to process file: {filename}",
            error_code="FILE_PROCESSING_ERROR",
            details={"filename": filename},
            status_code=422
        )


class DatabaseException(ESGCopilotException):
    """Raised when database operations fail"""
    
    def __init__(self, operation: str, message: str = None):
        super().__init__(
            message=message or f"Database operation failed: {operation}",
            error_code="DATABASE_ERROR",
            details={"operation": operation},
            status_code=500
        )


class ConfigurationException(ESGCopilotException):
    """Raised when configuration is invalid"""
    
    def __init__(self, setting: str, message: str = None):
        super().__init__(
            message=message or f"Invalid configuration: {setting}",
            error_code="CONFIGURATION_ERROR",
            details={"setting": setting},
            status_code=500
        )


# Error response formatters
def create_error_response(
    error: ESGCopilotException,
    request: Request = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """Create a standardized error response"""
    
    response = {
        "error": {
            "code": error.error_code,
            "message": error.message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
    
    # Add details if available
    if error.details:
        response["error"]["details"] = error.details
    
    # Add request information
    if request:
        response["error"]["request_id"] = getattr(request.state, "request_id", None)
        response["error"]["path"] = str(request.url.path)
        response["error"]["method"] = request.method
    
    # Add traceback in development
    if include_traceback:
        import traceback
        response["error"]["traceback"] = traceback.format_exc()
    
    return response


# Exception handlers
async def esg_copilot_exception_handler(request: Request, exc: ESGCopilotException):
    """Handle custom ESG Co-Pilot exceptions"""
    
    # Log the error
    logger.error(
        f"ESG Co-Pilot error: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    # Create error response
    from app.core.config import settings
    error_response = create_error_response(
        exc, 
        request, 
        include_traceback=settings.debug
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    
    # Extract validation details
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error",
        extra={
            "errors": errors,
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    # Create standardized error response
    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "validation_errors": errors
            },
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    
    logger.warning(
        f"HTTP error: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    # Create standardized error response
    error_response = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        },
        exc_info=True
    )
    
    # Create generic error response
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method
        }
    }
    
    # Add exception details in debug mode
    from app.core.config import settings
    if settings.debug:
        error_response["error"]["debug"] = {
            "exception_type": type(exc).__name__,
            "message": str(exc)
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# Utility functions for error handling
def handle_external_service_error(service_name: str, error: Exception) -> ExternalServiceException:
    """Convert external service errors to our custom exception"""
    
    error_message = str(error)
    
    # OpenAI specific errors
    if "openai" in service_name.lower():
        if "rate limit" in error_message.lower():
            raise RateLimitException()
        elif "invalid api key" in error_message.lower():
            raise AuthenticationException("Invalid OpenAI API key")
        elif "quota exceeded" in error_message.lower():
            raise ExternalServiceException(service_name, "API quota exceeded")
    
    # Generic external service error
    raise ExternalServiceException(service_name, error_message)


def validate_file_upload(filename: str, content_type: str, file_size: int) -> None:
    """Validate file upload parameters"""
    
    from app.core.config import settings
    
    # Check file size
    if file_size > settings.max_file_size:
        max_size_mb = settings.max_file_size / (1024 * 1024)
        raise ValidationException(
            f"File size exceeds maximum limit of {max_size_mb:.1f}MB",
            field="file",
            details={"file_size": file_size, "max_size": settings.max_file_size}
        )
    
    # Check file extension
    import os
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in settings.allowed_file_types:
        raise ValidationException(
            f"File type '{file_ext}' not allowed. Allowed types: {', '.join(settings.allowed_file_types)}",
            field="file",
            details={"file_extension": file_ext, "allowed_types": settings.allowed_file_types}
        )
    
    # Additional content type validation could be added here
    logger.info(f"File validation passed for: {filename}")


def require_feature_enabled(feature_name: str) -> None:
    """Check if a feature is enabled, raise exception if not"""
    
    from app.core.config import settings
    
    feature_map = {
        "chat": settings.enable_chat,
        "document_upload": settings.enable_document_upload,
        "report_generation": settings.enable_report_generation,
        "compliance_check": settings.enable_compliance_check,
        "supply_chain": settings.enable_supply_chain
    }
    
    if feature_name not in feature_map:
        raise ConfigurationException(f"Unknown feature: {feature_name}")
    
    if not feature_map[feature_name]:
        raise AuthorizationException(f"Feature '{feature_name}' is currently disabled")
