# Firebase Complete Integrated Setup Guide

**Deploy Backend + Database + Frontend + Scheduler all on Firebase**

---

## Overview

This guide shows how to deploy your entire NYISO Dashboard on Firebase:
- **Frontend**: Firebase Hosting (React)
- **Backend**: Cloud Functions (FastAPI via proxy or native)
- **Database**: Firestore or Cloud SQL
- **Scheduler**: Cloud Scheduler → Cloud Functions

**All integrated, all in one platform!**

---

## Prerequisites

1. **Firebase Account**: Sign up at [firebase.google.com](https://firebase.google.com)
2. **Node.js 18+**: For Firebase CLI
3. **Python 3.11+**: For backend (if using Python functions)

---

## Step 1: Initialize Firebase Project

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize project in your repo root
firebase init

# Select:
# ✅ Hosting: Configure files for Firebase Hosting
# ✅ Functions: Configure a Cloud Functions directory
# ✅ Firestore: Set up security rules and indexes files
# ✅ Storage: Set up Cloud Storage
```

This creates:
- `firebase.json` - Configuration
- `.firebaserc` - Project settings
- `functions/` - Cloud Functions directory
- `firestore.rules` - Database security rules
- `firestore.indexes.json` - Database indexes

---

## Step 2: Set Up Backend (Cloud Functions)

### Option A: Proxy to Cloud Run (Recommended - Keep FastAPI)

This keeps your existing FastAPI code on Cloud Run but routes through Firebase Functions for integration.

**File**: `functions/package.json`

```json
{
  "name": "functions",
  "engines": {
    "node": "18"
  },
  "main": "index.js",
  "dependencies": {
    "firebase-admin": "^12.0.0",
    "firebase-functions": "^4.5.0",
    "axios": "^1.6.0"
  }
}
```

**File**: `functions/index.js`

```javascript
const {onRequest} = require('firebase-functions/v2/https');
const axios = require('axios');

// Your Cloud Run URL (set as environment variable)
const CLOUD_RUN_URL = process.env.CLOUD_RUN_URL;

// API proxy function
exports.api = onRequest(
  {
    cors: true,
    memory: '512MiB',
    timeoutSeconds: 300,
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
      console.error('Proxy error:', error.message);
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data,
      });
    }
  }
);
```

**Set Environment Variable**:

```bash
# After deploying Cloud Run, get URL
CLOUD_RUN_URL=$(gcloud run services describe nyiso-api --format 'value(status.url)')

# Set in Firebase Functions
firebase functions:config:set cloud_run.url="${CLOUD_RUN_URL}"

# Or use .env file (Firebase Functions v2)
echo "CLOUD_RUN_URL=${CLOUD_RUN_URL}" > functions/.env
```

### Option B: Run FastAPI in Cloud Functions (Advanced)

If you want everything in Firebase, you can run FastAPI directly in Cloud Functions using Python runtime.

**File**: `functions/requirements.txt`

```
fastapi>=0.104.0
mangum>=0.17.0
uvicorn>=0.24.0
# ... copy rest from your main requirements.txt
```

**File**: `functions/main.py`

```python
from fastapi import FastAPI
from mangum import Mangum
import sys
import os

# Add parent directory to path to import your API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing FastAPI app
from api.main import app

# Wrap for Cloud Functions
handler = Mangum(app, lifespan="off")
```

**File**: `functions/index.js`

```javascript
const {onRequest} = require('firebase-functions/v2/https');
const {PythonRuntime} = require('firebase-functions/v2');

exports.api = onRequest(
  {
    runtime: PythonRuntime.PYTHON_311,
    memory: '1GiB',
    timeoutSeconds: 300,
    cors: true,
  },
  async (req, res) => {
    const {handler} = require('./main');
    return handler(req, res);
  }
);
```

**Note**: This is more complex. Option A (proxy) is recommended.

---

## Step 3: Set Up Database

### Option A: Firestore (NoSQL - Easier)

Firestore is automatically set up with `firebase init`.

**File**: `firestore.rules`

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write for authenticated users
    // Or make public for your use case
    match /{document=**} {
      allow read, write: if true; // Public access (adjust for production)
    }
  }
}
```

**File**: `api/main.py` (Connect to Firestore)

```python
from google.cloud import firestore
import os

# Initialize Firestore client
db = firestore.Client()

# Example: Store LBMP data
def store_lbmp(zone_name: str, lbmp: float, timestamp: datetime):
    doc_ref = db.collection('lbmp').document()
    doc_ref.set({
        'zone_name': zone_name,
        'lbmp': lbmp,
        'timestamp': timestamp,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

# Example: Query data
def get_latest_lbmp(zone_name: str):
    docs = db.collection('lbmp') \
        .where('zone_name', '==', zone_name) \
        .order_by('timestamp', direction=firestore.Query.DESCENDING) \
        .limit(1) \
        .stream()
    
    for doc in docs:
        return doc.to_dict()
    return None
```

### Option B: Cloud SQL (PostgreSQL - Better for your use case)

Keep using PostgreSQL but connect from Firebase Functions.

```bash
# Create Cloud SQL instance (if not already created)
gcloud sql instances create nyiso-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create nyiso --instance=nyiso-db

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe nyiso-db --format 'value(connectionName)')
```

**File**: `functions/index.js` (Update to connect to Cloud SQL)

```javascript
exports.api = onRequest(
  {
    cors: true,
    memory: '512MiB',
    timeoutSeconds: 300,
    // Connect to Cloud SQL
    vpcConnector: 'projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME',
    vpcConnectorEgressSettings: 'PRIVATE_RANGES_ONLY',
  },
  async (req, res) => {
    // Your proxy code
  }
);
```

**File**: `api/main.py` (Connection string)

```python
import os

# Cloud SQL connection via Unix socket
DATABASE_URL = os.getenv('DATABASE_URL')
# Format: postgresql://user:pass@/db?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

---

## Step 4: Set Up Scheduler (5-minute scraping)

**File**: `functions/scheduledScraper.js`

```javascript
const {onSchedule} = require('firebase-functions/v2/scheduler');
const {onRequest} = require('firebase-functions/v2/https');
const axios = require('axios');

// Scraper function (called by scheduler)
exports.scrape = onRequest(
  {
    memory: '1GiB',
    timeoutSeconds: 540, // 9 minutes max
    cors: true,
  },
  async (req, res) => {
    try {
      // Call your scraper endpoint on Cloud Run
      const CLOUD_RUN_URL = process.env.CLOUD_RUN_URL;
      const response = await axios.post(`${CLOUD_RUN_URL}/scrape`);
      
      console.log('Scraper completed:', response.status);
      res.json({status: 'success', message: 'Scraper completed'});
    } catch (error) {
      console.error('Scraper error:', error);
      res.status(500).json({error: error.message});
    }
  }
);

// Scheduled function (runs every 5 minutes)
exports.scraperScheduled = onSchedule(
  {
    schedule: '*/5 * * * *', // Every 5 minutes
    timeZone: 'America/New_York',
    memory: '256MiB',
    timeoutSeconds: 60,
  },
  async (event) => {
    // Call the scrape function
    const scrapeUrl = `https://${process.env.GCLOUD_PROJECT}-${process.env.FUNCTION_REGION}.cloudfunctions.net/scrape`;
    
    try {
      const response = await axios.post(scrapeUrl);
      console.log('Scheduled scraper completed:', response.status);
    } catch (error) {
      console.error('Scheduled scraper error:', error);
      throw error;
    }
  }
);
```

**Alternative: Use Cloud Scheduler directly**

```bash
# Create Cloud Scheduler job
gcloud scheduler jobs create http scraper-job \
  --schedule="*/5 * * * *" \
  --uri="https://PROJECT_ID-REGION.cloudfunctions.net/scrape" \
  --http-method=POST \
  --time-zone="America/New_York" \
  --location=us-central1
```

---

## Step 5: Set Up Frontend

**File**: `firebase.json`

```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "function": "api"
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
  },
  "functions": {
    "source": "functions",
    "runtime": "nodejs18"
  },
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  }
}
```

**File**: `frontend/src/constants/config.ts`

```typescript
// Use relative URL - Firebase will route to functions
export const API_BASE_URL = '/api';
```

**File**: `frontend/.env.production`

```env
# Empty or use relative path (Firebase handles routing)
VITE_API_BASE_URL=/api
```

---

## Step 6: Deploy Everything

```bash
# Install function dependencies
cd functions
npm install
cd ..

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Deploy everything at once
firebase deploy

# Or deploy individually:
firebase deploy --only hosting    # Frontend
firebase deploy --only functions  # Backend
firebase deploy --only firestore  # Database rules
```

---

## Step 7: Environment Variables

### For Cloud Functions v2 (Recommended)

**File**: `functions/.env`

```env
CLOUD_RUN_URL=https://nyiso-api-XXXXX-uc.a.run.app
DATABASE_URL=postgresql://user:pass@/nyiso?host=/cloudsql/PROJECT_ID:REGION:INSTANCE
GCLOUD_PROJECT=your-project-id
FUNCTION_REGION=us-central1
```

### For Cloud Functions v1

```bash
# Set config
firebase functions:config:set \
  cloud_run.url="https://nyiso-api-XXXXX-uc.a.run.app" \
  database.url="postgresql://..."

# Access in code
const config = functions.config();
const cloudRunUrl = config.cloud_run.url;
```

---

## Step 8: Verify Deployment

```bash
# Check hosting
firebase hosting:channel:list

# Check functions
firebase functions:list

# View logs
firebase functions:log

# Test API
curl https://PROJECT_ID.web.app/api/stats
```

---

## Cost Breakdown

### Monthly Costs

| Service | Cost | Notes |
|---------|------|-------|
| **Firebase Hosting** | FREE | 10GB storage + 10GB bandwidth/month |
| **Cloud Functions** | ~$0.40/1M invocations | First 2M invocations free |
| **Cloud Scheduler** | $0.10/job/month | 3 jobs free |
| **Firestore** | FREE | 1GB storage, 50K reads/day, 20K writes/day |
| **Cloud SQL** | $7.67 | db-f1-micro (if using PostgreSQL) |
| **Total** | **$8-15/month** | Very cost-effective! |

---

## Troubleshooting

### Functions Not Deploying

```bash
# Check Node.js version
node --version  # Should be 18+

# Check Firebase CLI
firebase --version

# View deployment logs
firebase deploy --only functions --debug
```

### CORS Errors

```bash
# Ensure CORS is enabled in function config
# In functions/index.js:
exports.api = onRequest(
  {
    cors: true,  # ← Make sure this is set
    ...
  },
  ...
);
```

### Database Connection Issues

```bash
# For Cloud SQL, ensure VPC connector is set up
gcloud compute networks vpc-access connectors create connector-name \
  --region=us-central1 \
  --subnet=default \
  --subnet-project=PROJECT_ID
```

---

## Next Steps

1. ✅ Set up custom domain (optional)
2. ✅ Configure monitoring and alerts
3. ✅ Set up CI/CD with GitHub Actions
4. ✅ Configure backups for database
5. ✅ Set up staging environment

---

## Quick Reference

```bash
# Deploy everything
firebase deploy

# Deploy frontend only
firebase deploy --only hosting

# Deploy backend only
firebase deploy --only functions

# View logs
firebase functions:log

# Test locally
firebase emulators:start
```

---

**Your fully integrated Firebase deployment is complete!** 🎉

Access your dashboard at:
- **Frontend**: `https://PROJECT_ID.web.app`
- **API**: `https://PROJECT_ID.web.app/api/*` (routed through Firebase Functions)



