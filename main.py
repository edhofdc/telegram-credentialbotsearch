#!/usr/bin/env python3
"""
Telegram Recon Bot - Main Entry Point
A security reconnaissance bot for detecting credentials and API endpoints.

This bot operates in group chats within specific topics and allows private messaging to admin.
Implements MVP pattern with separated concerns for maintainability.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application

# Import our MVP components
from presenters.bot_presenter import BotPresenter
from services.scanner_service import ScannerService
from services.pdf_service import PDFReportService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables."""
    required_vars = ['BOT_TOKEN', 'ADMIN_CHAT_ID', 'TARGET_TOPIC_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        return False
    
    return True

def main():
    """Main function to start the Telegram bot."""
    logger.info("🚀 Starting Telegram Recon Bot...")
    
    # Validate environment
    if not validate_environment():
        logger.error("❌ Environment validation failed. Exiting.")
        return
    
    # Get configuration from environment
    bot_token = os.getenv('BOT_TOKEN')
    admin_chat_id_str = os.getenv('ADMIN_CHAT_ID')
    target_topic_id_str = os.getenv('TARGET_TOPIC_ID')
    
    # Convert to integers with validation
    admin_chat_id = int(admin_chat_id_str) if admin_chat_id_str else 0
    target_topic_id = int(target_topic_id_str) if target_topic_id_str else 0
    
    logger.info(f"📋 Configuration loaded:")
    logger.info(f"   Admin Chat ID: {admin_chat_id}")
    logger.info(f"   Target Topic ID: {target_topic_id}")
    
    try:
        # Initialize services
        scanner_service = ScannerService()
        pdf_service = PDFReportService()
        
        # Initialize presenter with services
        bot_presenter = BotPresenter(
            admin_chat_id=str(admin_chat_id),
            target_topic_id=str(target_topic_id)
        )
        
        # Create application
        application = Application.builder().token(bot_token).build()
        
        # Register handlers through presenter
        bot_presenter.register_handlers(application)
        
        logger.info("✅ Bot initialized successfully")
        logger.info("🔄 Starting polling...")
        
        # Start the bot
        application.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise