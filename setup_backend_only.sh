#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
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

echo ""
echo "🚀 Setting up ESG AI Co-Pilot Backend Only..."
echo ""

# Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.10" || "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found"
    exit 1
fi

# Create backend directories
print_info "Creating backend directories..."
mkdir -p backend/uploads
mkdir -p backend/chroma_db
mkdir -p backend/logs

# Setup Python backend
print_info "Setting up Python backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r backend/requirements.txt

# Create backend environment file
print_info "Creating backend environment file..."
cat > backend/.env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db

# Security
SECRET_KEY=your-secret-key-change-this-in-production

# File Upload Configuration
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800
EOF

print_warning "Please update the OPENAI_API_KEY in backend/.env with your actual OpenAI API key"

# Create sample data
print_info "Creating sample ESG data..."
python3 -c "
import sys
import os
sys.path.append('backend')
from app.data.sample_esg_data import *
print('Sample ESG data created successfully')
"

print_success "Backend setup completed!"
echo ""
print_info "To start the backend server:"
echo "  source venv/bin/activate"
echo "  cd backend"
echo "  python main.py"
echo ""
print_info "The API will be available at: http://localhost:8000"
print_info "API documentation will be at: http://localhost:8000/docs"
echo ""
print_warning "For the frontend setup, you'll need to:"
echo "  1. Free up disk space (currently at 99% capacity)"
echo "  2. Run: cd frontend && npm install"
echo "  3. Run: npm start"
echo ""
print_success "Backend is ready to use! 🌍✨"
