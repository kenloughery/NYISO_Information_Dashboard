#!/bin/bash
# Manual cron setup script
# macOS may require manual crontab editing due to security restrictions

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
PYTHON_PATH=$(which python3)

echo "NYISO Hourly Update - Manual Cron Setup"
echo "========================================"
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"
echo ""
echo "To set up the cron job manually:"
echo ""
echo "1. Open crontab editor:"
echo "   crontab -e"
echo ""
echo "2. Add this line (runs every hour at 5 minutes past):"
echo "   5 * * * * cd \"$PROJECT_DIR\" && $PYTHON_PATH run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1"
echo ""
echo "3. Save and exit (in vim: press ESC, type :wq, press Enter)"
echo ""
echo "4. Verify it was added:"
echo "   crontab -l"
echo ""
echo "5. Test manually:"
echo "   cd \"$PROJECT_DIR\" && $PYTHON_PATH run_hourly_updates.py"
echo ""
echo "The cron job will run every hour at :05 (e.g., 1:05, 2:05, 3:05, etc.)"
echo ""

# Try to add it automatically if possible
read -p "Attempt automatic setup? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CRON_ENTRY="5 * * * * cd \"$PROJECT_DIR\" && $PYTHON_PATH run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1"
    
    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "run_hourly_updates.py"; then
        echo "Cron job already exists. Current crontab:"
        crontab -l
    else
        # Try to add
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab - 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Cron job added successfully!"
            echo ""
            echo "Current crontab:"
            crontab -l
        else
            echo "⚠️  Automatic setup failed. Please use manual steps above."
            echo "   macOS may require you to grant Terminal 'Full Disk Access' in System Preferences > Security & Privacy"
        fi
    fi
fi

