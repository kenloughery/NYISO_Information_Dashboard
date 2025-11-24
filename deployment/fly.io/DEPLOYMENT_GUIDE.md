# Fly.io Deployment Guide

Complete step-by-step guide to deploy NYISO Dashboard on Fly.io.

## Prerequisites

- Fly.io account (sign up at https://fly.io)
- Fly CLI installed
- Git repository with your code
- Domain name (optional, Fly.io provides free subdomain)

## Step 1: Install Fly CLI

### macOS
```bash
curl -L https://fly.io/install.sh | sh
```

### Linux
```bash
curl -L https://fly.io/install.sh | sh
```

### Windows
Download from: https://fly.io/docs/hands-on/install-flyctl/

## Step 2: Login to Fly.io

```bash
fly auth login
```

This will open your browser to authenticate.

## Step 3: Initialize Fly App

Navigate to your project directory:

```bash
cd /path/to/nyiso-product
fly launch
```

Follow the prompts:
- **App name**: `nyiso-dashboard` (or your choice)
- **Region**: Choose closest to you (e.g., `iad` for Washington D.C.)
- **PostgreSQL**: 
  - Type `y` if you want managed PostgreSQL (recommended)
  - Type `n` if you want to use SQLite (simpler, but less scalable)

## Step 4: Configure Environment Variables

Set the frontend API base URL:

```bash
fly secrets set VITE_API_BASE_URL=https://nyiso-dashboard.fly.dev
```

If using PostgreSQL, the connection string is automatically set as `DATABASE_URL`.

## Step 5: Deploy

```bash
fly deploy
```

This will:
1. Build the Docker image
2. Push to Fly.io
3. Deploy the app
4. Show you the URL

## Step 6: Verify Deployment

Check the app status:

```bash
fly status
```

View logs:

```bash
fly logs
```

Open the app:

```bash
fly open
```

## Step 7: Set Up Database (if using SQLite)

If you chose SQLite, you need to create a persistent volume:

```bash
fly volumes create nyiso_data --size 1 --region iad
```

Then update `fly.toml` to mount the volume:

```toml
[[mounts]]
  source = "nyiso_data"
  destination = "/app/data"
```

And update your code to use `/app/data/nyiso_data.db` as the database path.

## Step 8: Initialize Database Schema

SSH into the app and run database initialization:

```bash
fly ssh console
python -c "from database.schema import init_db; init_db()"
```

Or create a migration script and run it:

```bash
fly ssh console -C "python scripts/init_db.py"
```

## Step 9: Monitor and Debug

### View Logs
```bash
fly logs
```

### SSH into Container
```bash
fly ssh console
```

### Check App Status
```bash
fly status
```

### View Metrics
```bash
fly metrics
```

## Step 10: Set Up Custom Domain (Optional)

1. Add your domain in Fly.io dashboard
2. Get DNS records from Fly.io
3. Add DNS records to your domain registrar
4. Wait for DNS propagation (5-60 minutes)

## Troubleshooting

### App Won't Start

Check logs:
```bash
fly logs
```

Check status:
```bash
fly status
```

### Database Connection Issues

If using PostgreSQL, check connection string:
```bash
fly secrets list
```

### Scheduler Not Running

The scheduler runs in the background. Check logs:
```bash
fly logs | grep scheduler
```

### Frontend Not Loading

Check if frontend was built correctly:
```bash
fly ssh console
ls -la frontend/dist
```

## Updating the App

1. Make changes to your code
2. Commit to Git
3. Deploy:
   ```bash
   fly deploy
   ```

## Auto-Deploy from GitHub (Optional)

1. Install GitHub integration:
   ```bash
   fly github connect
   ```

2. Enable auto-deploy in Fly.io dashboard

## Cost Management

Monitor usage:
```bash
fly dashboard
```

Set up billing alerts in Fly.io dashboard.

## Scaling

Scale up (more resources):
```bash
fly scale vm shared-cpu-2x --memory 1024
```

Scale down:
```bash
fly scale vm shared-cpu-1x --memory 512
```

## Backup Strategy

### For SQLite
```bash
fly ssh console
cp /app/data/nyiso_data.db /tmp/backup.db
fly sftp shell
get /tmp/backup.db
```

### For PostgreSQL
Fly Postgres includes automatic backups. Check dashboard for restore options.

## Next Steps

- Set up monitoring (optional)
- Configure custom domain
- Set up CI/CD pipeline
- Configure backups

## Support

- Fly.io Docs: https://fly.io/docs/
- Fly.io Community: https://community.fly.io/
- Fly.io Status: https://status.fly.io/


