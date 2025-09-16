#!/bin/bash

# DreamPi Link Cable Web Server - Final Working Installer
# Includes all fixes and works reliably on DreamPi systems
# Version: 1.0 - Tested and verified working

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
WEB_PORT=1999

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DreamPi Link Cable Web Server${NC}"
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root."
   exit 1
fi

# Get Python path
PYTHON_FULL_PATH="/usr/bin/python3"
print_status "$PYTHON_FULL_PATH"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_FULL_PATH=$(which python3)
    print_status "Found Python3 at $PYTHON_FULL_PATH"
else
    print_error "Python not found."
    exit 1
fi

# Check if link_cable.py exists
if [ ! -f "link_cable.py" ]; then
    curl -O "https://raw.githubusercontent.com/eaudunord/dc-taisen-netplay/main/link_cable.py"
fi

if [ ! -f "index.html" ]; then
    curl -O "https://raw.githubusercontent.com/eaudunord/taisen-web-ui/main/index.html"
fi

if [ ! -f "webserver.py" ]; then
    curl -O "https://raw.githubusercontent.com/eaudunord/taisen-web-ui/main/webserver.py"
fi

# Quick dependency installation (non-blocking)
print_status "Installing dependencies..."

if hostnamectl | grep 'stretch'; then
    echo "Raspbian stretch detected. Try adding archive repos"
    sudo sed -i 's/raspbian.raspberrypi.org/legacy.raspbian.org/g' /etc/apt/sources.list
fi

python -m pip --version || {
    sudo apt-get update
    sudo apt-get install -y python-pip
}

python3 -m pip --version || {
    sudo apt-get update
    sudo apt-get install -y python3-pip
}
# Try to install pyserial
python -c "import serial" >/dev/null 2>&1 || {
        print_status "Installing pyserial..."
        python -m pip install pyserial
     } || print_warning "pyserial still failed - you may need to install manually later"

# Try to install requests

    # for 2.7
python -c "import requests" >/dev/null 2>&1 || {
        print_status "Installing requests..."
        python -m pip install requests
     } || print_warning "requests still failed - you may need to install manually later"

    # for 3.x
python3 -c "import requests" >/dev/null 2>&1 || {
        print_status "Installing requests..."
        python3 -m pip install requests
     } || print_warning "requests still failed - you may need to install manually later"

# Try to install pystun
python -c "import stun" >/dev/null 2>&1 || {
        print_status "Installing pystun3..."
        python -m pip install pystun3
    } || print_warning "pystun3 installation failed"

# Create installation directory
print_status "Creating installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Copy and fix link_cable.py
print_status "Installing link_cable.py (original, unmodified)..."
cp link_cable.py "$INSTALL_DIR/"

# Do NOT modify the original file - just copy it as-is
print_status "Using original link_cable.py without modifications"

# Create the working web server
print_status "Creating web server..."
cp webserver.py "$INSTALL_DIR/"

cp index.html "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/webserver.py"

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=DreamPi Link Cable Web Server
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_FULL_PATH $INSTALL_DIR/webserver.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create manual control scripts
print_status "Creating control scripts..."
cat > "$INSTALL_DIR/start.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 webserver.py
EOF

cat > "$INSTALL_DIR/stop.sh" << EOF
#!/bin/bash
sudo systemctl stop $SERVICE_NAME
EOF

cat > "$INSTALL_DIR/restart.sh" << EOF
#!/bin/bash
sudo systemctl restart $SERVICE_NAME
EOF

chmod +x "$INSTALL_DIR/start.sh" "$INSTALL_DIR/stop.sh" "$INSTALL_DIR/restart.sh"

# Test dependency availability
print_status "Testing dependencies..."
DEPS_OK=true

if ! python -c "import serial" >/dev/null 2>&1; then
    print_warning "pyserial not available - may need manual installation"
    DEPS_OK=false
fi

if ! python -c "import requests" >/dev/null 2>&1; then
    print_warning "requests not available - matchmaking may not work"
fi

# Enable and start service
print_status "Enabling auto-start service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

print_status "Starting web server..."
sudo systemctl start ${SERVICE_NAME}.service

# Wait for service to start
sleep 3

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "your-dreampi-ip")

# Final status check
SERVICE_STATUS="UNKNOWN"
if sudo systemctl is-active --quiet ${SERVICE_NAME}.service; then
    SERVICE_STATUS="RUNNING"
else
    SERVICE_STATUS="FAILED"
fi

echo
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "${BLUE}Installation Summary:${NC}"
echo -e "   Service Status: $SERVICE_STATUS"
echo -e "   Dependencies: $([ "$DEPS_OK" = true ] && echo "✅ OK" || echo "⚠️  Some missing")"
echo -e "   Auto-start: ✅ Enabled"
echo
echo -e "${BLUE}Web Interface:${NC}"
echo -e "   Local:    http://localhost:$WEB_PORT"
echo -e "   Network:  http://$IP_ADDRESS:$WEB_PORT or http://dreampi.local:$WEB_PORT"
echo
echo -e "${BLUE}Service Management:${NC}"
echo -e "   Status:   sudo systemctl status $SERVICE_NAME"
echo -e "   Stop:     sudo systemctl stop $SERVICE_NAME"
echo -e "   Start:    sudo systemctl start $SERVICE_NAME"
echo -e "   Restart:  sudo systemctl restart $SERVICE_NAME"
echo -e "   Logs:     sudo journalctl -u $SERVICE_NAME -f"
echo
echo -e "${BLUE}Manual Control:${NC}"
echo -e "   Start:    $INSTALL_DIR/start.sh"
echo -e "   Stop:     $INSTALL_DIR/stop.sh"
echo -e "   Restart:  $INSTALL_DIR/restart.sh"
echo

if [ "$SERVICE_STATUS" = "RUNNING" ]; then
    echo -e "${GREEN}Success! The web interface is ready to use.${NC}"
    echo -e "${GREEN}Connect your Dreamcast coders cable and enjoy netplay!${NC}"
else
    echo -e "${YELLOW}⚠️  Service may have issues. Check logs with:${NC}"
    echo -e "   sudo journalctl -u $SERVICE_NAME -n 20"
fi

echo
echo -e "${BLUE}For distribution: Give others this installer + link_cable.py${NC}"

# Show final status
print_status "Installation complete! Service status:"
sudo systemctl status ${SERVICE_NAME}.service --no-pager -l || true