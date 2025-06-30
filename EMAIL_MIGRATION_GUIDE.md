# 📧 EMAIL SYSTEM MIGRATION GUIDE

Hướng dẫn di chuyển từ SMTP sang Google Apps Script để gửi email qua Discord Booking Bot.

## 🚀 TL;DR - Quick Setup

1. **Deploy Apps Script:**
   ```javascript
   // Copy code từ google_apps_script_email.js
   // Deploy as Web App với quyền "Anyone"
   ```

2. **Cập nhật .env:**
   ```bash
   EMAIL_PROVIDER=appscript
   APPSCRIPT_WEBHOOK_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
   ```

3. **Test:**
   ```bash
   python test_email_system.py
   ```

## 🔧 Chi tiết setup

### Bước 1: Setup Google Apps Script

1. **Truy cập Apps Script:**
   - Vào https://script.google.com
   - Tạo project mới

2. **Deploy Web App:**
   - Copy code từ file `google_apps_script_email.js`
   - Paste vào Apps Script Editor
   - Chạy function `setupPermissions()` một lần để cấp quyền
   - Deploy > New deployment > Web app
   - Settings:
     - **Execute as:** Me
     - **Who has access:** Anyone
   - Copy Web App URL

3. **Test Apps Script:**
   ```javascript
   // Chạy function testSendEmail() để test
   testSendEmail();
   ```

### Bước 2: Cập nhật cấu hình Python

1. **Cập nhật file .env:**
   ```bash
   # Email Configuration via Apps Script (RECOMMENDED)
   EMAIL_PROVIDER=appscript
   APPSCRIPT_WEBHOOK_URL=https://script.google.com/macros/s/AKfycbx.../exec
   APPSCRIPT_TIMEOUT=30
   APPSCRIPT_MAX_RETRIES=3
   
   # Disable email nếu cần
   DISABLE_EMAIL=false
   ```

2. **Test trên local:**
   ```bash
   python test_email_system.py
   ```

### Bước 3: Deploy lên VPS

1. **Cập nhật .env trên VPS:**
   ```bash
   sudo -u discord-bot nano /home/discord-bot/discord-booking-bot/.env
   
   # Thêm/sửa các dòng:
   EMAIL_PROVIDER=appscript
   APPSCRIPT_WEBHOOK_URL=your_web_app_url_here
   DISABLE_EMAIL=false
   ```

2. **Restart services:**
   ```bash
   sudo systemctl restart discord-bot
   sudo systemctl restart discord-webhook
   ```

3. **Test trên VPS:**
   ```bash
   sudo -u discord-bot bash -c "
   cd /home/discord-bot/discord-booking-bot
   source venv/bin/activate
   python test_email_system.py
   "
   ```

## 📋 Code Changes Summary

### ✅ Đã thay đổi:

1. **mail/appscript_mailer.py** - Email sender mới qua Apps Script
2. **mail/unified_email_manager.py** - Manager thống nhất auto-fallback
3. **mail/__init__.py** - Export classes mới
4. **config.py** - Thêm Apps Script config
5. **bot/discord_bot.py** - Cập nhật import
6. **google_apps_script_email.js** - Apps Script Web App code

### 🔄 Backward Compatibility:

- Code cũ vẫn hoạt động bình thường
- `EmailManager` tự động chọn provider
- SMTP fallback nếu Apps Script fail
- Có thể disable email hoàn toàn

## 🧪 Testing

### Test local:
```bash
python test_email_system.py
```

### Test trong Discord:
1. Tạo booking mới từ Google Form
2. Xác nhận/hủy booking trong Discord
3. Kiểm tra email đã được gửi

### Debug logs:
```bash
# Trên VPS
sudo journalctl -u discord-bot -f | grep -i email
```

## 🚨 Troubleshooting

### Lỗi Apps Script URL not configured:
```bash
# Kiểm tra .env
grep APPSCRIPT /home/discord-bot/discord-booking-bot/.env

# Thêm URL nếu thiếu
echo "APPSCRIPT_WEBHOOK_URL=your_url_here" >> .env
```

### Lỗi Apps Script permissions:
1. Vào Apps Script console
2. Chạy `setupPermissions()` 
3. Cấp quyền Gmail/MailApp

### Email không gửi được:
```bash
# Test connection
python -c "
from mail import create_email_manager
manager = create_email_manager()
print(manager.test_email_system())
"
```

### Fallback to SMTP:
```bash
# Nếu Apps Script fail, sẽ tự động dùng SMTP
EMAIL_PROVIDER=smtp  # Force SMTP
```

## 📊 Monitoring

### Kiểm tra email system status:
```python
from mail import create_email_manager
manager = create_email_manager()
print(manager.get_status())
```

### Apps Script execution logs:
- Vào Apps Script console
- View > Executions
- Xem logs chi tiết

## 🔒 Security Notes

1. **Apps Script Web App:** Deployed với quyền "Anyone" - an toàn vì chỉ nhận email data
2. **No credentials in requests:** Không gửi password/token qua HTTP
3. **Rate limiting:** Apps Script có giới hạn 100 emails/day miễn phí
4. **Error handling:** Không crash server nếu email fail

## ⚡ Performance

- **Apps Script:** ~2-5 giây response time
- **SMTP:** ~1-2 giây (khi hoạt động)
- **Auto-retry:** 3 lần với exponential backoff
- **Timeout:** 30 giây default

## 📈 Benefits

✅ **Không bị block SMTP ports trên VPS**  
✅ **Reliable email delivery qua Google**  
✅ **Auto-fallback to SMTP**  
✅ **Backward compatible**  
✅ **Easy monitoring qua Apps Script console**  
✅ **Free tier: 100 emails/day**  

## 🎯 Next Steps

1. Deploy Apps Script Web App ✅
2. Update VPS .env configuration ✅
3. Test email functionality ✅  
4. Monitor email delivery ⏳
5. Setup email quota monitoring ⏳

---

*Được tạo bởi AI Assistant - Discord Booking Bot Email Migration*
