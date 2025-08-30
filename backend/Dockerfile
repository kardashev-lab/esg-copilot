# Multi-stage build for production optimization
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# Development stage
# ============================================================================
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p uploads chroma_db logs backups && \
    chmod 755 uploads chroma_db logs backups

# Create non-root user for security
RUN groupadd -r appgroup && \
    useradd --create-home --shell /bin/bash -r -g appgroup app && \
    chown -R app:appgroup /app

USER app

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# Production stage
# ============================================================================
FROM base as production

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-dev -r requirements.txt && \
    pip install gunicorn==21.2.0 && \
    rm -rf ~/.cache/pip

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p uploads chroma_db logs backups tmp && \
    chmod 755 uploads chroma_db logs backups tmp

# Create non-root user for security
RUN groupadd -r appgroup && \
    useradd --create-home --shell /bin/bash -r -g appgroup app && \
    chown -R app:appgroup /app

# Copy production configuration
COPY env.production.template .env.template

# Set proper file permissions
RUN chmod 644 .env.template && \
    chown app:appgroup .env.template

USER app

# Create gunicorn configuration
RUN cat > gunicorn.conf.py << 'EOF'
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "esg-copilot-api"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
tmp_upload_dir = "/app/tmp"

# SSL (if certificates are provided)
keyfile = os.getenv("SSL_KEY_FILE")
certfile = os.getenv("SSL_CERT_FILE")
ca_certs = os.getenv("SSL_CA_FILE")

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
EOF

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with graceful shutdown
CMD ["sh", "-c", "exec gunicorn -c gunicorn.conf.py main:app"]

# ============================================================================
# Final stage selection
# ============================================================================
FROM ${BUILD_TARGET:-production} as final
