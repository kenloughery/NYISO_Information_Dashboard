# NYISO Dashboard - Deployment Solution

**Date**: 2025-01-27  
**Status**: Ready for Deployment

## Executive Summary

Based on your requirements (simplicity, low cost, easy deployment, compatible with current codebase), I recommend **3 deployment options** ranked by priority:

### 🥇 **Option 1: Fly.io** (Recommended)
- **Cost**: $4-10/month
- **Setup Time**: 30-60 minutes
- **Deployment**: CLI (`fly deploy`)
- **Why**: Modern platform, Docker-based, very affordable, easy GitHub integration

### 🥈 **Option 2: VPS (Hetzner)** 
- **Cost**: $5/month
- **Setup Time**: 2-3 hours
- **Deployment**: Git push + SSH
- **Why**: Lowest cost, full control, native cron support

### 🥉 **Option 3: Railway**
- **Cost**: $10-20/month
- **Setup Time**: 15-30 minutes
- **Deployment**: Auto-deploy from GitHub
- **Why**: Simplest setup, zero configuration

---

## Quick Decision Guide

**Choose Fly.io if:**
- ✅ Want modern platform with Docker
- ✅ Prefer CLI deployment
- ✅ Want global edge deployment
- ✅ Budget: $4-10/month

**Choose VPS (Hetzner) if:**
- ✅ Want lowest cost ($5/month)
- ✅ Need full server control
- ✅ Comfortable with Linux/SSH
- ✅ Want native systemd services

**Choose Railway if:**
- ✅ Want zero configuration
- ✅ Prefer auto-deploy from GitHub
- ✅ Want managed infrastructure
- ✅ Budget: $10-20/month

---

## Option 1: Fly.io Deployment ⭐ RECOMMENDED

### Why Fly.io?
- **Very affordable**: $4-10/month
- **Docker-native**: Works with your existing codebase
- **Global deployment**: Edge computing worldwide
- **Easy deployment**: Single CLI command
- **GitHub integration**: Auto-deploy on push (optional)

### Architecture
```
┌─────────────────────────────────┐
│      Fly.io Platform            │
│  ┌───────────────────────────┐  │
│  │  Backend App (Docker)      │  │
│  │  - FastAPI (port 8000)     │  │
│  │  - Scheduler (background)  │  │
│  │  - SQLite/Postgres          │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Frontend (Static)         │  │
│  │  - React build (dist/)     │  │
│  │  - Served by FastAPI       │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Setup Steps

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Initialize Fly App**
   ```bash
   cd /path/to/nyiso-product
   fly launch
   # Follow prompts:
   # - App name: nyiso-dashboard (or your choice)
   # - Region: Choose closest to you
   # - PostgreSQL: Yes (or use SQLite)
   ```

3. **Deploy**
   ```bash
   fly deploy
   ```

4. **Set Environment Variables**
   ```bash
   fly secrets set VITE_API_BASE_URL=https://your-app.fly.dev
   ```

5. **View Logs**
   ```bash
   fly logs
   ```

### Files Created
- `Dockerfile` - Container configuration
- `fly.toml` - Fly.io configuration
- `.dockerignore` - Files to exclude from Docker build

### Cost Breakdown
- **App hosting**: $1.94/month (shared-cpu-1x)
- **PostgreSQL** (optional): $1.94/month (1GB)
- **Bandwidth**: $0.02/GB (first 160GB free)
- **Total**: **$4-10/month**

### Pros
- ✅ Very affordable
- ✅ Docker-native (familiar)
- ✅ Global edge deployment
- ✅ Easy CLI deployment
- ✅ Good documentation

### Cons
- ⚠️ Need to configure scheduler (runs in same container)
- ⚠️ Newer platform (less mature than AWS/Heroku)

---

## Option 2: VPS (Hetzner) Deployment

### Why Hetzner VPS?
- **Lowest cost**: €4.51/month (~$5/month)
- **Full control**: Complete server access
- **Native cron**: Systemd services
- **Simple**: Standard Linux server

### Architecture
```
┌─────────────────────────────────┐
│      Hetzner VPS                │
│  ┌───────────────────────────┐  │
│  │  Systemd Services:         │  │
│  │  - nyiso-api.service       │  │
│  │  - nyiso-scraper.service   │  │
│  │  - nginx (reverse proxy)   │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  SQLite Database          │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Frontend (static files)  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Setup Steps

1. **Create VPS Instance**
   - Sign up at hetzner.com
   - Create Cloud Server: Ubuntu 22.04, 2GB RAM, 20GB SSD
   - Cost: €4.51/month

2. **Initial Server Setup**
   ```bash
   ssh root@your-server-ip
   apt update && apt upgrade -y
   apt install -y python3.11 python3-pip python3-venv nodejs npm nginx git
   ```

3. **Deploy Application**
   ```bash
   git clone <your-repo-url> /opt/nyiso-dashboard
   cd /opt/nyiso-dashboard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Build frontend
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure Services**
   - Copy systemd service files (see `deployment/vps/` directory)
   - Copy nginx configuration
   - Enable and start services

5. **Set Up SSL**
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d your-domain.com
   ```

### Files Created
- `deployment/vps/nyiso-api.service` - API systemd service
- `deployment/vps/nyiso-scraper.service` - Scraper systemd service
- `deployment/vps/nginx.conf` - Nginx configuration
- `deployment/vps/deploy.sh` - Deployment script

### Cost Breakdown
- **VPS**: €4.51/month (~$5/month)
- **Domain** (optional): $12/year (~$1/month)
- **SSL**: Free (Let's Encrypt)
- **Total**: **$5-6/month**

### Pros
- ✅ Lowest cost
- ✅ Full control
- ✅ Native cron support
- ✅ Simple Linux server
- ✅ Easy to understand

### Cons
- ⚠️ Manual setup required
- ⚠️ Server management needed
- ⚠️ Single point of failure

---

## Option 3: Railway Deployment

### Why Railway?
- **Simplest setup**: Almost zero configuration
- **Auto-deploy**: Git push = deploy
- **Managed**: No server management
- **PostgreSQL included**: Better than SQLite

### Architecture
```
┌─────────────────────────────────┐
│      Railway Platform           │
│  ┌───────────────────────────┐  │
│  │  Backend Service            │  │
│  │  - FastAPI                  │  │
│  │  - Scheduler (background)    │  │
│  │  - PostgreSQL (managed)     │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Frontend Service           │  │
│  │  - Static React build       │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Setup Steps

1. **Sign Up**
   - Go to railway.app
   - Sign up with GitHub

2. **Create Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Backend**
   - Railway auto-detects Python
   - Add environment variable: `VITE_API_BASE_URL=https://your-app.railway.app`
   - Add PostgreSQL database (Railway provides connection string)

4. **Configure Frontend**
   - Add second service for frontend
   - Build command: `cd frontend && npm install && npm run build`
   - Start command: `npx serve -s dist -l 3000`

5. **Deploy**
   - Railway auto-deploys on Git push
   - View logs in Railway dashboard

### Files Created
- `railway.json` - Railway configuration (optional)
- `.railway/` - Railway metadata

### Cost Breakdown
- **Hobby Plan**: $5/month + usage
- **Usage**: ~$0.01/hour for running services
- **PostgreSQL**: Included
- **Estimated Total**: **$10-20/month**

### Pros
- ✅ Simplest setup
- ✅ Auto-deploy from Git
- ✅ Managed infrastructure
- ✅ PostgreSQL included
- ✅ Zero server management

### Cons
- ⚠️ More expensive than VPS
- ⚠️ Less control
- ⚠️ Vendor lock-in

---

## Comparison Table

| Feature | Fly.io | VPS (Hetzner) | Railway |
|---------|--------|---------------|---------|
| **Monthly Cost** | $4-10 | $5 | $10-20 |
| **Setup Time** | 30-60 min | 2-3 hours | 15-30 min |
| **Deployment** | CLI (`fly deploy`) | Git + SSH | Auto (Git push) |
| **Control** | Medium | Full | Low |
| **Database** | SQLite/Postgres | SQLite/Postgres | Postgres (managed) |
| **Cron Support** | Container-based | Native systemd | Service-based |
| **Scalability** | Auto-scales | Manual | Auto-scales |
| **Best For** | Modern platform | Cost-conscious | Zero config |

---

## Recommended: Fly.io

**Why Fly.io is the best choice for you:**

1. **Cost-effective**: $4-10/month (very affordable)
2. **Simple deployment**: Single CLI command (`fly deploy`)
3. **Compatible**: Works with your existing Python/FastAPI codebase
4. **Docker-native**: Uses Docker (industry standard)
5. **GitHub integration**: Can auto-deploy on push
6. **Global**: Edge deployment worldwide

**Next Steps:**
1. Follow the Fly.io setup guide in `deployment/fly.io/`
2. Run `fly deploy` to deploy
3. Set environment variables
4. Done!

---

## Migration Path

### From Local Development to Production

1. **Database Migration**
   - Export SQLite data (if needed)
   - Import to production database
   - Update `DATABASE_URL` environment variable

2. **Environment Variables**
   - Set `VITE_API_BASE_URL` for frontend
   - Set `DATABASE_URL` for backend
   - Set any API keys/secrets

3. **Build Frontend**
   - Run `npm run build` in `frontend/` directory
   - Frontend will be served by backend or static hosting

4. **Deploy**
   - Follow deployment guide for chosen platform
   - Test endpoints
   - Monitor logs

---

## Security Checklist

- [ ] Set strong database passwords
- [ ] Configure CORS properly
- [ ] Use HTTPS (SSL certificates)
- [ ] Set up firewall rules
- [ ] Rotate API keys regularly
- [ ] Enable database backups
- [ ] Monitor logs for errors
- [ ] Keep dependencies updated

---

## Monitoring & Maintenance

### Daily
- Check logs for errors
- Verify scraper is running
- Monitor database size

### Weekly
- Review error logs
- Check disk space
- Verify backups

### Monthly
- Update dependencies
- Review costs
- Security patches

---

## Support & Resources

- **Fly.io Docs**: https://fly.io/docs/
- **Hetzner Docs**: https://docs.hetzner.com/
- **Railway Docs**: https://docs.railway.app/

---

**Ready to deploy?** Choose your option and follow the detailed guide in the `deployment/` directory!


