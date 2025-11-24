# Fly.io Resource Analysis for NYISO Scraper

## Question: Can Fly.io handle the computational requirements?

**Short Answer: Yes, but you'll need to configure adequate resources.**

## Computational Requirements Analysis

### What the Scraper Does

1. **HTTP Downloads** (I/O bound)
   - Downloads CSV files from NYISO servers
   - Retry logic with exponential backoff
   - Archive ZIP fallback if direct CSV fails
   - **CPU Impact**: Low (mostly network I/O)

2. **CSV Parsing** (CPU + Memory bound)
   - Uses pandas to parse CSV files
   - Data transformation and cleaning
   - **CPU Impact**: Moderate (pandas operations)
   - **Memory Impact**: Moderate-High (pandas DataFrames)

3. **Database Writes** (I/O bound)
   - Writes parsed data to SQLite/PostgreSQL
   - Upsert operations to prevent duplicates
   - **CPU Impact**: Low (mostly disk I/O)
   - **Memory Impact**: Low

4. **Scheduler** (CPU bound)
   - Runs every 5 minutes for real-time sources (9 sources)
   - Runs hourly for hourly sources (3 sources)
   - Runs daily for daily sources (8 sources)
   - **CPU Impact**: Low (just scheduling logic)

### Resource Requirements

**Per Scrape Operation:**
- **CPU**: ~0.1-0.3 CPU cores (spikes during pandas operations)
- **Memory**: ~50-200MB (depends on CSV size)
- **Duration**: 5-30 seconds per source

**Peak Load (Every 5 Minutes):**
- 9 real-time sources scraping simultaneously
- **Total CPU**: ~0.9-2.7 cores (if sequential) or ~1-3 cores (if parallel)
- **Total Memory**: ~450MB-1.8GB (if parallel) or ~200MB (if sequential)
- **Duration**: 30-90 seconds total

## Current Fly.io Configuration

```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

**Assessment**: This configuration is **marginal** and may cause issues.

### Issues with Current Config

1. **512MB RAM is too low**
   - Pandas operations can use 100-200MB per DataFrame
   - Multiple concurrent scrapes could exceed 512MB
   - Risk of OOM (Out of Memory) kills

2. **1 shared CPU may be slow**
   - Shared CPUs are throttled
   - Pandas operations are CPU-intensive
   - Multiple scrapes could queue up

3. **No resource headroom**
   - API server also needs resources
   - No buffer for spikes

## Recommended Fly.io Configuration

### Option 1: Minimum Viable (Recommended Start)

```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024  # 1GB
```

**Cost**: ~$3.88/month  
**Why**: 
- 1GB RAM provides headroom for pandas operations
- 2 CPUs allow parallel processing
- Shared CPUs are cost-effective

### Option 2: Comfortable (Recommended Production)

```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 2048  # 2GB
```

**Cost**: ~$7.76/month  
**Why**:
- 2GB RAM provides plenty of headroom
- Handles spikes and concurrent operations
- Better performance for database operations

### Option 3: High Performance

```toml
[[vm]]
  cpu_kind = "performance"
  cpus = 2
  memory_mb = 4096  # 4GB
```

**Cost**: ~$31.04/month  
**Why**:
- Dedicated performance CPUs
- 4GB RAM for heavy workloads
- Best for high-traffic scenarios

## Optimizations for Fly.io

### 1. Sequential Scraping (Recommended)

Instead of parallel scraping, process sources sequentially:

```python
# In scheduler, scrape one at a time
for source in sources:
    scrape(source)  # Wait for completion
```

**Benefits**:
- Lower memory usage (only one DataFrame at a time)
- More predictable resource usage
- Works better with limited resources

### 2. Process Sources in Batches

```python
# Process 3 sources at a time
batch_size = 3
for i in range(0, len(sources), batch_size):
    batch = sources[i:i+batch_size]
    scrape_batch(batch)  # Process batch
```

**Benefits**:
- Balance between speed and resource usage
- Prevents memory spikes

### 3. Use Streaming for Large CSVs

Instead of loading entire CSV into memory:

```python
# Stream large CSVs in chunks
for chunk in pd.read_csv(csv_file, chunksize=1000):
    process_chunk(chunk)
```

**Benefits**:
- Lower memory usage
- Can handle larger files

### 4. Database Connection Pooling

For PostgreSQL (recommended over SQLite):

```python
# Use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

**Benefits**:
- Better performance
- Handles concurrent operations

## Updated fly.toml Configuration

```toml
# Fly.io configuration for NYISO Dashboard

app = "nyiso-dashboard"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  PYTHONUNBUFFERED = "1"
  API_HOST = "0.0.0.0"
  API_PORT = "8000"
  # Optimize pandas memory usage
  PANDAS_MEMORY_LIMIT = "512MB"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    timeout = "5s"
    path = "/health"

# Recommended: 2 CPUs, 1GB RAM (minimum)
[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024

# For production: 2 CPUs, 2GB RAM (comfortable)
# [[vm]]
#   cpu_kind = "shared"
#   cpus = 2
#   memory_mb = 2048

# Use Fly Postgres (recommended over SQLite)
[postgres]
  size_gb = 1
```

## Monitoring and Scaling

### Monitor Resource Usage

```bash
# Check resource usage
fly metrics

# View logs for memory issues
fly logs | grep -i "memory\|oom\|killed"
```

### Scale Up if Needed

```bash
# Scale to 2GB RAM
fly scale vm shared-cpu-2x --memory 2048

# Scale to performance CPUs
fly scale vm performance-2x --memory 4096
```

## Comparison: Fly.io vs VPS

| Aspect | Fly.io (2 CPU, 1GB) | VPS (Hetzner) |
|--------|---------------------|---------------|
| **Cost** | ~$3.88/month | €4.51/month (~$5) |
| **CPU** | 2 shared CPUs | 1 dedicated CPU |
| **RAM** | 1GB | 2GB |
| **Storage** | Ephemeral (use Postgres) | Persistent (20GB SSD) |
| **Scraping** | ✅ Can handle | ✅ Can handle |
| **Scalability** | Auto-scales | Manual scaling |
| **Management** | Managed | Self-managed |

## Recommendations

### For Development/Testing
- **Start with**: 1 CPU, 512MB RAM
- **Cost**: ~$1.94/month
- **Test**: Monitor for OOM kills

### For Production (Recommended)
- **Use**: 2 CPUs, 1GB RAM (minimum)
- **Cost**: ~$3.88/month
- **Optimize**: Sequential scraping, connection pooling

### For High Traffic
- **Use**: 2 CPUs, 2GB RAM
- **Cost**: ~$7.76/month
- **Database**: Fly Postgres (recommended)

## Alternative: Hybrid Approach

If Fly.io resources are insufficient:

1. **Fly.io for API**: Host API on Fly.io
2. **VPS for Scraper**: Run scraper on cheap VPS (Hetzner €4.51/month)
3. **Shared Database**: Use Fly Postgres or external Postgres

**Benefits**:
- API benefits from Fly.io's global edge network
- Scraper has dedicated resources on VPS
- Total cost: ~$8-10/month

## Conclusion

**Yes, Fly.io can handle the computational requirements**, but:

1. ✅ **Start with 2 CPUs, 1GB RAM** (minimum)
2. ✅ **Use sequential scraping** to reduce memory usage
3. ✅ **Use Fly Postgres** instead of SQLite
4. ✅ **Monitor resource usage** and scale up if needed
5. ✅ **Optimize code** for memory efficiency

**Recommended Configuration**:
- 2 shared CPUs
- 1-2GB RAM
- Fly Postgres database
- Sequential scraping
- **Total Cost**: ~$5-8/month

This configuration will comfortably handle:
- 9 real-time sources every 5 minutes
- 3 hourly sources
- 8 daily sources
- API serving dashboard requests


