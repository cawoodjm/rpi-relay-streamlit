#!/bin/bash

# FlexRadio Power Control - Remote Bootstrap
# Intended usage:
#   curl -fsSL https://raw.githubusercontent.com/cawoodjm/rpi-relay-streamlit/main/remote-install.sh | bash
#
# Clones (or updates) the project repo, then hands off to the project's
# own interactive install.sh.

set -e

REPO_URL="https://github.com/cawoodjm/rpi-relay-streamlit.git"
INSTALL_DIR="${INSTALL_DIR:-$HOME/rpi-relay-streamlit}"

echo "------------------------------------------------"
echo "  FlexRadio Relay - Remote Bootstrap"
echo "------------------------------------------------"

if ! command -v git &> /dev/null; then
    echo "Error: git is required but not installed."
    echo "Install it first with: sudo apt update && sudo apt install -y git"
    exit 1
fi

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Existing installation found at $INSTALL_DIR, pulling latest changes..."
    git -C "$INSTALL_DIR" pull
else
    echo "Cloning repository into $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
chmod +x install.sh

echo "Handing off to install.sh..."
echo "------------------------------------------------"

# Re-attach stdin to the controlling terminal: when this script itself was
# piped in via `curl | bash`, fd 0 is the (now-exhausted) pipe, not the
# user's keyboard, so install.sh's interactive `read` prompts need to read
# from /dev/tty directly instead.
exec ./install.sh < /dev/tty
