# Railway Deployment Checklist & Troubleshooting

## ✅ Recent Fixes (Must be deployed)

Ensure your deployment includes these critical fixes:

1.  **Scheduler Delay (30s)**: Prevents "Connection Refused" (502) errors by delaying heavy scraping until *after* the API starts.
2.  **Frontend API URL**: Sets API URL to relative (`''`) in production so the frontend connects to the backend correctly.
3.  **SQLite Timeout**: Increased to 30s to prevent database locking errors.
4.  **Health Check**: Always returns 200 OK to keep Railway happy, even if the database is initializing.

## 🔍 How to Verify Fixes

Check your Railway deployment logs for these specific messages:

### 1. Verify Scheduler Delay
Look for:
```
Waiting 30s before starting scheduler to allow API startup...
```
*If you don't see this, you are running old code. Redeploy!*

### 2. Verify Frontend Configuration
Look for:
```
Frontend File Serving Configuration
Static directory exists: True
Index.html exists: True
```

### 3. Verify Database
Look for:
```
Database URL: sqlite:////app/data/nyiso_data.db
Database schema initialized successfully
Database connection verified successfully
```

## 🚨 Troubleshooting 502 Errors

If 502 errors persist:

1.  **Check Logs**: Do you see "Uvicorn running on http://0.0.0.0:8080"?
2.  **Wait**: The first 30-60 seconds might be slow due to initial data scraping (after the 30s delay).
3.  **Health Check**: Ensure Railway shows the service as "Active".
4.  **Redeploy**: Sometimes a fresh build is needed to clear specific Docker caching issues.

## 🛠 Frontend Connection

The frontend is now configured to use **relative URLs** in production. This means:
- It automatically connects to the backend on the same domain.
- No CORS configuration is needed.
- No hardcoded `localhost` or IP addresses.

If the site loads but shows "Network Error":
- Check the browser console (F12).
- Ensure API requests go to `/api/...` (e.g., `https://your-app.railway.app/api/zones`).

