#!/bin/bash
# Stop the running scheduler

echo "Stopping scheduler..."

# Find and kill scheduler processes
PIDS=$(ps aux | grep -v grep | grep "scraper.scheduler" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "⚠️  No scheduler process found"
    exit 0
fi

for PID in $PIDS; do
    echo "Stopping process $PID..."
    kill $PID 2>/dev/null
done

# Wait a moment and check
sleep 2

# Force kill if still running
REMAINING=$(ps aux | grep -v grep | grep "scraper.scheduler" | awk '{print $2}')
if [ ! -z "$REMAINING" ]; then
    echo "Force killing remaining processes..."
    for PID in $REMAINING; do
        kill -9 $PID 2>/dev/null
    done
fi

# Verify
if ps aux | grep -v grep | grep -q "scraper.scheduler"; then
    echo "⚠️  Some processes may still be running"
else
    echo "✅ Scheduler stopped"
fi

