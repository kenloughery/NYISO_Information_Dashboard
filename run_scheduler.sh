#!/bin/bash
# Run the Python scheduler in the background
# This script ensures proper Python path and runs as a module

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Find Python
PYTHON=$(which python3)
if [ -z "$PYTHON" ]; then
    echo "Error: python3 not found"
    exit 1
fi

# Check if already running
if ps aux | grep -v grep | grep -q "scraper.scheduler"; then
    echo "⚠️  Scheduler appears to be already running"
    ps aux | grep -v grep | grep "scraper.scheduler"
    echo ""
    read -p "Start another instance anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Start scheduler in background
# Use PYTHONPATH to ensure imports work correctly
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

echo "Starting scheduler in background..."
cd "$PROJECT_DIR"
nohup $PYTHON -m scraper.scheduler > scheduler.log 2>&1 &

PID=$!
echo "✅ Scheduler started!"
echo "   PID: $PID"
echo "   Log file: scheduler.log"
echo ""
echo "To check status:"
echo "   ps aux | grep scheduler"
echo ""
echo "To view logs:"
echo "   tail -f scheduler.log"
echo ""
echo "To stop:"
echo "   kill $PID"
echo "   (or: pkill -f 'scraper.scheduler')"

