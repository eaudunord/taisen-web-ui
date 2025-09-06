#!/bin/bash

# DreamPi Link Cable Web Server - Complete Uninstaller
# Removes all traces of the installation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="/opt/dreampi-linkcable"
SERVICE_NAME="dreampi-linkcable"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DreamPi Link Cable Web Server${NC}"
echo -e "${BLUE}Complete Uninstaller${NC}"
echo -e "${BLUE}================================${NC}"
echo

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Confirm uninstall
echo -e "${YELLOW}This will completely remove the DreamPi Link Cable Web Server.${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  - Web server and all files"
echo -e "  - Auto-start service"
echo -e "  - Control scripts"
echo -e ""
echo -e "${YELLOW}Your original link_cable.py will NOT be affected.${NC}"
echo
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo

# Stop service if running
print_status "Stopping service..."
if sudo systemctl is-active --quiet ${SERVICE_NAME}.service 2>/dev/null; then
    sudo systemctl stop ${SERVICE_NAME}.service
    print_status "Service stopped"
else
    print_status "Service was not running"
fi

# Disable auto-start
print_status "Disabling auto-start..."
if sudo systemctl is-enabled --quiet ${SERVICE_NAME}.service 2>/dev/null; then
    sudo systemctl disable ${SERVICE_NAME}.service
    print_status "Auto-start disabled"
else
    print_status "Auto-start was not enabled"
fi

# Remove service file
print_status "Removing service file..."
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    sudo rm "/etc/systemd/system/${SERVICE_NAME}.service"
    print_status "Service file removed"
else
    print_status "Service file was not found"
fi

# Reload systemd
print_status "Reloading systemd configuration..."
sudo systemctl daemon-reload

# Remove installation directory
print_status "Removing installation files..."
if [ -d "$INSTALL_DIR" ]; then
    sudo rm -rf "$INSTALL_DIR"
    print_status "Installation directory removed: $INSTALL_DIR"
else
    print_status "Installation directory was not found"
fi

echo
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Uninstall Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "${GREEN}✅ Service stopped and disabled${NC}"
echo -e "${GREEN}✅ All installation files removed${NC}"
echo -e "${GREEN}✅ Auto-start configuration removed${NC}"
echo -e "${GREEN}✅ DreamPi Link Cable Web Server completely removed${NC}"
echo
echo -e "${BLUE}📋 What was NOT affected:${NC}"
echo -e "  - Your original link_cable.py script"
echo -e "  - Python packages (pyserial, requests, etc.)"
echo -e "  - DreamPi system functionality"
echo -e "  - Any other installed software"
echo
echo -e "${BLUE}📦 To reinstall:${NC}"
echo -e "  - Place link_cable.py and install-final.sh in a directory"
echo -e "  - Run: chmod +x install-final.sh && ./install-final.sh"
echo
print_status "Uninstall completed successfully!"
