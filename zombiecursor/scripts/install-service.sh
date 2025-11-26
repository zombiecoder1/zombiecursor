#!/bin/bash

# ZombieCursor Local AI - Service Installation Script

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Get current user
CURRENT_USER=${SUDO_USER:-$USER}

print_status "Installing ZombieCursor as a system service..."
print_status "Project directory: $PROJECT_DIR"
print_status "Service user: $CURRENT_USER"

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/zombiecursor.service"

print_status "Creating systemd service file..."

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=ZombieCursor Local AI
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=DEBUG=false
Environment=LOG_LEVEL=INFO
ExecStart=$PROJECT_DIR/venv/bin/python -m server.main
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=zombiecursor

[Install]
WantedBy=multi-user.target
EOF

print_success "Service file created: $SERVICE_FILE"

# Create environment file for service
ENV_FILE="/etc/zombiecursor.env"

print_status "Creating environment file..."

if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$ENV_FILE"
    print_success "Environment file created from existing .env"
else
    cat > "$ENV_FILE" << EOF
# ZombieCursor Service Configuration
HOST=0.0.0.0
PORT=5051
DEBUG=false
LOG_LEVEL=INFO
PROJECT_ROOT=$PROJECT_DIR
EOF
    print_success "Default environment file created"
fi

# Set proper permissions
chown "$CURRENT_USER:$CURRENT_USER" "$ENV_FILE"
chmod 600 "$ENV_FILE"

print_success "Environment file created: $ENV_FILE"

# Reload systemd
print_status "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service
print_status "Enabling ZombieCursor service..."
systemctl enable zombiecursor

print_success "ZombieCursor service has been installed and enabled!"

# Instructions
echo ""
print_status "Service Management Commands:"
echo "  Start service:     sudo systemctl start zombiecursor"
echo "  Stop service:      sudo systemctl stop zombiecursor"
echo "  Restart service:   sudo systemctl restart zombiecursor"
echo "  Check status:      sudo systemctl status zombiecursor"
echo "  View logs:         sudo journalctl -u zombiecursor -f"
echo "  Enable on boot:    sudo systemctl enable zombiecursor"
echo "  Disable on boot:   sudo systemctl disable zombiecursor"
echo ""

print_status "To start the service now, run:"
echo "  sudo systemctl start zombiecursor"

print_status "To check the service status, run:"
echo "  sudo systemctl status zombiecursor"

print_warning "Make sure your LLM server (Ollama/Llama.cpp) is running before starting ZombieCursor"