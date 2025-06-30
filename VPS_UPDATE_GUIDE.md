# VPS Update Guide - Pull Code Mới và Restart Service

## 🚀 Các bước cập nhật code trên VPS

### 1. SSH vào VPS
```bash
ssh your_user@your_vps_ip
```

### 2. Chuyển đến thư mục project
```bash
cd /home/discord-bot/discord-booking-bot
```

### 3. Pull code mới từ GitHub
```bash
# Kiểm tra git status
sudo -u discord-bot git status

# Pull code mới
sudo -u discord-bot git pull origin main
```

### 4. Kiểm tra thay đổi (optional)
```bash
# Xem files đã thay đổi
sudo -u discord-bot git log --oneline -5

# Kiểm tra cấu hình .env vẫn còn
sudo -u discord-bot ls -la .env
```

### 5. Restart Discord Bot Service
```bash
# Stop service
sudo systemctl stop discord-bot

# Start service
sudo systemctl start discord-bot

# Kiểm tra status
sudo systemctl status discord-bot

# Xem logs real-time
sudo journalctl -u discord-bot -f
```

### 6. Test hệ thống

#### 6.1 Kiểm tra Health Endpoint
```bash
curl http://localhost:5001/health
```

#### 6.2 Kiểm tra Discord Bot
- Vào Discord server
- Thử gửi form booking mới
- Kiểm tra bot có nhận được và reply không

#### 6.3 Kiểm tra Email System  
- Test gửi email confirmation/cancellation
- Check logs xem có lỗi email không

## 🔍 Troubleshooting

### Nếu service không start được:
```bash
# Xem lỗi chi tiết
sudo journalctl -u discord-bot --no-pager

# Kiểm tra port có bị conflict không
sudo netstat -tulpn | grep :5001

# Test chạy thủ công
sudo -u discord-bot cd /home/discord-bot/discord-booking-bot && python3 main.py
```

### Nếu git pull bị lỗi:
```bash
# Reset về trạng thái clean
sudo -u discord-bot git stash

# Hoặc force pull
sudo -u discord-bot git reset --hard origin/main
sudo -u discord-bot git pull origin main
```

### Nếu cần update dependencies:
```bash
# Cài đặt packages mới (nếu có)
sudo -u discord-bot pip3 install -r requirements.txt
```

## ✅ Xác nhận thành công

Sau khi restart, bạn sẽ thấy:
- ✅ Service status: Active (running)
- ✅ Health endpoint trả về 200 OK
- ✅ Discord bot online trong server
- ✅ Logs không có lỗi critical
- ✅ Email system hoạt động (chỉ Apps Script)

## 📝 Commands tóm tắt

```bash
# Full update sequence
cd /home/discord-bot/discord-booking-bot
sudo -u discord-bot git pull origin main
sudo systemctl restart discord-bot
sudo systemctl status discord-bot
curl http://localhost:5001/health
```

**Lưu ý**: Hệ thống bây giờ chỉ dùng Google Apps Script để gửi email, không còn SMTP nên sẽ ổn định hơn trên VPS!
