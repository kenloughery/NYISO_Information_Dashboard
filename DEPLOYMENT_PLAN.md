# Deployment Plan - NYISO Dashboard

**Date**: 2025-11-14  
**Goal**: Deploy backend and frontend with cost-effective, simple solution  
**Key Requirement**: Run scraper every 5 minutes without expensive resources

---

## Executive Summary

**Recommended Approach**: **Option 1 - VPS (DigitalOcean/Linode)** - Best balance of simplicity, cost, and control.

**Total Estimated Monthly Cost**: $12-24/month

---

## Current System Requirements

### Backend Requirements
- **Python 3.11+** with FastAPI
- **SQLite database** (can upgrade to PostgreSQL)
- **Continuous process**: Scheduler runs every 5 minutes
- **API server**: FastAPI on port 8000
- **Memory**: ~200-500MB for scraper + API
- **Storage**: Database grows over time (estimate: 50-200MB/month)

### Frontend Requirements
- **Static files**: React/Vite build output
- **API endpoint**: Points to backend URL
- **No server needed**: Can be served from CDN or same server

### Update Frequency
- **Real-time sources**: Every 5 minutes (9 sources)
- **Hourly sources**: Every hour (3 sources)
- **Daily sources**: Once per day (8 sources)
- **Total API calls**: ~2,600 per day (mostly 5-minute sources)

---

## Deployment Options Analysis

### Option 1: VPS (Virtual Private Server) ⭐ **RECOMMENDED**

#### Providers
- **DigitalOcean**: $12/month (2GB RAM, 1 vCPU, 50GB SSD)
- **Linode**: $12/month (2GB RAM, 1 vCPU, 50GB SSD)
- **Vultr**: $12/month (2GB RAM, 1 vCPU, 55GB SSD)
- **Hetzner**: €4.51/month (~$5) (2GB RAM, 1 vCPU, 20GB SSD) - Best value

#### Architecture
```
┌─────────────────────────────────┐
│         VPS Server              │
│  ┌───────────────────────────┐  │
│  │  Systemd Services:         │  │
│  │  - nyiso-scraper.service  │  │ ← Runs every 5 min
│  │  - nyiso-api.service      │  │ ← FastAPI server
│  │  - nginx                  │  │ ← Reverse proxy
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  SQLite Database          │  │
│  │  (nyiso_data.db)          │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Static Frontend Files    │  │
│  │  (React build output)     │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Provision VPS**
   ```bash
   # Choose provider and create droplet/instance
   # Recommended: Ubuntu 22.04 LTS
   ```

2. **Initial Server Setup**
   ```bash
   # SSH into server
   ssh root@your-server-ip
   
   # Update system
   apt update && apt upgrade -y
   
   # Install Python, Node.js, Nginx
   apt install -y python3.11 python3-pip python3-venv nodejs npm nginx
   
   # Install PostgreSQL (optional, better than SQLite for production)
   apt install -y postgresql postgresql-contrib
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone <your-repo-url> /opt/nyiso-dashboard
   cd /opt/nyiso-dashboard
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Build frontend
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure Systemd Services**

   **File**: `/etc/systemd/system/nyiso-scraper.service`
   ```ini
   [Unit]
   Description=NYISO Data Scraper (5-minute updates)
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/nyiso-dashboard
   Environment="PATH=/opt/nyiso-dashboard/venv/bin"
   ExecStart=/opt/nyiso-dashboard/venv/bin/python -m scraper.scheduler
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

   **File**: `/etc/systemd/system/nyiso-api.service`
   ```ini
   [Unit]
   Description=NYISO FastAPI Server
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/nyiso-dashboard
   Environment="PATH=/opt/nyiso-dashboard/venv/bin"
   Environment="DATABASE_URL=sqlite:///opt/nyiso-dashboard/nyiso_data.db"
   ExecStart=/opt/nyiso-dashboard/venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

5. **Configure Nginx**

   **File**: `/etc/nginx/sites-available/nyiso-dashboard`
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       # Frontend (static files)
       location / {
           root /opt/nyiso-dashboard/frontend/dist;
           try_files $uri $uri/ /index.html;
       }

       # API proxy
       location /api {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

6. **Enable Services**
   ```bash
   systemctl enable nyiso-scraper
   systemctl enable nyiso-api
   systemctl start nyiso-scraper
   systemctl start nyiso-api
   systemctl reload nginx
   ```

#### Cost Breakdown
- **VPS**: $12/month (DigitalOcean/Linode) or $5/month (Hetzner)
- **Domain**: $12/year (~$1/month) - Optional
- **SSL Certificate**: Free (Let's Encrypt)
- **Total**: **$6-13/month**

#### Pros
- ✅ **Simple**: Standard Linux server, easy to understand
- ✅ **Cost-effective**: Predictable monthly cost
- ✅ **Full control**: Complete access to server
- ✅ **Reliable**: Server runs 24/7, scheduler always active
- ✅ **Scalable**: Easy to upgrade resources if needed
- ✅ **No vendor lock-in**: Can migrate easily

#### Cons
- ⚠️ **Manual setup**: Requires initial configuration
- ⚠️ **Server management**: Need to handle updates, backups
- ⚠️ **Single point of failure**: One server (mitigate with backups)

#### Maintenance
- **Backups**: Daily database backup (cron job)
- **Updates**: Monthly system updates
- **Monitoring**: Simple health check script
- **Logs**: Systemd journal for service logs

---

### Option 2: Railway.app (PaaS) ⭐ **SIMPLEST**

#### Overview
Railway is a modern PaaS that auto-deploys from Git and handles infrastructure.

#### Architecture
```
┌─────────────────────────────────┐
│      Railway Platform           │
│  ┌───────────────────────────┐  │
│  │  Backend Service          │  │
│  │  - FastAPI                │  │
│  │  - SQLite/PostgreSQL      │  │
│  │  - Scheduler (cron)       │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Frontend Service          │  │
│  │  - Static React build      │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Connect Repository**
   - Sign up at railway.app
   - Connect GitHub/GitLab repository
   - Railway auto-detects Python project

2. **Configure Backend Service**
   - Add `railway.json` or use Railway dashboard
   - Set environment variables:
     ```
     DATABASE_URL=postgresql://... (Railway provides)
     PORT=8000
     ```
   - Railway auto-builds and deploys

3. **Configure Scheduler**
   - Use Railway's cron jobs feature
   - Or use `schedule` library with long-running service
   - Railway keeps services running

4. **Configure Frontend**
   - Add second service for frontend
   - Build command: `npm run build`
   - Serve static files

#### Cost Breakdown
- **Hobby Plan**: $5/month + usage
- **Usage**: ~$0.01/hour for running services
- **Database**: PostgreSQL included
- **Estimated Total**: **$10-20/month**

#### Pros
- ✅ **Simplest**: Almost zero configuration
- ✅ **Auto-deploy**: Git push = deploy
- ✅ **Managed**: Railway handles infrastructure
- ✅ **Free tier**: $5 credit/month for testing
- ✅ **PostgreSQL included**: Better than SQLite

#### Cons
- ⚠️ **Cost**: Can be more expensive than VPS
- ⚠️ **Less control**: Limited server access
- ⚠️ **Vendor lock-in**: Harder to migrate
- ⚠️ **Scheduler complexity**: Need to ensure service stays running

---

### Option 3: Render.com (PaaS)

#### Overview
Similar to Railway, but with better free tier and simpler pricing.

#### Architecture
Same as Railway - managed services

#### Setup Steps

1. **Create Web Service** (Backend)
   - Connect repository
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - Add PostgreSQL database (free tier available)

2. **Create Static Site** (Frontend)
   - Connect frontend directory
   - Build: `npm run build`
   - Publish: `dist` directory

3. **Configure Cron Jobs**
   - Use Render's cron job feature
   - Run `python run_hourly_updates.py` every hour
   - For 5-minute updates, use long-running service with `schedule` library

#### Cost Breakdown
- **Free Tier**: 
  - Web service: Free (spins down after 15 min inactivity)
  - PostgreSQL: Free (90-day limit, then $7/month)
- **Paid Tier**: $7/month per service
- **Estimated Total**: **$0-14/month** (free tier works but not ideal for 5-min updates)

#### Pros
- ✅ **Free tier**: Good for testing
- ✅ **Simple**: Easy setup
- ✅ **PostgreSQL**: Free database included

#### Cons
- ⚠️ **Free tier limitations**: Services spin down (not good for 5-min updates)
- ⚠️ **Cost**: Paid tier needed for continuous operation
- ⚠️ **Scheduler**: Need workaround for 5-minute updates

---

### Option 4: AWS Amplify

#### Overview
AWS Amplify is a full-stack deployment platform that integrates hosting, APIs, and backend services.

#### Architecture
```
┌─────────────────────────────────┐
│      AWS Amplify Platform       │
│  ┌───────────────────────────┐  │
│  │  Frontend Hosting (CDN)    │  │
│  │  - React build              │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Backend (Lambda Functions)│  │
│  │  - FastAPI via Lambda      │  │
│  │  - Scheduled tasks (EventBridge)│
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Database (DynamoDB/RDS)  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Install Amplify CLI**
   ```bash
   npm install -g @aws-amplify/cli
   amplify configure
   ```

2. **Initialize Project**
   ```bash
   amplify init
   amplify add api  # For FastAPI backend
   amplify add hosting  # For frontend
   ```

3. **Configure Scheduled Tasks**
   - Use AWS EventBridge (CloudWatch Events) for cron
   - Trigger Lambda function every 5 minutes
   - Lambda runs scraper code

4. **Deploy**
   ```bash
   amplify publish
   ```

#### Cost Breakdown
- **Build & Deploy**: $0.01 per build minute
- **Hosting**: $0.023 per GB served, $0.15 per GB stored
- **Lambda**: $0.20 per 1M requests, $0.0000166667 per GB-second
- **EventBridge**: $1.00 per million events (cron triggers)
- **DynamoDB**: $1.25 per million reads, $1.25 per million writes
- **Estimated Total**: **$15-30/month** (varies with usage)

#### Pros
- ✅ **Integrated**: Full AWS ecosystem integration
- ✅ **Scalable**: Auto-scales with traffic
- ✅ **Serverless**: No server management
- ✅ **CI/CD**: Built-in Git-based deployment

#### Cons
- ⚠️ **Complex**: AWS learning curve
- ⚠️ **Cost**: Can be expensive with usage
- ⚠️ **Vendor Lock-in**: Deep AWS integration
- ⚠️ **Scheduled Tasks**: Requires EventBridge setup

**Best For**: Already using AWS, need enterprise features

---

### Option 5: Vercel

#### Overview
Vercel is optimized for frontend frameworks with serverless functions and edge computing.

#### Architecture
```
┌─────────────────────────────────┐
│      Vercel Platform            │
│  ┌───────────────────────────┐  │
│  │  Frontend (Edge Network)   │  │
│  │  - React build             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Serverless Functions      │  │
│  │  - API routes              │  │
│  │  - Cron jobs (Vercel Cron)│  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  External Database         │  │
│  │  (Vercel Postgres/Supabase)│  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Connect Repository**
   ```bash
   npm i -g vercel
   vercel login
   vercel
   ```

2. **Configure API Routes**
   - Create `api/` directory in project
   - Convert FastAPI to Vercel serverless functions
   - Or use Vercel's Python runtime

3. **Configure Scheduled Tasks**
   - Use Vercel Cron Jobs (Pro plan)
   - Or external cron service (cron-job.org)

4. **Deploy**
   ```bash
   vercel --prod
   ```

#### Cost Breakdown
- **Hobby (Free)**: 
  - 100GB bandwidth/month
  - Serverless functions: 100GB-hours/month
  - No cron jobs (need Pro)
- **Pro**: $20/month
  - Unlimited bandwidth
  - Cron jobs included
  - Team features
- **Database**: Vercel Postgres $0.25/GB-month or external
- **Estimated Total**: **$20-30/month** (Pro plan needed for cron)

#### Pros
- ✅ **Simple**: Very easy deployment
- ✅ **Fast**: Global edge network
- ✅ **Great DX**: Excellent developer experience
- ✅ **Free Tier**: Good for testing

#### Cons
- ⚠️ **Cron Limitation**: Cron jobs require Pro plan ($20/month)
- ⚠️ **Backend**: Not ideal for long-running processes
- ⚠️ **Database**: Need external database service
- ⚠️ **5-Min Updates**: May need workaround for frequent cron

**Best For**: Frontend-focused, willing to pay for Pro plan

---

### Option 6: Netlify

#### Overview
Netlify provides continuous deployment, serverless functions, and form handling.

#### Architecture
```
┌─────────────────────────────────┐
│      Netlify Platform           │
│  ┌───────────────────────────┐  │
│  │  Frontend (CDN)            │  │
│  │  - React build             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Serverless Functions      │  │
│  │  - API endpoints           │  │
│  │  - Scheduled functions     │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  External Database         │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Connect Repository**
   - Sign up at netlify.com
   - Connect GitHub/GitLab
   - Auto-detects build settings

2. **Configure Functions**
   - Create `netlify/functions/` directory
   - Convert FastAPI to Netlify functions
   - Or use Netlify's Python runtime

3. **Configure Scheduled Tasks**
   - Use Netlify Scheduled Functions (Pro plan)
   - Or external cron service

4. **Deploy**
   - Auto-deploys on Git push

#### Cost Breakdown
- **Starter (Free)**: 
  - 100GB bandwidth/month
  - 125K function invocations/month
  - No scheduled functions
- **Pro**: $19/month
  - Unlimited bandwidth
  - Scheduled functions included
  - Team features
- **Database**: External (Supabase, PlanetScale, etc.)
- **Estimated Total**: **$19-30/month** (Pro plan needed)

#### Pros
- ✅ **Simple**: Very easy setup
- ✅ **CI/CD**: Auto-deploy from Git
- ✅ **Free Tier**: Good for testing
- ✅ **Forms**: Built-in form handling

#### Cons
- ⚠️ **Cron Limitation**: Scheduled functions require Pro ($19/month)
- ⚠️ **Backend**: Limited for complex backends
- ⚠️ **Database**: Need external service
- ⚠️ **5-Min Updates**: May need external cron service

**Best For**: Simple deployments, JAMstack apps

---

### Option 7: Fly.io

#### Overview
Fly.io runs Docker containers globally with edge computing capabilities.

#### Architecture
```
┌─────────────────────────────────┐
│      Fly.io Platform            │
│  ┌───────────────────────────┐  │
│  │  Backend App (Docker)      │  │
│  │  - FastAPI                 │  │
│  │  - Scheduler (cron)        │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Frontend (Static)         │  │
│  │  - React build             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Database (Postgres)       │  │
│  │  (Fly Postgres or external)│  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Deploy**
   ```bash
   fly launch
   fly deploy
   ```

4. **Configure Cron**
   - Use `fly.toml` with `[processes]` section
   - Or use Fly Machines API for scheduled tasks

#### Cost Breakdown
- **Free Tier**: 3 shared-cpu-1x VMs, 3GB persistent volumes
- **Paid**: $1.94/month per shared-cpu-1x VM
- **Postgres**: $1.94/month (1GB) or external
- **Bandwidth**: $0.02/GB
- **Estimated Total**: **$4-10/month** (very cost-effective!)

#### Pros
- ✅ **Cost-Effective**: Very affordable
- ✅ **Docker**: Full control with containers
- ✅ **Global**: Deploy close to users
- ✅ **Simple**: Easy deployment

#### Cons
- ⚠️ **Cron Setup**: Requires configuration for scheduled tasks
- ⚠️ **Newer Platform**: Less mature than others
- ⚠️ **Documentation**: Less extensive than AWS/Heroku

**Best For**: Cost-conscious, Docker-friendly, need full control

---

### Option 8: Heroku

#### Overview
Heroku is a classic PaaS platform with simple Git-based deployment.

#### Architecture
```
┌─────────────────────────────────┐
│      Heroku Platform            │
│  ┌───────────────────────────┐  │
│  │  Backend Dyno             │  │
│  │  - FastAPI                │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Scheduler Add-on          │  │
│  │  - Cron jobs               │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Postgres Add-on           │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Install Heroku CLI**
   ```bash
   heroku login
   ```

2. **Create App**
   ```bash
   heroku create nyiso-dashboard
   ```

3. **Add Add-ons**
   ```bash
   heroku addons:create scheduler:standard  # For cron
   heroku addons:create heroku-postgresql:mini  # Database
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Configure Scheduler**
   - Use Heroku Scheduler add-on
   - Set up cron jobs via dashboard

#### Cost Breakdown
- **Eco Dyno**: $5/month (sleeps after 30 min inactivity - not ideal)
- **Basic Dyno**: $7/month (always on)
- **Scheduler Add-on**: Free (basic) or $25/month (advanced)
- **Postgres Mini**: $5/month (10M rows)
- **Estimated Total**: **$12-37/month**

#### Pros
- ✅ **Simple**: Very easy deployment
- ✅ **Mature**: Well-established platform
- ✅ **Add-ons**: Rich ecosystem
- ✅ **Documentation**: Excellent docs

#### Cons
- ⚠️ **Cost**: Can be expensive
- ⚠️ **Eco Dyno**: Sleeps after inactivity (not good for 5-min updates)
- ⚠️ **Basic Dyno**: Need always-on dyno ($7/month minimum)

**Best For**: Simple deployment, willing to pay for convenience

---

### Option 9: Google Cloud Run + Firebase Hosting ⭐

#### Overview
Cloud Run is a serverless container platform that scales to zero when not in use. **Frontend can be hosted on Firebase Hosting (free) or Cloud Storage + CDN (very cheap)**.

#### Architecture
```
┌─────────────────────────────────┐
│   Google Cloud Platform         │
│  ┌───────────────────────────┐  │
│  │  Firebase Hosting          │  │ ← React Frontend (FREE)
│  │  - Static files (dist/)    │  │
│  │  - Global CDN              │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Cloud Run (Container)     │  │
│  │  - FastAPI                 │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Cloud Scheduler           │  │
│  │  - Cron jobs (5-min)       │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Cloud SQL (Postgres)      │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

##### Part 1: Backend (Cloud Run)

1. **Install gcloud CLI**
   ```bash
   # Install Google Cloud SDK
   # https://cloud.google.com/sdk/docs/install
   gcloud init
   gcloud auth login
   ```

2. **Create Project**
   ```bash
   gcloud projects create nyiso-dashboard
   gcloud config set project nyiso-dashboard
   ```

3. **Enable APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudscheduler.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

4. **Build and Deploy Backend**
   ```bash
   # Create Dockerfile for backend
   # (see Dockerfile.backend example below)
   
   # Build and deploy
   gcloud builds submit --tag gcr.io/PROJECT_ID/nyiso-api
   gcloud run deploy nyiso-api \
     --image gcr.io/PROJECT_ID/nyiso-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DATABASE_URL="postgresql://..."
   ```

5. **Configure Cloud Scheduler**
   ```bash
   # Get Cloud Run URL
   API_URL=$(gcloud run services describe nyiso-api --format 'value(status.url)')
   
   # Create scheduled job (every 5 minutes)
   gcloud scheduler jobs create http scraper-job \
     --schedule="*/5 * * * *" \
     --uri="${API_URL}/scrape" \
     --http-method=POST \
     --oidc-service-account-email=PROJECT_NUMBER-compute@developer.gserviceaccount.com
   ```

6. **Set Up Database**
   ```bash
   # Create Cloud SQL instance
   gcloud sql instances create nyiso-db \
     --database-version=POSTGRES_14 \
     --tier=db-f1-micro \
     --region=us-central1
   
   # Create database
   gcloud sql databases create nyiso --instance=nyiso-db
   
   # Get connection string
   gcloud sql instances describe nyiso-db --format 'value(connectionName)'
   ```

##### Part 2: Frontend (Firebase Hosting) ✅

**Option A: Firebase Hosting (Recommended - FREE)**

1. **Install Firebase CLI**
   ```bash
   npm install -g firebase-tools
   firebase login
   ```

2. **Initialize Firebase in Frontend**
   ```bash
   cd frontend
   firebase init hosting
   # Select: Use existing project
   # Public directory: dist
   # Single-page app: Yes
   # Auto-build: No (we'll build manually)
   ```

3. **Configure firebase.json**
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
         }
       ]
     }
   }
   ```

4. **Update API Base URL**
   ```bash
   # In frontend/.env.production
   VITE_API_BASE_URL=https://nyiso-api-XXXXX.run.app
   ```

5. **Build and Deploy Frontend**
   ```bash
   cd frontend
   npm run build
   firebase deploy --only hosting
   ```

**Option B: Cloud Storage + Cloud CDN (Alternative)**

1. **Create Storage Bucket**
   ```bash
   gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://nyiso-frontend
   gsutil web set -m index.html gs://nyiso-frontend
   ```

2. **Upload Frontend Build**
   ```bash
   cd frontend
   npm run build
   gsutil -m cp -r dist/* gs://nyiso-frontend/
   ```

3. **Set Up Cloud CDN** (optional, for better performance)
   ```bash
   # Create load balancer with Cloud CDN
   # (More complex, but better performance)
   ```

#### Dockerfile for Backend

**File**: `Dockerfile.backend`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Cost Breakdown

**Backend (Cloud Run)**:
- **Compute**: $0.40 per million requests, $0.0000025 per GB-second
- **Cloud Scheduler**: $0.10 per job per month (1 job = $0.10)
- **Cloud SQL**: $7.67/month (db-f1-micro)
- **Cloud Build**: $0.003 per build-minute (first 120 min/day free)

**Frontend (Firebase Hosting)**:
- **Storage**: **FREE** (10GB included)
- **Bandwidth**: **FREE** (10GB/month included)
- **SSL**: **FREE** (automatic)
- **CDN**: **FREE** (global CDN included)

**Alternative (Cloud Storage + CDN)**:
- **Storage**: $0.020 per GB/month (first 5GB free)
- **Bandwidth**: $0.12 per GB (first 1GB free)
- **CDN**: $0.08 per GB (first 1GB free)

**Estimated Total**: **$8-15/month** (backend only, frontend is FREE!)

#### Pros
- ✅ **Cost-Effective**: Pay only for backend usage
- ✅ **Frontend FREE**: Firebase Hosting is free for reasonable usage
- ✅ **Scalable**: Auto-scales to zero
- ✅ **Scheduled Tasks**: Built-in Cloud Scheduler
- ✅ **Global CDN**: Firebase Hosting includes global CDN
- ✅ **SSL Included**: Automatic SSL certificates
- ✅ **Google Integration**: Works with other GCP services

#### Cons
- ⚠️ **Cold Starts**: Containers may have cold start delays (1-2 seconds)
- ⚠️ **Complexity**: More setup than simple PaaS
- ⚠️ **GCP Learning**: Need to learn GCP ecosystem
- ⚠️ **Multiple Services**: Need to manage multiple GCP services

**Best For**: Cost-conscious, need scheduled tasks, want free frontend hosting, Google ecosystem

---

### Option 10: Supabase

#### Overview
Supabase is an open-source Firebase alternative with PostgreSQL, auth, and edge functions.

#### Architecture
```
┌─────────────────────────────────┐
│      Supabase Platform           │
│  ┌───────────────────────────┐  │
│  │  Frontend Hosting          │  │
│  │  (or external)             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Edge Functions            │  │
│  │  - API endpoints           │  │
│  │  - Scheduled tasks         │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Postgres Database         │  │
│  │  (managed)                 │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Create Project**
   - Sign up at supabase.com
   - Create new project

2. **Set Up Edge Functions**
   ```bash
   supabase init
   supabase functions new scraper
   ```

3. **Configure Scheduled Tasks**
   - Use pg_cron extension (PostgreSQL cron)
   - Or external cron service

4. **Deploy**
   ```bash
   supabase functions deploy scraper
   ```

#### Cost Breakdown
- **Free Tier**: 
  - 500MB database
  - 2GB bandwidth
  - 2M edge function invocations
- **Pro**: $25/month
  - 8GB database
  - 250GB bandwidth
  - 2M edge function invocations
- **Estimated Total**: **$0-25/month**

#### Pros
- ✅ **Postgres**: Full PostgreSQL database
- ✅ **Open Source**: Self-hostable
- ✅ **Free Tier**: Good for testing
- ✅ **Real-time**: Built-in real-time features

#### Cons
- ⚠️ **Scheduled Tasks**: Need pg_cron or external service
- ⚠️ **Backend**: Edge functions are Deno-based (not Python)
- ⚠️ **Migration**: Need to adapt FastAPI to edge functions

**Best For**: Need PostgreSQL, real-time features, open-source preference

---

### Option 11: Cloudflare Workers + Pages

#### Overview
Cloudflare Workers provides edge computing with scheduled events (cron triggers).

#### Architecture
```
┌─────────────────────────────────┐
│   Cloudflare Platform            │
│  ┌───────────────────────────┐  │
│  │  Pages (Frontend)          │  │
│  │  - React build             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Workers (Backend)         │  │
│  │  - API endpoints           │  │
│  │  - Cron triggers           │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  D1 Database (SQLite)     │  │
│  │  or external DB            │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Install Wrangler CLI**
   ```bash
   npm install -g wrangler
   wrangler login
   ```

2. **Create Worker**
   ```bash
   wrangler init nyiso-api
   ```

3. **Configure Cron Triggers**
   ```toml
   # wrangler.toml
   [triggers]
   crons = ["*/5 * * * *"]
   ```

4. **Deploy**
   ```bash
   wrangler publish
   ```

#### Cost Breakdown
- **Free Tier**: 
  - 100K requests/day
  - 10ms CPU time per request
  - Cron triggers included
- **Paid**: $5/month
  - 10M requests/month
  - 50ms CPU time per request
- **D1 Database**: $0.001 per million reads, $1 per million writes
- **Estimated Total**: **$5-10/month** (very affordable!)

#### Pros
- ✅ **Cost-Effective**: Very cheap
- ✅ **Global**: Edge network worldwide
- ✅ **Cron**: Built-in cron triggers
- ✅ **Fast**: Edge computing

#### Cons
- ⚠️ **Runtime**: JavaScript/TypeScript (not Python)
- ⚠️ **Migration**: Need to rewrite backend
- ⚠️ **Database**: D1 is SQLite (limited), or external

**Best For**: Cost-conscious, willing to rewrite in JavaScript

---

### Option 12: DigitalOcean App Platform

#### Overview
DigitalOcean's managed PaaS platform with simple deployment.

#### Architecture
```
┌─────────────────────────────────┐
│   DigitalOcean App Platform      │
│  ┌───────────────────────────┐  │
│  │  Web Service (Backend)     │  │
│  │  - FastAPI                 │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Worker (Scheduler)        │  │
│  │  - Cron jobs               │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Static Site (Frontend)    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Managed Database          │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Setup Steps

1. **Connect Repository**
   - Sign up at digitalocean.com
   - Connect GitHub/GitLab
   - Create new app

2. **Configure Services**
   - Add web service (backend)
   - Add worker service (scheduler)
   - Add static site (frontend)
   - Add managed database

3. **Deploy**
   - Auto-deploys on Git push

#### Cost Breakdown
- **Basic Web Service**: $5/month (512MB RAM)
- **Worker Service**: $5/month (for scheduler)
- **Static Site**: Free
- **Managed Postgres**: $15/month (1GB RAM)
- **Estimated Total**: **$25-30/month**

#### Pros
- ✅ **Simple**: Easy deployment
- ✅ **Managed**: DigitalOcean handles infrastructure
- ✅ **Database**: Managed Postgres included
- ✅ **Predictable**: Clear pricing

#### Cons
- ⚠️ **Cost**: More expensive than VPS
- ⚠️ **Workers**: Need separate worker for scheduler
- ⚠️ **Less Control**: Less control than VPS

**Best For**: Want managed platform, DigitalOcean ecosystem

---

### Option 5: Hybrid Approach (VPS + CDN)

#### Architecture
- **VPS**: Backend API + Scraper
- **Cloudflare Pages/Netlify**: Frontend hosting (free)

#### Setup
1. Deploy backend to VPS (Option 1)
2. Deploy frontend to Cloudflare Pages (free)
3. Configure frontend to point to VPS API

#### Cost
- **VPS**: $12/month
- **Frontend hosting**: Free
- **Total**: **$12/month**

#### Pros
- ✅ **Best of both**: Simple backend, free frontend
- ✅ **CDN**: Fast frontend delivery worldwide
- ✅ **Cost-effective**: Only pay for backend

#### Cons
- ⚠️ **CORS**: Need to configure CORS properly
- ⚠️ **Two deployments**: Manage two systems

---

## Recommended Deployment Strategy

### Primary Recommendation: **Option 1 - VPS (Hetzner or DigitalOcean)**

**Why**:
1. **Simplicity**: Standard Linux server, well-documented
2. **Cost**: $5-12/month (very affordable)
3. **Reliability**: Server runs 24/7, scheduler always active
4. **Control**: Full access, easy to debug
5. **Scalability**: Easy to upgrade if needed

### Alternative: **Option 2 - Railway** (if you want zero server management)

**Why**:
1. **Easiest**: Almost no configuration
2. **Auto-deploy**: Git push = deploy
3. **Managed**: No server maintenance

**Trade-off**: Slightly more expensive, less control

---

## Implementation Plan

### Phase 1: Preparation (1-2 hours)

1. **Choose Provider**
   - Recommended: Hetzner ($5/month) or DigitalOcean ($12/month)
   - Sign up and create account

2. **Prepare Repository**
   - Ensure code is in Git repository
   - Add deployment configuration files (see below)

3. **Create Deployment Scripts**
   - `deploy.sh`: Automated deployment script
   - `backup.sh`: Database backup script
   - `health-check.sh`: Service health monitoring

### Phase 2: Server Setup (2-3 hours)

1. **Provision VPS**
   - Create Ubuntu 22.04 instance
   - Configure SSH keys
   - Set up firewall (allow ports 22, 80, 443)

2. **Install Dependencies**
   - Python 3.11, Node.js, Nginx
   - PostgreSQL (optional but recommended)

3. **Deploy Application**
   - Clone repository
   - Set up virtual environment
   - Build frontend
   - Configure services

### Phase 3: Service Configuration (1-2 hours)

1. **Systemd Services**
   - Create scraper service
   - Create API service
   - Enable and start services

2. **Nginx Configuration**
   - Configure reverse proxy
   - Set up SSL (Let's Encrypt)
   - Configure static file serving

3. **Database Setup**
   - Initialize database
   - Run migrations
   - Set up backups

### Phase 4: Monitoring & Maintenance (Ongoing)

1. **Health Checks**
   - API endpoint monitoring
   - Scraper job monitoring
   - Database size monitoring

2. **Backups**
   - Daily database backups
   - Weekly full backups
   - Off-site backup storage

3. **Updates**
   - Monthly system updates
   - Application updates as needed

---

## Required Configuration Files

### 1. Production API Start Script

**File**: `start_api_prod.py`
```python
"""Production API server startup."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",  # Only localhost (Nginx proxies)
        port=8000,
        reload=False,  # No auto-reload in production
        log_level="info",
        workers=1  # Single worker for SQLite
    )
```

### 2. Production Scraper Script

**File**: `run_scraper_prod.py`
```python
"""Production scraper with better error handling."""
import logging
import sys
from pathlib import Path
from scraper.scheduler import NYISOScheduler

# Production logging
log_file = Path(__file__).parent / 'logs' / 'scraper.log'
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    scheduler = NYISOScheduler()
    try:
        scheduler.start(run_immediately=True)
    except KeyboardInterrupt:
        scheduler.stop()
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)
```

### 3. Environment Configuration

**File**: `.env.production`
```bash
# Database
DATABASE_URL=sqlite:///opt/nyiso-dashboard/nyiso_data.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/nyiso

# API
API_HOST=127.0.0.1
API_PORT=8000

# Frontend
VITE_API_BASE_URL=https://your-domain.com/api
```

### 4. Deployment Script

**File**: `deploy.sh`
```bash
#!/bin/bash
# Deployment script for VPS

set -e

echo "Starting deployment..."

# Activate virtual environment
source venv/bin/activate

# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Run database migrations (if any)
# python -m alembic upgrade head

# Restart services
systemctl restart nyiso-scraper
systemctl restart nyiso-api
systemctl reload nginx

echo "Deployment complete!"
```

### 5. Backup Script

**File**: `backup.sh`
```bash
#!/bin/bash
# Daily database backup

BACKUP_DIR="/opt/nyiso-dashboard/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nyiso_data_$DATE.db"

mkdir -p $BACKUP_DIR

# Backup SQLite database
cp /opt/nyiso-dashboard/nyiso_data.db $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "nyiso_data_*.db" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

### 6. Health Check Script

**File**: `health-check.sh`
```bash
#!/bin/bash
# Health check for services

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "API: OK"
else
    echo "API: FAILED"
    systemctl restart nyiso-api
fi

# Check scraper process
if systemctl is-active --quiet nyiso-scraper; then
    echo "Scraper: OK"
else
    echo "Scraper: FAILED"
    systemctl restart nyiso-scraper
fi
```

---

## Cost Comparison Summary

| Option | Monthly Cost | Setup Time | Complexity | 5-Min Cron | Best For |
|--------|--------------|------------|------------|------------|----------|
| **VPS (Hetzner)** | $5 | 3-4 hours | Low | ✅ Built-in | ⭐ **Best value** |
| **VPS (DigitalOcean)** | $12 | 3-4 hours | Low | ✅ Built-in | ⭐ **Recommended** |
| **Fly.io** | $4-10 | 2-3 hours | Low | ⚠️ Config needed | **Best cost/control** |
| **Google Cloud Run** | $8-15 | 3-4 hours | Medium | ✅ Built-in | **Cost-effective serverless** |
| **Cloudflare Workers** | $5-10 | 2-3 hours | Medium | ✅ Built-in | **Edge computing** |
| **Railway** | $10-20 | 1 hour | Very Low | ⚠️ Service-based | **Simplest PaaS** |
| **Render** | $0-14 | 1 hour | Very Low | ⚠️ Service-based | **Free tier testing** |
| **Heroku** | $12-37 | 1 hour | Very Low | ✅ Add-on | **Classic PaaS** |
| **DigitalOcean App** | $25-30 | 1 hour | Low | ✅ Worker service | **Managed platform** |
| **Vercel** | $20-30 | 1 hour | Very Low | ⚠️ Pro plan | **Frontend-focused** |
| **Netlify** | $19-30 | 1 hour | Very Low | ⚠️ Pro plan | **JAMstack apps** |
| **AWS Amplify** | $15-30 | 4-6 hours | High | ✅ EventBridge | **AWS ecosystem** |
| **Supabase** | $0-25 | 2-3 hours | Medium | ⚠️ pg_cron | **Postgres + real-time** |
| **Hybrid (VPS+CDN)** | $12 | 4-5 hours | Medium | ✅ Built-in | **Global frontend** |

**Legend**:
- ✅ = Native support for 5-minute cron jobs
- ⚠️ = Requires configuration or workaround

---

## Migration Path

### From Development to Production

1. **Database Migration**
   - Export SQLite data (if needed)
   - Set up PostgreSQL (recommended for production)
   - Import data

2. **Environment Variables**
   - Create `.env.production`
   - Set `DATABASE_URL`
   - Set `VITE_API_BASE_URL` for frontend

3. **Service Configuration**
   - Update systemd service files
   - Configure Nginx
   - Set up SSL certificates

4. **Monitoring**
   - Set up health checks
   - Configure backups
   - Set up log rotation

---

## Security Considerations

### Essential Security Steps

1. **Firewall**
   ```bash
   ufw allow 22/tcp  # SSH
   ufw allow 80/tcp  # HTTP
   ufw allow 443/tcp # HTTPS
   ufw enable
   ```

2. **SSL Certificate**
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d your-domain.com
   ```

3. **SSH Hardening**
   - Disable password authentication
   - Use SSH keys only
   - Change default SSH port (optional)

4. **Database Security**
   - Use PostgreSQL with strong password
   - Or keep SQLite file permissions restricted
   - Regular backups

5. **API Security**
   - CORS properly configured
   - Rate limiting (optional)
   - Input validation (already in FastAPI)

---

## Monitoring & Maintenance

### Daily Tasks (Automated)
- Database backups
- Health checks
- Log rotation

### Weekly Tasks
- Review logs for errors
- Check disk space
- Verify scraper is running

### Monthly Tasks
- System updates
- Security patches
- Review costs

### Alerts (Optional)
- Set up email alerts for:
  - Service failures
  - Disk space > 80%
  - Database backup failures

---

## Backup Strategy

### Database Backups

**Daily Backup** (Cron job):
```bash
# Add to crontab: crontab -e
0 2 * * * /opt/nyiso-dashboard/backup.sh
```

**Off-site Backup** (Optional):
- Upload to S3/Backblaze: $0.023/GB/month
- Or use rsync to another server

**Backup Retention**:
- Daily backups: Keep 30 days
- Weekly backups: Keep 12 weeks
- Monthly backups: Keep 12 months

---

## Scaling Considerations

### When to Scale

**Current Setup Handles**:
- ✅ 5-minute scraping (9 sources)
- ✅ Hourly scraping (3 sources)
- ✅ Daily scraping (8 sources)
- ✅ API serving dashboard
- ✅ ~100-500 concurrent users

**When to Upgrade**:
- Database > 10GB: Consider PostgreSQL
- > 1000 concurrent users: Add load balancer
- Need redundancy: Add second server

### Upgrade Path

1. **Database**: SQLite → PostgreSQL (same VPS)
2. **Resources**: Upgrade VPS plan (2GB → 4GB RAM)
3. **Redundancy**: Add second server + load balancer
4. **CDN**: Add Cloudflare for frontend (free)

---

## Quick Start: VPS Deployment

### Step-by-Step (DigitalOcean Example)

1. **Create Droplet**
   - Ubuntu 22.04 LTS
   - $12/month plan (2GB RAM)
   - Add SSH key

2. **Initial Setup** (5 minutes)
   ```bash
   ssh root@your-server-ip
   apt update && apt upgrade -y
   apt install -y python3.11 python3-pip python3-venv nodejs npm nginx git
   ```

3. **Deploy Application** (10 minutes)
   ```bash
   git clone <your-repo> /opt/nyiso-dashboard
   cd /opt/nyiso-dashboard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure Services** (15 minutes)
   - Copy systemd service files (from this doc)
   - Copy Nginx config (from this doc)
   - Enable and start services

5. **Set Up SSL** (5 minutes)
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d your-domain.com
   ```

6. **Set Up Backups** (5 minutes)
   ```bash
   chmod +x backup.sh
   crontab -e
   # Add: 0 2 * * * /opt/nyiso-dashboard/backup.sh
   ```

**Total Setup Time**: ~40 minutes

---

## Cost Optimization Tips

1. **Use Hetzner**: $5/month vs $12/month (same specs)
2. **SQLite First**: Start with SQLite, upgrade to PostgreSQL only if needed
3. **Free Frontend Hosting**: Use Cloudflare Pages or Netlify (free)
4. **Monitor Usage**: Set up billing alerts
5. **Optimize Scraper**: Only scrape what you need

---

## Final Recommendation

### 🏆 Top 3 Recommendations

#### 1st Choice: **VPS (Hetzner - $5/month)** ⭐

**Why**:
- **Lowest cost** ($5/month)
- **Simple** Linux server
- **Full control** over everything
- **Native cron** support (systemd)
- **Easy to understand** and maintain

**Setup Time**: 3-4 hours one-time  
**Monthly Cost**: $5  
**Ongoing Maintenance**: ~1 hour/month  
**Best For**: Cost-conscious, want full control, simple setup

---

#### 2nd Choice: **Fly.io ($4-10/month)** ⭐

**Why**:
- **Very affordable** ($4-10/month)
- **Docker-based** (familiar)
- **Global deployment** (edge computing)
- **Good documentation**
- **Modern platform**

**Setup Time**: 2-3 hours one-time  
**Monthly Cost**: $4-10  
**Ongoing Maintenance**: Minimal  
**Best For**: Want modern platform, Docker-friendly, cost-effective

---

#### 3rd Choice: **Google Cloud Run ($8-15/month)** ⭐

**Why**:
- **Cost-effective** serverless ($8-15/month)
- **Built-in cron** (Cloud Scheduler)
- **Scales to zero** (pay only when running)
- **Enterprise-grade** infrastructure
- **Good for scheduled tasks**

**Setup Time**: 3-4 hours one-time  
**Monthly Cost**: $8-15  
**Ongoing Maintenance**: Minimal  
**Best For**: Want serverless, need scheduled tasks, Google ecosystem

---

### Alternative Recommendations by Use Case

#### For Zero Management: **Railway ($10-20/month)**
- Almost zero configuration
- Auto-deploy from Git
- Managed infrastructure
- **Best For**: Want zero server management

#### For Frontend-Focused: **Vercel ($20/month)**
- Excellent frontend deployment
- Global edge network
- Serverless functions
- **Best For**: Frontend-first, willing to pay for Pro

#### For AWS Ecosystem: **AWS Amplify ($15-30/month)**
- Full AWS integration
- Enterprise features
- Scalable infrastructure
- **Best For**: Already using AWS, need enterprise features

#### For Postgres + Real-time: **Supabase ($0-25/month)**
- Full PostgreSQL database
- Real-time features
- Open-source
- **Best For**: Need Postgres, real-time features, open-source preference

#### For Edge Computing: **Cloudflare Workers ($5-10/month)**
- Very affordable
- Global edge network
- Built-in cron triggers
- **Best For**: Cost-conscious, willing to rewrite in JavaScript

---

**Document Status**: ✅ Complete - Ready for Implementation

