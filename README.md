# Discord Booking System 🤖

Hệ thống quản lý đặt lịch tự động tích hợp Discord, Google Sheets, Gmail và Google Calendar cho Coffee Workspace.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Tính năng chính

- 🔄 **Tự động nhận booking** từ Google Forms qua webhook
- 💬 **Gửi thông báo Discord** với interactive buttons  
- ✅ **Xác nhận/Hủy booking** trực tiếp từ Discord
- 📅 **Tự động tạo Google Calendar event** khi xác nhận
- 📧 **Gửi email tự động** (xác nhận/hủy)
- 🔍 **Kiểm tra conflict lịch phòng** thời gian thực
- 📊 **Cập nhật trạng thái** trong Google Sheets
- 🛡️ **Bảo mật và logging** đầy đủ

## 🏗️ Kiến trúc hệ thống

```
Google Forms → Apps Script → Webhook → Discord Bot
                                  ↓
Google Calendar ← Google Sheets ← Email System
```

## 📋 Yêu cầu hệ thống

- Python 3.10+
- Gmail với App Password
- Google Cloud Project với Sheets API + Calendar API enabled
- Discord Bot Token
- ngrok (để expose local server)

## 🛠️ Cài đặt

### 1. Clone và cài đặt dependencies

```bash
# Clone repository
git clone <repo-url>
cd discord-bot-system

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt packages
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường

```bash
# Copy file .env.example thành .env
cp .env.example .env

# Chỉnh sửa file .env với thông tin thực tế
nano .env
```

### 3. Cấu hình Google Cloud & Sheets API

#### 3.1. Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Enable Google Sheets API:
   - Vào "APIs & Services" > "Library"
   - Tìm "Google Sheets API" và enable

#### 3.2. Tạo Service Account

1. Vào "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Điền thông tin service account
4. Tạo và download JSON key file
5. Đổi tên file thành `credentials.json` và đặt trong thư mục gốc

#### 3.3. Chia sẻ Google Sheet

1. Mở Google Sheet của bạn
2. Click "Share" 
3. Thêm email của service account (tìm trong file credentials.json)
4. Cấp quyền "Editor"

#### 3.4. Enable Google Calendar API

**⚠️ QUAN TRỌNG: Cần enable Google Calendar API để tự động thêm lịch đã xác nhận vào Calendar**

1. Truy cập [Google Cloud Console - Calendar API](https://console.developers.google.com/apis/library/calendar-json.googleapis.com)
2. Chọn project của bạn
3. Click **"Enable"** 
4. Đợi 2-3 phút để hệ thống áp dụng

Hoặc enable từ API Library:
1. Vào [API Library](https://console.cloud.google.com/apis/library)
2. Tìm "Google Calendar API"
3. Click "Enable"

### 4. Cấu hình Discord Bot

#### 4.1. Tạo Discord Application

1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Đặt tên và tạo application

#### 4.2. Tạo Bot User

1. Vào tab "Bot" 
2. Click "Add Bot"
3. Copy Bot Token và paste vào file `.env`

#### 4.3. Cấu hình Bot Permissions

Cần các permissions sau:
- Send Messages
- Use Slash Commands
- Read Message History
- Add Reactions
- Embed Links

#### 4.4. Mời Bot vào Server

1. Vào tab "OAuth2" > "URL Generator"
2. Chọn scope: `bot` và `applications.commands`
3. Chọn permissions cần thiết
4. Copy URL và mời bot vào server

### 5. Cấu hình Gmail SMTP

#### 5.1. Bật 2-Factor Authentication

1. Vào Google Account Settings
2. Security > 2-Step Verification
3. Bật 2FA

#### 5.2. Tạo App Password

1. Vào Security > App passwords
2. Chọn app: "Mail"
3. Chọn device: "Other"
4. Nhập tên (VD: "Discord Booking Bot")
5. Copy password và paste vào `.env`

### 6. Cấu hình Google Apps Script

#### 6.1. Tạo Apps Script Project

1. Truy cập [Google Apps Script](https://script.google.com/)
2. Tạo project mới
3. Copy code từ file `google_apps_script.js`
4. Paste vào Apps Script editor

#### 6.2. Cấu hình Variables

Trong Apps Script, cập nhật các biến:
```javascript
const WEBHOOK_URL = 'https://your-ngrok-url.ngrok.io/webhook/booking';
const FORM_ID = 'your-google-form-id';
const SHEET_ID = 'your-google-sheet-id';
```

#### 6.3. Setup Form Trigger

1. Chạy function `setupFormTrigger()` một lần
2. Cấp quyền truy cập khi được hỏi

## 🔧 Chạy hệ thống

### 1. Expose Local Server với ngrok

```bash
# Cài đặt ngrok
# Đăng ký tài khoản tại https://ngrok.com/

# Chạy ngrok
ngrok http 5000

# Copy HTTPS URL (VD: https://abc123.ngrok.io)
# Cập nhật URL này trong Google Apps Script
```

### 2. Khởi chạy Bot

```bash
# Kích hoạt virtual environment nếu chưa
source venv/bin/activate  # macOS/Linux
# hoặc
venv\Scripts\activate     # Windows

# Khởi chạy hệ thống
python main.py
```

### 3. Test hệ thống

#### 3.1. Test Flask Webhook

```bash
# Test endpoint
curl http://localhost:5000/health

# Test webhook
curl -X POST http://localhost:5000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

#### 3.2. Test Google Apps Script

1. Vào Apps Script editor
2. Chạy function `testWebhook()`
3. Kiểm tra logs

#### 3.3. Test Form Submission

1. Điền Google Form
2. Kiểm tra Discord channel
3. Test nút xác nhận/hủy
4. Kiểm tra email

## 📁 Cấu trúc Project

```
discord-bot-system/
├── bot/
│   ├── __init__.py
│   └── discord_bot.py          # Discord bot chính
├── google_sheets/
│   ├── __init__.py
│   └── manager.py              # Google Sheets API
├── mail/
│   ├── __init__.py
│   └── email_manager.py        # Gmail SMTP
├── web/
│   ├── __init__.py
│   └── webhook_server.py       # Flask webhook
├── config.py                   # Cấu hình
├── main.py                     # File chính
├── requirements.txt            # Dependencies
├── .env.example               # Template biến môi trường
├── credentials.json           # Google Service Account (tự tạo)
├── google_apps_script.js      # Code Apps Script
└── README.md                  # Hướng dẫn này
```

## 🔧 Troubleshooting

### Lỗi thường gặp

#### 1. Discord Bot không online
- Kiểm tra Bot Token trong `.env`
- Kiểm tra bot đã được mời vào server
- Kiểm tra quyền bot

#### 2. Google Sheets API lỗi
- Kiểm tra file `credentials.json`
- Kiểm tra service account đã được chia sẻ sheet
- Kiểm tra Sheet ID trong `.env`

#### 3. Gmail SMTP lỗi
- Kiểm tra App Password (không phải password thường)
- Kiểm tra 2FA đã bật
- Kiểm tra Less Secure Apps setting

#### 4. Webhook không nhận được
- Kiểm tra ngrok đang chạy
- Kiểm tra URL trong Apps Script đúng
- Kiểm tra Flask server đang chạy

### Debug Commands

```bash
# Kiểm tra logs
tail -f booking_system.log

# Test riêng từng component
python -c "from google_sheets.manager import GoogleSheetsManager; print('Sheets OK')"
python -c "from mail.email_manager import EmailManager; print('Email OK')"
python -c "from config import validate_config; validate_config(); print('Config OK')"
```

## 📝 Cấu trúc Google Sheet

Sheet cần có các cột theo thứ tự:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| Timestamp | Email | Name | Phone | Date | Time | Room | Status | ProcessedTime |

## 🔒 Bảo mật

- Không commit file `.env` hoặc `credentials.json`
- Sử dụng App Password cho Gmail
- Giới hạn quyền Service Account
- Sử dụng HTTPS cho webhook (ngrok tự động)

## 📧 Template Email

Hệ thống tự động gửi email đẹp với:
- ✅ Email xác nhận booking
- ❌ Email hủy booking
- 📋 Thông tin đầy đủ
- 💡 Hướng dẫn cho khách

## 🚀 Deploy Production

Để deploy lên VPS:

1. **Cài đặt server**:
   ```bash
   # Cài đặt Python, Git
   sudo apt update
   sudo apt install python3.10 python3-pip git
   ```

2. **Clone và setup**:
   ```bash
   git clone <repo-url>
   cd discord-bot-system
   pip install -r requirements.txt
   ```

3. **Cấu hình systemd service**:
   ```ini
   # /etc/systemd/system/discord-booking.service
   [Unit]
   Description=Discord Booking System
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/discord-bot-system
   Environment=PATH="/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/python main.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Reverse proxy với Nginx**:
   ```nginx
   # /etc/nginx/sites-available/booking-webhook
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **SSL với Let's Encrypt**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs trong file `booking_system.log`
2. Kiểm tra cấu hình trong file `.env`
3. Test từng component riêng biệt
4. Liên hệ admin qua Discord hoặc email

## 📜 License

MIT License - Xem file LICENSE để biết chi tiết.

---

💡 **Tips**: 
- Backup file `credentials.json` và `.env`
- Monitor logs thường xuyên
- Test trước khi deploy production
- Cấu hình monitoring và alerting
