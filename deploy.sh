#!/bin/bash
# Deployment script for production VPS
# Usage: ./deploy.sh

set -e

echo "🚀 Starting deployment..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "📥 Pulling latest code..."
    git pull origin main || echo "⚠️  Git pull failed, continuing..."
fi

# Install/update Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Build frontend
if [ -d "frontend" ]; then
    echo "🏗️  Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
fi

# Create logs directory
mkdir -p logs

# Restart services (if systemd services are set up)
if systemctl is-active --quiet nyiso-api 2>/dev/null; then
    echo "🔄 Restarting API service..."
    sudo systemctl restart nyiso-api
fi

if systemctl is-active --quiet nyiso-scraper 2>/dev/null; then
    echo "🔄 Restarting scraper service..."
    sudo systemctl restart nyiso-scraper
fi

# Reload Nginx (if installed)
if command -v nginx &> /dev/null; then
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx || echo "⚠️  Nginx reload failed"
fi

echo "✅ Deployment complete!"

