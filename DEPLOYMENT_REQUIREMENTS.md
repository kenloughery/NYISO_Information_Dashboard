# NYISO Dashboard - Deployment Requirements

**Date**: 2025-01-27  
**Status**: Comprehensive Deployment Requirements Document

## Table of Contents

1. [Overview](#overview)
2. [Data Requirements](#data-requirements)
3. [Update Scheduler Requirements](#update-scheduler-requirements)
4. [API Connection Requirements](#api-connection-requirements)
5. [Frontend Requirements](#frontend-requirements)
6. [Infrastructure Requirements](#infrastructure-requirements)
7. [Environment Variables](#environment-variables)
8. [Dependencies](#dependencies)
9. [Deployment Checklist](#deployment-checklist)

---

## Overview

The NYISO Dashboard is a full-stack application consisting of:
- **Backend**: FastAPI Python application with data scraping pipeline
- **Database**: SQLite (development) or PostgreSQL (production)
- **Scheduler**: Automated data collection from NYISO public data sources
- **Frontend**: React + TypeScript dashboard with real-time data visualization

---

## Data Requirements

### 1. Database

#### Database Options

**SQLite (Development/Testing)**
- **File**: `nyiso_data.db` (default location)
- **Size**: Grows with time-series data (~100MB-1GB+ depending on retention)
- **Limitations**: 
  - Single-writer concurrency
  - Not recommended for production with high traffic
  - No network access

**PostgreSQL (Production Recommended)**
- **Version**: PostgreSQL 12+ recommended
- **Storage**: Minimum 10GB, scales with data retention period
- **Connection**: Requires `DATABASE_URL` environment variable
- **Format**: `postgresql://user:password@host:port/database`

#### Database Schema

The application uses SQLAlchemy ORM with the following key tables:

**Metadata Tables:**
- `data_sources` - Configuration for NYISO data sources
- `scraping_jobs` - Job execution tracking
- `scraping_logs` - Detailed operation logs

**Reference Tables:**
- `zones` - NYISO zone definitions (CAPITL, CENTRL, etc.)
- `interfaces` - Interface names for flows

**Time-Series Tables:**
- `realtime_lbmp` - 5-minute real-time pricing data
- `dayahead_lbmp` - Hourly day-ahead pricing
- `timeweighted_lbmp` - Hourly time-weighted pricing
- `realtime_load` - 5-minute actual load
- `load_forecast` - Hourly load forecasts
- `interface_flows` - 5-minute interface flows
- `ancillary_services` - Ancillary service prices
- `market_advisories` - Market notifications
- `constraints` - Transmission constraints
- `external_rto_prices` - External RTO prices (PJM, ISO-NE, IESO)
- `atc_ttc` - Available Transfer Capability
- `outages` - Outage information
- `weather_forecast` - Weather data
- `fuel_mix` - Real-time generation stack
- `page_views` - Analytics tracking
- `visitor_sessions` - Session tracking

#### Database Initialization

```bash
# Automatic initialization on first run
# Or manually:
python -c "from database.schema import init_database; init_database()"
```

#### Database Indexes

The schema includes optimized indexes for:
- Timestamp-based queries (all time-series tables)
- Foreign key lookups (zone_id, interface_id)
- Unique constraints to prevent duplicates

#### Storage Growth Estimates

- **Real-time data (5-min)**: ~288 records/day per zone × 11 zones = ~3,168 records/day
- **Hourly data**: ~24 records/day per zone × 11 zones = ~264 records/day
- **Estimated growth**: ~1-2GB per year (depending on data sources enabled)

### 2. Data Sources

#### NYISO Data Sources

The application scrapes data from NYISO public data sources:

**Configuration Files:**
- `URL_Instructions.txt` - URL patterns and file naming conventions
- `URL_Lookup.txt` - Metadata (categories, update frequencies)

**Data Source Types:**
- Real-time LBMP (5-minute updates)
- Day-ahead LBMP (hourly updates)
- Load forecasts and actual load
- Interface flows and limits
- Ancillary services
- Market advisories
- Constraints
- External RTO prices
- ATC/TTC data
- Outages
- Weather forecasts
- Fuel mix/generation stack

#### Data Source Requirements

- **Internet Access**: Required for scraping NYISO public data
- **HTTP/HTTPS**: Access to NYISO data portal
- **User-Agent**: Polite scraping with identifiable user-agent
- **Retry Logic**: Built-in exponential backoff for transient failures
- **Archive Fallback**: Automatic fallback to ZIP archives when direct CSV unavailable

### 3. Static Files

**GeoJSON Zone Boundaries:**
- **File**: `static/nyiso_zones.geojson`
- **Purpose**: Zone boundary polygons for map visualization
- **Generation**: Run `scripts/generate_nyiso_zones.py` or `scripts/fetch_nyiso_zones.py`
- **Size**: ~100KB-1MB

---

## Update Scheduler Requirements

### 1. Scheduler Architecture

The scheduler (`scraper/scheduler.py`) uses the `schedule` library to run scraping jobs based on update frequencies:

**Update Frequencies:**
- **Real-time (5-minute)**: Every 5 minutes
- **Hourly**: Every hour at :00
- **Daily**: Once per day at 01:00
- **Multiple times daily**: Every 6 hours (or hourly for weather data)

### 2. Scheduler Execution Modes

#### Mode 1: Continuous Scheduler (Production)

**File**: `run_scraper_prod.py`

```bash
python run_scraper_prod.py
```

**Characteristics:**
- Runs continuously in background
- Automatically schedules jobs based on update frequencies
- Runs initial scrape on startup
- Logs to `logs/scraper.log`
- Graceful shutdown on interrupt

**Requirements:**
- Long-running process (systemd service, Docker container, or process manager)
- Persistent connection to database
- Internet access for scraping

#### Mode 2: Hourly Cron Job

**File**: `run_hourly_updates.py`

```bash
# Cron entry (runs at 5 minutes past every hour)
5 * * * * cd /path/to/project && python run_hourly_updates.py
```

**Characteristics:**
- Runs once per hour
- Scrapes all data sources for current day
- Skips already-scraped dates (unless `force=True`)
- Exits after completion
- Logs to `nyiso_hourly.log`

**Requirements:**
- Cron daemon or system scheduler
- Python environment accessible from cron
- Database access

### 3. Scheduler Dependencies

**Python Packages:**
- `schedule>=1.2.0` - Job scheduling
- `requests>=2.31.0` - HTTP requests
- `pandas>=2.1.0` - Data processing
- `sqlalchemy>=2.0.0` - Database ORM

**System Requirements:**
- Python 3.11+ recommended
- Persistent storage for database
- Network access to NYISO data sources
- Sufficient memory for data processing (512MB-1GB recommended)

### 4. Scheduler Logging

**Log Files:**
- `logs/scraper.log` - Continuous scheduler logs
- `nyiso_hourly.log` - Hourly update script logs
- `nyiso_scraper.log` - General scraper logs

**Log Rotation:**
- Recommended: Use logrotate or similar tool
- Retention: 30-90 days recommended

### 5. Error Handling

**Built-in Features:**
- Automatic retry with exponential backoff
- Archive ZIP fallback for failed direct CSV downloads
- Transaction rollback on database errors
- Job status tracking (pending/running/completed/failed)
- Error messages stored in database

**Monitoring:**
- Check `scraping_jobs` table for failed jobs
- Monitor `scraping_logs` table for error patterns
- Set up alerts for consecutive failures

---

## API Connection Requirements

### 1. API Server

**Framework**: FastAPI (Python)
**Port**: 8000 (default, configurable)
**Protocol**: HTTP/HTTPS

### 2. API Endpoints

#### Core Data Endpoints

- `GET /api/zones` - List all zones
- `GET /api/interfaces` - List all interfaces
- `GET /api/realtime-lbmp` - Real-time LBMP data
- `GET /api/dayahead-lbmp` - Day-ahead LBMP data
- `GET /api/timeweighted-lbmp` - Time-weighted LBMP
- `GET /api/ancillary-services` - Ancillary service prices
- `GET /api/realtime-load` - Real-time load data
- `GET /api/load-forecast` - Load forecasts
- `GET /api/interface-flows` - Interface flows
- `GET /api/interregional-flows` - Interregional flows

#### Additional Data Endpoints

- `GET /api/market-advisories` - Market notifications
- `GET /api/constraints` - Transmission constraints
- `GET /api/external-rto-prices` - External RTO prices
- `GET /api/atc-ttc` - ATC/TTC data
- `GET /api/outages` - Outage information
- `GET /api/weather-forecast` - Weather forecasts
- `GET /api/weather-current` - Current weather
- `GET /api/fuel-mix` - Fuel mix/generation stack

#### Calculated Metrics Endpoints

- `GET /api/rt-da-spreads` - RT-DA price spreads
- `GET /api/zone-spreads` - Intra-zonal price differentials
- `GET /api/load-forecast-errors` - Load forecast errors
- `GET /api/reserve-margins` - Reserve margins
- `GET /api/price-volatility` - Price volatility metrics
- `GET /api/correlations` - Zone-to-zone correlations
- `GET /api/trading-signals` - Trading signals

#### Utility Endpoints

- `GET /` - API root with endpoint list
- `GET /health` - Health check endpoint
- `GET /api/stats` - Database statistics
- `GET /api/analytics/summary` - Analytics summary
- `GET /api/maps/nyiso-zones` - GeoJSON zone boundaries

### 3. API Dependencies

**Python Packages:**
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pydantic>=2.0.0` - Data validation
- `sqlalchemy>=2.0.0` - Database ORM
- `python-dateutil>=2.8.2` - Date parsing

**System Requirements:**
- Python 3.11+ recommended
- Database connection (SQLite or PostgreSQL)
- Sufficient memory for query processing (256MB-512MB recommended)

### 4. CORS Configuration

**Current Setting**: Allows all origins (`allow_origins=["*"]`)

**Production Recommendation**: Restrict to frontend domain(s)

```python
# In api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://www.your-domain.com",
        "http://localhost:3000"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. API Performance

**Query Limits:**
- Default limit: 1000 records per endpoint
- Maximum limit: 10,000 records per endpoint
- Pagination: Not currently implemented (consider for large datasets)

**Response Times:**
- Simple queries: <100ms
- Complex aggregations: 100-500ms
- Large date ranges: 500ms-2s

**Optimization:**
- Database indexes on timestamp and foreign keys
- Query result limits
- Consider caching for frequently accessed data

### 6. API Health Monitoring

**Health Check Endpoint**: `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Monitoring Recommendations:**
- Set up health check monitoring (every 1-5 minutes)
- Alert on 503 responses (database connection failures)
- Monitor response times
- Track error rates

---

## Frontend Requirements

### 1. Frontend Architecture

**Framework**: React 19 with TypeScript
**Build Tool**: Vite 7
**Package Manager**: npm

### 2. Frontend Dependencies

**Core Dependencies:**
- `react>=19.2.0` - UI framework
- `react-dom>=19.2.0` - DOM rendering
- `typescript~5.9.3` - Type safety
- `vite>=7.2.2` - Build tool and dev server

**State Management:**
- `@tanstack/react-query>=5.90.8` - Server state management
- `zustand>=5.0.8` - Client state management

**UI Libraries:**
- `@mui/material>=7.3.5` - Material-UI components
- `@mui/icons-material>=7.3.5` - Material icons
- `tailwindcss>=4.1.17` - Utility-first CSS

**Data Visualization:**
- `recharts>=3.4.1` - Chart library
- `react-sparklines>=1.7.0` - Sparkline charts
- `leaflet>=1.9.4` - Map library
- `react-leaflet>=5.0.0` - React bindings for Leaflet

**Utilities:**
- `axios>=1.13.2` - HTTP client
- `date-fns>=4.1.0` - Date manipulation

### 3. Frontend Build Requirements

**Node.js**: 18+ required
**npm**: Comes with Node.js

**Build Process:**
```bash
cd frontend
npm install
npm run build
```

**Output**: `frontend/dist/` directory with static files

**Build Size**: ~1-5MB (compressed, depending on dependencies)

### 4. Frontend Environment Variables

**Required:**
- `VITE_API_BASE_URL` - Backend API URL

**Example:**
```env
# Development
VITE_API_BASE_URL=http://localhost:8000

# Production
VITE_API_BASE_URL=https://api.your-domain.com
```

**Note**: Vite requires `VITE_` prefix for environment variables to be exposed to the frontend.

### 5. Frontend API Integration

**API Client**: `frontend/src/services/api.ts`

**Features:**
- Axios-based HTTP client
- Automatic error handling
- TypeScript types for all endpoints
- React Query integration for caching and refetching

**Refresh Intervals:**
- Real-time data: 5 minutes
- Historical data: 30 minutes
- Static data: 1 hour

### 6. Frontend Static Assets

**GeoJSON Zones:**
- Served from API: `GET /api/maps/nyiso-zones`
- Cached in browser
- Used for map visualizations

**Other Assets:**
- Images, icons, fonts served from `frontend/dist/assets/`

### 7. Frontend Deployment

**Static Hosting Options:**
- Nginx (served by FastAPI in current setup)
- Firebase Hosting
- Cloudflare Pages
- AWS S3 + CloudFront
- Vercel
- Netlify

**Current Setup**: FastAPI serves static files from `frontend/dist/`

**SPA Routing**: All non-API routes serve `index.html` for client-side routing

---

## Infrastructure Requirements

### 1. Compute Resources

**Minimum Requirements:**
- **CPU**: 1 vCPU (shared OK for low traffic)
- **RAM**: 512MB (1GB recommended)
- **Storage**: 10GB (20GB+ recommended for database growth)

**Recommended for Production:**
- **CPU**: 2 vCPUs
- **RAM**: 2GB
- **Storage**: 50GB+ (with database backups)

### 2. Network Requirements

**Inbound:**
- HTTP/HTTPS port (80/443) for API and frontend
- Optional: SSH (22) for server management

**Outbound:**
- HTTPS access to NYISO data sources
- DNS resolution
- Database connection (if using external PostgreSQL)

### 3. Process Management

**Options:**
- **Systemd** (Linux): Service files provided in `systemd/`
- **Docker**: Dockerfile provided
- **Process Manager**: PM2, Supervisor, etc.
- **Cloud Platforms**: Fly.io, Railway, Heroku, etc.

### 4. Reverse Proxy (Optional but Recommended)

**Nginx Configuration**: `nginx/nyiso-dashboard.conf`

**Benefits:**
- SSL/TLS termination
- Load balancing (if scaling)
- Static file serving (alternative to FastAPI)
- Rate limiting
- Security headers

### 5. SSL/TLS Certificates

**Options:**
- Let's Encrypt (free, automated)
- Cloud provider managed certificates
- Self-signed (development only)

---

## Environment Variables

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///nyiso_data.db` | Database connection string |
| `API_HOST` | No | `127.0.0.1` | API server host |
| `API_PORT` | No | `8000` | API server port |
| `ALLOWED_ORIGINS` | No | `*` | CORS allowed origins (comma-separated) |
| `ANALYTICS_SECRET_KEY` | No | `nyiso-analytics-secret-key-change-in-production` | Analytics secret key |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | Backend API URL |

### Scheduler Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///nyiso_data.db` | Database connection string (shared with API) |

---

## Dependencies

### Python Dependencies (`requirements.txt`)

```
requests>=2.31.0
pandas>=2.1.0
geopandas>=0.14.0
sqlalchemy>=2.0.0
python-dateutil>=2.8.2
pytz>=2023.3
schedule>=1.2.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.9
openpyxl>=3.1.2
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
```

### Node.js Dependencies (`frontend/package.json`)

See `frontend/package.json` for complete list. Key dependencies:
- React 19
- TypeScript 5.9
- Vite 7
- Material-UI 7
- TanStack Query 5
- Recharts 3
- Leaflet 1.9

---

## Deployment Checklist

### Pre-Deployment

- [ ] Review and update environment variables
- [ ] Set up database (SQLite or PostgreSQL)
- [ ] Generate GeoJSON zone boundaries (`scripts/generate_nyiso_zones.py`)
- [ ] Test database connection
- [ ] Verify internet access to NYISO data sources
- [ ] Review CORS settings for production
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (if using)
- [ ] Set up logging and log rotation
- [ ] Plan database backup strategy

### Deployment Steps

- [ ] Install Python 3.11+ and dependencies
- [ ] Install Node.js 18+ and npm
- [ ] Clone repository
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Install frontend dependencies: `cd frontend && npm install`
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Initialize database: `python -c "from database.schema import init_database; init_database()"`
- [ ] Set environment variables
- [ ] Configure scheduler (systemd, cron, or Docker)
- [ ] Start API server
- [ ] Verify health check: `curl http://localhost:8000/health`
- [ ] Test API endpoints
- [ ] Test frontend access
- [ ] Run initial data scrape
- [ ] Verify scheduler is running

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Verify scheduler is running and scraping data
- [ ] Check database growth
- [ ] Set up monitoring and alerts
- [ ] Configure backups
- [ ] Test failover scenarios
- [ ] Document deployment process
- [ ] Set up CI/CD (optional)

### Ongoing Maintenance

- [ ] Monitor database size and plan for growth
- [ ] Review and rotate logs
- [ ] Update dependencies regularly
- [ ] Monitor scraping job success rates
- [ ] Review error logs
- [ ] Backup database regularly
- [ ] Monitor API performance
- [ ] Review and update security settings

---

## Additional Considerations

### Security

- [ ] Use strong database passwords (if PostgreSQL)
- [ ] Restrict CORS to known origins
- [ ] Use HTTPS in production
- [ ] Set up firewall rules
- [ ] Rotate API keys/secrets regularly
- [ ] Keep dependencies updated
- [ ] Review and restrict file permissions

### Performance

- [ ] Monitor database query performance
- [ ] Consider database connection pooling (PostgreSQL)
- [ ] Implement caching for frequently accessed data (optional)
- [ ] Monitor API response times
- [ ] Consider CDN for static assets (if not using FastAPI)

### Scalability

- [ ] Plan for database growth
- [ ] Consider read replicas for high traffic (PostgreSQL)
- [ ] Implement pagination for large datasets (if needed)
- [ ] Consider horizontal scaling for API (load balancer)
- [ ] Monitor resource usage (CPU, memory, disk)

### Backup and Recovery

- [ ] Set up automated database backups
- [ ] Test backup restoration process
- [ ] Store backups off-site
- [ ] Document recovery procedures
- [ ] Consider point-in-time recovery (PostgreSQL)

---

## Support and Resources

- **API Documentation**: Available at `/docs` (Swagger UI) when API is running
- **Architecture Documentation**: See `ARCHITECTURE.md`
- **Deployment Guides**: See `DEPLOYMENT_SOLUTION.md` and deployment-specific guides
- **API Reference**: See `API_README.md` and `API_ENDPOINTS_REFERENCE.md`

---

**Last Updated**: 2025-01-27


