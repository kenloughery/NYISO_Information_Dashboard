# NYISO Data API

REST API for accessing NYISO market data for dashboard consumption.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start the API server:**
```bash
python start_api.py
```

The API will be available at `http://localhost:8000`

3. **View API documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Zones
- `GET /api/zones` - Get all zones

### Real-Time LBMP
- `GET /api/realtime-lbmp` - Get real-time locational marginal pricing
  - Query parameters:
    - `start_date` (optional): ISO format datetime
    - `end_date` (optional): ISO format datetime
    - `zones` (optional): Comma-separated zone names (e.g., "CAPITL,CENTRL")
    - `limit` (optional): Max records (default: 1000, max: 10000)

### Day-Ahead LBMP
- `GET /api/dayahead-lbmp` - Get day-ahead locational marginal pricing
  - Same query parameters as real-time LBMP

### Real-Time Load
- `GET /api/realtime-load` - Get real-time actual load
  - Same query parameters as real-time LBMP

### Load Forecast
- `GET /api/load-forecast` - Get ISO load forecast
  - Same query parameters as real-time LBMP

### Interface Flows
- `GET /api/interface-flows` - Get interface limits and flows
  - Query parameters:
    - `start_date`, `end_date`, `limit` (same as above)
    - `interfaces` (optional): Comma-separated interface names

### Statistics
- `GET /api/stats` - Get database statistics and metadata

### Health Check
- `GET /health` - Check API and database connectivity

## Example Requests

### Get real-time LBMP for specific zones
```bash
curl "http://localhost:8000/api/realtime-lbmp?zones=CAPITL,CENTRL&limit=100"
```

### Get day-ahead LBMP for date range
```bash
curl "http://localhost:8000/api/dayahead-lbmp?start_date=2025-11-10T00:00:00&end_date=2025-11-13T23:59:59"
```

### Get all zones
```bash
curl "http://localhost:8000/api/zones"
```

### Get database statistics
```bash
curl "http://localhost:8000/api/stats"
```

## React Integration Example

```javascript
// Fetch real-time LBMP data
const fetchRealTimeLBMP = async (zones, startDate, endDate) => {
  const params = new URLSearchParams({
    zones: zones.join(','),
    limit: '1000'
  });
  
  if (startDate) params.append('start_date', startDate.toISOString());
  if (endDate) params.append('end_date', endDate.toISOString());
  
  const response = await fetch(`http://localhost:8000/api/realtime-lbmp?${params}`);
  return await response.json();
};

// Fetch zones
const fetchZones = async () => {
  const response = await fetch('http://localhost:8000/api/zones');
  return await response.json();
};

// Usage in React component
const MyComponent = () => {
  const [data, setData] = useState([]);
  const [zones, setZones] = useState([]);
  
  useEffect(() => {
    // Load zones
    fetchZones().then(setZones);
    
    // Load LBMP data
    fetchRealTimeLBMP(['CAPITL', 'CENTRL'], new Date('2025-11-10'), new Date('2025-11-13'))
      .then(setData);
  }, []);
  
  return (
    <div>
      {/* Render your dashboard */}
    </div>
  );
};
```

## Response Format

All endpoints return JSON arrays of objects. Example response:

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

## CORS Configuration

The API is configured to allow CORS from all origins (for development). In production, update the `allow_origins` in `api/main.py` to specify your React app's URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    ...
)
```

## Production Deployment

For production, use a production ASGI server:

```bash
# Using gunicorn with uvicorn workers
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or directly with uvicorn (for smaller deployments)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable (database connection issues)

Error responses include a `detail` field with error information.

## Performance Considerations

- Default limit is 1000 records (max 10000)
- Use date ranges to limit query scope
- Filter by zones/interfaces to reduce data transfer
- Consider implementing pagination for large datasets
- Database indexes are in place for timestamp queries

## Security Notes

- No authentication is currently implemented (add as needed)
- Input validation is handled by FastAPI/Pydantic
- SQL injection is prevented by SQLAlchemy ORM
- In production, add rate limiting and authentication

