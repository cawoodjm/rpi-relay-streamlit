#!/bin/bash

# FlexRadio Power Control - Interactive Installer
# Designed for Raspberry Pi 5 & Waveshare Relay Board

set -e # Exit on error

echo "------------------------------------------------"
echo "  FlexRadio Relay Power Control Installer"
echo "------------------------------------------------"

# 0. Change to the script's directory
cd "$(dirname "$0")"

# 1. Check/Install System Dependencies
echo "[1/7] Checking system dependencies..."
MISSING_PKGS=()

# Check for BCM2835 (often a manual install, but we check for common paths)
if [ ! -f /usr/local/lib/libbcm2835.a ] && [ ! -f /usr/lib/libbcm2835.a ]; then
    echo "  ! Warning: BCM2835 library not found in standard paths."
fi

# Check for WiringPi (gpio command)
if ! command -v gpio &> /dev/null; then
    echo "  ! Warning: WiringPi ('gpio' command) not found."
    MISSING_PKGS+=("git") # Needed to build WiringPi if they choose to
fi

# Check for python-dev-is-python3
if ! dpkg -l | grep -q "python-dev-is-python3"; then
    MISSING_PKGS+=("python-dev-is-python3")
fi

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo "  The following packages/tools are missing: ${MISSING_PKGS[*]}"
    read -p "  Would you like to attempt to install them via apt? (y/n): " install_apt
    if [[ $install_apt == "y" ]]; then
        sudo apt update
        sudo apt install -y "${MISSING_PKGS[@]}"
    fi
fi

# 2. Setup Virtual Environment
echo "[2/7] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Virtual environment created."
else
    echo "  Virtual environment already exists."
fi

echo "  Installing Python requirements..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 3. Configure .env file
echo "[3/7] Configuring Security..."
if [ ! -f .env ]; then
    read -sp "  Enter a password for web access: " AUTH_PASS
    echo ""
    echo "AUTH_PASSWORD=$AUTH_PASS" > .env
    echo "  .env file created with your password."
else
    echo "  .env file already exists. Skipping."
fi

# 4. Permissions
echo "[4/7] Setting script permissions..."
chmod +x Relay.sh

# 5. Systemd Service Setup
echo "[5/7] Configuring System Service (Production)..."
read -p "  Would you like to install the systemd service to start on boot? (y/n): " install_service
if [[ $install_service == "y" ]]; then
    CURRENT_USER=$(whoami)
    CURRENT_DIR=$(pwd)

    # Create temporary service file with correct paths
    sed -e "s|User=pi|User=$CURRENT_USER|" \
        -e "s|WorkingDirectory=/home/pi/rpi-gpio-streamlit|WorkingDirectory=$CURRENT_DIR|" \
        -e "s|/home/pi/rpi-gpio-streamlit/venv/bin/streamlit|$CURRENT_DIR/venv/bin/streamlit|" \
        relay_app.service > temp_relay_app.service

    sudo cp temp_relay_app.service /etc/systemd/system/relay_app.service
    rm temp_relay_app.service

    sudo systemctl daemon-reload
    sudo systemctl enable relay_app.service
    sudo systemctl start relay_app.service
    echo "  Service installed and started."
fi

# 6. Desktop Shortcut
echo "[6/7] Creating Desktop Shortcut..."
read -p "  Would you like to create a desktop shortcut for the app? (y/n): " create_shortcut
if [[ $create_shortcut == "y" ]]; then
    DESKTOP_DIR="/home/$(whoami)/Desktop"
    if [ -d "$DESKTOP_DIR" ]; then
        cat <<EOF > "$DESKTOP_DIR/FlexRadio_Relay.desktop"
[Desktop Entry]
Name=FlexRadio Relay
Comment=Open FlexRadio Relay Power Control
Exec=chromium-browser http://$(hostname -I | awk '{print $1}'):8501
Icon=network-wired
Terminal=false
Type=Application
Categories=Utility;
EOF
        chmod +x "$DESKTOP_DIR/FlexRadio_Relay.desktop"
        echo "  Desktop shortcut created."
    else
        echo "  Desktop directory not found. Skipping shortcut."
    fi
fi

# 7. Launch Browser
echo "[7/7] Finalizing..."
echo "------------------------------------------------"
echo "  Setup Complete!"
echo "------------------------------------------------"

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')
URL="http://$IP_ADDR:8501"

echo "  The app should now be running at: $URL"
read -p "  Would you like to open the browser now? (y/n): " open_browser
if [[ $open_browser == "y" ]]; then
    if command -v chromium-browser &> /dev/null; then
        chromium-browser "$URL" &
    else
        echo "  Could not find chromium-browser. Please open $URL manually."
    fi
fi