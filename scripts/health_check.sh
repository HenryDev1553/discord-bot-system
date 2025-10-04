#!/bin/bash

# Discord Bot Health Check Script
# Simplified bash version for cron jobs

set -e

# Configuration
APP_DIR="/home/discord-bot/discord-booking-bot"
LOG_FILE="$APP_DIR/logs/health-check.log"
WEBHOOK_URL="http://localhost:5001/health"

# Ensure log directory exists
mkdir -p "$APP_DIR/logs"

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_message "🏥 Starting health check..."

# Check webhook endpoint
if curl -f -s --max-time 10 "$WEBHOOK_URL" > /dev/null 2>&1; then
    log_message "✅ Webhook is healthy"
    webhook_healthy=true
else
    log_message "❌ Webhook is down! Attempting restart..."
    webhook_healthy=false
    
    # Restart webhook service
    if sudo systemctl restart discord-webhook; then
        log_message "🔄 Webhook service restarted"
        sleep 10
        
        # Check again
        if curl -f -s --max-time 10 "$WEBHOOK_URL" > /dev/null 2>&1; then
            log_message "✅ Webhook recovered after restart"
            webhook_healthy=true
        else
            log_message "❌ Webhook still down after restart"
        fi
    else
        log_message "❌ Failed to restart webhook service"
    fi
fi

# Check Discord bot service
if systemctl is-active --quiet discord-bot; then
    log_message "✅ Discord bot is running"
    bot_healthy=true
else
    log_message "❌ Discord bot is down! Attempting restart..."
    bot_healthy=false
    
    # Restart bot service
    if sudo systemctl restart discord-bot; then
        log_message "🔄 Discord bot service restarted"
        sleep 15
        
        # Check again
        if systemctl is-active --quiet discord-bot; then
            log_message "✅ Discord bot recovered after restart"
            bot_healthy=true
        else
            log_message "❌ Discord bot still down after restart"
        fi
    else
        log_message "❌ Failed to restart Discord bot service"
    fi
fi

# Check disk space
DISK_USAGE=$(df "$APP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    log_message "⚠️ High disk usage: ${DISK_USAGE}%"
    
    # Clean up old backups (keep last 10)
    find "$APP_DIR/backups" -name "*.tar.gz" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
    log_message "🧹 Cleaned up old backups"
    
    # Truncate large log files
    find "$APP_DIR/logs" -name "*.log" -size +50M -exec truncate -s 10M {} \; 2>/dev/null || true
    log_message "🧹 Truncated large log files"
else
    log_message "✅ Disk usage normal: ${DISK_USAGE}%"
fi

# Clean old log entries (keep last 1000 lines)
if [ -f "$LOG_FILE" ]; then
    tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

# Summary
if [ "$webhook_healthy" = true ] && [ "$bot_healthy" = true ]; then
    log_message "✅ All services healthy"
    exit 0
else
    log_message "❌ Some services are unhealthy"
    exit 1
fi