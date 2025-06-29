@echo off
REM Setup script cho Windows

echo 🚀 Discord Booking System Setup Script (Windows)
echo ======================================

REM Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.10+
    pause
    exit /b 1
)

echo 🐍 Python found
python --version

REM Tạo virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Kích hoạt virtual environment
echo ⚡ Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 🔧 Upgrading pip...
python -m pip install --upgrade pip

REM Cài đặt dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Kiểm tra file .env
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your actual credentials!
) else (
    echo ✅ .env file already exists
)

REM Kiểm tra credentials.json
if not exist "credentials.json" (
    echo ⚠️  credentials.json not found!
    echo    Please download your Google Service Account key and save as credentials.json
) else (
    echo ✅ credentials.json found
)

echo.
echo 🎉 Setup completed!
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Add credentials.json from Google Cloud Console
echo 3. Run: python test_components.py
echo 4. Run: python main.py
echo.
echo For ngrok setup:
echo 1. Download and install ngrok from https://ngrok.com/
echo 2. Run: ngrok http 5000
echo 3. Copy the HTTPS URL to Google Apps Script
echo.
echo Happy coding! 🎈

pause
