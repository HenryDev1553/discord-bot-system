#!/bin/bash

# Script kiểm tra credentials file trên VPS
# Chạy script này trên VPS để kiểm tra file service-account.json

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

echo "🔍 Kiểm tra credentials file trên VPS..."
echo "================================================"

# Đường dẫn file credentials
CREDENTIALS_PATH="/home/discord-bot/discord-booking-bot/credentials/service-account.json"
ENV_FILE="/home/discord-bot/discord-booking-bot/.env"

# 1. Kiểm tra thư mục credentials có tồn tại không
print_info "1. Kiểm tra thư mục credentials..."
if [ -d "/home/discord-bot/discord-booking-bot/credentials" ]; then
    print_success "Thư mục credentials tồn tại"
    ls -la /home/discord-bot/discord-booking-bot/credentials/
else
    print_error "Thư mục credentials không tồn tại"
    print_info "Tạo thư mục credentials..."
    sudo -u discord-bot mkdir -p /home/discord-bot/discord-booking-bot/credentials
    print_success "Đã tạo thư mục credentials"
fi

echo ""

# 2. Kiểm tra file service-account.json có tồn tại không
print_info "2. Kiểm tra file service-account.json..."
if [ -f "$CREDENTIALS_PATH" ]; then
    print_success "File service-account.json tồn tại"
    
    # Kiểm tra quyền file
    print_info "   Quyền file:"
    ls -la "$CREDENTIALS_PATH"
    
    # Kiểm tra kích thước file
    FILE_SIZE=$(stat -c%s "$CREDENTIALS_PATH")
    print_info "   Kích thước file: $FILE_SIZE bytes"
    
    if [ $FILE_SIZE -eq 0 ]; then
        print_error "   File rỗng!"
    else
        print_success "   File có nội dung"
    fi
    
else
    print_error "File service-account.json không tồn tại"
    print_warning "Bạn cần upload file này từ máy local"
    echo ""
    print_info "Cách upload file:"
    echo "   scp /path/to/your/service-account.json username@your-vps-ip:/home/discord-bot/discord-booking-bot/credentials/"
    echo "   hoặc"
    echo "   rsync -avz /path/to/your/service-account.json username@your-vps-ip:/home/discord-bot/discord-booking-bot/credentials/"
fi

echo ""

# 3. Kiểm tra nội dung file JSON (nếu tồn tại)
if [ -f "$CREDENTIALS_PATH" ]; then
    print_info "3. Kiểm tra format JSON..."
    
    # Kiểm tra xem file có phải JSON hợp lệ không
    if python3 -m json.tool "$CREDENTIALS_PATH" > /dev/null 2>&1; then
        print_success "File JSON hợp lệ"
        
        # Hiển thị các field quan trọng (không hiển thị private_key)
        print_info "   Các field quan trọng:"
        python3 -c "
import json
try:
    with open('$CREDENTIALS_PATH', 'r') as f:
        data = json.load(f)
    
    important_fields = ['type', 'project_id', 'private_key_id', 'client_email', 'client_id', 'auth_uri', 'token_uri']
    
    for field in important_fields:
        if field in data:
            if field == 'private_key_id':
                print(f'   - {field}: {data[field][:20]}...')
            else:
                print(f'   - {field}: {data[field]}')
        else:
            print(f'   - {field}: MISSING')
            
except Exception as e:
    print(f'   Lỗi đọc file: {e}')
"
    else
        print_error "File JSON không hợp lệ"
        print_info "   Kiểm tra nội dung file:"
        head -5 "$CREDENTIALS_PATH"
    fi
else
    print_warning "3. Bỏ qua kiểm tra JSON - file không tồn tại"
fi

echo ""

# 4. Kiểm tra biến môi trường trong .env
print_info "4. Kiểm tra file .env..."
if [ -f "$ENV_FILE" ]; then
    print_success "File .env tồn tại"
    
    # Kiểm tra biến GOOGLE_CREDENTIALS_PATH
    if grep -q "GOOGLE_CREDENTIALS_PATH" "$ENV_FILE"; then
        CRED_PATH_IN_ENV=$(grep "GOOGLE_CREDENTIALS_PATH" "$ENV_FILE" | cut -d'=' -f2)
        print_info "   GOOGLE_CREDENTIALS_PATH trong .env: $CRED_PATH_IN_ENV"
        
        if [ "$CRED_PATH_IN_ENV" = "$CREDENTIALS_PATH" ]; then
            print_success "   Đường dẫn trong .env đúng"
        else
            print_error "   Đường dẫn trong .env không khớp"
            print_info "   Nên là: $CREDENTIALS_PATH"
        fi
    else
        print_error "   Không tìm thấy GOOGLE_CREDENTIALS_PATH trong .env"
    fi
else
    print_error "File .env không tồn tại"
fi

echo ""

# 5. Kiểm tra quyền truy cập
print_info "5. Kiểm tra quyền truy cập..."
if [ -f "$CREDENTIALS_PATH" ]; then
    # Kiểm tra user discord-bot có thể đọc file không
    if sudo -u discord-bot test -r "$CREDENTIALS_PATH"; then
        print_success "User discord-bot có thể đọc file"
    else
        print_error "User discord-bot không thể đọc file"
        print_info "   Sửa quyền file:"
        echo "   sudo chown discord-bot:discord-bot $CREDENTIALS_PATH"
        echo "   sudo chmod 600 $CREDENTIALS_PATH"
    fi
else
    print_warning "Bỏ qua kiểm tra quyền - file không tồn tại"
fi

echo ""

# 6. Test kết nối Google API (nếu có Python dependencies)
print_info "6. Test kết nối Google API..."
if [ -f "$CREDENTIALS_PATH" ] && [ -f "/home/discord-bot/discord-booking-bot/venv/bin/python" ]; then
    print_info "   Thử kết nối Google Sheets API..."
    
    sudo -u discord-bot bash -c "
    cd /home/discord-bot/discord-booking-bot
    source venv/bin/activate
    python3 -c '
import os
import sys
sys.path.append(\".\")

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        \"$CREDENTIALS_PATH\",
        scopes=[\"https://www.googleapis.com/auth/spreadsheets\"]
    )
    
    # Test connection
    service = build(\"sheets\", \"v4\", credentials=credentials)
    print(\"✓ Kết nối Google Sheets API thành công\")
    
except ImportError as e:
    print(f\"✗ Thiếu thư viện: {e}\")
    print(\"Cài đặt: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client\")
except Exception as e:
    print(f\"✗ Lỗi kết nối: {e}\")
'
    " 2>/dev/null || print_warning "   Không thể test API (có thể thiếu dependencies)"
else
    print_warning "   Bỏ qua test API - thiếu file hoặc venv"
fi

echo ""
echo "================================================"
print_info "Tóm tắt kết quả kiểm tra:"

# Tóm tắt
if [ -f "$CREDENTIALS_PATH" ]; then
    FILE_SIZE=$(stat -c%s "$CREDENTIALS_PATH")
    if [ $FILE_SIZE -gt 0 ]; then
        print_success "File credentials.json: OK"
    else
        print_error "File credentials.json: Rỗng"
    fi
else
    print_error "File credentials.json: Không tồn tại"
fi

if [ -f "$ENV_FILE" ]; then
    if grep -q "GOOGLE_CREDENTIALS_PATH.*$CREDENTIALS_PATH" "$ENV_FILE"; then
        print_success "Cấu hình .env: OK"
    else
        print_error "Cấu hình .env: Sai đường dẫn"
    fi
else
    print_error "File .env: Không tồn tại"
fi

echo ""
print_info "Script hoàn thành!"
