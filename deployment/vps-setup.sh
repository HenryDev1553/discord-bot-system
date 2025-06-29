#!/bin/bash

# Discord Bot System - One-click VPS Setup Script
# Run this script on a fresh Ubuntu 22.04 VPS

set -e

echo "🚀 Starting Discord Bot VPS Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw htop curl software-properties-common

# Install Docker (optional, for containerization)
print_status "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Create application user
print_status "Creating discord-bot user..."
sudo useradd -m -s /bin/bash discord-bot || true
sudo usermod -aG sudo discord-bot

# Setup application directory
print_status "Setting up application directory..."
sudo mkdir -p /home/discord-bot/discord-booking-bot
sudo chown discord-bot:discord-bot /home/discord-bot/discord-booking-bot

# Prompt for domain name
read -p "Enter your domain name (e.g., bot.example.com): " DOMAIN_NAME
if [[ -z "$DOMAIN_NAME" ]]; then
    print_error "Domain name is required!"
    exit 1
fi

# Create environment file template
print_status "Creating environment configuration..."
sudo -u discord-bot tee /home/discord-bot/discord-booking-bot/.env.template << EOF
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_discord_channel_id_here

# Google Services Configuration
GOOGLE_SHEETS_ID=your_google_sheets_id_here
GOOGLE_CREDENTIALS_PATH=/home/discord-bot/discord-booking-bot/credentials/service-account.json
GOOGLE_CALENDAR_ID=your_google_calendar_id_here
SHEET_NAME=Sheet1

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password_here

# Webhook Configuration
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
WEBHOOK_URL=https://${DOMAIN_NAME}/webhook/booking

# Application Settings
TIMEZONE=Asia/Ho_Chi_Minh
DEBUG=False
LOG_LEVEL=INFO
EOF

# Create credentials directory
sudo -u discord-bot mkdir -p /home/discord-bot/discord-booking-bot/credentials

# Create systemd service files
print_status "Creating systemd service files..."

# Discord Bot Service
sudo tee /etc/systemd/system/discord-bot.service << EOF
[Unit]
Description=Discord Booking Bot
After=network.target

[Service]
Type=simple
User=discord-bot
WorkingDirectory=/home/discord-bot/discord-booking-bot
Environment=PATH=/home/discord-bot/discord-booking-bot/venv/bin
ExecStart=/home/discord-bot/discord-booking-bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

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
User=discord-bot
WorkingDirectory=/home/discord-bot/discord-booking-bot
Environment=PATH=/home/discord-bot/discord-booking-bot/venv/bin
ExecStart=/home/discord-bot/discord-booking-bot/venv/bin/python -c "from web.webhook_server import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000)"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/discord-bot << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=webhook:10m rate=10r/m;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    location /webhook/booking {
        limit_req zone=webhook burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000/webhook/booking;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }

    # Security: Hide server info
    server_tokens off;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Configure firewall
print_status "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Create backup script
print_status "Creating backup script..."
sudo -u discord-bot tee /home/discord-bot/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/discord-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup application
tar -czf $BACKUP_DIR/discord-bot-$DATE.tar.gz \
    /home/discord-bot/discord-booking-bot \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git"

# Keep only last 7 backups
find $BACKUP_DIR -name "discord-bot-*.tar.gz" -type f -mtime +7 -delete

echo "Backup completed: discord-bot-$DATE.tar.gz"
EOF

sudo chmod +x /home/discord-bot/backup.sh

# Create health check script
print_status "Creating health check script..."
sudo -u discord-bot tee /home/discord-bot/health-check.sh << EOF
#!/bin/bash
WEBHOOK_URL="https://${DOMAIN_NAME}/health"
LOG_FILE="/home/discord-bot/health-check.log"

# Function to log with timestamp
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> \$LOG_FILE
}

# Check webhook endpoint
if curl -f -s \$WEBHOOK_URL > /dev/null; then
    log_message "Webhook is healthy"
else
    log_message "Webhook is down! Attempting restart..."
    sudo systemctl restart discord-webhook
    sleep 10
    if curl -f -s \$WEBHOOK_URL > /dev/null; then
        log_message "Webhook restarted successfully"
    else
        log_message "Webhook restart failed!"
    fi
fi

# Check Discord bot service
if systemctl is-active --quiet discord-bot; then
    log_message "Discord bot is running"
else
    log_message "Discord bot is down! Attempting restart..."
    sudo systemctl restart discord-bot
fi

# Clean old logs (keep last 100 lines)
tail -n 100 \$LOG_FILE > \$LOG_FILE.tmp && mv \$LOG_FILE.tmp \$LOG_FILE
EOF

sudo chmod +x /home/discord-bot/health-check.sh

# Create deployment script
print_status "Creating deployment script..."
sudo -u discord-bot tee /home/discord-bot/deploy.sh << 'EOF'
#!/bin/bash
set -e

cd /home/discord-bot/discord-booking-bot

echo "🚀 Starting deployment..."

# Backup current version
./backup.sh

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests (if available)
if [ -f "run_tests.py" ]; then
    echo "🧪 Running tests..."
    python run_tests.py
fi

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart discord-bot
sudo systemctl restart discord-webhook

# Wait for services to start
sleep 5

# Check service status
if systemctl is-active --quiet discord-bot && systemctl is-active --quiet discord-webhook; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed! Check service status."
    sudo systemctl status discord-bot
    sudo systemctl status discord-webhook
    exit 1
fi
EOF

sudo chmod +x /home/discord-bot/deploy.sh

# Setup log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/discord-bot << 'EOF'
/home/discord-bot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 discord-bot discord-bot
    postrotate
        systemctl reload discord-bot >/dev/null 2>&1 || true
        systemctl reload discord-webhook >/dev/null 2>&1 || true
    endscript
}
EOF

# Reload systemd
sudo systemctl daemon-reload

print_status "✅ VPS setup completed successfully!"
print_warning "Next steps:"
echo "1. Upload your source code to /home/discord-bot/discord-booking-bot/"
echo "2. Copy .env.template to .env and configure your settings"
echo "3. Upload your Google service account JSON to /home/discord-bot/discord-booking-bot/credentials/"
echo "4. Setup SSL certificate: sudo certbot --nginx -d $DOMAIN_NAME"
echo "5. Start services: sudo systemctl start discord-bot discord-webhook"
echo "6. Setup cron jobs for health check and backup"
echo ""
print_status "Useful commands:"
echo "- Check status: sudo systemctl status discord-bot discord-webhook"
echo "- View logs: sudo journalctl -u discord-bot -f"
echo "- Deploy updates: /home/discord-bot/deploy.sh"
echo "- Backup: /home/discord-bot/backup.sh"
echo "- Health check: /home/discord-bot/health-check.sh"
echo ""
print_status "Your webhook URL will be: https://$DOMAIN_NAME/webhook/booking"
EOF
