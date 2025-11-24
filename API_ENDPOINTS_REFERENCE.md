# NYISO Data API - Complete Endpoint Reference

**Last Updated**: 2025-11-22  
**API Version**: 1.0.0  
**Base URL**: `http://localhost:8000`

## Overview

The NYISO Data API provides comprehensive access to real-time and historical NYISO market data through RESTful endpoints. All endpoints support filtering, pagination, and return JSON responses.

## Endpoint Categories

### Reference Data
- `GET /api/zones` - Get all zones
- `GET /api/interfaces` - Get all interfaces
- `GET /api/stats` - Get database statistics

### Priority 1 - Core Trading Data

#### 1. Market Advisories
**Endpoint**: `GET /api/market-advisories`

**Description**: Market advisory notifications and HAM energy reports.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (default: 100): Maximum records to return (1-1000)

**Response**: Array of advisory objects with timestamp, advisory_type, title, message, severity

**Example**:
```bash
GET /api/market-advisories?start_date=2025-11-13T00:00:00&limit=10
```

#### 2. Constraints
**Endpoint**: `GET /api/constraints`

**Description**: Real-time and day-ahead transmission constraints.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `market_type` (optional): Filter by 'realtime' or 'dayahead'
- `constraint_name` (optional): Filter by constraint name
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of constraint objects with timestamp, constraint_name, market_type, shadow_price, binding_status, limit_mw, flow_mw

**Example**:
```bash
GET /api/constraints?market_type=realtime&limit=50
```

#### 3. Time-Weighted LBMP
**Endpoint**: `GET /api/timeweighted-lbmp`

**Description**: Hourly time-weighted/integrated real-time LBMP data.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `zones` (optional): Comma-separated zone names
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of LBMP objects with timestamp, zone_name, lbmp, marginal_cost_losses, marginal_cost_congestion

**Example**:
```bash
GET /api/timeweighted-lbmp?zones=WEST,NYC&limit=100
```

#### 4. Ancillary Services
**Endpoint**: `GET /api/ancillary-services`

**Description**: Real-time and day-ahead ancillary service prices.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `market_type` (optional): Filter by 'realtime' or 'dayahead'
- `zones` (optional): Comma-separated zone names
- `service_type` (optional): Filter by service type
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of service objects with timestamp, zone_name, market_type, service_type, price

**Example**:
```bash
GET /api/ancillary-services?market_type=realtime&service_type=regulation
```

### Priority 2 - Market Intelligence

#### 5. External RTO Prices
**Endpoint**: `GET /api/external-rto-prices`

**Description**: Inter-ISO price differentials (RTC vs External RTO CTS Prices).

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `rto_name` (optional): Filter by RTO name (e.g., 'PJM', 'ISO-NE')
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of price objects with timestamp, rto_name, rtc_price, cts_price, price_difference

#### 6. ATC/TTC
**Endpoint**: `GET /api/atc-ttc`

**Description**: Available Transfer Capability / Total Transfer Capability.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `forecast_type` (optional): Filter by 'short_term' or 'long_term'
- `interface_name` (optional): Filter by interface name
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of ATC/TTC objects with timestamp, interface_name, forecast_type, atc_mw, ttc_mw, trm_mw, direction

#### 7. Outages
**Endpoint**: `GET /api/outages`

**Description**: Generator and transmission outages.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `outage_type` (optional): Filter by type (scheduled, actual, maintenance)
- `market_type` (optional): Filter by 'realtime' or 'dayahead'
- `resource_type` (optional): Filter by resource type
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of outage objects with timestamp, outage_type, market_type, resource_name, resource_type, mw_capacity, mw_outage, start_time, end_time, status

#### 8. Weather Forecast
**Endpoint**: `GET /api/weather-forecast`

**Description**: Weather forecast data used for load forecasting.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `location` (optional): Filter by location
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of weather objects with timestamp, forecast_time, location, temperature_f, humidity_percent, wind_speed_mph, wind_direction, cloud_cover_percent

#### 9. Fuel Mix
**Endpoint**: `GET /api/fuel-mix`

**Description**: Real-time generation by fuel type.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `fuel_type` (optional): Filter by fuel type
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of fuel mix objects with timestamp, fuel_type, generation_mw, percentage

### Priority 3 - Calculated Metrics

#### 10. RT-DA Spreads
**Endpoint**: `GET /api/rt-da-spreads`

**Description**: Calculated RT-DA price spreads by zone.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `zones` (optional): Comma-separated zone names
- `min_spread` (optional): Minimum spread threshold ($/MWh)
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of spread objects with timestamp, zone_name, rt_lbmp, da_lbmp, spread, spread_percent

**Calculation**: `spread = rt_lbmp - da_lbmp`

**Example**:
```bash
GET /api/rt-da-spreads?min_spread=10&zones=WEST,NYC
```

#### 11. Zone Spreads
**Endpoint**: `GET /api/zone-spreads`

**Description**: Intra-zonal price differentials (max zone price - min zone price per timestamp).

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `include_all_zones` (default: false): Include all zone prices in response
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of spread objects with timestamp, max_zone, min_zone, max_price, min_price, spread, all_zones (optional)

**Calculation**: `spread = max(zone_prices) - min(zone_prices)`

#### 12. Load Forecast Errors
**Endpoint**: `GET /api/load-forecast-errors`

**Description**: Forecast vs actual load deviations.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `zones` (optional): Comma-separated zone names
- `max_error_percent` (optional): Maximum error percentage threshold
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of error objects with timestamp, zone_name, actual_load, forecast_load, error_mw, error_percent

**Calculation**: `error_mw = actual_load - forecast_load`, `error_percent = (error_mw / forecast_load) * 100`

#### 13. Reserve Margins
**Endpoint**: `GET /api/reserve-margins`

**Description**: Calculated reserve margins (generation capacity - load).

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of margin objects with timestamp, total_load, total_generation, reserve_margin_mw, reserve_margin_percent, zones

**Calculation**: `reserve_margin_mw = total_generation - total_load`, `reserve_margin_percent = (reserve_margin_mw / total_load) * 100`

#### 14. Price Volatility
**Endpoint**: `GET /api/price-volatility`

**Description**: Rolling price volatility metrics.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `zones` (optional): Comma-separated zone names
- `window_hours` (default: 24): Rolling window size in hours (1-168)
- `limit` (default: 1000): Maximum records to return (1-10000)

**Response**: Array of volatility objects with timestamp, zone_name, volatility, window_hours, mean_price, std_dev

**Calculation**: Rolling standard deviation of prices over the specified window, expressed as percentage of mean price.

#### 15. Correlations
**Endpoint**: `GET /api/correlations`

**Description**: Zone-to-zone price correlations.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `zones` (optional): Comma-separated zone names (default: all)
- `limit` (default: 100): Maximum zone pairs to return (1-500)

**Response**: Array of correlation objects with zone1, zone2, correlation, sample_count, period_start, period_end

**Calculation**: Pearson correlation coefficient between zone prices over the time period.

**Example**:
```bash
GET /api/correlations?zones=WEST,NYC,LONGIL&limit=20
```

#### 16. Trading Signals
**Endpoint**: `GET /api/trading-signals`

**Description**: Rule-based trading alerts generated from market conditions.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `signal_type` (optional): Filter by signal type (rt_da_spread, load_forecast_error, low_reserve_margin)
- `severity` (optional): Filter by severity (low, medium, high)
- `limit` (default: 100): Maximum signals to return (1-1000)

**Response**: Array of signal objects with timestamp, signal_type, severity, zone_name, message, value, threshold

**Signal Types**:
- `rt_da_spread`: RT-DA spread >= $15/MWh (high if >= $25/MWh)
- `load_forecast_error`: Load forecast error >= 5% (high if >= 10%)
- `low_reserve_margin`: Reserve margin < 10% (high if < 5%)

**Example**:
```bash
GET /api/trading-signals?severity=high&limit=50
```

## Standard Endpoints

### Real-Time Data
- `GET /api/realtime-lbmp` - Real-time LBMP (5-minute intervals)
- `GET /api/realtime-load` - Real-time actual load (5-minute intervals)

### Day-Ahead Data
- `GET /api/dayahead-lbmp` - Day-ahead LBMP (hourly)

### Forecast Data
- `GET /api/load-forecast` - ISO load forecast (7-day, hourly)

### Interface Data
- `GET /api/interface-flows` - Interface limits and flows (5-minute intervals)
- `GET /api/interregional-flows` - Interregional flows for external interfaces (PJM, ISO-NE, IESO, HQ)

#### Interregional Flows
**Endpoint**: `GET /api/interregional-flows`

**Description**: Real-time interregional flow data for external interfaces. Returns all interfaces separately to show individual locational price deltas. Each interface represents a different physical connection point between NYISO and neighboring RTOs.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (default: 100): Maximum records to return (1-1000)

**Response**: Array of interregional flow objects with:
- `timestamp`: Data timestamp
- `interface_name`: Full interface name (e.g., "SCH - PJM_HTP")
- `region`: Region identifier ("PJM", "ISO-NE", "IESO", "HQ")
- `node_name`: Specific node/connection (e.g., "HTP", "NEPTUNE", "VFT" for PJM)
- `flow_mw`: Flow in MW (positive = import, negative = export)
- `direction`: Flow direction ("import", "export", "zero")
- `positive_limit_mw`: Import limit (positive)
- `negative_limit_mw`: Export limit (negative)
- `utilization_percent`: Utilization percentage (0-100) based on flow direction

**Note**: Returns latest data by default if no date filters are provided. All external interfaces are returned separately (no aggregation) to preserve individual locational price deltas.

**Example**:
```bash
GET /api/interregional-flows
GET /api/interregional-flows?start_date=2025-11-21T00:00:00
```

**Response Example**:
```json
[
  {
    "timestamp": "2025-11-21T15:55:00",
    "interface_name": "SCH - PJM_HTP",
    "region": "PJM",
    "node_name": "HTP",
    "flow_mw": 200.0,
    "direction": "import",
    "positive_limit_mw": 660.0,
    "negative_limit_mw": -660.0,
    "utilization_percent": 30.3
  },
  {
    "timestamp": "2025-11-21T15:55:00",
    "interface_name": "SCH - NE - NY",
    "region": "ISO-NE",
    "node_name": "NE - NY",
    "flow_mw": -897.9,
    "direction": "export",
    "positive_limit_mw": 1100.0,
    "negative_limit_mw": -1100.0,
    "utilization_percent": 81.6
  }
]
```

## Response Format

All endpoints return JSON arrays of objects. Each object follows the response model defined in the endpoint documentation.

### Error Responses

- `400 Bad Request`: Invalid query parameters
- `404 Not Found`: Endpoint not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Database connection failed

### Pagination

All endpoints support the `limit` parameter to control the maximum number of records returned. Results are ordered by timestamp (descending) by default.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Rate Limiting

Currently no rate limiting is implemented. In production, consider implementing rate limiting based on your usage patterns.

## CORS

CORS is enabled for all origins (`*`). In production, restrict this to your frontend domain.

## Analytics

### Analytics Summary
**Endpoint**: `GET /api/analytics/summary`

**Description**: Get website analytics summary including page views, unique visitors, sessions, and top pages.

**Query Parameters**:
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `days` (default: 30): Number of days to analyze (if dates not provided, 1-365)

**Response**: Analytics summary object with:
- `total_page_views`: Total page views in period
- `unique_visitors`: Number of unique visitors (by IP hash)
- `sessions`: Number of visitor sessions
- `page_views_today`: Page views today
- `unique_visitors_today`: Unique visitors today
- `top_pages`: Array of top pages with view counts
- `referrers`: Array of top referrers with view counts
- `countries`: Array of top countries with view counts

**Example**:
```bash
GET /api/analytics/summary
GET /api/analytics/summary?days=7
GET /api/analytics/summary?start_date=2025-11-01T00:00:00&end_date=2025-11-30T23:59:59
```

**Response Example**:
```json
{
  "total_page_views": 1250,
  "unique_visitors": 45,
  "sessions": 67,
  "page_views_today": 23,
  "unique_visitors_today": 8,
  "top_pages": [
    {"path": "/", "views": 450},
    {"path": "/dashboard", "views": 320}
  ],
  "referrers": [
    {"referrer": "https://google.com", "views": 120},
    {"referrer": "https://example.com", "views": 45}
  ],
  "countries": []
}
```

**Privacy Note**: IP addresses are hashed for privacy. No personal data is collected.

---

## Health Check

**Endpoint**: `GET /health`

Returns API health status and database connection status.

**Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

