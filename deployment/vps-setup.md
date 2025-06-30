# VPS Setup Guide cho Discord Booking Bot

## 1. Tạo VPS trên Digital Ocean

### Cấu hình khuyến nghị:
- **Distro**: Ubuntu 22.04 LTS
- **RAM**: Tối thiểu 1GB (khuyến nghị 2GB)
- **Storage**: 25GB
- **Region**: Singapore hoặc gần Việt Nam

### Bước đầu:
```bash
# Kết nối SSH
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Cài đặt các package cần thiết
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw htop
```

## 2. Cài đặt Python Environment

```bash
# Tạo user cho application
useradd -m -s /bin/bash discord-bot
usermod -aG sudo discord-bot

# Đổi sang user discord-bot
su - discord-bot

# Tạo thư mục project
mkdir -p /home/discord-bot/discord-booking-bot
cd /home/discord-bot/discord-booking-bot

# Clone source code (hoặc upload file)
git clone https://github.com/your-repo/discord-bot-system.git .
# Hoặc: scp -r local-folder/* root@vps-ip:/home/discord-bot/discord-booking-bot/

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

## 3. Cấu hình Environment Variables

```bash
# Tạo file .env
cp .env.example .env
nano .env
```

Nội dung file .env:
```env
# Discord Bot
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_channel_id

# Google Sheets & Calendar
GOOGLE_SHEETS_ID=your_sheet_id
GOOGLE_CREDENTIALS_PATH=/home/discord-bot/discord-booking-bot/credentials/service-account.json
GOOGLE_CALENDAR_ID=your_calendar_id
SHEET_NAME=Sheet1

# Email via Google Apps Script
APPSCRIPT_WEBHOOK_URL=your_appscript_webhook_url
APPSCRIPT_TIMEOUT=30
APPSCRIPT_MAX_RETRIES=3
DISABLE_EMAIL=false

# Webhook
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
WEBHOOK_URL=https://your-domain.com/webhook/booking

# Other
TIMEZONE=Asia/Ho_Chi_Minh
DEBUG=False
```

## 4. Upload Credentials

```bash
# Tạo thư mục credentials
mkdir -p /home/discord-bot/discord-booking-bot/credentials

# Upload service account key
# Từ máy local:
scp path/to/service-account.json discord-bot@vps-ip:/home/discord-bot/discord-booking-bot/credentials/

# Set permissions
chmod 600 /home/discord-bot/discord-booking-bot/credentials/service-account.json
```

## 5. Cấu hình Systemd Services

### Discord Bot Service:
```bash
sudo nano /etc/systemd/system/discord-bot.service
```

```ini
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

[Install]
WantedBy=multi-user.target
```

### Webhook Service:
```bash
sudo nano /etc/systemd/system/discord-webhook.service
```

```ini
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

[Install]
WantedBy=multi-user.target
```

## 6. Cấu hình Nginx

```bash
sudo nano /etc/nginx/sites-available/discord-bot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Cấu hình SSL Certificate

```bash
# Cài đặt SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 8. Cấu hình Firewall

```bash
# Cấu hình UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Kiểm tra status
sudo ufw status
```

## 9. Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable và start services
sudo systemctl enable discord-bot
sudo systemctl enable discord-webhook
sudo systemctl start discord-bot
sudo systemctl start discord-webhook

# Kiểm tra status
sudo systemctl status discord-bot
sudo systemctl status discord-webhook
```

## 10. Monitoring & Logging

```bash
# Xem logs
sudo journalctl -u discord-bot -f
sudo journalctl -u discord-webhook -f

# Xem logs với filter
sudo journalctl -u discord-bot --since "1 hour ago"

# Tạo log rotation
sudo nano /etc/logrotate.d/discord-bot
```

```
/var/log/discord-bot/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 discord-bot discord-bot
    postrotate
        systemctl reload discord-bot
        systemctl reload discord-webhook
    endscript
}
```

## 11. Backup Script

```bash
nano /home/discord-bot/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/discord-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup source code
tar -czf $BACKUP_DIR/discord-bot-$DATE.tar.gz \
    /home/discord-bot/discord-booking-bot \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude="*.pyc"

# Keep only last 7 backups
find $BACKUP_DIR -name "discord-bot-*.tar.gz" -type f -mtime +7 -delete

echo "Backup completed: discord-bot-$DATE.tar.gz"
```

```bash
chmod +x /home/discord-bot/backup.sh

# Thêm vào crontab
crontab -e
# Thêm dòng: 0 2 * * * /home/discord-bot/backup.sh
```

## 12. Health Check Script

```bash
nano /home/discord-bot/health-check.sh
```

```bash
#!/bin/bash
WEBHOOK_URL="https://your-domain.com/health"
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your-webhook-id/your-webhook-token"

# Check webhook endpoint
if curl -f -s $WEBHOOK_URL > /dev/null; then
    echo "Webhook is healthy"
else
    echo "Webhook is down!"
    # Send alert to Discord
    curl -X POST $DISCORD_WEBHOOK_URL \
        -H "Content-Type: application/json" \
        -d '{"content": "🚨 Discord Bot Webhook is DOWN! Please check the server."}'
fi

# Check Discord bot service
if systemctl is-active --quiet discord-bot; then
    echo "Discord bot is running"
else
    echo "Discord bot is down!"
    sudo systemctl restart discord-bot
fi
```

```bash
chmod +x /home/discord-bot/health-check.sh

# Thêm vào crontab để check mỗi 5 phút
crontab -e
# Thêm dòng: */5 * * * * /home/discord-bot/health-check.sh
```

## 13. Update Webhook URL

Cập nhật webhook URL trong Google Apps Script:
```javascript
// Trong Apps Script
const WEBHOOK_URL = 'https://your-domain.com/webhook/booking';
```

## 14. Troubleshooting Commands

```bash
# Kiểm tra services
sudo systemctl status discord-bot discord-webhook nginx

# Xem logs
sudo journalctl -u discord-bot -f
sudo journalctl -u discord-webhook -f
sudo tail -f /var/log/nginx/error.log

# Test webhook
curl -X POST https://your-domain.com/health

# Restart services
sudo systemctl restart discord-bot
sudo systemctl restart discord-webhook
sudo systemctl reload nginx

# Check ports
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## 15. Performance Optimization

```bash
# Cấu hình swap (nếu VPS có ít RAM)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize Python
pip install gunicorn

# Cập nhật webhook service để dùng gunicorn
sudo nano /etc/systemd/system/discord-webhook.service
```

```ini
[Unit]
Description=Discord Booking Webhook
After=network.target

[Service]
Type=simple
User=discord-bot
WorkingDirectory=/home/discord-bot/discord-booking-bot
Environment=PATH=/home/discord-bot/discord-booking-bot/venv/bin
ExecStart=/home/discord-bot/discord-booking-bot/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 "web.webhook_server:create_app()"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 16. Security Checklist

- [ ] Đổi port SSH mặc định
- [ ] Cấu hình SSH key authentication
- [ ] Disable root login
- [ ] Cài đặt fail2ban
- [ ] Cấu hình firewall UFW
- [ ] SSL certificate cho domain
- [ ] Backup credentials an toàn
- [ ] Monitoring và alerting
- [ ] Regular updates

## 17. Maintenance

```bash
# Weekly maintenance script
nano /home/discord-bot/maintenance.sh
```

```bash
#!/bin/bash
# Update system
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart discord-bot
sudo systemctl restart discord-webhook

# Clean up logs older than 30 days
sudo journalctl --vacuum-time=30d

# Check disk space
df -h

echo "Maintenance completed at $(date)"
```

Chạy script này hàng tuần để maintain VPS.
