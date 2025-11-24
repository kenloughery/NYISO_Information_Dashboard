#!/bin/bash
# VPS Deployment Script for NYISO Dashboard
# Run this script on your VPS server after initial setup

set -e

echo "=========================================="
echo "NYISO Dashboard - VPS Deployment"
echo "=========================================="

# Configuration
APP_DIR="/opt/nyiso-dashboard"
VENV_DIR="$APP_DIR/venv"
REPO_URL="${REPO_URL:-https://github.com/your-username/nyiso-product.git}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3.11 python3-pip python3-venv nodejs npm nginx git certbot python3-certbot-nginx

echo -e "${GREEN}Step 2: Creating application directory...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or update repository
if [ -d ".git" ]; then
    echo -e "${YELLOW}Repository exists, pulling latest changes...${NC}"
    git pull
else
    echo -e "${GREEN}Cloning repository...${NC}"
    git clone $REPO_URL .
fi

echo -e "${GREEN}Step 3: Setting up Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3.11 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Step 4: Building frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

echo -e "${GREEN}Step 5: Setting up systemd services...${NC}"
# Copy systemd service files
cp deployment/vps/nyiso-api.service /etc/systemd/system/
cp deployment/vps/nyiso-scraper.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable nyiso-api
systemctl enable nyiso-scraper

echo -e "${GREEN}Step 6: Setting up Nginx...${NC}"
# Copy nginx configuration
cp deployment/vps/nginx.conf /etc/nginx/sites-available/nyiso-dashboard

# Create symlink
ln -sf /etc/nginx/sites-available/nyiso-dashboard /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

echo -e "${GREEN}Step 7: Setting permissions...${NC}"
# Create logs directory
mkdir -p $APP_DIR/logs
chown -R www-data:www-data $APP_DIR
chmod +x $APP_DIR/deployment/vps/*.sh

echo -e "${GREEN}Step 8: Starting services...${NC}"
systemctl restart nyiso-api
systemctl restart nyiso-scraper
systemctl reload nginx

echo -e "${GREEN}Step 9: Checking service status...${NC}"
systemctl status nyiso-api --no-pager
systemctl status nyiso-scraper --no-pager

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Set up SSL certificate:"
echo "   certbot --nginx -d your-domain.com"
echo ""
echo "2. Check service logs:"
echo "   journalctl -u nyiso-api -f"
echo "   journalctl -u nyiso-scraper -f"
echo ""
echo "3. Test API:"
echo "   curl http://localhost:8000/health"
echo ""


