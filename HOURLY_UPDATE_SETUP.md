# Hourly Update Setup Guide

This guide explains how to set up automatic hourly updates for the NYISO database.

## Option 1: Cron Job (Recommended for macOS/Linux)

Cron is the most reliable method for scheduled tasks on Unix-like systems.

### Setup Steps

1. **Make the script executable:**
```bash
chmod +x run_hourly_updates.py
```

2. **Find your Python path:**
```bash
which python3
# Example output: /usr/bin/python3 or /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
```

3. **Open crontab editor:**
```bash
crontab -e
```

4. **Add this line to run every hour at minute 0:**
```cron
0 * * * * cd "/Users/kenloughery/Desktop/Power Markets/NYISO Product" && /usr/bin/python3 run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1
```

**Or run at minute 5 past every hour (to avoid peak times):**
```cron
5 * * * * cd "/Users/kenloughery/Desktop/Power Markets/NYISO Product" && /usr/bin/python3 run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1
```

**Replace `/usr/bin/python3` with your actual Python path from step 2.**

5. **Verify cron job is set:**
```bash
crontab -l
```

6. **Test the cron job manually:**
```bash
# Run the script directly to test
python3 run_hourly_updates.py
```

### Cron Schedule Examples

- `0 * * * *` - Every hour at minute 0
- `5 * * * *` - Every hour at minute 5
- `0 */2 * * *` - Every 2 hours
- `0 9-17 * * *` - Every hour from 9 AM to 5 PM

## Option 2: macOS LaunchAgent (macOS-specific)

For macOS, you can use LaunchAgent for better integration.

### Setup Steps

1. **Create LaunchAgent plist file:**
```bash
mkdir -p ~/Library/LaunchAgents
```

2. **Create the plist file:**
```bash
nano ~/Library/LaunchAgents/com.nyiso.hourly.plist
```

3. **Add this content (adjust paths as needed):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nyiso.hourly</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/kenloughery/Desktop/Power Markets/NYISO Product/run_hourly_updates.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/kenloughery/Desktop/Power Markets/NYISO Product</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/nyiso_launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/nyiso_launchd_error.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

4. **Load the LaunchAgent:**
```bash
launchctl load ~/Library/LaunchAgents/com.nyiso.hourly.plist
```

5. **Start it immediately (optional):**
```bash
launchctl start com.nyiso.hourly
```

6. **Check status:**
```bash
launchctl list | grep nyiso
```

7. **Unload (if needed):**
```bash
launchctl unload ~/Library/LaunchAgents/com.nyiso.hourly.plist
```

## Option 3: Systemd Service (Linux)

For Linux systems, use systemd.

### Setup Steps

1. **Create service file:**
```bash
sudo nano /etc/systemd/system/nyiso-hourly.service
```

2. **Add this content:**
```ini
[Unit]
Description=NYISO Hourly Data Update
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/NYISO Product
ExecStart=/usr/bin/python3 /path/to/NYISO Product/run_hourly_updates.py
StandardOutput=append:/var/log/nyiso-hourly.log
StandardError=append:/var/log/nyiso-hourly-error.log

[Install]
WantedBy=multi-user.target
```

3. **Create timer file:**
```bash
sudo nano /etc/systemd/system/nyiso-hourly.timer
```

4. **Add this content:**
```ini
[Unit]
Description=Run NYISO hourly update
Requires=nyiso-hourly.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

5. **Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable nyiso-hourly.timer
sudo systemctl start nyiso-hourly.timer
```

6. **Check status:**
```bash
sudo systemctl status nyiso-hourly.timer
sudo systemctl list-timers | grep nyiso
```

## Option 4: Continuous Scheduler (Python-based)

Run the scheduler continuously (good for development, less ideal for production).

### Setup Steps

1. **Run the scheduler:**
```bash
python main.py schedule
```

2. **Run in background (Linux/macOS):**
```bash
nohup python main.py schedule > scheduler.log 2>&1 &
```

3. **Or use screen/tmux:**
```bash
screen -S nyiso_scheduler
python main.py schedule
# Press Ctrl+A then D to detach
```

## Option 5: Windows Task Scheduler

For Windows systems.

### Setup Steps

1. **Open Task Scheduler** (search for it in Start menu)

2. **Create Basic Task:**
   - Name: "NYISO Hourly Update"
   - Trigger: Daily, repeat every 1 hour
   - Action: Start a program
   - Program: `python.exe` (or full path to Python)
   - Arguments: `"C:\path\to\NYISO Product\run_hourly_updates.py"`
   - Start in: `"C:\path\to\NYISO Product"`

3. **Set to run whether user is logged on or not**

4. **Save and test**

## Verification

### Check if updates are running:

1. **Check log files:**
```bash
tail -f nyiso_hourly.log
# or
tail -f /tmp/nyiso_cron.log
```

2. **Check database for recent data:**
```bash
python3 -c "
from database.schema import get_session, RealTimeLBMP
from sqlalchemy import func, desc
from datetime import datetime, timedelta

db = get_session()
recent = db.query(RealTimeLBMP).order_by(desc(RealTimeLBMP.timestamp)).limit(5).all()
print('Most recent records:')
for r in recent:
    print(f'  {r.timestamp} - {r.zone.name} - LBMP: {r.lbmp}')
db.close()
"
```

3. **Check scraping jobs:**
```bash
python3 -c "
from database.schema import get_session, ScrapingJob
from sqlalchemy import desc
from datetime import datetime, timedelta

db = get_session()
recent_jobs = db.query(ScrapingJob).order_by(desc(ScrapingJob.started_at)).limit(10).all()
print('Recent scraping jobs:')
for j in recent_jobs:
    print(f'  {j.started_at} - {j.data_source.report_code} - {j.status} - {j.rows_inserted} inserted')
db.close()
"
```

## Troubleshooting

### Cron job not running:

1. **Check cron service is running:**
```bash
# macOS
sudo launchctl list | grep cron

# Linux
sudo systemctl status cron
```

2. **Check cron logs:**
```bash
# macOS
grep CRON /var/log/system.log

# Linux
grep CRON /var/log/syslog
```

3. **Verify Python path:**
```bash
which python3
# Use this exact path in crontab
```

4. **Check file permissions:**
```bash
ls -la run_hourly_updates.py
chmod +x run_hourly_updates.py
```

### Script fails silently:

1. **Add error output to cron:**
```cron
0 * * * * cd "/path/to/project" && /usr/bin/python3 run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1
```

2. **Check log files:**
```bash
tail -f nyiso_hourly.log
tail -f /tmp/nyiso_cron.log
```

### Database locked errors:

- Ensure only one instance runs at a time
- Add file locking to the script if needed
- Use SQLite WAL mode (already configured)

## Recommended Setup

**For Production:**
- Use **Cron** (macOS/Linux) or **Task Scheduler** (Windows)
- Run at minute 5 past each hour to avoid peak times
- Monitor logs regularly
- Set up alerts for failures

**For Development:**
- Use the continuous scheduler: `python main.py schedule`
- Or run manually: `python run_hourly_updates.py`

## Monitoring

Create a simple monitoring script:

```python
# check_updates.py
from database.schema import get_session, ScrapingJob
from datetime import datetime, timedelta
from sqlalchemy import desc

db = get_session()
one_hour_ago = datetime.utcnow() - timedelta(hours=1)
recent_jobs = db.query(ScrapingJob).filter(
    ScrapingJob.started_at >= one_hour_ago
).order_by(desc(ScrapingJob.started_at)).all()

if not recent_jobs:
    print("WARNING: No jobs in the last hour!")
else:
    print(f"OK: {len(recent_jobs)} jobs in the last hour")
    for j in recent_jobs:
        print(f"  {j.data_source.report_code}: {j.status}")

db.close()
```

Run this as a separate cron job to monitor the updates.

