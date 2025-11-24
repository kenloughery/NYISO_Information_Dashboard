# NYISO Data Scraping Pipeline

A robust, production-ready pipeline for scraping NYISO (New York Independent System Operator) market data and storing it in a database.

## Features

- **Comprehensive Data Coverage**: Supports all major NYISO data types including:
  - Real-time and Day-ahead LBMP (Locational Marginal Pricing)
  - Load forecasts and actual load
  - Interface flows and limits
  - Ancillary services
  - And more (see URL_Instructions.txt and URL_Lookup.txt)

- **Robust Error Handling**:
  - Automatic retry logic with exponential backoff
  - Archive ZIP fallback when direct CSV unavailable
  - Comprehensive logging and error tracking
  - Transaction-safe database writes

- **Flexible Scheduling**:
  - Automatic scheduling based on update frequencies
  - Manual scraping for specific dates or date ranges
  - Support for historical data backfill

- **Database Design**:
  - Normalized schema with reference tables
  - Efficient time-series storage with indexes
  - Upsert logic to prevent duplicates
  - Job tracking and audit logging

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set up PostgreSQL database:
```bash
export DATABASE_URL="postgresql://user:password@localhost/nyiso"
```

If not set, the system will use SQLite (nyiso_data.db).

## API Server (for Dashboards)

The system includes a REST API for dashboard consumption:

```bash
# Start API server
python start_api.py

# API will be available at http://localhost:8000
# Documentation: http://localhost:8000/docs
```

See `API_README.md` for detailed API documentation and React integration examples.

## Usage

### Scrape Recent Data

```bash
# Scrape last 7 days
python main.py scrape --days 7

# Scrape specific date
python main.py scrape --date 2025-11-13

# Scrape specific report code
python main.py scrape --report-code P-24A --days 1

# Force re-scrape (overwrite existing)
python main.py scrape --date 2025-11-13 --force
```

### Run Scheduler

```bash
# Run scheduler (continuous)
python main.py schedule

# Run scheduled jobs once (for testing)
python main.py schedule --run-once
```

### Python API

```python
from scraper.scraper import NYISOScraper
from datetime import datetime

scraper = NYISOScraper()

# Scrape today
job = scraper.scrape_date(datetime.now())

# Scrape date range
jobs = scraper.scrape_date_range(
    datetime(2025, 11, 1),
    datetime(2025, 11, 13)
)

# Scrape recent days
jobs = scraper.scrape_recent(days=7)

scraper.close()
```

## Database Schema

### Metadata Tables
- `data_sources`: Configuration for each data source
- `scraping_jobs`: Tracks each scraping job execution
- `scraping_logs`: Detailed logs for debugging

### Reference Tables
- `zones`: NYISO zones (CAPITL, CENTRL, etc.)
- `interfaces`: Interface names for flows

### Time-Series Tables
- `realtime_lbmp`: Real-time zonal LBMP (5-min)
- `dayahead_lbmp`: Day-ahead zonal LBMP (hourly)
- `timeweighted_lbmp`: Time-weighted RT LBMP (hourly)
- `realtime_load`: Real-time actual load (5-min)
- `load_forecast`: ISO load forecast (hourly)
- `interface_flows`: Interface limits and flows (5-min)
- `ancillary_services`: Ancillary service prices

## Architecture

```
┌─────────────────┐
│  URL Config     │  Reads URL_Instructions.txt & URL_Lookup.txt
│  Loader         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Downloader    │  Handles HTTP requests, retries, archive fallback
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CSV Parser    │  Parses and transforms data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Database Writer   │  Upserts with transaction management
└────────────────────┘
```

## Configuration

Data source configurations are loaded from:
- `URL_Instructions.txt`: URL patterns and file naming
- `URL_Lookup.txt`: Metadata (categories, update frequencies)

## Logging

Logs are written to:
- Console (stdout)
- File: `nyiso_scraper.log`
- Database: `scraping_logs` table

## Error Recovery

The system includes multiple layers of error recovery:

1. **Download Level**: Retry with exponential backoff, archive fallback
2. **Parse Level**: Schema validation, data cleaning
3. **Database Level**: Transaction rollback on errors, job status tracking
4. **Scheduler Level**: Continues running even if individual jobs fail

## Testing

Run the data exploration script to test data structure:

```bash
python test_data_exploration.py
```

This will download sample CSVs and analyze their structure, saving results to `data_exploration_results.json`.

## Hourly Updates

To set up automatic hourly database updates:

### Quick Setup (macOS/Linux)

```bash
# Run the setup script
./setup_hourly_cron.sh

# Or manually add to crontab
crontab -e
# Add: 5 * * * * cd "/path/to/project" && /usr/bin/python3 run_hourly_updates.py >> /tmp/nyiso_cron.log 2>&1
```

### Manual Setup

```bash
# Test the hourly update script
python run_hourly_updates.py

# Add to crontab (runs at 5 minutes past every hour)
crontab -e
```

See `HOURLY_UPDATE_SETUP.md` for detailed instructions for:
- Cron jobs (macOS/Linux)
- LaunchAgent (macOS)
- Systemd (Linux)
- Task Scheduler (Windows)
- Continuous scheduler (development)

## Production Considerations

1. **Database**: Use PostgreSQL for production (set `DATABASE_URL`)
2. **Monitoring**: Set up monitoring for scraping job failures
3. **Backup**: Regular database backups
4. **Rate Limiting**: The scheduler respects update frequencies to avoid over-scraping
5. **Storage**: Monitor database size as time-series data grows
6. **Automated Updates**: Set up hourly cron job for continuous data updates

## License

This project is designed for internal use with NYISO public data.

