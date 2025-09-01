#!/bin/bash

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

# Check if Python 3.8+ is installed
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 1 ]]; then
    print_success "Python $python_version found"
else
    print_error "Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

# Check if Node.js is installed
print_status "Checking Node.js..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    print_success "Node.js $node_version found"
else
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if npm is installed
print_status "Checking npm..."
if command -v npm &> /dev/null; then
    npm_version=$(npm --version)
    print_success "npm $npm_version found"
else
    print_error "npm is not installed. Please install npm."
    exit 1
fi

# Create project directories
print_status "Creating project directories..."
mkdir -p backend/uploads
mkdir -p backend/logs
mkdir -p backend/chroma_db

# Setup Backend
print_status "Setting up Python backend..."
cd backend

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file for backend
print_status "Creating backend environment file..."
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
CHROMA_DB_PATH=./chroma_db

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO
EOF

print_warning "Please update the OPENAI_API_KEY in backend/.env with your actual OpenAI API key"

cd ..

# Setup Frontend
print_status "Setting up React frontend..."
cd frontend

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install

# Create .env file for frontend
print_status "Creating frontend environment file..."
cat > .env << EOF
# API Configuration
REACT_APP_API_URL=http://localhost:8000

# Application Configuration
REACT_APP_NAME=Reggie - AI Regulations Co-Pilot
REACT_APP_VERSION=1.0.0
EOF

cd ..

print_success "Setup completed successfully!"
print_status "Next steps:"
echo "1. Update OPENAI_API_KEY in backend/.env"
echo "2. Start the backend: ./start_backend.sh"
echo "3. Start the frontend: ./start_frontend.sh"
echo "4. Access the application at http://localhost:3000"
