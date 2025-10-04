#!/usr/bin/env python3
"""
Discord Bot Health Monitoring Script
Checks bot status, webhook endpoints, and system health
"""

import requests
import subprocess
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/discord-bot/discord-booking-bot/logs/health-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.app_dir = Path('/home/discord-bot/discord-booking-bot')
        self.webhook_url = 'http://localhost:5001/health'
        self.services = ['discord-bot', 'discord-webhook']
        
    def check_webhook_health(self):
        """Check webhook endpoint health"""
        try:
            response = requests.get(self.webhook_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Webhook endpoint is healthy")
                return True
            else:
                logger.error(f"❌ Webhook returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Webhook health check failed: {e}")
            return False
    
    def check_service_status(self, service_name):
        """Check systemd service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"✅ Service {service_name} is running")
                return True
            else:
                logger.error(f"❌ Service {service_name} is not running")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to check service {service_name}: {e}")
            return False
    
    def restart_service(self, service_name):
        """Restart a systemd service"""
        try:
            logger.info(f"🔄 Restarting service {service_name}")
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', service_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"✅ Service {service_name} restarted successfully")
                return True
            else:
                logger.error(f"❌ Failed to restart {service_name}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error restarting service {service_name}: {e}")
            return False
    
    def get_service_logs(self, service_name, lines=10):
        """Get recent logs from a service"""
        try:
            result = subprocess.run(
                ['journalctl', '-u', service_name, '--no-pager', '-n', str(lines)],
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            logger.error(f"❌ Failed to get logs for {service_name}: {e}")
            return ""
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            result = subprocess.run(['df', '-h', str(self.app_dir)], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                usage_line = lines[1].split()
                usage_percent = usage_line[4].replace('%', '')
                if int(usage_percent) > 85:
                    logger.warning(f"⚠️ Disk usage is high: {usage_percent}%")
                    return False
                else:
                    logger.info(f"✅ Disk usage is normal: {usage_percent}%")
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to check disk space: {e}")
            return False
    
    def cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            logs_dir = self.app_dir / 'logs'
            if logs_dir.exists():
                # Keep only last 100MB of logs
                subprocess.run([
                    'find', str(logs_dir), '-name', '*.log',
                    '-size', '+10M', '-mtime', '+7', '-delete'
                ], capture_output=True)
                logger.info("🧹 Cleaned up old log files")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup logs: {e}")
    
    def send_alert(self, message):
        """Send alert notification"""
        # You can implement Discord webhook or email alerts here
        logger.critical(f"🚨 ALERT: {message}")
    
    def run_health_check(self):
        """Run complete health check"""
        logger.info("🏥 Starting health check...")
        
        issues = []
        
        # Check webhook
        if not self.check_webhook_health():
            issues.append("Webhook endpoint is down")
            # Try to restart webhook service
            if self.restart_service('discord-webhook'):
                time.sleep(10)
                if self.check_webhook_health():
                    logger.info("✅ Webhook service recovered after restart")
                else:
                    issues.append("Webhook service failed to recover")
        
        # Check services
        for service in self.services:
            if not self.check_service_status(service):
                issues.append(f"Service {service} is down")
                # Try to restart
                if self.restart_service(service):
                    time.sleep(5)
                    if self.check_service_status(service):
                        logger.info(f"✅ Service {service} recovered after restart")
                    else:
                        issues.append(f"Service {service} failed to recover")
        
        # Check system resources
        self.check_disk_space()
        self.cleanup_old_logs()
        
        # Send alerts if there are issues
        if issues:
            alert_message = "Bot health issues detected: " + ", ".join(issues)
            self.send_alert(alert_message)
            return False
        else:
            logger.info("✅ All health checks passed")
            return True

def main():
    """Main function"""
    monitor = HealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Continuous monitoring mode
        logger.info("🔄 Starting continuous monitoring...")
        while True:
            try:
                monitor.run_health_check()
                time.sleep(300)  # Check every 5 minutes
            except KeyboardInterrupt:
                logger.info("👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)
    else:
        # Single check mode
        success = monitor.run_health_check()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()