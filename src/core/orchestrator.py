"""
Core Orchestrator - Coordinates all bot components
"""

import asyncio
from typing import Dict, Any

from src.utils.logger import get_logger
from src.core.config import Config
from src.database.db_manager import DatabaseManager
from src.ml.inference.predictor import MLPredictor
from src.notifications.notification_manager import NotificationManager

logger = get_logger(__name__)

class Orchestrator:
    """Main orchestrator for the scanner bot"""
    
    def __init__(self):
        """Initialize orchestrator"""
        logger.info("Initializing Orchestrator...")
        
        # Load configuration
        self.config = Config()
        logger.info("✅ Configuration loaded")
        
        # Initialize database
        self.db = DatabaseManager(self.config.database_url)
        logger.info("✅ Database connected")
        
        # Initialize ML predictor
        self.ml_predictor = MLPredictor()
        logger.info("✅ ML models loaded")
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(self.config)
        logger.info("✅ Notification manager ready")
        
        logger.info("Orchestrator initialization complete!")
    
    async def start(self):
        """Start the bot"""
        logger.info("🚀 Bot is starting...")
        
        # TODO: Start scanners
        # TODO: Start processing pipeline
        
        logger.info("🤖 Bot is running! Waiting for opportunities...")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Bot shutdown requested")
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down gracefully...")
        # TODO: Close connections, save state
        logger.info("✅ Shutdown complete")
