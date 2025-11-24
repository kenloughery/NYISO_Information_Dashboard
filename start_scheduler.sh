#!/bin/bash
# Start the Python scheduler with proper environment
# This script ensures PYTHONPATH is set correctly

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Find Python
PYTHON=$(which python3)
if [ -z "$PYTHON" ]; then
    echo "Error: python3 not found"
    exit 1
fi

# Start scheduler
nohup $PYTHON scraper/scheduler.py > scheduler.log 2>&1 &

echo "Scheduler started in background"
echo "PID: $!"
echo "Log file: scheduler.log"
echo ""
echo "To check status: ps aux | grep scheduler.py"
echo "To view logs: tail -f scheduler.log"
echo "To stop: kill $(ps aux | grep scheduler.py | grep -v grep | awk '{print $2}')"

