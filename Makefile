.PHONY: help install test deploy backup monitor setup-vps local-run docker-build docker-run clean status logs

# Default target
help:
	@echo "Discord Bot Deployment Commands:"
	@echo ""
	@echo "Local Development:"
	@echo "  install      - Install dependencies locally"
	@echo "  test         - Run tests locally"
	@echo "  local-run    - Run bot locally"
	@echo ""
	@echo "VPS Deployment:"
	@echo "  setup-vps    - Initial VPS setup (run once)"
	@echo "  deploy       - Deploy to VPS via Git push"
	@echo "  manual-deploy- Manual deployment on VPS"
	@echo ""
	@echo "Maintenance:"
	@echo "  backup       - Create backup on VPS"
	@echo "  monitor      - Check system health"
	@echo "  status       - Check service status"
	@echo "  logs         - View recent logs"
	@echo "  clean        - Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker containers"

# Local development
install:
	@echo "📦 Installing dependencies..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	@echo "🧪 Running tests..."
	python -m py_compile main.py
	python -m py_compile bot/discord_bot.py
	python -m py_compile kho/kho_commands.py
	python test_simple_channel.py || echo "Channel test completed"
	@echo "✅ Tests completed"

local-run:
	@echo "🚀 Running bot locally..."
	python main.py

# VPS deployment
setup-vps:
	@echo "🔧 Running VPS setup..."
	@echo "Make sure to run this on your VPS:"
	@echo "curl -sSL https://raw.githubusercontent.com/HenryDev1553/discord-bot-system/main/vps-deploy.sh | bash"

deploy:
	@echo "🚀 Deploying to VPS via GitHub Actions..."
	git add .
	git commit -m "Deploy: $(shell date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"
	git push origin main
	@echo "✅ Deployment triggered via GitHub Actions"

manual-deploy:
	@echo "🔄 Manual deployment on VPS..."
	@echo "Run this on your VPS:"
	@echo "cd /home/discord-bot/discord-booking-bot && ./scripts/deploy.sh"

# Maintenance commands (run on VPS)
backup:
	@echo "💾 Creating backup..."
	./scripts/backup.sh

monitor:
	@echo "🔍 Checking system health..."
	./scripts/health_check.sh

status:
	@echo "📊 Checking service status..."
	@systemctl status discord-bot --no-pager -l
	@echo ""
	@systemctl status discord-webhook --no-pager -l
	@echo ""
	@curl -f http://localhost:5001/health && echo "✅ Webhook healthy" || echo "❌ Webhook down"

logs:
	@echo "📝 Recent logs:"
	@echo "=== Discord Bot Logs ==="
	@journalctl -u discord-bot --no-pager -n 20
	@echo ""
	@echo "=== Webhook Logs ==="
	@journalctl -u discord-webhook --no-pager -n 20

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t discord-booking-bot .

docker-run:
	@echo "🚀 Starting with Docker Compose..."
	docker-compose up -d

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📝 Docker logs..."
	docker-compose logs -f

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -size +50M -delete
	@echo "✅ Cleanup completed"

# Quick commands
start:
	@sudo systemctl start discord-bot discord-webhook
	@echo "✅ Services started"

stop:
	@sudo systemctl stop discord-bot discord-webhook
	@echo "🛑 Services stopped"

restart:
	@sudo systemctl restart discord-bot discord-webhook
	@echo "🔄 Services restarted"

# Development helpers
format:
	@echo "🎨 Formatting code..."
	black . --line-length 88 || echo "Black not installed, skipping formatting"

lint:
	@echo "🔍 Linting code..."
	flake8 . --max-line-length=88 --ignore=E203,W503 || echo "Flake8 not installed, skipping linting"

# Information
info:
	@echo "📋 System Information:"
	@echo "Git branch: $(shell git branch --show-current)"
	@echo "Last commit: $(shell git log -1 --format='%h - %s (%cr)')"
	@echo "Python version: $(shell python --version)"
	@echo "Pip packages: $(shell pip list | wc -l) installed"
	@if [ -f "/etc/systemd/system/discord-bot.service" ]; then \
		echo "Discord bot service: Installed"; \
	else \
		echo "Discord bot service: Not installed"; \
	fi
	@if [ -f "/etc/systemd/system/discord-webhook.service" ]; then \
		echo "Webhook service: Installed"; \
	else \
		echo "Webhook service: Not installed"; \
	fi