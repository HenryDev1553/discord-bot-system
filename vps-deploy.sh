#!/bin/bash

# Discord Bot VPS Deployment Script
# Chạy script này trên VPS để deploy hệ thống Discord Booking Bot

set -e

echo "🚀 Discord Bot VPS Deployment"
echo "==============================="

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

# Variables
GITHUB_REPO="https://github.com/HenryDev1553/discord-bot-system.git"
APP_DIR="/home/discord-bot/discord-booking-bot"
SERVICE_USER="discord-bot"

print_step "1. System Update and Dependencies Installation"
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw htop curl jq

print_step "2. Create Application User"
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $SERVICE_USER
    print_status "Created user: $SERVICE_USER"
else
    print_warning "User $SERVICE_USER already exists"
fi

print_step "3. Clone Repository"
sudo -u $SERVICE_USER mkdir -p $APP_DIR
cd $APP_DIR
sudo -u $SERVICE_USER git clone $GITHUB_REPO .

print_step "4. Setup Python Virtual Environment"
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER bash -c "source venv/bin/activate && pip install -r requirements.txt"

print_step "5. Setup Configuration"
sudo -u $SERVICE_USER cp .env.example .env
sudo -u $SERVICE_USER mkdir -p credentials logs backups

print_warning "IMPORTANT: You need to configure the following:"
echo "1. Edit .env file: sudo -u $SERVICE_USER nano $APP_DIR/.env"
echo "2. Upload Google credentials: sudo cp your-credentials.json $APP_DIR/credentials/service-account.json"
echo "3. Set proper permissions: sudo chown $SERVICE_USER:$SERVICE_USER $APP_DIR/credentials/service-account.json"

print_step "6. Create Systemd Services"

# Discord Bot Service
sudo tee /etc/systemd/system/discord-bot.service << EOF
[Unit]
Description=Discord Booking Bot
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
EOF

# Webhook Service
sudo tee /etc/systemd/system/discord-webhook.service << EOF
[Unit]
Description=Discord Booking Webhook
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python -c "from web.webhook_server import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000)"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

print_step "7. Setup Nginx"
read -p "Enter your domain name (e.g., bot.example.com): " DOMAIN_NAME
if [[ -z "$DOMAIN_NAME" ]]; then
    print_error "Domain name is required!"
    exit 1
fi

sudo tee /etc/nginx/sites-available/discord-bot << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=webhook:10m rate=30r/m;
    limit_req_zone \$binary_remote_addr zone=health:10m rate=60r/m;

    # Health check endpoint
    location /health {
        limit_req zone=health burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }

    # Webhook endpoint
    location /webhook/booking {
        limit_req zone=webhook burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000/webhook/booking;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 30;
        proxy_connect_timeout 30;
        proxy_send_timeout 30;
    }

    # Block other requests
    location / {
        return 404;
    }

    # Security
    server_tokens off;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain application/json;
}
EOF

sudo ln -sf /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

print_step "8. Setup Firewall"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

print_step "9. Setup SSL Certificate"
print_status "Setting up SSL certificate with Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME

print_step "10. Create Management Scripts"

# Deployment script
sudo -u $SERVICE_USER tee $APP_DIR/deploy.sh << 'EOF'
#!/bin/bash
set -e
cd /home/discord-bot/discord-booking-bot

echo "🚀 Starting deployment..."

# Backup current version
tar -czf backups/backup-$(date +%Y%m%d_%H%M%S).tar.gz . --exclude=backups --exclude=venv --exclude=.git

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart discord-bot discord-webhook

# Wait and check status
sleep 5
if systemctl is-active --quiet discord-bot && systemctl is-active --quiet discord-webhook; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed! Check service status."
    exit 1
fi
EOF

# Health check script
sudo -u $SERVICE_USER tee $APP_DIR/health-check.sh << EOF
#!/bin/bash
WEBHOOK_URL="https://$DOMAIN_NAME/health"
LOG_FILE="$APP_DIR/logs/health-check.log"

mkdir -p $APP_DIR/logs

log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> \$LOG_FILE
}

# Check webhook endpoint
if curl -f -s \$WEBHOOK_URL > /dev/null 2>&1; then
    log_message "✅ Webhook is healthy"
else
    log_message "❌ Webhook is down! Attempting restart..."
    sudo systemctl restart discord-webhook
    sleep 10
    if curl -f -s \$WEBHOOK_URL > /dev/null 2>&1; then
        log_message "✅ Webhook restarted successfully"
    else
        log_message "❌ Webhook restart failed!"
    fi
fi

# Check Discord bot service
if systemctl is-active --quiet discord-bot; then
    log_message "✅ Discord bot is running"
else
    log_message "❌ Discord bot is down! Attempting restart..."
    sudo systemctl restart discord-bot
    log_message "🔄 Discord bot restart initiated"
fi

# Clean old logs (keep last 1000 lines)
tail -n 1000 \$LOG_FILE > \$LOG_FILE.tmp && mv \$LOG_FILE.tmp \$LOG_FILE
EOF

sudo chmod +x $APP_DIR/deploy.sh $APP_DIR/health-check.sh

print_step "11. Setup Cron Jobs"
# Add cron jobs for health check and cleanup
(sudo -u $SERVICE_USER crontab -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/health-check.sh") | sudo -u $SERVICE_USER crontab -
(sudo -u $SERVICE_USER crontab -l 2>/dev/null; echo "0 2 * * 0 find $APP_DIR/backups -name '*.tar.gz' -mtime +30 -delete") | sudo -u $SERVICE_USER crontab -

print_step "12. Setup Log Rotation"
sudo tee /etc/logrotate.d/discord-bot << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload discord-bot >/dev/null 2>&1 || true
        systemctl reload discord-webhook >/dev/null 2>&1 || true
    endscript
}
EOF

print_step "✅ VPS Setup Completed!"
echo ""
print_warning "NEXT STEPS:"
echo "1. Configure environment variables:"
echo "   sudo -u $SERVICE_USER nano $APP_DIR/.env"
echo ""
echo "2. Upload Google Service Account credentials:"
echo "   sudo cp /path/to/your-credentials.json $APP_DIR/credentials/service-account.json"
echo "   sudo chown $SERVICE_USER:$SERVICE_USER $APP_DIR/credentials/service-account.json"
echo ""
echo "3. Start services:"
echo "   sudo systemctl enable discord-bot discord-webhook"
echo "   sudo systemctl start discord-bot discord-webhook"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status discord-bot discord-webhook"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u discord-bot -f"
echo "   sudo journalctl -u discord-webhook -f"
echo ""
print_status "🌍 Your webhook URL: https://$DOMAIN_NAME/webhook/booking"
print_status "🏥 Health check URL: https://$DOMAIN_NAME/health"
print_status "📁 Application directory: $APP_DIR"
print_status "🔧 Deploy command: $APP_DIR/deploy.sh"
print_status "💊 Health check: $APP_DIR/health-check.sh"
