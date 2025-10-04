#!/bin/bash

# Backup Script for Discord Bot
# Creates backups of the application and database

set -e

# Configuration
APP_DIR="/home/discord-bot/discord-booking-bot"
BACKUP_BASE_DIR="/home/discord-bot/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directories
mkdir -p "$BACKUP_BASE_DIR/application"
mkdir -p "$BACKUP_BASE_DIR/logs"
mkdir -p "$BACKUP_BASE_DIR/config"

print_status "🗄️ Starting backup process..."

# Backup application files
print_status "📦 Backing up application files..."
cd "$APP_DIR"

# Create application backup
tar -czf "$BACKUP_BASE_DIR/application/app-$DATE.tar.gz" \
    --exclude=venv \
    --exclude=.git \
    --exclude=backups \
    --exclude='*.log' \
    --exclude=__pycache__ \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    . 2>/dev/null

if [ $? -eq 0 ]; then
    print_status "Application backup created: app-$DATE.tar.gz"
else
    print_error "Application backup failed!"
    exit 1
fi

# Backup configuration files
print_status "⚙️ Backing up configuration..."
tar -czf "$BACKUP_BASE_DIR/config/config-$DATE.tar.gz" \
    .env \
    credentials/ \
    systemd/ 2>/dev/null

if [ $? -eq 0 ]; then
    print_status "Configuration backup created: config-$DATE.tar.gz"
fi

# Backup logs
print_status "📝 Backing up logs..."
if [ -d "$APP_DIR/logs" ] && [ "$(ls -A $APP_DIR/logs)" ]; then
    tar -czf "$BACKUP_BASE_DIR/logs/logs-$DATE.tar.gz" \
        -C "$APP_DIR" logs/ 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status "Logs backup created: logs-$DATE.tar.gz"
    fi
fi

# Backup system configuration
print_status "🔧 Backing up system configuration..."
sudo tar -czf "$BACKUP_BASE_DIR/config/system-$DATE.tar.gz" \
    /etc/systemd/system/discord-bot.service \
    /etc/systemd/system/discord-webhook.service \
    /etc/nginx/sites-available/discord-bot 2>/dev/null || true

# Clean up old backups
print_status "🧹 Cleaning up old backups..."

# Remove backups older than retention period
find "$BACKUP_BASE_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Get backup statistics
app_backups=$(find "$BACKUP_BASE_DIR/application" -name "*.tar.gz" | wc -l)
config_backups=$(find "$BACKUP_BASE_DIR/config" -name "*.tar.gz" | wc -l)
log_backups=$(find "$BACKUP_BASE_DIR/logs" -name "*.tar.gz" | wc -l)

print_status "✅ Backup completed successfully!"
print_status "📊 Backup statistics:"
print_status "   Application backups: $app_backups"
print_status "   Configuration backups: $config_backups"
print_status "   Log backups: $log_backups"

# Calculate backup size
total_size=$(du -sh "$BACKUP_BASE_DIR" | cut -f1)
print_status "   Total backup size: $total_size"

# Create backup manifest
cat > "$BACKUP_BASE_DIR/backup-manifest-$DATE.txt" << EOF
Discord Bot Backup Manifest
Created: $(date)
Backup Directory: $BACKUP_BASE_DIR
Application Directory: $APP_DIR

Files included in backup:
- Application code and configuration
- Environment variables (.env)
- Service account credentials
- System service files
- Application logs
- Nginx configuration

Retention Policy: $RETENTION_DAYS days

Backup Statistics:
- Application backups: $app_backups
- Configuration backups: $config_backups
- Log backups: $log_backups
- Total size: $total_size
EOF

print_status "📋 Backup manifest created: backup-manifest-$DATE.txt"