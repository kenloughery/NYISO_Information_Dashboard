# Railway 502 "Connection Refused" Troubleshooting Guide

## Critical Check: Railway Service Settings

The "connection refused" error means Railway's proxy can't connect to your app. **Check these settings in Railway Dashboard:**

### 1. Target Port Configuration
1. Go to your Railway service
2. Click **Settings** → **Networking**
3. Verify **Target Port** matches the port your app listens on (usually `8080` or whatever `$PORT` is set to)
4. If it's wrong, set it to match your `PORT` environment variable

### 2. Health Check Configuration
1. Go to **Settings** → **Healthcheck**
2. **Path**: Should be `/health` or `/`
3. **Timeout**: Should be at least 30 seconds
4. **Interval**: 30 seconds is fine

### 3. Environment Variables
Verify these are set correctly:
- `PORT` - Railway sets this automatically (usually `8080`)
- `HOST` - Should be `0.0.0.0` (default if not set)

## What We Fixed

1. **Removed Invalid Uvicorn Parameters**: Some parameters like `timeout_keep_alive`, `limit_concurrency` might not be valid for `uvicorn.run()` and could cause silent failures
2. **Added Port Availability Check**: Verifies the port is available before starting
3. **Simplified Uvicorn Config**: Using only well-known, valid parameters

## Next Steps After Redeploy

1. **Check Logs**: Look for "Port X is available" message
2. **Test `/ping`**: Simplest endpoint - should return immediately
3. **Test `/health`**: Should return database status
4. **Check Railway Metrics**: Look for CPU/Memory spikes that might indicate crashes

## If Still Failing

The issue might be:
- **Railway Target Port Mismatch**: Most common cause - check Settings → Networking
- **App Crashing After Startup**: Check logs for exceptions after "Uvicorn running"
- **Resource Limits**: Check if you're hitting memory/CPU limits

