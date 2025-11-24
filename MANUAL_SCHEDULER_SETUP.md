# Manual Scheduler Setup Guide

**Status**: Ready for manual setup

## Quick Start

### Option 1: Run Scheduler in Background (Recommended)

```bash
./run_scheduler.sh
```

This will:
- Start the scheduler in the background
- Show you the process ID (PID)
- Create/update `scheduler.log` with all output

### Option 2: Run Scheduler in Terminal (for testing)

```bash
python3 -m scraper.scheduler
```

Press `Ctrl+C` to stop.

## Managing the Scheduler

### Check Status
```bash
./check_scheduler.sh
```

Or manually:
```bash
ps aux | grep scheduler
tail -f scheduler.log
```

### Stop the Scheduler
```bash
./stop_scheduler.sh
```

Or manually:
```bash
# Find the PID
ps aux | grep scheduler

# Kill it
kill <PID>

# Or kill all scheduler processes
pkill -f 'scraper.scheduler'
```

## Setting Up Cron Job (Hourly Updates)

Since automatic cron setup requires permissions, here's the manual process:

### Step 1: Open Crontab Editor
```bash
crontab -e
```

### Step 2: Add This Line
```
5 * * * * cd "/Users/kenloughery/Desktop/Power Markets/NYISO Product" && /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1
```

**Note**: This runs every hour at 5 minutes past the hour (1:05, 2:05, 3:05, etc.)

### Step 3: Save and Exit
- In **vim**: Press `ESC`, type `:wq`, press `Enter`
- In **nano**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Verify
```bash
crontab -l
```

### Step 5: Test Manually
```bash
python3 run_hourly_updates.py
```

## What Each Scheduler Does

### Python Scheduler (`scraper.scheduler`)
- **Runs continuously** in the background
- **Real-time sources**: Every 5 minutes (P-24A, P-58B, P-32, P-6B, P-33, P-42, etc.)
- **Hourly sources**: Every hour (P-4A, P-7, P-8)
- **Daily sources**: Once per day at 01:00 (P-2A, P-5, P-511A, etc.)
- **Multiple times daily**: Every 6 hours (P-7A)

### Cron Job (`run_hourly_updates.py`)
- **Runs once per hour** at :05 past the hour
- **Scrapes all sources** for the current day
- **Idempotent**: Skips already-scraped dates
- **Reliable**: System-level scheduling, survives reboots

## Recommended Setup

**For best coverage, use BOTH:**

1. **Start Python Scheduler** (for real-time 5-minute updates):
   ```bash
   ./run_scheduler.sh
   ```

2. **Set up Cron Job** (for reliable hourly updates):
   ```bash
   crontab -e
   # Add the cron entry (see above)
   ```

This gives you:
- Real-time data every 5 minutes (via Python scheduler)
- Reliable hourly backups (via cron)
- Redundancy if one fails

## Troubleshooting

### Scheduler Won't Start
```bash
# Check Python path
which python3

# Test imports
python3 -c "import sys; sys.path.insert(0, '.'); from scraper.scheduler import NYISOScheduler; print('OK')"

# Check log file
cat scheduler.log
```

### Cron Job Not Running
```bash
# Check if cron service is running (macOS)
sudo launchctl list | grep cron

# Check cron logs
tail -f /tmp/nyiso_cron.log

# Verify Python path in crontab matches actual path
which python3
```

### Permission Issues (macOS)
If cron setup fails, you may need to:
1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Add **Terminal** (or your terminal app) to **Full Disk Access**
3. Try setting up cron again

## Monitoring

### Check Recent Scraping Activity
```bash
python3 << 'EOF'
from database.schema import get_session, ScrapingJob
from sqlalchemy import desc
from datetime import datetime, timedelta

db = get_session()
recent = db.query(ScrapingJob).order_by(desc(ScrapingJob.started_at)).limit(10).all()
print("Recent scraping jobs:")
for j in recent:
    print(f"  {j.started_at}: {j.status} ({j.rows_inserted} rows)")
db.close()
EOF
```

### View Logs
```bash
# Scheduler log
tail -f scheduler.log

# Hourly update log
tail -f nyiso_hourly.log

# Cron log
tail -f /tmp/nyiso_cron.log
```

## Summary

✅ **Python Scheduler**: Run `./run_scheduler.sh` to start in background  
✅ **Cron Job**: Manually edit `crontab -e` to add hourly updates  
✅ **Status Check**: Run `./check_scheduler.sh` anytime  
✅ **Stop**: Run `./stop_scheduler.sh` when needed

Both schedulers are now ready for manual setup!

