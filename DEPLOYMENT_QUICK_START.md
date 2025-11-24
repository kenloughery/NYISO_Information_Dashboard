# Deployment Quick Start Guide

**Choose your deployment option and follow the steps below.**

## 🚀 Option 1: Fly.io (Recommended - 30 minutes)

### Prerequisites
- Fly.io account (free signup at https://fly.io)
- Fly CLI installed

### Steps

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Deploy**
   ```bash
   cd /path/to/nyiso-product
   fly launch
   # Follow prompts, choose PostgreSQL if you want managed database
   fly deploy
   ```

3. **Set Environment Variables**
   ```bash
   fly secrets set VITE_API_BASE_URL=https://your-app.fly.dev
   ```

4. **Done!** Your app is live at `https://your-app.fly.dev`

**Cost**: $4-10/month  
**Full Guide**: See `deployment/fly.io/DEPLOYMENT_GUIDE.md`

---

## 🖥️ Option 2: VPS (Hetzner) - Lowest Cost

### Prerequisites
- Hetzner account (signup at https://hetzner.com)
- SSH access to server

### Steps

1. **Create VPS**
   - Hetzner Cloud Console
   - Ubuntu 22.04, 2GB RAM, 20GB SSD
   - Cost: €4.51/month

2. **Run Deployment Script**
   ```bash
   ssh root@your-server-ip
   git clone <your-repo-url> /opt/nyiso-dashboard
   cd /opt/nyiso-dashboard
   chmod +x deployment/vps/deploy.sh
   ./deployment/vps/deploy.sh
   ```

3. **Set Up SSL** (optional)
   ```bash
   certbot --nginx -d your-domain.com
   ```

**Cost**: €5.51/month (~$6/month)  
**Full Guide**: See `deployment/vps/DEPLOYMENT_GUIDE.md`

---

## 🚂 Option 3: Railway - Simplest

### Prerequisites
- Railway account (signup at https://railway.app)
- GitHub repository

### Steps

1. **Connect Repository**
   - Go to railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Services**
   - Railway auto-detects Python
   - Add PostgreSQL database (Railway provides connection string)
   - Set environment variable: `VITE_API_BASE_URL=https://your-app.railway.app`

3. **Deploy**
   - Railway auto-deploys on Git push
   - View logs in Railway dashboard

**Cost**: $10-20/month  
**Full Guide**: See Railway documentation

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure:

- [ ] Code is committed to Git repository
- [ ] Frontend builds successfully (`cd frontend && npm run build`)
- [ ] Backend API runs locally (`python start_api_prod.py`)
- [ ] Database schema is initialized
- [ ] Environment variables are set
- [ ] Domain name is configured (optional)

---

## 🔧 Post-Deployment Steps

1. **Initialize Database**
   ```bash
   # SSH into server or use fly ssh console
   python -c "from database.schema import init_db; init_db()"
   ```

2. **Verify Services**
   - Check API: `curl https://your-app.com/health`
   - Check frontend: Open `https://your-app.com` in browser
   - Check logs for errors

3. **Set Up Backups**
   - Configure daily database backups
   - Set up monitoring alerts

---

## 🆘 Troubleshooting

### App Won't Start
- Check logs: `fly logs` or `journalctl -u nyiso-api`
- Verify environment variables are set
- Check database connection

### Frontend Not Loading
- Verify frontend was built: `ls frontend/dist`
- Check API base URL in environment variables
- Check browser console for errors

### Database Issues
- Verify database file exists and has permissions
- Check database connection string
- Initialize database schema if needed

---

## 📚 Full Documentation

- **Fly.io**: `deployment/fly.io/DEPLOYMENT_GUIDE.md`
- **VPS**: `deployment/vps/DEPLOYMENT_GUIDE.md`
- **Main Guide**: `DEPLOYMENT_SOLUTION.md`

---

## 💡 Recommendation

**For most users, I recommend Fly.io** because:
- ✅ Very affordable ($4-10/month)
- ✅ Simple CLI deployment
- ✅ Works with your existing codebase
- ✅ Global edge deployment
- ✅ Good documentation

**Start with Fly.io, then migrate to VPS if you need more control or lower cost.**

---

**Questions?** Check the full deployment guides or open an issue.
