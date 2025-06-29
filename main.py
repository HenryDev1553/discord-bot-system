import asyncio
import logging
from config import Config, validate_config
from bot.discord_bot import DiscordBookingBot
from web.webhook_server import create_app

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('booking_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """
    Hàm main để khởi chạy cả Discord bot và Flask webhook server
    """
    try:
        # Validate cấu hình trước khi khởi chạy
        validate_config()
        logger.info("Configuration validated successfully")
        
        # Tạo Discord bot instance
        bot = DiscordBookingBot()
        
        # Tạo Flask app
        flask_app = create_app(bot)
        
        # Khởi chạy Flask server trong thread riêng
        import threading
        from werkzeug.serving import run_simple
        
        def run_flask():
            run_simple(
                Config.FLASK_HOST, 
                Config.FLASK_PORT, 
                flask_app,
                use_reloader=False,
                use_debugger=False,
                threaded=True
            )
        
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        logger.info(f"Flask webhook server started on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
        logger.info("Starting Discord bot...")
        
        # Khởi chạy Discord bot (blocking)
        await bot.start(Config.DISCORD_BOT_TOKEN)
        
    except Exception as e:
        logger.error(f"Error starting booking system: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Booking system stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
