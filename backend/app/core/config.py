from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os
import secrets
from urllib.parse import urlparse

class Settings(BaseSettings):
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "ESG AI Co-Pilot"
    version: str = "1.0.0"
    
    # Environment
    environment: str = "production"
    debug: bool = False
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2000
    openai_timeout: int = 60
    
    # ChromaDB Configuration
    chroma_db_path: str = "./chroma_db"
    
    # File Upload Configuration
    upload_dir: str = "./uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = [".pdf", ".docx", ".xlsx", ".csv", ".txt"]
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_keys: List[str] = []  # For API key authentication
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # IP Filtering
    blocked_ips: List[str] = []
    allowed_ips: List[str] = []  # If set, only these IPs are allowed
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None
    
    # Database Settings
    database_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis Settings
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_pool_size: int = 10
    
    # Monitoring & Health Checks
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # Performance Settings
    worker_processes: int = 1
    worker_connections: int = 1000
    keepalive_timeout: int = 65
    max_request_size: int = 100 * 1024 * 1024  # 100MB
    
    # Cache Settings
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000
    
    # SSL/TLS Settings
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None
    ssl_ca_file: Optional[str] = None
    
    # External Services
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    
    # Backup Settings
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    
    # Feature Flags
    enable_chat: bool = True
    enable_document_upload: bool = True
    enable_report_generation: bool = True
    enable_compliance_check: bool = True
    enable_supply_chain: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate configuration settings"""
        # Validate OpenAI API key in production
        if self.environment == "production" and not self.openai_api_key:
            raise ValueError("OpenAI API key is required in production")
        
        # Validate secret key strength
        if len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # Validate database URL format if provided
        if self.database_url:
            try:
                parsed = urlparse(self.database_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("Invalid database URL format")
            except Exception:
                raise ValueError("Invalid database URL format")
        
        # Validate Redis URL format if provided
        if self.redis_url:
            try:
                parsed = urlparse(self.redis_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("Invalid Redis URL format")
            except Exception:
                raise ValueError("Invalid Redis URL format")
        
        # Ensure required directories exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.chroma_db_path, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() in ["development", "dev"]
    
    @property
    def database_config(self) -> dict:
        """Get database configuration"""
        if not self.database_url:
            return {}
        
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow
        }
    
    @property
    def redis_config(self) -> dict:
        """Get Redis configuration"""
        if not self.redis_url:
            return {}
        
        return {
            "url": self.redis_url,
            "password": self.redis_password,
            "db": self.redis_db,
            "max_connections": self.redis_pool_size
        }

settings = Settings()
