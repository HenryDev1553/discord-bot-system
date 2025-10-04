#!/bin/bash

# Discord Bot Deployment Script
# Chạy script này để deploy bot lên VPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
APP_DIR="/home/discord-bot/discord-booking-bot"
BACKUP_DIR="$APP_DIR/backups"

print_step "🚀 Starting deployment..."

# Check if running as discord-bot user or with sudo
if [[ $EUID -eq 0 ]] && [[ -z "$SUDO_USER" ]]; then
    print_error "Don't run this script as root directly. Use sudo or run as discord-bot user."
    exit 1
fi

# Navigate to app directory
if [ ! -d "$APP_DIR" ]; then
    print_error "App directory not found: $APP_DIR"
    print_error "Please run initial setup first!"
    exit 1
fi

cd "$APP_DIR"

print_step "📦 Creating backup..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d_%H%M%S).tar.gz"

# Create backup excluding unnecessary files
if tar -czf "$BACKUP_FILE" \
    --exclude=backups \
    --exclude=venv \
    --exclude=.git \
    --exclude='*.log' \
    --exclude=__pycache__ \
    --exclude='*.pyc' \
    . 2>/dev/null; then
    print_status "Backup created: $(basename "$BACKUP_FILE")"
else
    print_warning "Backup creation failed, continuing anyway..."
fi

print_step "📥 Pulling latest changes..."
git fetch origin
git reset --hard origin/main

print_step "📚 Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

print_step "🔧 Setting permissions..."
chmod +x scripts/*.sh
chmod +x scripts/*.py

print_step "🔄 Restarting services..."
sudo systemctl restart discord-bot
sudo systemctl restart discord-webhook

print_step "⏰ Waiting for services to start..."
sleep 15

print_step "🏥 Health check..."
health_ok=true

# Check Discord bot service
if systemctl is-active --quiet discord-bot; then
    print_status "Discord bot service is running"
else
    print_error "Discord bot service failed to start!"
    print_error "Recent logs:"
    sudo journalctl -u discord-bot --no-pager -n 10
    health_ok=false
fi

# Check webhook service
if systemctl is-active --quiet discord-webhook; then
    print_status "Webhook service is running"
else
    print_error "Webhook service failed to start!"
    print_error "Recent logs:"
    sudo journalctl -u discord-webhook --no-pager -n 10
    health_ok=false
fi

# Check webhook endpoint
if curl -f -s --max-time 10 http://localhost:5001/health > /dev/null; then
    print_status "Webhook endpoint is responding"
else
    print_warning "Webhook endpoint not responding"
    health_ok=false
fi

# Clean up old backups (keep last 10)
find "$BACKUP_DIR" -name "backup-*.tar.gz" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true

if [ "$health_ok" = true ]; then
    print_step "✅ Deployment completed successfully!"
    print_status "Services are healthy and running"
else
    print_step "⚠️ Deployment completed with warnings"
    print_warning "Some services may have issues. Check logs for details."
    exit 1
fi