import os
from dotenv import load_dotenv

# Load environment variables từ file .env
load_dotenv()

class Config:
    # Discord Bot Configuration
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', '0'))
    
    # Flask Webhook Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    SHEET_NAME = os.getenv('SHEET_NAME', 'Sheet1')
    
    # Google Calendar Configuration
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    
    # Gmail SMTP Configuration
    GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
    GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')  # App password
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    
    # Timezone Configuration
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Ho_Chi_Minh')
    
    # Company/Organization Info
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Your Company')
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'contact@company.com')
    COMPANY_PHONE = os.getenv('COMPANY_PHONE', '+84 123 456 789')

# Validation để kiểm tra các biến môi trường bắt buộc
def validate_config():
    required_vars = [
        'DISCORD_BOT_TOKEN',
        'DISCORD_CHANNEL_ID',
        'GOOGLE_SHEETS_ID',
        'GMAIL_EMAIL',
        'GMAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True
