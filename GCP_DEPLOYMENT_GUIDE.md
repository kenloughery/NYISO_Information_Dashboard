# Google Cloud Platform Deployment Guide

**Complete guide for deploying NYISO Dashboard to Google Cloud Run + Firebase Hosting**

---

## Overview

This guide covers deploying:
- **Backend API**: Google Cloud Run (serverless containers)
- **Frontend**: Firebase Hosting (FREE static hosting)
- **Database**: Cloud SQL (PostgreSQL)
- **Scheduler**: Cloud Scheduler (5-minute cron jobs)

**Total Cost**: ~$8-15/month (frontend hosting is FREE!)

---

## Prerequisites

1. **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com)
2. **Firebase Account**: Same as Google account (free)
3. **gcloud CLI**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk)
4. **Firebase CLI**: `npm install -g firebase-tools`

---

## Step 1: Initial Setup

### 1.1 Install Tools

```bash
# Install Google Cloud SDK
# macOS:
brew install --cask google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install

# Install Firebase CLI
npm install -g firebase-tools
```

### 1.2 Login and Initialize

```bash
# Login to Google Cloud
gcloud auth login
gcloud auth application-default login

# Login to Firebase
firebase login
```

### 1.3 Create Project

```bash
# Create GCP project
gcloud projects create nyiso-dashboard --name="NYISO Dashboard"

# Set as default project
gcloud config set project nyiso-dashboard

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"
```

### 1.4 Enable Required APIs

```bash
# Enable Cloud Run
gcloud services enable run.googleapis.com

# Enable Cloud Scheduler
gcloud services enable cloudscheduler.googleapis.com

# Enable Cloud SQL
gcloud services enable sqladmin.googleapis.com

# Enable Cloud Build
gcloud services enable cloudbuild.googleapis.com

# Enable Firebase (for hosting)
gcloud services enable firebase.googleapis.com
```

---

## Step 2: Backend Setup (Cloud Run)

### 2.1 Create Dockerfile

**File**: `Dockerfile.backend`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run uses PORT env var, default 8080)
ENV PORT=8080

# Run FastAPI
CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

### 2.2 Create .dockerignore

**File**: `.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv
*.db
*.log
.git
.gitignore
README.md
frontend/
node_modules/
.DS_Store
```

### 2.3 Build and Deploy Backend

```bash
# Set variables
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
SERVICE_NAME=nyiso-api

# Build container image
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@/nyiso?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME"

# Get service URL
API_URL=$(gcloud run services describe ${SERVICE_NAME} --format 'value(status.url)')
echo "API URL: ${API_URL}"
```

### 2.4 Set Up Database (Cloud SQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create nyiso-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=${REGION} \
  --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create nyiso --instance=nyiso-db

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe nyiso-db --format 'value(connectionName)')
echo "Connection Name: ${CONNECTION_NAME}"

# Update Cloud Run service to connect to Cloud SQL
gcloud run services update ${SERVICE_NAME} \
  --add-cloudsql-instances ${CONNECTION_NAME} \
  --region ${REGION}
```

### 2.5 Configure Cloud Scheduler (5-minute scraping)

```bash
# Get service account email
SERVICE_ACCOUNT="${PROJECT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create scheduled job (every 5 minutes)
gcloud scheduler jobs create http scraper-job \
  --schedule="*/5 * * * *" \
  --uri="${API_URL}/scrape" \
  --http-method=POST \
  --oidc-service-account-email=${SERVICE_ACCOUNT} \
  --location=${REGION}

# Test the job
gcloud scheduler jobs run scraper-job --location=${REGION}
```

---

## Step 3: Frontend Setup (Firebase Hosting)

### 3.1 Initialize Firebase

```bash
cd frontend

# Initialize Firebase
firebase init hosting

# Select options:
# - Use an existing project: Yes
# - Select project: nyiso-dashboard
# - Public directory: dist
# - Single-page app: Yes
# - Set up automatic builds: No (we'll build manually)
# - Overwrite index.html: No
```

### 3.2 Configure firebase.json

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
      },
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=86400"
          }
        ]
      }
    ]
  }
}
```

### 3.3 Update Environment Variables

**File**: `frontend/.env.production`

```env
VITE_API_BASE_URL=https://nyiso-api-XXXXX-uc.a.run.app
```

Replace `XXXXX` with your actual Cloud Run service URL.

### 3.4 Build and Deploy Frontend

```bash
# Build frontend
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Your site will be available at:
# https://PROJECT_ID.web.app
# or
# https://PROJECT_ID.firebaseapp.com
```

### 3.5 Set Up Custom Domain (Optional)

```bash
# Add custom domain in Firebase Console
# https://console.firebase.google.com/project/PROJECT_ID/hosting

# Or via CLI:
firebase hosting:channel:deploy production --only hosting
```

---

## Step 4: Configure Frontend-Backend Connection

You have two options for connecting React to Cloud Run:

### Option A: Direct API Calls (Simplest) ⭐ **RECOMMENDED**

**File**: `frontend/.env.production`
```env
VITE_API_BASE_URL=https://nyiso-api-XXXXX-uc.a.run.app
```

**File**: `api/main.py`
```python
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Get allowed origins from environment
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
```

**Set in Cloud Run**:
```bash
gcloud run services update nyiso-api \
  --set-env-vars "ALLOWED_ORIGINS=https://PROJECT_ID.web.app,https://PROJECT_ID.firebaseapp.com" \
  --region us-central1
```

### Option B: Firebase Hosting Rewrites (Same Domain)

**File**: `frontend/firebase.json`
```json
{
  "hosting": {
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "nyiso-api",
          "region": "us-central1"
        }
      }
    ]
  }
}
```

**File**: `frontend/src/constants/config.ts`
```typescript
export const API_BASE_URL = '/api'; // Relative URL
```

**See `FIREBASE_CLOUD_RUN_INTEGRATION.md` for detailed options and setup.**

---

## Step 5: Continuous Deployment (Optional)

### 5.1 GitHub Actions Workflow

**File**: `.github/workflows/deploy.yml`

```yaml
name: Deploy to GCP

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Deploy
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/nyiso-api
          gcloud run deploy nyiso-api \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/nyiso-api \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Build
        run: |
          cd frontend
          npm run build
      
      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          channelId: live
          projectId: ${{ secrets.GCP_PROJECT_ID }}
```

---

## Step 6: Monitoring and Logs

### 6.1 View Logs

```bash
# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Firebase Hosting logs
# View in Firebase Console: https://console.firebase.google.com/project/PROJECT_ID/hosting
```

### 6.2 Set Up Alerts

```bash
# Create alert for Cloud Run errors
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Cloud Run Errors" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05
```

---

## Cost Breakdown

### Monthly Costs

| Service | Cost | Notes |
|---------|------|-------|
| **Cloud Run** | ~$2-5 | Pay per request + compute time |
| **Cloud Scheduler** | $0.10 | 1 job per month |
| **Cloud SQL** | $7.67 | db-f1-micro instance |
| **Cloud Build** | ~$0-2 | First 120 min/day free |
| **Firebase Hosting** | **FREE** | 10GB storage + 10GB bandwidth/month |
| **Total** | **$8-15/month** | Very cost-effective! |

### Free Tier Limits

- **Cloud Run**: 2 million requests/month free
- **Cloud SQL**: No free tier (but db-f1-micro is cheap)
- **Cloud Scheduler**: 3 free jobs/month
- **Firebase Hosting**: 10GB storage + 10GB bandwidth/month

---

## Troubleshooting

### Backend Issues

```bash
# Check service status
gcloud run services describe nyiso-api --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=nyiso-api" --limit 50

# Test locally
docker build -t nyiso-api -f Dockerfile.backend .
docker run -p 8080:8080 nyiso-api
```

### Frontend Issues

```bash
# Check Firebase deployment
firebase hosting:channel:list

# View deployment history
firebase hosting:channel:open live

# Test build locally
cd frontend
npm run build
npm run preview
```

### Database Connection Issues

```bash
# Test database connection
gcloud sql connect nyiso-db --user=postgres

# Check Cloud SQL instance
gcloud sql instances describe nyiso-db

# Verify Cloud Run can connect
gcloud run services describe nyiso-api --format="value(spec.template.spec.containers[0].env)"
```

---

## Security Best Practices

1. **Environment Variables**: Use Secret Manager for sensitive data
   ```bash
   # Store secret
   echo -n "your-secret" | gcloud secrets create db-password --data-file=-
   
   # Use in Cloud Run
   gcloud run services update nyiso-api \
     --update-secrets DATABASE_PASSWORD=db-password:latest
   ```

2. **IAM Roles**: Use least privilege
   ```bash
   # Grant minimal permissions
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SERVICE_ACCOUNT" \
     --role="roles/cloudsql.client"
   ```

3. **HTTPS Only**: Firebase Hosting enforces HTTPS automatically

---

## Next Steps

1. ✅ Set up custom domain (optional)
2. ✅ Configure monitoring and alerts
3. ✅ Set up CI/CD pipeline
4. ✅ Configure backups for Cloud SQL
5. ✅ Set up staging environment

---

## Quick Reference Commands

```bash
# Deploy backend
gcloud builds submit --tag gcr.io/PROJECT_ID/nyiso-api
gcloud run deploy nyiso-api --image gcr.io/PROJECT_ID/nyiso-api

# Deploy frontend
cd frontend && npm run build && firebase deploy --only hosting

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Update scheduler
gcloud scheduler jobs update http scraper-job --schedule="*/5 * * * *"
```

---

**Deployment Complete!** 🎉

Your dashboard is now live at:
- **Frontend**: `https://PROJECT_ID.web.app`
- **Backend API**: `https://nyiso-api-XXXXX.run.app`

