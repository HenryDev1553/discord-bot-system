# VPS Deployment Guide

## 📋 Yêu cầu VPS

- **OS**: Ubuntu 22.04 LTS
- **RAM**: Tối thiểu 1GB (khuyến nghị 2GB)
- **Storage**: Tối thiểu 10GB
- **Network**: Public IP với domain name
- **Access**: SSH root hoặc sudo user

## 🚀 Deployment Steps

### 1. Chuẩn bị VPS

```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Tạo user mới (nếu chưa có)
sudo adduser admin
sudo usermod -aG sudo admin

# Chuyển sang user mới
su - admin
```

### 2. Download và chạy deployment script

```bash
# Download script
curl -sSL https://raw.githubusercontent.com/HenryDev1553/discord-bot-system/main/vps-deploy.sh -o vps-deploy.sh

# Cấp quyền thực thi
chmod +x vps-deploy.sh

# Chạy script
./vps-deploy.sh
```

Script sẽ tự động:
- Cài đặt Python, Git, Nginx, Certbot
- Tạo user `discord-bot`
- Clone repository từ GitHub
- Setup virtual environment
- Tạo systemd services
- Cấu hình Nginx với SSL
- Setup firewall
- Tạo scripts quản lý

### 3. Cấu hình sau khi deploy

#### 3.1. Cấu hình biến môi trường

```bash
sudo -u discord-bot nano /home/discord-bot/discord-booking-bot/.env
```

Điền thông tin:
- `DISCORD_BOT_TOKEN`: Token của Discord Bot
- `DISCORD_CHANNEL_ID`: ID channel Discord
- `GOOGLE_SHEETS_ID`: ID của Google Sheet
- `APPSCRIPT_WEBHOOK_URL`: URL của Google Apps Script Web App để gửi email
- `GOOGLE_CALENDAR_ID`: ID của Google Calendar

#### 3.2. Upload Google Service Account credentials

```bash
# Copy file credentials từ máy local lên server
scp /path/to/your-service-account.json user@your-server:/tmp/

# Move và set permissions
sudo cp /tmp/your-service-account.json /home/discord-bot/discord-booking-bot/credentials/service-account.json
sudo chown discord-bot:discord-bot /home/discord-bot/discord-booking-bot/credentials/service-account.json
sudo chmod 600 /home/discord-bot/discord-booking-bot/credentials/service-account.json
```

### 4. Khởi động services

```bash
# Enable services
sudo systemctl enable discord-bot discord-webhook

# Start services
sudo systemctl start discord-bot discord-webhook

# Kiểm tra status
sudo systemctl status discord-bot discord-webhook
```

### 5. Kiểm tra hoạt động

```bash
# Test health endpoint
curl https://your-domain.com/health

# Xem logs
sudo journalctl -u discord-bot -f
sudo journalctl -u discord-webhook -f

# Test webhook (optional)
curl -X POST https://your-domain.com/webhook/booking \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## 🔧 Quản lý hệ thống

### Commands thường dùng

```bash
# Restart services
sudo systemctl restart discord-bot discord-webhook

# Stop services
sudo systemctl stop discord-bot discord-webhook

# View logs
sudo journalctl -u discord-bot --since "1 hour ago"
sudo journalctl -u discord-webhook --since "1 hour ago"

# Deploy update
/home/discord-bot/discord-booking-bot/deploy.sh

# Manual health check
/home/discord-bot/discord-booking-bot/health-check.sh
```

### File locations

- **Application**: `/home/discord-bot/discord-booking-bot/`
- **Logs**: `/home/discord-bot/discord-booking-bot/logs/`
- **Backups**: `/home/discord-bot/discord-booking-bot/backups/`
- **Nginx config**: `/etc/nginx/sites-available/discord-bot`
- **Services**: `/etc/systemd/system/discord-*.service`

## 📊 Monitoring

### Health check endpoint
```
GET https://your-domain.com/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-15T10:30:00",
  "service": "Discord Booking System"
}
```

### Log monitoring

```bash
# Real-time logs
sudo journalctl -u discord-bot -u discord-webhook -f

# Error logs
sudo journalctl -u discord-bot -p err

# Logs trong 24h qua
sudo journalctl -u discord-bot --since "24 hours ago"
```

## 🔄 Updates và Deployment

### Auto deployment

```bash
# Chạy deployment script
/home/discord-bot/discord-booking-bot/deploy.sh
```

Script sẽ:
1. Backup version hiện tại
2. Pull code mới từ GitHub
3. Update dependencies
4. Restart services
5. Verify deployment

### Manual deployment

```bash
cd /home/discord-bot/discord-booking-bot
sudo -u discord-bot git pull origin main
sudo -u discord-bot bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart discord-bot discord-webhook
```

## 🔒 Security

### SSL Certificate renewal

```bash
# Auto renewal đã được setup, kiểm tra:
sudo crontab -l | grep certbot

# Manual renewal
sudo certbot renew --dry-run
```

### Firewall status

```bash
sudo ufw status verbose
```

### Service hardening

Services chạy với user `discord-bot` (không phải root) để đảm bảo security.

## 📈 Performance tuning

### Nginx rate limiting

Current settings trong `/etc/nginx/sites-available/discord-bot`:
- Webhook: 30 requests/minute
- Health check: 60 requests/minute

### System resources

```bash
# Kiểm tra memory usage
sudo systemctl status discord-bot discord-webhook
htop

# Kiểm tra disk usage
df -h
du -sh /home/discord-bot/discord-booking-bot/
```

## 🚨 Troubleshooting

### Service không start

```bash
# Kiểm tra logs
sudo journalctl -u discord-bot --since "10 minutes ago"

# Kiểm tra config
sudo -u discord-bot /home/discord-bot/discord-booking-bot/venv/bin/python -c "from config import Config; print('Config OK')"
```

### Nginx errors

```bash
# Test config
sudo nginx -t

# Reload config
sudo systemctl reload nginx

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### SSL issues

```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs: `sudo journalctl -u discord-bot -u discord-webhook`
2. Kiểm tra health endpoint: `curl https://your-domain.com/health`
3. Kiểm tra firewall: `sudo ufw status`
4. Kiểm tra Nginx: `sudo nginx -t`

---

## ⚙️ Advanced Configuration

### Custom domain với Cloudflare

1. Thêm DNS record trong Cloudflare
2. Enable SSL/TLS encryption mode: "Full (strict)"
3. Cấu hình WAF rules để bảo vệ webhook endpoint

### Database backup (nếu cần)

```bash
# Tạo script backup cho Google Sheets data
# (Data đã được lưu trong Google Sheets nên không cần backup riêng)
```

### Load balancing (cho traffic cao)

Nếu cần handle traffic cao, có thể setup multiple instances với load balancer.
