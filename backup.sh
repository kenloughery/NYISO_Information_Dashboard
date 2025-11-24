#!/bin/bash
# Daily database backup script
# Add to crontab: 0 2 * * * /opt/nyiso-dashboard/backup.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_DIR="$SCRIPT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="$SCRIPT_DIR/nyiso_data.db"
BACKUP_FILE="$BACKUP_DIR/nyiso_data_$DATE.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "⚠️  Database file not found: $DB_FILE"
    exit 1
fi

# Backup SQLite database
echo "💾 Backing up database..."
cp "$DB_FILE" "$BACKUP_FILE"

# Compress backup
echo "📦 Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Keep only last 30 days
echo "🧹 Cleaning old backups..."
find "$BACKUP_DIR" -name "nyiso_data_*.db.gz" -mtime +30 -delete

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "✅ Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

# Optional: Upload to S3 or other storage
# aws s3 cp "$BACKUP_FILE" s3://your-bucket/backups/

