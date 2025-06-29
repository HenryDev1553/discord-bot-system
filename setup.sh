#!/bin/bash

# Script setup hệ thống Discord Booking System

echo "🚀 Discord Booking System Setup Script"
echo "======================================"

# Kiểm tra Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Tạo virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Kích hoạt virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Cài đặt dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Kiểm tra file .env
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual credentials!"
else
    echo "✅ .env file already exists"
fi

# Kiểm tra credentials.json
if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found!"
    echo "   Please download your Google Service Account key and save as credentials.json"
else
    echo "✅ credentials.json found"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Add credentials.json from Google Cloud Console"
echo "3. Run: python test_components.py"
echo "4. Run: python main.py"
echo ""
echo "For ngrok setup:"
echo "1. Download and install ngrok from https://ngrok.com/"
echo "2. Run: ngrok http 5000"
echo "3. Copy the HTTPS URL to Google Apps Script"
echo ""
echo "Happy coding! 🎈"
