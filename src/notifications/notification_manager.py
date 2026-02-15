"""
Notification Manager - Routes alerts to different channels
"""

import asyncio
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.notifications.telegram_bot import TelegramBot

logger = get_logger(__name__)


class NotificationManager:
    """Manages notifications across different channels"""
    
    def __init__(self, config):
        """
        Initialize notification manager
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.telegram_bot: Optional[TelegramBot] = None
        self._notification_queue = asyncio.Queue()
        self._is_running = False
        
        # Initialize Telegram bot if configured
        if self._is_telegram_enabled():
            self._init_telegram_bot()
        
        logger.info("Notification manager initialized")
    
    def _is_telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled"""
        telegram_enabled = self.config.get('notifications.telegram.enabled', False)
        has_token = bool(self.config.telegram_token)
        has_chat_id = bool(self.config.telegram_chat_id)
        
        if telegram_enabled and not (has_token and has_chat_id):
            logger.warning("Telegram enabled but missing token or chat_id")
            return False
        
        return telegram_enabled and has_token and has_chat_id
    
    def _init_telegram_bot(self):
        """Initialize Telegram bot"""
        try:
            self.telegram_bot = TelegramBot(
                token=self.config.telegram_token,
                chat_id=self.config.telegram_chat_id
            )
            logger.info("✅ Telegram bot initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.telegram_bot = None
    
    async def start(self):
        """Start the notification manager"""
        if self.telegram_bot:
            await self.telegram_bot.initialize()
            
            # Test connection
            if await self.telegram_bot.test_connection():
                logger.info("✅ Telegram bot connection verified")
            else:
                logger.error("❌ Telegram bot connection failed")
        
        self._is_running = True
        logger.info("Notification manager started")
    
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send alert to configured channels
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            True if sent to at least one channel successfully
        """
        token_symbol = alert.get('token_symbol', 'Unknown')
        logger.info(f"Sending alert for token: {token_symbol}")
        
        success = False
        
        # Send to Telegram
        if self.telegram_bot:
            try:
                # Check format preference
                compact = self.config.get('notifications.telegram.format', 'detailed') == 'compact'
                
                # Send the alert
                telegram_success = await self.telegram_bot.send_alert(
                    alert_data=alert,
                    compact=compact
                )
                
                if telegram_success:
                    logger.info(f"✅ Alert sent to Telegram for {token_symbol}")
                    success = True
                else:
                    logger.error(f"❌ Failed to send alert to Telegram for {token_symbol}")
                    
            except Exception as e:
                logger.error(f"Error sending to Telegram: {e}")
        
        # TODO: Send to Discord if enabled
        # TODO: Update dashboard if enabled
        
        if success:
            logger.info(f"✅ Alert sent successfully for {token_symbol}")
        else:
            logger.warning(f"⚠️ Alert not sent to any channel for {token_symbol}")
        
        return success
    
    async def send_test_message(self) -> bool:
        """
        Send a test message to verify connectivity
        
        Returns:
            True if test message sent successfully
        """
        if not self.telegram_bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            from src.notifications.formatter import MessageFormatter
            test_message = MessageFormatter.format_test_message()
            
            success = await self.telegram_bot.send_message(test_message)
            
            if success:
                logger.info("✅ Test message sent successfully")
            else:
                logger.error("❌ Failed to send test message")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False
    
    async def stop(self):
        """Stop the notification manager"""
        self._is_running = False
        
        if self.telegram_bot:
            await self.telegram_bot.close()
        
        logger.info("Notification manager stopped")
