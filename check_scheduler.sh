#!/bin/bash
# Check scheduler status

echo "Scheduler Status Check"
echo "====================="
echo ""

# Check for running processes
PROCESSES=$(ps aux | grep -v grep | grep "scraper.scheduler")

if [ -z "$PROCESSES" ]; then
    echo "❌ Scheduler is NOT running"
    echo ""
    echo "To start it:"
    echo "   ./run_scheduler.sh"
else
    echo "✅ Scheduler IS running:"
    echo ""
    echo "$PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        TIME=$(echo "$line" | awk '{print $10}')
        CMD=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        echo "   PID: $PID | CPU Time: $TIME"
    done
fi

echo ""
echo "Recent log entries (last 10 lines):"
echo "-----------------------------------"
if [ -f "scheduler.log" ]; then
    tail -10 scheduler.log
else
    echo "   (No log file found)"
fi

echo ""
echo "To view full logs:"
echo "   tail -f scheduler.log"

