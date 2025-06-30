# Hướng Dẫn Sử Dụng Lệnh Kho - Giới Hạn Kênh

## 🔒 Giới Hạn Kênh

Tất cả các lệnh quản lý kho **chỉ hoạt động trong kênh `#report-kho`**. Đây là một biện pháp bảo mật để:

- Tránh spam trong các kênh khác
- Tập trung quản lý kho tại một nơi
- Dễ theo dõi và kiểm soát

## 📋 Danh Sách Lệnh Bị Giới Hạn

Các lệnh sau **chỉ hoạt động trong `#report-kho`**:

| Lệnh | Mô tả |
|------|-------|
| `/nhapkho` | Nhập kho nguyên liệu |
| `/xuatkho` | Xuất kho nguyên liệu |
| `/chebien` | Chế biến nguyên liệu |
| `/huynguyenlieu` | Hủy nguyên liệu |
| `/khostatus` | Kiểm tra trạng thái hệ thống kho |
| `/khohelp` | Hiển thị hướng dẫn sử dụng |

## ⚠️ Thông Báo Lỗi

Nếu bạn sử dụng lệnh kho trong kênh khác (ví dụ: `#general`), bot sẽ gửi thông báo:

```
❌ Kênh Không Hợp Lệ
🚫 Lệnh quản lý kho chỉ có thể sử dụng trong kênh #report-kho

📍 Vui lòng chuyển sang kênh #report-kho để sử dụng các lệnh kho.
```

Thông báo này sẽ tự động xóa sau 10 giây.

## 🔧 Cấu Hình

### Biến Môi Trường

Tên kênh được cấu hình trong file `.env`:

```bash
# Kho Management Configuration
KHO_CHANNEL_NAME=report-kho
```

### Thay Đổi Kênh

Để thay đổi kênh cho phép:

1. **Cập nhật file `.env`**:
   ```bash
   # Thay đổi tên kênh
   KHO_CHANNEL_NAME=kho-management
   ```

2. **Khởi động lại bot**:
   ```bash
   python3 main.py
   ```

## 🧪 Kiểm Tra

### Test Chức Năng

Chạy script test để kiểm tra:

```bash
python3 test_simple_channel.py
```

### Kiểm Tra Logs

Khi bot khởi động, bạn sẽ thấy log:

```
KhoCommands cog initialized - allowed channel: #report-kho
```

## 📱 Sử Dụng Thực Tế

### Bước 1: Vào Kênh Đúng
- Chuyển sang kênh `#report-kho`

### Bước 2: Sử dụng Lệnh
```
/khohelp
```

### Bước 3: Thực Hiện Thao Tác
```
/nhapkho Cà phê - 10 - 50
/xuatkho Sugar - 5 - 20
```

## 🔍 Troubleshooting

### Vấn Đề: Lệnh không hoạt động

**Nguyên nhân**: Đang ở sai kênh

**Giải pháp**: Chuyển sang kênh `#report-kho`

### Vấn Đề: Bot không phản hồi

**Kiểm tra**:
1. Bot có online không?
2. Bot có quyền gửi tin nhắn trong kênh không?
3. Cú pháp lệnh có đúng không?

### Vấn Đề: Muốn thay đổi kênh

**Giải pháp**:
1. Cập nhật `KHO_CHANNEL_NAME` trong `.env`
2. Khởi động lại bot
3. Tạo kênh mới trong Discord (nếu cần)

## 📊 Ví Dụ Thực Tế

### Kênh Đúng (`#report-kho`)
```
User: /nhapkho Cà phê - 10 - 50
Bot: ✅ Nhập Kho Thành Công
     Nguyên liệu: Cà phê
     Số lượng nhập: 10
     Tổng số lượng: 50
     Người nhập: Username
```

### Kênh Sai (`#general`)
```
User: /nhapkho Cà phê - 10 - 50
Bot: ❌ Kênh Không Hợp Lệ
     🚫 Lệnh quản lý kho chỉ có thể sử dụng trong kênh #report-kho
     📍 Vui lòng chuyển sang kênh #report-kho để sử dụng các lệnh kho.
     (Tin nhắn này sẽ tự xóa sau 10 giây)
```

## 🛡️ Bảo Mật

- **Chỉ admin** có thể thay đổi cấu hình kênh
- **Tất cả users** có thể sử dụng lệnh kho trong kênh được phép
- **Log đầy đủ** mọi thao tác để audit

---

💡 **Lưu ý**: Chức năng này giúp tổ chức và bảo mật hệ thống quản lý kho hiệu quả hơn.
