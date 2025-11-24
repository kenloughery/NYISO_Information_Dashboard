#!/bin/bash
# Setup script for hourly NYISO updates via cron
# This script helps configure a cron job for automatic hourly updates

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Find Python executable
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: python3 not found in PATH"
    exit 1
fi

echo "NYISO Hourly Update - Cron Setup"
echo "================================"
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"
echo ""

# Create the cron job entry
CRON_ENTRY="5 * * * * cd \"$PROJECT_DIR\" && $PYTHON_PATH run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1"

echo "Cron job entry that will be added:"
echo "$CRON_ENTRY"
echo ""

# Ask for confirmation
read -p "Add this cron job? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_hourly_updates.py"; then
    echo "Warning: A cron job for run_hourly_updates.py already exists."
    read -p "Replace it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing entry
        crontab -l 2>/dev/null | grep -v "run_hourly_updates.py" | crontab -
    else
        echo "Cancelled. Existing cron job not modified."
        exit 0
    fi
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo ""
echo "✓ Cron job added successfully!"
echo ""
echo "The script will run every hour at 5 minutes past the hour."
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To test manually:"
echo "  cd \"$PROJECT_DIR\" && $PYTHON_PATH run_hourly_updates.py"
echo ""
echo "To view logs:"
echo "  tail -f /tmp/nyiso_cron.log"
echo "  tail -f $PROJECT_DIR/nyiso_hourly.log"
echo ""

