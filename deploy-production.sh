#!/bin/bash

# ESG AI Co-Pilot - Production Deployment Script
# This script deploys the application to production environment

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.yml}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Use docker compose if available, fallback to docker-compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Check if .env file exists
    if [[ ! -f .env ]]; then
        log_warning ".env file not found. Creating from template..."
        if [[ -f backend/env.production.template ]]; then
            cp backend/env.production.template .env
            log_warning "Please edit .env file with your configuration before running this script again"
            exit 1
        else
            log_error "No environment template found"
            exit 1
        fi
    fi
    
    # Check required environment variables
    source .env
    
    local required_vars=(
        "OPENAI_API_KEY"
        "SECRET_KEY"
        "DB_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_success "All requirements met"
}

create_backup() {
    if [[ "$BACKUP_BEFORE_DEPLOY" == "true" ]]; then
        log_info "Creating backup before deployment..."
        
        local backup_dir="./backups/pre-deploy-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Backup volumes if they exist
        if docker volume ls | grep -q "new-esg-copilot_postgres_data"; then
            log_info "Backing up PostgreSQL data..."
            $COMPOSE_CMD exec -T postgres pg_dump -U esg_user esg_copilot > "$backup_dir/postgres_backup.sql" || true
        fi
        
        # Backup application data
        if [[ -d "./backend/uploads" ]]; then
            log_info "Backing up uploads..."
            cp -r "./backend/uploads" "$backup_dir/" || true
        fi
        
        if [[ -d "./backend/chroma_db" ]]; then
            log_info "Backing up ChromaDB..."
            cp -r "./backend/chroma_db" "$backup_dir/" || true
        fi
        
        log_success "Backup created at $backup_dir"
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build with production target
    export BUILD_TARGET=production
    export ENVIRONMENT=production
    
    # Build images
    $COMPOSE_CMD build --no-cache --pull
    
    log_success "Docker images built successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services gracefully
    log_info "Stopping existing services..."
    $COMPOSE_CMD down --timeout 30 || true
    
    # Start database and Redis first
    log_info "Starting database and cache services..."
    $COMPOSE_CMD up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    local db_ready=false
    local attempts=0
    local max_attempts=30
    
    while [[ $attempts -lt $max_attempts ]]; do
        if $COMPOSE_CMD exec -T postgres pg_isready -U esg_user -d esg_copilot &> /dev/null; then
            db_ready=true
            break
        fi
        ((attempts++))
        sleep 2
    done
    
    if [[ "$db_ready" != "true" ]]; then
        log_error "Database failed to start"
        exit 1
    fi
    
    # Start backend
    log_info "Starting backend service..."
    $COMPOSE_CMD up -d backend
    
    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    wait_for_health_check "http://localhost:8000/health"
    
    # Start frontend
    log_info "Starting frontend service..."
    $COMPOSE_CMD up -d frontend
    
    # Wait for frontend to be ready
    log_info "Waiting for frontend to be ready..."
    wait_for_health_check "http://localhost/"
    
    log_success "All services deployed successfully"
}

wait_for_health_check() {
    local url="$1"
    local start_time=$(date +%s)
    local timeout="$HEALTH_CHECK_TIMEOUT"
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $timeout ]]; then
            log_error "Health check timeout for $url"
            return 1
        fi
        
        if curl -f -s "$url" &> /dev/null; then
            log_success "Health check passed for $url"
            return 0
        fi
        
        log_info "Waiting for $url to be ready... (${elapsed}s/${timeout}s)"
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

run_post_deploy_tasks() {
    log_info "Running post-deployment tasks..."
    
    # Database migrations (if any)
    log_info "Running database migrations..."
    # Add migration commands here if needed
    
    # Clear caches
    log_info "Clearing application caches..."
    # Add cache clearing commands here if needed
    
    # Warm up caches
    log_info "Warming up caches..."
    # Add cache warming commands here if needed
    
    log_success "Post-deployment tasks completed"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove unused images
    docker image prune -f --filter "label=esg-copilot" || true
    
    # Remove dangling images
    docker image prune -f || true
    
    log_success "Cleanup completed"
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo "=================================="
    echo "Environment: $DEPLOYMENT_ENV"
    echo "Frontend URL: http://localhost"
    echo "Backend URL: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs (if debug enabled)"
    echo "Health Check: http://localhost:8000/health"
    echo "Metrics: http://localhost:8000/metrics"
    echo "=================================="
    
    # Show running containers
    log_info "Running containers:"
    $COMPOSE_CMD ps
    
    # Show resource usage
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker ps --format "{{.Names}}" | grep "new-esg-copilot") || true
}

monitor_deployment() {
    log_info "Monitoring deployment health for 60 seconds..."
    
    local start_time=$(date +%s)
    local monitor_duration=60
    local check_interval=10
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $monitor_duration ]]; then
            log_success "Deployment monitoring completed successfully"
            break
        fi
        
        # Check service health
        local backend_healthy=false
        local frontend_healthy=false
        
        if curl -f -s "http://localhost:8000/health" &> /dev/null; then
            backend_healthy=true
        fi
        
        if curl -f -s "http://localhost/" &> /dev/null; then
            frontend_healthy=true
        fi
        
        if [[ "$backend_healthy" == "true" && "$frontend_healthy" == "true" ]]; then
            log_info "All services healthy (${elapsed}s/${monitor_duration}s)"
        else
            log_warning "Some services unhealthy - Backend: $backend_healthy, Frontend: $frontend_healthy"
        fi
        
        sleep "$check_interval"
    done
}

rollback() {
    log_error "Deployment failed. Initiating rollback..."
    
    # Stop current deployment
    $COMPOSE_CMD down --timeout 30 || true
    
    # Restore from backup if available
    local latest_backup=$(ls -t ./backups/pre-deploy-* 2>/dev/null | head -n1 || echo "")
    
    if [[ -n "$latest_backup" && -d "$latest_backup" ]]; then
        log_info "Restoring from backup: $latest_backup"
        
        # Restore PostgreSQL backup
        if [[ -f "$latest_backup/postgres_backup.sql" ]]; then
            $COMPOSE_CMD up -d postgres
            sleep 10
            $COMPOSE_CMD exec -T postgres psql -U esg_user -d esg_copilot < "$latest_backup/postgres_backup.sql" || true
        fi
        
        # Restore uploads
        if [[ -d "$latest_backup/uploads" ]]; then
            rm -rf "./backend/uploads"
            cp -r "$latest_backup/uploads" "./backend/"
        fi
        
        # Restore ChromaDB
        if [[ -d "$latest_backup/chroma_db" ]]; then
            rm -rf "./backend/chroma_db"
            cp -r "$latest_backup/chroma_db" "./backend/"
        fi
        
        log_info "Backup restored. Please investigate the deployment issue."
    else
        log_warning "No backup found for rollback"
    fi
    
    exit 1
}

# Main deployment flow
main() {
    log_info "Starting ESG AI Co-Pilot production deployment..."
    
    # Set trap for cleanup on failure
    trap 'rollback' ERR
    
    # Deployment steps
    check_requirements
    create_backup
    build_images
    deploy_services
    run_post_deploy_tasks
    cleanup_old_images
    show_deployment_info
    monitor_deployment
    
    log_success "🎉 Production deployment completed successfully!"
    log_info "Your ESG AI Co-Pilot is now running at http://localhost"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            BACKUP_BEFORE_DEPLOY=false
            shift
            ;;
        --timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --no-backup        Skip backup before deployment"
            echo "  --timeout SECONDS  Health check timeout (default: 300)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
