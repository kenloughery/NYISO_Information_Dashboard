# Scheduler Setup - Complete ✅

**Date**: 2025-11-14  
**Status**: ✅ **BOTH SCHEDULERS CONFIGURED**

## Setup Summary

### ✅ Option 1: Cron Job (Hourly Updates)
**Status**: Configured and active

**Configuration:**
- **Schedule**: Every hour at 5 minutes past the hour (`5 * * * *`)
- **Script**: `run_hourly_updates.py`
- **Log File**: `/tmp/nyiso_cron.log`
- **Project Log**: `nyiso_hourly.log`

**What it does:**
- Runs every hour
- Scrapes all data sources for the current day
- Skips already-scraped dates (idempotent)
- Updates all sources based on their update frequencies

**To verify:**
```bash
crontab -l
tail -f /tmp/nyiso_cron.log
tail -f nyiso_hourly.log
```

### ✅ Option 2: Python Scheduler (Real-Time Updates)
**Status**: Running in background

**Configuration:**
- **Process**: `scraper/scheduler.py`
- **Log File**: `scheduler.log`
- **Update Frequencies**:
  - Real-time sources: Every 5 minutes
  - Hourly sources: Every hour
  - Daily sources: Once per day at 01:00
  - Multiple times daily: Every 6 hours

**What it does:**
- Runs continuously
- Schedules jobs based on update frequencies from `URL_Lookup.txt`
- Handles different update frequencies automatically
- More granular control for real-time sources

**To verify:**
```bash
ps aux | grep scheduler.py
tail -f scheduler.log
```

## Update Frequencies by Source

### Real-Time (Every 5 minutes) - Handled by Python Scheduler
- P-24A: Real-Time Zonal LBMP
- P-58B: Real-Time Actual Load
- P-32: Interface Limits & Flows
- P-6B: Real-Time Ancillary Services
- P-33: Real-Time Limiting Constraints
- P-42: RTC vs External RTO CTS Prices
- P-31: Balancing Market Advisory Summary
- P-54A: Real-Time Scheduled Outages
- P-54B: Real-Time Actual Outages

### Hourly - Handled by Both
- P-4A: Time-Weighted RT LBMP
- P-7: ISO Load Forecast
- P-8: Available Transfer Capability / Total Transfer Capability

### Daily - Handled by Both
- P-2A: Day-Ahead Zonal LBMP
- P-5: Day-Ahead Ancillary Services
- P-511A: Day-Ahead Limiting Constraints
- P-8A: Long Term ATC/TTC
- P-54C: Day-Ahead Scheduled Outages
- P-14B: Outage Schedules CSV
- P-15: Generation Maintenance Report
- P-7A: Weather Forecast
- P-63: Real-Time Fuel Mix

## Monitoring

### Check Cron Job Status
```bash
# View cron job
crontab -l

# View cron logs
tail -f /tmp/nyiso_cron.log
tail -f nyiso_hourly.log

# Test manually
python3 run_hourly_updates.py
```

### Check Python Scheduler Status
```bash
# Check if running
ps aux | grep scheduler.py

# View scheduler logs
tail -f scheduler.log

# Check recent scraping jobs
python3 -c "
from database.schema import get_session, ScrapingJob
from sqlalchemy import desc
from datetime import datetime, timedelta

db = get_session()
recent = db.query(ScrapingJob).order_by(desc(ScrapingJob.started_at)).limit(10).all()
for j in recent:
    print(f'{j.started_at}: {j.status}')
db.close()
"
```

## Troubleshooting

### Cron Job Not Running
1. Check cron service: `sudo service cron status` (Linux) or check System Preferences (macOS)
2. Check logs: `tail -f /tmp/nyiso_cron.log`
3. Verify Python path in crontab matches actual path: `which python3`
4. Test script manually: `python3 run_hourly_updates.py`

### Scheduler Not Running
1. Check process: `ps aux | grep scheduler.py`
2. Check logs: `tail -f scheduler.log`
3. Restart: `nohup python3 scraper/scheduler.py > scheduler.log 2>&1 &`

### Both Running
- This is fine! They complement each other:
  - Cron: Reliable hourly updates for all sources
  - Scheduler: Real-time updates every 5 minutes for fast-changing data

## Next Steps

1. **Monitor for 24 hours** to ensure both are working correctly
2. **Check logs** regularly to catch any issues
3. **Verify data freshness** by checking recent timestamps in database

## Status

✅ **Cron Job**: Configured  
✅ **Python Scheduler**: Running  
✅ **Both Systems**: Active and monitoring

The backend will now automatically update data on schedule!

