# Dashboard Architecture - API Layer

## Overview

A REST API layer has been added to expose NYISO data for React dashboard consumption. The API is built with **FastAPI**, providing automatic documentation, type validation, and async support.

## Architecture Addition

```
┌─────────────┐
│   React     │  Dashboard Frontend
│  Dashboard  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│  FastAPI    │  REST API Layer (NEW)
│    API      │  - Endpoints for all data types
│             │  - Query parameters (date ranges, zones)
│             │  - CORS enabled
└──────┬──────┘
       │ SQLAlchemy ORM
       ▼
┌─────────────┐
│  Database   │  SQLite/PostgreSQL
│  (SQLite)   │  - Time-series data
│             │  - Reference tables
└─────────────┘
```

## API Endpoints

### Data Endpoints

1. **`GET /api/zones`** - Get all zones
2. **`GET /api/interfaces`** - Get all interfaces
3. **`GET /api/realtime-lbmp`** - Real-time LBMP data
4. **`GET /api/dayahead-lbmp`** - Day-ahead LBMP data
5. **`GET /api/realtime-load`** - Real-time load data
6. **`GET /api/load-forecast`** - Load forecast data
7. **`GET /api/interface-flows`** - Interface flow data
8. **`GET /api/stats`** - Database statistics

### Utility Endpoints

- **`GET /`** - API information
- **`GET /health`** - Health check

## Query Parameters

All data endpoints support:

- `start_date` (ISO datetime): Filter from date
- `end_date` (ISO datetime): Filter to date
- `zones` (comma-separated): Filter by zone names
- `limit` (1-10000): Maximum records (default: 1000)

Example:
```
GET /api/realtime-lbmp?zones=CAPITL,CENTRL&start_date=2025-11-10T00:00:00&limit=500
```

## Features

### Robustness

1. **Database Connection Management**
   - Proper session handling with try/finally
   - Automatic connection cleanup
   - Health check endpoint

2. **Error Handling**
   - HTTP status codes (200, 400, 500, 503)
   - Detailed error messages
   - Database connection failure detection

3. **Input Validation**
   - Pydantic models for request/response validation
   - Query parameter validation (limits, date formats)
   - Type safety with FastAPI

4. **Performance**
   - Query limits to prevent large responses
   - Indexed database queries
   - Efficient joins with SQLAlchemy

### CORS Support

CORS middleware configured for React frontend:
- Allows all origins (development)
- Configurable for production
- Supports all HTTP methods

### Automatic Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- Interactive API testing

## Usage

### Start API Server

```bash
python start_api.py
```

Or directly:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### React Integration Example

```javascript
// api.js
const API_BASE = 'http://localhost:8000';

export const fetchRealTimeLBMP = async (zones, startDate, endDate) => {
  const params = new URLSearchParams({
    zones: zones.join(','),
    limit: '1000'
  });
  
  if (startDate) params.append('start_date', startDate.toISOString());
  if (endDate) params.append('end_date', endDate.toISOString());
  
  const response = await fetch(`${API_BASE}/api/realtime-lbmp?${params}`);
  if (!response.ok) throw new Error('API request failed');
  return await response.json();
};

export const fetchZones = async () => {
  const response = await fetch(`${API_BASE}/api/zones`);
  return await response.json();
};

// Component.jsx
import { useEffect, useState } from 'react';
import { fetchRealTimeLBMP, fetchZones } from './api';

const Dashboard = () => {
  const [data, setData] = useState([]);
  const [zones, setZones] = useState([]);
  
  useEffect(() => {
    const loadData = async () => {
      const zoneList = await fetchZones();
      setZones(zoneList);
      
      const lbmpData = await fetchRealTimeLBMP(
        ['CAPITL', 'CENTRL'],
        new Date('2025-11-10'),
        new Date('2025-11-13')
      );
      setData(lbmpData);
    };
    
    loadData();
  }, []);
  
  return (
    <div>
      {/* Render charts, tables, etc. */}
    </div>
  );
};
```

## Response Format

All endpoints return JSON arrays:

```json
[
  {
    "timestamp": "2025-11-13T12:00:00",
    "zone_name": "CAPITL",
    "lbmp": 52.42,
    "marginal_cost_losses": 1.58,
    "marginal_cost_congestion": 0.0
  }
]
```

## Production Considerations

### Security

1. **CORS Configuration**
   - Update `allow_origins` in `api/main.py` to your React app URL
   - Remove wildcard `*` in production

2. **Authentication** (Optional)
   - Add API key authentication
   - JWT tokens for user sessions
   - Rate limiting

3. **HTTPS**
   - Use reverse proxy (nginx) with SSL
   - Or deploy to cloud with HTTPS

### Performance

1. **Caching**
   - Add Redis for frequently accessed data
   - Cache zone/interfaces lists
   - Cache statistics

2. **Pagination**
   - Implement cursor-based pagination for large datasets
   - Add `offset` and `limit` parameters

3. **Database Optimization**
   - Connection pooling (already in SQLAlchemy)
   - Query optimization for date ranges
   - Consider read replicas for high traffic

### Monitoring

1. **Health Checks**
   - Use `/health` endpoint for monitoring
   - Set up alerts for 503 responses

2. **Logging**
   - Add structured logging
   - Track API usage metrics
   - Error tracking (Sentry, etc.)

## File Structure

```
api/
├── __init__.py
└── main.py          # FastAPI application

start_api.py        # Server startup script
API_README.md       # Detailed API documentation
```

## Next Steps for Dashboard Development

1. **Create React App**
   ```bash
   npx create-react-app nyiso-dashboard
   cd nyiso-dashboard
   ```

2. **Install Charting Library**
   ```bash
   npm install recharts  # or chart.js, d3, etc.
   ```

3. **Create API Client**
   - Create `src/api.js` with fetch functions
   - Handle errors and loading states

4. **Build Components**
   - Zone selector dropdown
   - Date range picker
   - Time-series charts
   - Data tables

5. **Add Real-time Updates** (Optional)
   - WebSocket support
   - Polling for latest data
   - Server-sent events

## Testing the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test zones endpoint
curl http://localhost:8000/api/zones

# Test real-time LBMP
curl "http://localhost:8000/api/realtime-lbmp?zones=CAPITL&limit=10"

# Test stats
curl http://localhost:8000/api/stats
```

## Summary

The API layer provides:
- ✅ Simple REST interface for all data types
- ✅ Robust error handling and validation
- ✅ CORS support for React
- ✅ Automatic documentation
- ✅ Production-ready architecture
- ✅ Easy to extend with new endpoints

The architecture is now complete for dashboard development!

