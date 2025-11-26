# Makefile for ZombieCursor Local AI

.PHONY: help install dev test lint format clean build docker run docker-stop docker-build docker-run service-install service-start service-stop service-status

# Default target
help:
	@echo "ZombieCursor Local AI - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install dependencies and setup environment"
	@echo "  dev          Start development server with hot reload"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean temporary files and caches"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run Docker container"
	@echo "  docker-stop  Stop Docker container"
	@echo ""
	@echo "Production:"
	@echo "  service-install Install as system service"
	@echo "  service-start  Start system service"
	@echo "  service-stop   Stop system service"
	@echo "  service-status Check service status"
	@echo ""
	@echo "Other:"
	@echo "  docs         Generate documentation"
	@echo "  check        Run all checks (lint + test)"

# Installation and setup
install:
	@echo "Installing ZombieCursor..."
	@chmod +x scripts/setup-dev.sh
	@./scripts/setup-dev.sh

# Development
dev:
	@echo "Starting development server..."
	@chmod +x scripts/dev.sh
	@./scripts/dev.sh

# Testing
test:
	@echo "Running tests..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh

test-cov:
	@echo "Running tests with coverage..."
	@chmod +x scripts/test.sh
	@./scripts/test.sh coverage

# Linting and formatting
lint:
	@echo "Running linting checks..."
	@chmod +x scripts/lint.sh
	@./scripts/lint.sh

format:
	@echo "Formatting code..."
	@chmod +x scripts/format.sh
	@./scripts/format.sh

# Combined checks
check: lint test
	@echo "All checks completed successfully!"

# Clean
clean:
	@echo "Cleaning temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete
	@rm -rf htmlcov/ .pytest_cache/ .mypy_cache/ dist/ build/
	@echo "Clean completed!"

# Docker commands
docker-build:
	@echo "Building Docker image..."
	@docker build -t zombiecursor:latest .

docker-run:
	@echo "Running Docker container..."
	@docker run -d --name zombiecursor -p 5051:5051 -v $(PWD)/data:/app/data -v $(PWD)/vectorstores:/app/vectorstores zombiecursor:latest

docker-stop:
	@echo "Stopping Docker container..."
	@docker stop zombiecursor || true
	@docker rm zombiecursor || true

# Docker Compose
docker-compose-up:
	@echo "Starting Docker Compose..."
	@docker-compose up -d

docker-compose-down:
	@echo "Stopping Docker Compose..."
	@docker-compose down

docker-compose-logs:
	@echo "Showing Docker Compose logs..."
	@docker-compose logs -f

# Service management (Linux only)
service-install:
	@echo "Installing system service..."
	@chmod +x scripts/install-service.sh
	@sudo ./scripts/install-service.sh

service-start:
	@echo "Starting system service..."
	@sudo systemctl start zombiecursor

service-stop:
	@echo "Stopping system service..."
	@sudo systemctl stop zombiecursor

service-status:
	@echo "Checking service status..."
	@sudo systemctl status zombiecursor

service-logs:
	@echo "Showing service logs..."
	@sudo journalctl -u zombiecursor -f

# Documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p docs/_build
	@echo "Documentation would be generated here"

# Quick start
quick-start: install
	@echo "Quick start completed!"
	@echo "Next steps:"
	@echo "1. Start your LLM server (Ollama or Llama.cpp)"
	@echo "2. Run 'make dev' to start the development server"
	@echo "3. Visit http://localhost:5051/docs"

# Production deployment
deploy: clean lint test docker-build
	@echo "Ready for deployment!"

# Development setup with all tools
setup-dev: install
	@echo "Development environment setup complete!"
	@echo "Run 'make dev' to start development server"

# CI/CD helpers
ci-test:
	@echo "Running CI tests..."
	@python -m pytest --cov=. --cov-report=xml --cov-report=term

ci-lint:
	@echo "Running CI linting..."
	@black --check .
	@isort --check-only .
	@flake8 .
	@mypy .

ci-build:
	@echo "Running CI build..."
	@python -m build

# Version management
version-patch:
	@echo "Bumping patch version..."
	@bump2version patch

version-minor:
	@echo "Bumping minor version..."
	@bump2version minor

version-major:
	@echo "Bumping major version..."
	@bump2version major

# Database operations (if applicable)
db-migrate:
	@echo "Running database migrations..."
	@alembic upgrade head

db-rollback:
	@echo "Rolling back database..."
	@alembic downgrade -1

db-reset:
	@echo "Resetting database..."
	@alembic downgrade base
	@alembic upgrade head

# Performance monitoring
benchmark:
	@echo "Running benchmarks..."
	@python -m pytest tests/benchmarks/ -v

profile:
	@echo "Running profiler..."
	@python -m cProfile -o profile.stats -m server.main

# Security checks
security-scan:
	@echo "Running security scan..."
	@bandit -r . -f json -o security-report.json

dependency-check:
	@echo "Checking dependencies for vulnerabilities..."
	@safety check --json --output safety-report.json

# Release management
release: clean lint test docker-build
	@echo "Preparing release..."
	@echo "Don't forget to:"
	@echo "1. Update version number"
	@echo "2. Update CHANGELOG.md"
	@echo "3. Create Git tag"
	@echo "4. Push to registry"