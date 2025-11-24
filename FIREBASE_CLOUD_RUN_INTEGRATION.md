# Firebase Hosting + Cloud Run Integration Guide

**How to connect your React frontend (Firebase Hosting) to your FastAPI backend (Cloud Run)**

---

## Overview

There are several ways to connect Firebase Hosting to Cloud Run:

1. **Direct API Calls** (Simplest) - React directly calls Cloud Run API
2. **Firebase Hosting Rewrites** (Recommended) - Proxy API calls through Firebase
3. **Firebase Functions Proxy** (Most Integrated) - Use Firebase Functions as API gateway
4. **Firestore Cache Layer** (Advanced) - Cache data in Firestore for real-time updates

---

## Option 1: Direct API Calls (Simplest) ⭐ **RECOMMENDED**

### How It Works

React makes HTTP requests directly to your Cloud Run API endpoint.

```
React App (Firebase Hosting) 
    ↓ HTTP Request
Cloud Run API (FastAPI)
    ↓ Response
React App (displays data)
```

### Setup

#### Step 1: Configure Environment Variable

**File**: `frontend/.env.production`

```env
VITE_API_BASE_URL=https://nyiso-api-XXXXX-uc.a.run.app
```

Replace `XXXXX` with your actual Cloud Run service URL.

#### Step 2: Update CORS in Backend

**File**: `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Get Firebase Hosting URLs from environment
FIREBASE_URLS = [
    "https://PROJECT_ID.web.app",
    "https://PROJECT_ID.firebaseapp.com",
    "http://localhost:3000",  # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FIREBASE_URLS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your existing routes...
```

#### Step 3: Deploy

```bash
# Backend (Cloud Run)
gcloud run deploy nyiso-api --image gcr.io/PROJECT_ID/nyiso-api

# Frontend (Firebase Hosting)
cd frontend
npm run build
firebase deploy --only hosting
```

### Pros
- ✅ **Simplest**: No additional setup
- ✅ **Direct**: No proxy overhead
- ✅ **Fast**: Direct connection to Cloud Run
- ✅ **Easy to debug**: Standard HTTP requests

### Cons
- ⚠️ **CORS**: Need to configure CORS properly
- ⚠️ **Two domains**: Frontend and API on different domains
- ⚠️ **No caching**: No built-in caching layer

---

## Option 2: Firebase Hosting Rewrites (Recommended) ⭐⭐

### How It Works

Firebase Hosting acts as a reverse proxy, forwarding API requests to Cloud Run. This makes it appear as if everything is on the same domain.

```
React App (Firebase Hosting)
    ↓ /api/* request
Firebase Hosting (rewrites to Cloud Run)
    ↓ Proxy request
Cloud Run API (FastAPI)
    ↓ Response
Firebase Hosting (forwards response)
React App (displays data)
```

### Setup

#### Step 1: Configure firebase.json

**File**: `frontend/firebase.json`

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "nyiso-api",
          "region": "us-central1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

**Note**: This requires Cloud Run service to be connected to Firebase Hosting.

#### Step 2: Connect Cloud Run to Firebase

```bash
# Get Cloud Run service URL
CLOUD_RUN_URL=$(gcloud run services describe nyiso-api --format 'value(status.url)')

# Connect Cloud Run to Firebase Hosting
firebase hosting:channel:deploy production \
  --only hosting \
  --config firebase.json
```

#### Step 3: Update Frontend Config

**File**: `frontend/src/constants/config.ts`

```typescript
// Use relative URLs - Firebase will proxy to Cloud Run
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
```

**File**: `frontend/.env.production`

```env
# Empty or use relative path
VITE_API_BASE_URL=/api
```

### Pros
- ✅ **Same domain**: All requests appear from same origin
- ✅ **No CORS**: No CORS issues
- ✅ **Simpler config**: Frontend uses relative URLs
- ✅ **Built-in**: Uses Firebase's built-in proxy

### Cons
- ⚠️ **Setup**: Requires connecting Cloud Run to Firebase
- ⚠️ **Latency**: Slight proxy overhead

---

## Option 3: Firebase Functions Proxy (Most Integrated) ⭐⭐⭐

### How It Works

Use Firebase Functions as an API gateway that calls your Cloud Run service. This provides the most integration and allows for additional features like caching, authentication, rate limiting, etc.

```
React App (Firebase Hosting)
    ↓ /api/* request
Firebase Functions (proxy)
    ↓ HTTP call
Cloud Run API (FastAPI)
    ↓ Response
Firebase Functions (process/cache)
React App (displays data)
```

### Setup

#### Step 1: Create Firebase Function

**File**: `functions/index.js`

```javascript
const functions = require('firebase-functions');
const { onRequest } = require('firebase-functions/v2/https');
const axios = require('axios');

// Your Cloud Run URL
const CLOUD_RUN_URL = 'https://nyiso-api-XXXXX-uc.a.run.app';

// Proxy all API requests to Cloud Run
exports.api = onRequest(
  {
    cors: true,
    maxInstances: 10,
  },
  async (req, res) => {
    try {
      // Forward request to Cloud Run
      const response = await axios({
        method: req.method,
        url: `${CLOUD_RUN_URL}${req.path}`,
        data: req.body,
        headers: {
          ...req.headers,
          host: undefined, // Remove host header
        },
        params: req.query,
      });

      // Forward response
      res.status(response.status).json(response.data);
    } catch (error) {
      console.error('Proxy error:', error);
      res.status(500).json({ error: 'Proxy error' });
    }
  }
);
```

#### Step 2: Initialize Firebase Functions

```bash
cd functions
npm init -y
npm install firebase-functions axios
```

**File**: `functions/package.json`

```json
{
  "name": "functions",
  "engines": {
    "node": "18"
  },
  "main": "index.js",
  "dependencies": {
    "firebase-functions": "^4.0.0",
    "axios": "^1.6.0"
  }
}
```

#### Step 3: Configure firebase.json

**File**: `firebase.json`

```json
{
  "hosting": {
    "public": "frontend/dist",
    "rewrites": [
      {
        "source": "/api/**",
        "function": "api"
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  },
  "functions": {
    "source": "functions"
  }
}
```

#### Step 4: Deploy

```bash
# Deploy functions
firebase deploy --only functions

# Deploy frontend
cd frontend
npm run build
firebase deploy --only hosting
```

#### Step 5: Update Frontend Config

**File**: `frontend/src/constants/config.ts`

```typescript
// Use relative URLs - Firebase Functions will handle
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
```

### Advanced: Add Caching

**File**: `functions/index.js` (Enhanced with caching)

```javascript
const functions = require('firebase-functions');
const { onRequest } = require('firebase-functions/v2/https');
const axios = require('axios');
const NodeCache = require('node-cache');

const CLOUD_RUN_URL = 'https://nyiso-api-XXXXX-uc.a.run.app';
const cache = new NodeCache({ stdTTL: 300 }); // 5 minute cache

exports.api = onRequest(
  {
    cors: true,
    maxInstances: 10,
  },
  async (req, res) => {
    // Check cache for GET requests
    if (req.method === 'GET') {
      const cacheKey = `${req.path}?${new URLSearchParams(req.query).toString()}`;
      const cached = cache.get(cacheKey);
      
      if (cached) {
        return res.json(cached);
      }
    }

    try {
      const response = await axios({
        method: req.method,
        url: `${CLOUD_RUN_URL}${req.path}`,
        data: req.body,
        headers: {
          ...req.headers,
          host: undefined,
        },
        params: req.query,
      });

      // Cache GET responses
      if (req.method === 'GET') {
        const cacheKey = `${req.path}?${new URLSearchParams(req.query).toString()}`;
        cache.set(cacheKey, response.data);
      }

      res.status(response.status).json(response.data);
    } catch (error) {
      console.error('Proxy error:', error);
      res.status(500).json({ error: 'Proxy error' });
    }
  }
);
```

### Pros
- ✅ **Most integrated**: Everything in Firebase ecosystem
- ✅ **Additional features**: Can add caching, auth, rate limiting
- ✅ **Same domain**: No CORS issues
- ✅ **Flexible**: Can transform requests/responses

### Cons
- ⚠️ **Complexity**: More moving parts
- ⚠️ **Cost**: Firebase Functions have usage costs
- ⚠️ **Latency**: Additional hop through Functions

---

## Option 4: Firestore Cache Layer (Advanced)

### How It Works

Use Firestore as a real-time cache layer. Cloud Run writes to Firestore, and React listens to Firestore changes in real-time.

```
Cloud Run API (FastAPI)
    ↓ Writes data
Firestore Database
    ↓ Real-time updates
React App (listens to Firestore)
```

### Setup

This requires modifying your backend to write to Firestore. See Firebase documentation for details.

**Note**: This is more complex and may not be necessary for your use case.

---

## Recommended Approach

### For Your Use Case: **Option 1 (Direct API Calls)** or **Option 2 (Firebase Rewrites)**

**Why**:
- ✅ Simple to set up
- ✅ Low latency
- ✅ Cost-effective
- ✅ Easy to maintain

**Choose Option 1 if**:
- You want the simplest setup
- You don't mind configuring CORS
- You want direct connection to Cloud Run

**Choose Option 2 if**:
- You want same-domain requests
- You want to avoid CORS issues
- You want cleaner frontend code (relative URLs)

---

## Complete Setup Example (Option 1 - Direct API)

### Step 1: Get Cloud Run URL

```bash
# Get your Cloud Run service URL
CLOUD_RUN_URL=$(gcloud run services describe nyiso-api \
  --region us-central1 \
  --format 'value(status.url)')

echo "Cloud Run URL: ${CLOUD_RUN_URL}"
```

### Step 2: Update Frontend Environment

**File**: `frontend/.env.production`

```env
VITE_API_BASE_URL=https://nyiso-api-XXXXX-uc.a.run.app
```

### Step 3: Update Backend CORS

**File**: `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'https://PROJECT_ID.web.app,https://PROJECT_ID.firebaseapp.com,http://localhost:3000'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your existing routes...
```

### Step 4: Set Environment Variable in Cloud Run

```bash
# Set allowed origins in Cloud Run
gcloud run services update nyiso-api \
  --set-env-vars "ALLOWED_ORIGINS=https://PROJECT_ID.web.app,https://PROJECT_ID.firebaseapp.com" \
  --region us-central1
```

### Step 5: Build and Deploy Frontend

```bash
cd frontend

# Build with production API URL
npm run build

# Deploy to Firebase
firebase deploy --only hosting
```

### Step 6: Test

```bash
# Test API from command line
curl https://nyiso-api-XXXXX-uc.a.run.app/api/stats

# Test from browser
# Open https://PROJECT_ID.web.app
# Check browser console for API calls
```

---

## Troubleshooting

### CORS Errors

**Error**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution**:
1. Check `ALLOWED_ORIGINS` in Cloud Run
2. Verify Firebase Hosting URLs are included
3. Check backend CORS middleware is configured

```bash
# Check current environment variables
gcloud run services describe nyiso-api --format 'value(spec.template.spec.containers[0].env)'
```

### API Not Responding

**Error**: `Failed to fetch` or `Network error`

**Solution**:
1. Verify Cloud Run service is running
2. Check Cloud Run URL is correct
3. Verify API endpoint exists

```bash
# Check Cloud Run service status
gcloud run services describe nyiso-api --region us-central1

# Test API endpoint
curl https://nyiso-api-XXXXX-uc.a.run.app/api/stats
```

### Environment Variable Not Working

**Error**: Frontend still using localhost API

**Solution**:
1. Rebuild frontend after changing `.env.production`
2. Clear browser cache
3. Verify environment variable is set

```bash
# Rebuild frontend
cd frontend
rm -rf dist
npm run build

# Verify build includes correct URL
grep -r "localhost:8000" dist/ || echo "No localhost found - good!"
```

---

## Quick Reference

### Direct API Calls (Option 1)

```typescript
// frontend/src/constants/config.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// frontend/.env.production
VITE_API_BASE_URL=https://nyiso-api-XXXXX-uc.a.run.app
```

### Firebase Rewrites (Option 2)

```json
// firebase.json
{
  "hosting": {
    "rewrites": [
      { "source": "/api/**", "run": { "serviceId": "nyiso-api", "region": "us-central1" } }
    ]
  }
}
```

```typescript
// frontend/src/constants/config.ts
export const API_BASE_URL = '/api'; // Relative URL
```

---

## Cost Comparison

| Option | Additional Cost | Latency | Complexity |
|--------|----------------|---------|------------|
| **Direct API** | $0 | Low | Low |
| **Firebase Rewrites** | $0 | Low-Medium | Medium |
| **Firebase Functions** | ~$0.40/million invocations | Medium | High |

---

**Recommendation**: Start with **Option 1 (Direct API Calls)** for simplicity, then move to **Option 2 (Firebase Rewrites)** if you want same-domain requests.



