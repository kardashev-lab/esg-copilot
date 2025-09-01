#!/bin/bash

# ESG AI Co-Pilot Deployment Script
# This script provides multiple deployment options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        cp backend/env.production.example .env
        print_warning "Please edit .env file with your configuration before continuing."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to deploy with Docker
deploy_docker() {
    print_status "Deploying with Docker Compose..."
    
    # Fix Docker credentials issue on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "Detected macOS, checking Docker credentials..."
        if ! docker info > /dev/null 2>&1; then
            print_warning "Docker credentials issue detected. Trying to fix..."
            # Try to reset Docker credentials
            rm -f ~/.docker/config.json
            print_status "Please restart Docker Desktop and try again."
            exit 1
        fi
    fi
    
    # Check if .env file has required variables
    if ! grep -q "OPENAI_API_KEY" .env; then
        print_warning "OPENAI_API_KEY not found in .env file"
        print_status "Please add your OpenAI API key to the .env file"
        exit 1
    fi
    
    # Try to pull images first to handle credentials issue
    print_status "Pulling base images..."
    docker pull postgres:13 || print_warning "Could not pull postgres image, will build locally"
    docker pull redis:6-alpine || print_warning "Could not pull redis image, will build locally"
    
    # Build and start services
    print_status "Building and starting services..."
    COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Docker deployment completed!"
        print_status "Services are starting up..."
        print_status "Frontend: http://localhost"
        print_status "Backend API: http://localhost:8000"
        print_status "Health Check: http://localhost:8000/health"
        
        # Wait a moment for services to start
        sleep 5
        
        # Show logs
        print_status "Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
    else
        print_error "Docker deployment failed!"
        print_status "Check the logs above for errors"
        exit 1
    fi
}

# Function to deploy with Docker (simple version)
deploy_docker_simple() {
    print_status "Deploying with Docker Compose (simple version - no external databases)..."
    
    # Check if .env file has required variables
    if ! grep -q "OPENAI_API_KEY" .env; then
        print_warning "OPENAI_API_KEY not found in .env file"
        print_status "Please add your OpenAI API key to the .env file"
        exit 1
    fi
    
    # Build and start services using simple compose file
    print_status "Building and starting services..."
    COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose -f docker-compose.simple.yml up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Docker deployment completed!"
        print_status "Services are starting up..."
        print_status "Frontend: http://localhost"
        print_status "Backend API: http://localhost:8000"
        print_status "Health Check: http://localhost:8000/health"
        
        # Wait a moment for services to start
        sleep 5
        
        # Show logs
        print_status "Showing logs (Ctrl+C to exit)..."
        docker-compose -f docker-compose.simple.yml logs -f
    else
        print_error "Docker deployment failed!"
        print_status "Check the logs above for errors"
        exit 1
    fi
}

# Function to deploy locally
deploy_local() {
    print_status "Deploying locally..."
    
    # Backend
    print_status "Starting backend..."
    cd backend
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Start backend in background
    python main.py &
    BACKEND_PID=$!
    cd ..
    
    # Frontend
    print_status "Starting frontend..."
    cd frontend
    npm install
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Local deployment completed!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend API: http://localhost:8000"
    print_status "Press Ctrl+C to stop services"
    
    # Wait for user to stop
    wait
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    if command -v docker-compose &> /dev/null; then
        # Try to stop both compose files
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
        print_success "Docker services stopped"
    else
        print_warning "Docker Compose not found"
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    
    if command -v docker-compose &> /dev/null; then
        # Check both compose files
        echo "Full deployment (docker-compose.yml):"
        docker-compose ps 2>/dev/null || echo "  No services running"
        echo ""
        echo "Simple deployment (docker-compose.simple.yml):"
        docker-compose -f docker-compose.simple.yml ps 2>/dev/null || echo "  No services running"
    else
        print_warning "Docker Compose not found"
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing logs..."
    
    if command -v docker-compose &> /dev/null; then
        # Try to show logs from both compose files
        if docker-compose ps | grep -q "Up"; then
            docker-compose logs -f
        elif docker-compose -f docker-compose.simple.yml ps | grep -q "Up"; then
            docker-compose -f docker-compose.simple.yml logs -f
        else
            print_warning "No running services found"
        fi
    else
        print_warning "Docker Compose not found"
    fi
}

# Function to backup data
backup_data() {
    print_status "Creating backup..."
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup uploads
    if [ -d "backend/uploads" ]; then
        cp -r backend/uploads "$BACKUP_DIR/"
    fi
    
    # Backup ChromaDB
    if [ -d "backend/chroma_db" ]; then
        cp -r backend/chroma_db "$BACKUP_DIR/"
    fi
    
    # Backup environment
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/"
    fi
    
    print_success "Backup created in $BACKUP_DIR"
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please specify backup directory"
        echo "Usage: $0 restore <backup_directory>"
        exit 1
    fi
    
    BACKUP_DIR="$1"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    print_status "Restoring from backup: $BACKUP_DIR"
    
    # Restore uploads
    if [ -d "$BACKUP_DIR/uploads" ]; then
        cp -r "$BACKUP_DIR/uploads" backend/
    fi
    
    # Restore ChromaDB
    if [ -d "$BACKUP_DIR/chroma_db" ]; then
        cp -r "$BACKUP_DIR/chroma_db" backend/
    fi
    
    # Restore environment
    if [ -f "$BACKUP_DIR/.env" ]; then
        cp "$BACKUP_DIR/.env" .
    fi
    
    print_success "Restore completed"
}

# Function to show help
show_help() {
    echo "ESG AI Co-Pilot Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  docker     Deploy using Docker Compose (recommended)"
    echo "  simple     Deploy using Docker Compose (simple - no external databases)"
    echo "  local      Deploy locally (development)"
    echo "  stop       Stop all services"
    echo "  status     Show service status"
    echo "  logs       Show service logs"
    echo "  backup     Create backup of data"
    echo "  restore    Restore from backup"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker          # Deploy with Docker (full version)"
    echo "  $0 simple          # Deploy with Docker (simple version)"
    echo "  $0 local           # Deploy locally"
    echo "  $0 backup          # Create backup"
    echo "  $0 restore backup_20240101_120000  # Restore from backup"
    echo ""
    echo "Note: Use 'simple' if you encounter Docker credential issues on macOS"
}

# Main script logic
case "${1:-help}" in
    docker)
        check_prerequisites
        deploy_docker
        ;;
    simple)
        check_prerequisites
        deploy_docker_simple
        ;;
    local)
        deploy_local
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
