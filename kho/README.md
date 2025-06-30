# Module Quản Lý Kho - Discord Bot

## 📦 Tổng quan

Module quản lý kho vật tư/nguyên liệu được tích hợp vào Discord Bot hiện tại, hoàn toàn tách biệt với module booking phòng.

## 🏗️ Kiến trúc

```
Discord Commands → KhoManager → HTTP POST → Google Apps Script → Google Sheets
```

## 📋 Các lệnh Discord

### 1. `/nhapkho` - Nhập kho nguyên liệu
**Cú pháp:** `Tên nguyên liệu - SL nhập - Tổng SL`
**Ví dụ:** `/nhapkho Cà phê - 10 - 50`

### 2. `/xuatkho` - Xuất kho nguyên liệu  
**Cú pháp:** `Tên nguyên liệu - SL xuất - SL còn lại`
**Ví dụ:** `/xuatkho Cà phê - 5 - 45`

### 3. `/chebien` - Chế biến nguyên liệu
**Cú pháp:** `Tên nguyên liệu - Dung tích có được`
**Ví dụ:** `/chebien Cà phê rang - 2 lít`

### 4. `/huynguyenlieu` - Hủy nguyên liệu
**Cú pháp:** `Tên nguyên liệu - Số lượng/trọng lượng - lý do huỷ`
**Ví dụ:** `/huynguyenlieu Cà phê - 1kg - hết hạn`

### 5. `/khostatus` - Kiểm tra trạng thái hệ thống
### 6. `/khohelp` - Hiển thị hướng dẫn

## ⚙️ Cấu hình

### Biến môi trường (.env):
```bash
# Kho Management Configuration
KHO_WEB_APP_URL=your_kho_appscript_url_here
KHO_TIMEOUT=30
KHO_MAX_RETRIES=3
```

## 📊 JSON Payload Format

Tất cả requests gửi đến Apps Script có format:

```json
{
  "action": "nhapkho|xuatkho|chebien|huynguyenlieu",
  "ten_nguyen_lieu": "string",
  "so_luong_nhap": "number",  // cho nhapkho
  "tong_so_luong": "string",  // cho nhapkho
  "so_luong_xuat": "number",  // cho xuatkho
  "so_luong_con_lai": "number", // cho xuatkho
  "dung_tich": "string",      // cho chebien
  "so_luong_huy": "string",   // cho huynguyenlieu
  "ly_do": "string",          // cho huynguyenlieu
  "nguoi_nhap": "string",     // username
  "nguoi_xuat": "string",     // username
  "nguoi_che_bien": "string", // username
  "nguoi_huy": "string"       // username
}
```

## 📝 Response Format

Apps Script trả về JSON:

```json
{
  "status": "success|error",
  "message": "string" // chỉ khi có lỗi
}
```

## 🔧 Cài đặt

### 1. Thêm vào .env:
```bash
KHO_WEB_APP_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

### 2. Bot sẽ tự động load commands khi khởi động

### 3. Test hệ thống:
```bash
python test_kho_system.py
```

## 📁 Cấu trúc files

```
kho/
├── __init__.py           # Module exports
├── kho_manager.py        # Business logic & HTTP client
└── kho_commands.py       # Discord commands
```

## 🔒 Bảo mật

- Tất cả commands có validation input
- Error handling đầy đủ
- Logging chi tiết
- Timeout requests
- Retry mechanism

## 📈 Mở rộng

Để thêm command mới:

1. Thêm method trong `KhoManager`
2. Thêm command trong `KhoCommands` 
3. Cập nhật JSON payload format
4. Test với Apps Script

## ⚠️ Lưu ý

- **KHÔNG** sửa đổi code module booking phòng
- Module kho hoàn toàn độc lập
- Sử dụng Apps Script riêng biệt cho kho
- Giữ nguyên cấu trúc project hiện tại
