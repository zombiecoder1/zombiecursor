#!/bin/bash

# ZombieCursor Local AI - Development Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_status "Setting up ZombieCursor development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

print_success "Python version check passed: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt
print_success "Dependencies installed"

# Install development dependencies
print_status "Installing development dependencies..."
pip install pytest pytest-asyncio pytest-cov black flake8 mypy isort pre-commit
print_success "Development dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    
    # Set development-specific values
    sed -i 's/DEBUG=false/DEBUG=true/' .env
    sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' .env
    
    print_success "Development .env file created"
else
    print_status ".env file already exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs vectorstores/data tests/{unit,integration} docs
print_success "Directories created"

# Set up pre-commit hooks
print_status "Setting up pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    print_success "Pre-commit hooks installed"
else
    print_warning "No .pre-commit-config.yaml found"
fi

# Create development configuration
print_status "Creating development configuration..."

cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["core", "server", "agents", "tools", "vectorstores"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--cov=.",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
EOF

print_success "Development configuration created"

# Create pre-commit configuration
print_status "Creating pre-commit configuration..."

cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

print_success "Pre-commit configuration created"

# Create development scripts
print_status "Creating development scripts..."

cat > scripts/dev.sh << 'EOF'
#!/bin/bash
# Development server with hot reload

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source venv/bin/activate
export DEBUG=true
export LOG_LEVEL=DEBUG

uvicorn server.main:app --host 0.0.0.0 --port 5051 --reload --log-level debug
EOF

cat > scripts/test.sh << 'EOF'
#!/bin/bash
# Run tests

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source venv/bin/activate

if [ "$1" = "coverage" ]; then
    pytest --cov=. --cov-report=html --cov-report=term
else
    pytest -v
fi
EOF

cat > scripts/lint.sh << 'EOF'
#!/bin/bash
# Run linting and formatting

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source venv/bin/activate

echo "Running black..."
black --check .

echo "Running isort..."
isort --check-only .

echo "Running flake8..."
flake8 .

echo "Running mypy..."
mypy .

echo "All checks passed!"
EOF

cat > scripts/format.sh << 'EOF'
#!/bin/bash
# Format code

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source venv/bin/activate

echo "Running black..."
black .

echo "Running isort..."
isort .

echo "Code formatted successfully!"
EOF

# Make scripts executable
chmod +x scripts/dev.sh scripts/test.sh scripts/lint.sh scripts/format.sh

print_success "Development scripts created"

# Create initial test structure
print_status "Creating test structure..."

cat > tests/__init__.py << 'EOF'
"""Test package for ZombieCursor."""
EOF

cat > tests/conftest.py << 'EOF'
"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create some test files
    (project_dir / "main.py").write_text("""
def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""")
    
    (project_dir / "README.md").write_text("# Test Project\n\nThis is a test project.")
    
    return project_dir
EOF

cat > tests/test_core/test_config.py << 'EOF'
"""Test configuration management."""

import pytest
from core.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings()
    
    assert settings.host == "0.0.0.0"
    assert settings.port == 5051
    assert settings.debug is False
    assert settings.llm_host == "http://localhost:8007"
    assert settings.llm_model == "llama2"


def test_settings_from_env():
    """Test that settings can be loaded from environment variables."""
    import os
    
    # Set environment variables
    os.environ["HOST"] = "127.0.0.1"
    os.environ["PORT"] = "8080"
    os.environ["DEBUG"] = "true"
    
    try:
        settings = Settings()
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        assert settings.debug is True
    finally:
        # Clean up
        os.environ.pop("HOST", None)
        os.environ.pop("PORT", None)
        os.environ.pop("DEBUG", None)
EOF

print_success "Test structure created"

# Final instructions
echo ""
print_success "Development environment setup complete!"
echo ""
print_status "Development commands:"
echo "  Start dev server:    ./scripts/dev.sh"
echo "  Run tests:           ./scripts/test.sh"
echo "  Run tests with coverage: ./scripts/test.sh coverage"
echo "  Run linting:         ./scripts/lint.sh"
echo "  Format code:         ./scripts/format.sh"
echo ""
print_status "Next steps:"
echo "1. Start your LLM server (Ollama or Llama.cpp)"
echo "2. Run ./scripts/dev.sh to start the development server"
echo "3. Visit http://localhost:5051/docs to see the API documentation"
echo ""
print_warning "Don't forget to:"
echo "- Edit .env file with your configuration"
echo "- Start your LLM server before running ZombieCursor"
echo "- Run tests to ensure everything works correctly"