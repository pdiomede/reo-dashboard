#!/bin/bash
# REO Dashboard Generator - Setup and Run Script
# Cron: every 8 hours starting at 2am UTC (2:00, 10:00, 18:00)
# 0 2,10,18 * * * /home/paolo/reo/runREO.sh >> /home/paolo/reo/logs/cron.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
NGINX_DIR="/var/www/reo/current"

cd "$SCRIPT_DIR"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install/update requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# Run the dashboard generator
echo "Running generate_dashboard.py..."
python3 generate_dashboard.py

# Ensure nginx directory exists and is owned by paolo:webapps
if [ ! -d "$NGINX_DIR" ]; then
    echo "Creating $NGINX_DIR..."
    sudo mkdir -p "$NGINX_DIR"
fi

sudo chown -R paolo:webapps /var/www/reo
sudo find /var/www/reo -type d -exec chmod 2775 {} \;

# Copy index.html to nginx directory
if [ -f "$SCRIPT_DIR/index.html" ]; then
    echo "Copying index.html to $NGINX_DIR..."
    cp "$SCRIPT_DIR/index.html" "$NGINX_DIR/index.html"

    # Copy the icon if it exists
    if [ -f "$SCRIPT_DIR/grt.png" ]; then
        cp "$SCRIPT_DIR/grt.png" "$NGINX_DIR/grt.png"
    fi

    # Copy social card if it exists
    if [ -f "$SCRIPT_DIR/images/social-card.png" ]; then
        mkdir -p "$NGINX_DIR/images"
        cp "$SCRIPT_DIR/images/social-card.png" "$NGINX_DIR/images/social-card.png"
    fi

    # Set permissions on deployed files
    chown paolo:webapps "$NGINX_DIR/index.html" 2>/dev/null || true
    chmod 644 "$NGINX_DIR/index.html"

    if [ -f "$NGINX_DIR/grt.png" ]; then
        chown paolo:webapps "$NGINX_DIR/grt.png" 2>/dev/null || true
        chmod 644 "$NGINX_DIR/grt.png"
    fi

    if [ -f "$NGINX_DIR/images/social-card.png" ]; then
        chown paolo:webapps "$NGINX_DIR/images/social-card.png" 2>/dev/null || true
        chmod 644 "$NGINX_DIR/images/social-card.png"
    fi

    echo "Dashboard deployed to $NGINX_DIR"
else
    echo "ERROR: index.html not found after running generate_dashboard.py"
    exit 1
fi

deactivate
echo "Done."