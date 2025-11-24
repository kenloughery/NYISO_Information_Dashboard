#!/bin/bash
# Health check script for services
# Run via cron: */5 * * * * /opt/nyiso-dashboard/health-check.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$SCRIPT_DIR/logs/health-check.log"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Function to log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 Starting health check..."

# Check API service
if systemctl is-active --quiet nyiso-api 2>/dev/null; then
    # Check API endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ API: OK"
    else
        log "❌ API: Health endpoint failed, restarting..."
        sudo systemctl restart nyiso-api
    fi
else
    log "❌ API: Service not running, starting..."
    sudo systemctl start nyiso-api
fi

# Check scraper service
if systemctl is-active --quiet nyiso-scraper 2>/dev/null; then
    log "✅ Scraper: OK"
else
    log "❌ Scraper: Service not running, starting..."
    sudo systemctl start nyiso-scraper
fi

# Check disk space
DISK_USAGE=$(df -h "$SCRIPT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log "⚠️  Disk usage: ${DISK_USAGE}% (warning threshold: 80%)"
fi

# Check database file
if [ -f "$SCRIPT_DIR/nyiso_data.db" ]; then
    DB_SIZE=$(du -h "$SCRIPT_DIR/nyiso_data.db" | cut -f1)
    log "📊 Database size: $DB_SIZE"
else
    log "⚠️  Database file not found"
fi

log "✅ Health check complete"

