"""
Telegram Bot for sending alerts
Handles bot initialization, message sending, and button interactions
"""

import asyncio
from typing import Dict, Any, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, TimedOut, NetworkError
from src.utils.logger import get_logger
from src.notifications.formatter import MessageFormatter

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot for sending trading alerts"""
    
    def __init__(self, token: str, chat_id: str):
        """
        Initialize Telegram bot
        
        Args:
            token: Telegram bot token from BotFather
            chat_id: Default chat ID to send messages to
        """
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
        self.application: Optional[Application] = None
        self.formatter = MessageFormatter()
        self._rate_limit_delay = 0.1  # 100ms between messages
        self._last_send_time = 0
        
        logger.info("Telegram bot initialized")
    
    async def initialize(self):
        """Initialize the application for callback handlers"""
        try:
            self.application = Application.builder().token(self.token).build()
            
            # Add callback handler for button clicks
            self.application.add_handler(
                CallbackQueryHandler(self.handle_button_callback)
            )
            
            # Initialize the application
            await self.application.initialize()
            logger.info("Telegram application initialized with handlers")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram application: {e}")
    
    async def send_message(
        self, 
        text: str, 
        parse_mode: str = "Markdown",
        chat_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        retry_count: int = 3
    ) -> bool:
        """
        Send a simple text message
        
        Args:
            text: Message text
            parse_mode: Parse mode (Markdown or HTML)
            chat_id: Optional chat ID override
            reply_markup: Optional inline keyboard
            retry_count: Number of retry attempts
            
        Returns:
            True if sent successfully, False otherwise
        """
        target_chat_id = chat_id or self.chat_id
        
        for attempt in range(retry_count):
            try:
                # Rate limiting
                await self._apply_rate_limit()
                
                # Send message
                await self.bot.send_message(
                    chat_id=target_chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                logger.info(f"Message sent successfully to chat {target_chat_id}")
                return True
                
            except TimedOut:
                logger.warning(f"Telegram timeout on attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    
            except NetworkError as e:
                logger.warning(f"Network error on attempt {attempt + 1}/{retry_count}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    
            except TelegramError as e:
                logger.error(f"Telegram error: {e}")
                return False
                
            except Exception as e:
                logger.error(f"Unexpected error sending message: {e}")
                return False
        
        logger.error(f"Failed to send message after {retry_count} attempts")
        return False
    
    async def send_alert(
        self, 
        alert_data: Dict[str, Any],
        compact: bool = False,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Send a formatted alert with buttons
        
        Args:
            alert_data: Alert data dictionary
            compact: Use compact format
            chat_id: Optional chat ID override
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format the alert message
            message = self.formatter.format_telegram_alert(alert_data, compact=compact)
            
            # Create inline buttons
            buttons = self._create_alert_buttons(alert_data)
            
            # Send the message
            success = await self.send_message(
                text=message,
                chat_id=chat_id,
                reply_markup=buttons
            )
            
            if success:
                token_symbol = alert_data.get('token_symbol', 'UNKNOWN')
                logger.info(f"Alert sent successfully for {token_symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def _create_alert_buttons(self, alert_data: Dict[str, Any]) -> InlineKeyboardMarkup:
        """
        Create inline keyboard buttons for an alert
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            InlineKeyboardMarkup with buttons
        """
        token_address = alert_data.get('token_address', '')
        
        # Create button rows
        buttons = [
            [
                InlineKeyboardButton(
                    "🚀 TRADE",
                    url=f"https://jup.ag/swap/SOL-{token_address}"
                ),
                InlineKeyboardButton(
                    "📊 CHART",
                    url=f"https://dexscreener.com/solana/{token_address}"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ TRACK",
                    callback_data=f"track_{token_address[:8]}"  # Shortened for callback data limit
                )
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    async def handle_button_callback(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle button callback queries
        
        Args:
            update: Update object from Telegram
            context: Context from Telegram
        """
        query = update.callback_query
        
        try:
            await query.answer()  # Acknowledge the button press
            
            callback_data = query.data
            
            if callback_data.startswith('track_'):
                # Extract token address from callback data
                token_ref = callback_data.replace('track_', '')
                
                # Send confirmation message
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n✅ *Tracking enabled for this token*",
                    parse_mode="Markdown"
                )
                
                logger.info(f"Track button pressed for token: {token_ref}")
                
                # Here you could add logic to actually track the token
                # For example, add to database, start monitoring, etc.
                
        except Exception as e:
            logger.error(f"Error handling button callback: {e}")
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between messages"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_send_time
        
        if time_since_last < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - time_since_last)
        
        self._last_send_time = asyncio.get_event_loop().time()
    
    async def test_connection(self) -> bool:
        """
        Test bot connection and permissions
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to bot: @{bot_info.username}")
            
            # Try to get chat info
            try:
                chat = await self.bot.get_chat(self.chat_id)
                logger.info(f"Chat found: {chat.type} - {chat.title or chat.first_name or 'Private'}")
            except Exception as e:
                logger.warning(f"Could not get chat info: {e}")
            
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing connection: {e}")
            return False
    
    async def close(self):
        """Close bot connections"""
        try:
            if self.application:
                await self.application.shutdown()
            logger.info("Telegram bot closed")
        except Exception as e:
            logger.error(f"Error closing Telegram bot: {e}")
