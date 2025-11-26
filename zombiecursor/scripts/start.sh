#!/bin/bash

# ZombieCursor Local AI - Linux/macOS Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

print_status "Starting ZombieCursor Local AI..."
print_status "Project directory: $PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
else
    print_error "Virtual environment activation script not found"
    exit 1
fi

# Check if dependencies are installed
if [ ! -f "venv/pyvenv.cfg" ] || ! python -c "import fastapi" 2>/dev/null; then
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration"
fi

# Check if LLM is running
check_llm() {
    local ollama_url="http://localhost:11434"
    local llama_url="http://localhost:8007"
    
    if curl -s "$ollama_url/api/tags" >/dev/null 2>&1; then
        print_success "Ollama is running on $ollama_url"
        return 0
    elif curl -s "$llama_url/health" >/dev/null 2>&1; then
        print_success "Llama.cpp is running on $llama_url"
        return 0
    else
        print_warning "No LLM server detected. Please start Ollama or Llama.cpp"
        print_status "To start Ollama: ollama serve"
        print_status "To start Llama.cpp: ./main -m model.gguf --host 0.0.0.0 --port 8007"
        return 1
    fi
}

# Check LLM status
check_llm

# Create necessary directories
mkdir -p logs vectorstores/data

# Start the server
print_status "Starting ZombieCursor server..."
print_status "Server will be available at: http://localhost:5051"
print_status "API Documentation: http://localhost:5051/docs"
print_status "Health Check: http://localhost:5051/health"

# Set environment variables for production
if [ "$1" = "production" ]; then
    export DEBUG=false
    export LOG_LEVEL=INFO
    print_status "Running in production mode"
else
    export DEBUG=true
    export LOG_LEVEL=DEBUG
    print_status "Running in development mode"
fi

# Start the server
if command -v uvicorn >/dev/null 2>&1; then
    uvicorn server.main:app --host 0.0.0.0 --port 5051 --reload
else
    python -m server.main
fi