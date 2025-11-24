# NYISO Scraping Pipeline Architecture

## Overview

This document describes the architecture and design decisions for the NYISO data scraping pipeline.

## System Components

### 1. Configuration Layer (`config/`)

**URLConfigLoader**
- Reads configuration from `URL_Instructions.txt` and `URL_Lookup.txt`
- Provides URL building functionality with date substitution
- Manages data source metadata (categories, update frequencies)

**Key Features:**
- Centralized configuration management
- Easy to extend with new data sources
- Supports both direct CSV and archive ZIP URLs

### 2. Download Layer (`scraper/downloader.py`)

**NYISODownloader**
- Handles HTTP requests with retry logic
- Implements exponential backoff for transient failures
- Archive ZIP fallback when direct CSV unavailable
- User-Agent headers for polite scraping

**Error Handling:**
- Distinguishes between retryable (timeout, 5xx) and non-retryable (404) errors
- Configurable retry attempts and delays
- Comprehensive logging

### 3. Parsing Layer (`scraper/csv_parser.py`)

**NYISOCSVParser**
- Dynamic schema detection
- Multiple date format support
- Data type conversion and cleaning
- Type-specific transformers for different report codes

**Transformations:**
- Real-time LBMP: Zone-based pricing data
- Day-ahead LBMP: Hourly pricing data
- Load data: Actual and forecasted load
- Interface flows: Transfer limits and flows
- Ancillary services: Regulation and reserve prices

### 4. Database Layer (`database/`)

**Schema Design:**
- **Metadata Tables**: Track data sources and scraping jobs
- **Reference Tables**: Zones, interfaces (normalized)
- **Time-Series Tables**: Optimized for time-range queries

**Key Design Decisions:**
- Normalized zones and interfaces to reduce redundancy
- Unique constraints on (timestamp, zone_id) to prevent duplicates
- Indexes on timestamp and foreign keys for performance
- Upsert logic to handle re-scrapes gracefully

**Tables:**
- `data_sources`: Configuration metadata
- `scraping_jobs`: Job execution tracking
- `scraping_logs`: Detailed operation logs
- `zones`: Zone reference data
- `interfaces`: Interface reference data
- `realtime_lbmp`: 5-minute real-time pricing
- `dayahead_lbmp`: Hourly day-ahead pricing
- `timeweighted_lbmp`: Hourly time-weighted pricing
- `realtime_load`: 5-minute actual load
- `load_forecast`: Hourly load forecasts
- `interface_flows`: 5-minute interface flows
- `ancillary_services`: Ancillary service prices

### 5. Orchestration Layer (`scraper/scraper.py`)

**NYISOScraper**
- Coordinates download, parse, and write operations
- Manages database sessions and transactions
- Tracks job status and errors
- Supports single date, date range, and recent scraping

**Features:**
- Automatic data source synchronization
- Duplicate detection (skip already-scraped dates)
- Comprehensive error logging
- Transaction-safe operations

### 6. Scheduling Layer (`scraper/scheduler.py`)

**NYISOScheduler**
- Automatic scheduling based on update frequencies
- Configurable schedules:
  - Real-time: Every 5 minutes
  - Hourly: Every hour
  - Daily: Once per day at configured time
  - Multiple daily: Every 6 hours

**Implementation:**
- Uses `schedule` library for cron-like scheduling
- Runs in background thread
- Graceful shutdown on interrupt

## Data Flow

```
1. Configuration Load
   URL_Instructions.txt + URL_Lookup.txt
   ↓
   URLConfigLoader
   ↓
   DataSourceConfig objects

2. Scraping Job
   Date + Report Code
   ↓
   URL Building (with date substitution)
   ↓
   Downloader (with retry + archive fallback)
   ↓
   CSV Content

3. Parsing
   CSV Content
   ↓
   NYISOCSVParser
   ↓
   DataFrame → Records (dicts)

4. Database Write
   Records
   ↓
   DatabaseWriter (upsert logic)
   ↓
   Database Tables

5. Job Tracking
   All operations logged to scraping_jobs and scraping_logs
```

## Error Recovery Strategy

### Multi-Level Error Handling

1. **Download Level**
   - Retry with exponential backoff (3 attempts)
   - Archive ZIP fallback
   - 404 errors are non-retryable (file doesn't exist)

2. **Parse Level**
   - Schema validation
   - Data type conversion with error handling
   - Null value handling

3. **Database Level**
   - Transaction rollback on errors
   - Unique constraint violations handled by upsert
   - Foreign key validation

4. **Job Level**
   - Job status tracking (pending → running → completed/failed)
   - Error messages stored in database
   - Failed jobs can be re-run with `force=True`

## Performance Considerations

### Database Optimization
- Indexes on timestamp columns for time-range queries
- Indexes on foreign keys (zone_id, interface_id)
- Unique constraints prevent duplicate inserts
- Batch inserts within transactions

### Scraping Optimization
- Skip already-scraped dates (unless `force=True`)
- Archive fallback reduces need for multiple requests
- Session reuse for HTTP connections
- Configurable timeouts prevent hanging

### Scalability
- Database-agnostic design (SQLite for dev, PostgreSQL for prod)
- Can run multiple scrapers in parallel (different report codes)
- Job-based architecture allows distributed execution

## Extensibility

### Adding New Data Sources

1. Add entry to `URL_Instructions.txt`:
   ```
   Data Type,Report Code,Dataset Name,Filename Pattern,Direct CSV URL,Archive ZIP URL,...
   ```

2. Add metadata to `URL_Lookup.txt`:
   ```
   Category,Data Type,Report Code,Access Point,Format,Update Frequency,Description
   ```

3. (Optional) Add transformer in `csv_parser.py`:
   ```python
   def _transform_new_type(self, df, timestamp_col):
       # Custom transformation logic
   ```

4. (Optional) Add database table in `schema.py`:
   ```python
   class NewDataType(Base):
       __tablename__ = 'new_data_type'
       # Columns...
   ```

5. (Optional) Add writer method in `db_writer.py`:
   ```python
   def upsert_new_data_type(self, records):
       # Upsert logic
   ```

### Custom Scheduling

Modify `scheduler.py` to add custom schedules:
```python
# Custom schedule example
schedule.every(30).minutes.do(
    self._scrape_wrapper,
    'P-XX',
    'custom'
)
```

## Monitoring and Observability

### Logging
- File logging: `nyiso_scraper.log`
- Console logging: stdout
- Database logging: `scraping_logs` table

### Job Tracking
- `scraping_jobs` table tracks:
  - Status (pending/running/completed/failed)
  - Row counts (scraped/inserted/updated)
  - Error messages
  - Execution timestamps

### Health Checks
- Query `scraping_jobs` for recent failures
- Check `scraping_logs` for error patterns
- Monitor database size and growth

## Security Considerations

- No authentication required (NYISO data is public)
- User-Agent header identifies scraper
- Rate limiting handled by scheduler (respects update frequencies)
- Input validation on date parameters
- SQL injection prevention via SQLAlchemy ORM

## Testing Strategy

1. **Unit Tests**: Individual components (downloader, parser, writer)
2. **Integration Tests**: End-to-end scraping (`test_pipeline.py`)
3. **Data Exploration**: `test_data_exploration.py` analyzes CSV structure
4. **Manual Testing**: CLI commands for specific dates/sources

## Future Enhancements

- [ ] Parallel scraping for multiple report codes
- [ ] Incremental updates (only scrape new data)
- [ ] Data validation rules (range checks, consistency)
- [ ] Alerting for scraping failures
- [ ] Dashboard for job monitoring
- [ ] API for querying scraped data
- [ ] Data export functionality
- [ ] Historical backfill optimization

