# VPS Deployment Guide (Hetzner/DigitalOcean)

Complete step-by-step guide to deploy NYISO Dashboard on a VPS.

## Prerequisites

- VPS account (Hetzner, DigitalOcean, Linode, etc.)
- Domain name (optional, can use IP address)
- SSH access to server
- Basic Linux command line knowledge

## Step 1: Create VPS Instance

### Hetzner (Recommended - €4.51/month)

1. Sign up at https://hetzner.com
2. Create Cloud Server:
   - **Image**: Ubuntu 22.04
   - **Type**: CX11 (2GB RAM, 1 vCPU, 20GB SSD)
   - **Location**: Choose closest to you
   - **SSH Key**: Add your SSH key
3. Note the server IP address

### DigitalOcean (Alternative - $12/month)

1. Sign up at https://digitalocean.com
2. Create Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($12/month, 2GB RAM)
   - **Region**: Choose closest to you
   - **SSH Key**: Add your SSH key
3. Note the server IP address

## Step 2: Initial Server Setup

SSH into your server:

```bash
ssh root@your-server-ip
```

Update system:

```bash
apt update && apt upgrade -y
```

Install basic tools:

```bash
apt install -y curl wget git
```

## Step 3: Run Deployment Script

Clone the repository and run the deployment script:

```bash
# Set your repository URL
export REPO_URL="https://github.com/your-username/nyiso-product.git"

# Run deployment script
curl -fsSL https://raw.githubusercontent.com/your-username/nyiso-product/main/deployment/vps/deploy.sh | bash
```

Or manually:

```bash
git clone $REPO_URL /opt/nyiso-dashboard
cd /opt/nyiso-dashboard
chmod +x deployment/vps/deploy.sh
./deployment/vps/deploy.sh
```

## Step 4: Configure Domain (Optional)

If you have a domain name:

1. Point your domain to the server IP:
   ```
   A record: @ -> your-server-ip
   ```

2. Update nginx configuration:
   ```bash
   nano /etc/nginx/sites-available/nyiso-dashboard
   # Change: server_name _; to server_name your-domain.com;
   ```

3. Reload nginx:
   ```bash
   systemctl reload nginx
   ```

## Step 5: Set Up SSL Certificate

Install Certbot:

```bash
apt install -y certbot python3-certbot-nginx
```

Get SSL certificate:

```bash
certbot --nginx -d your-domain.com
```

Or if using IP only:

```bash
# Use Let's Encrypt with DNS challenge
certbot certonly --manual --preferred-challenges dns -d your-domain.com
```

Certbot will automatically:
- Obtain SSL certificate
- Configure nginx
- Set up auto-renewal

## Step 6: Initialize Database

SSH into server and initialize database:

```bash
cd /opt/nyiso-dashboard
source venv/bin/activate
python -c "from database.schema import init_db; init_db()"
```

Or create a script:

```bash
cat > /opt/nyiso-dashboard/init_db.py << 'EOF'
from database.schema import init_db
init_db()
EOF

python init_db.py
```

## Step 7: Verify Deployment

### Check Services

```bash
systemctl status nyiso-api
systemctl status nyiso-scraper
systemctl status nginx
```

### Test API

```bash
curl http://localhost:8000/health
```

### View Logs

```bash
# API logs
journalctl -u nyiso-api -f

# Scraper logs
journalctl -u nyiso-scraper -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Step 8: Set Up Backups

Create backup script:

```bash
cat > /opt/nyiso-dashboard/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/nyiso-dashboard/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nyiso_data_$DATE.db"

mkdir -p $BACKUP_DIR
cp /opt/nyiso-dashboard/nyiso_data.db $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "nyiso_data_*.db" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x /opt/nyiso-dashboard/backup.sh
```

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /opt/nyiso-dashboard/backup.sh
```

## Step 9: Configure Firewall

```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

## Step 10: Monitor and Maintain

### Daily Checks

```bash
# Check service status
systemctl status nyiso-api nyiso-scraper

# Check disk space
df -h

# Check logs for errors
journalctl -u nyiso-api --since "1 day ago" | grep -i error
```

### Weekly Tasks

- Review error logs
- Check database size
- Verify backups are running

### Monthly Tasks

- Update system packages: `apt update && apt upgrade`
- Update Python packages: `pip install --upgrade -r requirements.txt`
- Review costs

## Troubleshooting

### Service Won't Start

Check logs:
```bash
journalctl -u nyiso-api -n 50
```

Check permissions:
```bash
ls -la /opt/nyiso-dashboard
chown -R www-data:www-data /opt/nyiso-dashboard
```

### Database Issues

Check database file:
```bash
ls -lh /opt/nyiso-dashboard/nyiso_data.db
```

Test database connection:
```bash
cd /opt/nyiso-dashboard
source venv/bin/activate
python -c "from database.schema import get_session; db = get_session(); print('OK')"
```

### Frontend Not Loading

Check if frontend was built:
```bash
ls -la /opt/nyiso-dashboard/frontend/dist
```

Rebuild frontend:
```bash
cd /opt/nyiso-dashboard/frontend
npm run build
```

### Nginx Issues

Test configuration:
```bash
nginx -t
```

Check error logs:
```bash
tail -f /var/log/nginx/error.log
```

## Updating the Application

1. SSH into server
2. Pull latest code:
   ```bash
   cd /opt/nyiso-dashboard
   git pull
   ```
3. Update dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   cd frontend && npm install && npm run build && cd ..
   ```
4. Restart services:
   ```bash
   systemctl restart nyiso-api
   systemctl restart nyiso-scraper
   systemctl reload nginx
   ```

## Cost Breakdown

- **VPS**: €4.51/month (Hetzner) or $12/month (DigitalOcean)
- **Domain**: $12/year (~$1/month) - Optional
- **SSL**: Free (Let's Encrypt)
- **Total**: **€5.51/month (~$6/month)** or **$13/month**

## Security Best Practices

1. **SSH Hardening**:
   - Disable password authentication
   - Use SSH keys only
   - Change default SSH port (optional)

2. **Firewall**:
   - Only open necessary ports
   - Use UFW or iptables

3. **Updates**:
   - Keep system updated
   - Monitor security advisories

4. **Backups**:
   - Daily database backups
   - Off-site backup storage (optional)

## Support

- Hetzner Docs: https://docs.hetzner.com/
- DigitalOcean Docs: https://docs.digitalocean.com/
- Ubuntu Server Guide: https://ubuntu.com/server/docs


