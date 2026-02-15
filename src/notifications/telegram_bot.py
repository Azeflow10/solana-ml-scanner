"""
Telegram Bot for sending alerts
Handles bot initialization, message sending, and button interactions
"""

import asyncio
import re
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
        parse_mode: str = "HTML",
        chat_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        retry_count: int = 3
    ) -> bool:
        """
        Send a simple text message
        
        Args:
            text: Message text
            parse_mode: Parse mode (HTML, Markdown, or None for plain text)
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
                error_msg = str(e).lower()
                
                # If it's a parse error and we're using HTML/Markdown, try plain text as fallback
                if "parse" in error_msg or "can't parse entities" in error_msg:
                    if parse_mode is not None:
                        logger.warning(f"Parse error with {parse_mode} mode: {e}")
                        logger.info(f"Attempting to send as plain text (attempt {attempt + 1}/{retry_count})")
                        logger.debug(f"Message that failed: {text[:200]}...")
                        
                        # Try sending without parse mode (plain text)
                        try:
                            await self.bot.send_message(
                                chat_id=target_chat_id,
                                text=text,
                                parse_mode=None,
                                reply_markup=reply_markup,
                                disable_web_page_preview=True
                            )
                            logger.info("Message sent successfully as plain text")
                            return True
                        except Exception as fallback_error:
                            logger.error(f"Failed to send even as plain text: {fallback_error}")
                            if attempt < retry_count - 1:
                                continue
                    else:
                        logger.error(f"Parse error even in plain text mode: {e}")
                else:
                    logger.error(f"Telegram error: {e}")
                
                if attempt >= retry_count - 1:
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
            
            # Try with buttons first
            try:
                buttons = self._create_alert_buttons(alert_data.get('token_address', ''))
                success = await self.send_message(
                    text=message,
                    chat_id=chat_id,
                    reply_markup=buttons,
                    parse_mode="HTML"
                )
                if success:
                    token_symbol = alert_data.get('token_symbol', 'UNKNOWN')
                    logger.info(f"Alert sent successfully for {token_symbol}")
                    return True
            except Exception as button_error:
                logger.warning(f"Failed to send with buttons: {button_error}")
                # Fallback: send without buttons
                logger.info("Sending alert without buttons as fallback")
            
            # Send without buttons as fallback
            success = await self.send_message(
                text=message,
                chat_id=chat_id,
                parse_mode="HTML"
            )
            
            if success:
                token_symbol = alert_data.get('token_symbol', 'UNKNOWN')
                logger.info(f"Alert sent successfully (without buttons) for {token_symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def _create_alert_buttons(self, token_address: str) -> InlineKeyboardMarkup:
        """
        Create inline keyboard buttons with validated URLs
        
        Args:
            token_address: Token address string
            
        Returns:
            InlineKeyboardMarkup with buttons
        """
        # Validate and clean token address
        clean_address = self._validate_token_address(token_address)
        
        # Create URLs with proper encoding
        jupiter_url = f"https://jup.ag/swap/SOL-{clean_address}"
        dexscreener_url = f"https://dexscreener.com/solana/{clean_address}"
        
        # Validate URLs before creating buttons
        # If invalid, use homepage as safe fallback and log warning
        if not self._is_valid_url(jupiter_url):
            logger.warning(f"Invalid Jupiter URL for token {clean_address}, using homepage fallback")
            jupiter_url = "https://jup.ag"
        
        if not self._is_valid_url(dexscreener_url):
            logger.warning(f"Invalid DexScreener URL for token {clean_address}, using homepage fallback")
            dexscreener_url = "https://dexscreener.com"
        
        # Create button rows
        buttons = [
            [
                InlineKeyboardButton(
                    "🚀 TRADE",
                    url=jupiter_url
                ),
                InlineKeyboardButton(
                    "📊 CHART",
                    url=dexscreener_url
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ TRACK",
                    callback_data=f"track_{clean_address[:8]}"  # Shortened for callback data limit
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
                    text=f"{query.message.text}\n\n✅ <b>Tracking enabled for this token</b>",
                    parse_mode="HTML"
                )
                
                logger.info(f"Track button pressed for token: {token_ref}")
                
                # Here you could add logic to actually track the token
                # For example, add to database, start monitoring, etc.
                
        except Exception as e:
            logger.error(f"Error handling button callback: {e}")
    
    def _validate_token_address(self, address: str) -> str:
        """
        Validate and clean Solana token address
        
        Args:
            address: Token address to validate
            
        Returns:
            Cleaned token address
        """
        # Remove any whitespace
        address = address.strip()
        
        # Solana addresses are base58 encoded, 32-44 characters
        # Valid characters: 1-9, A-H, J-N, P-Z, a-k, m-z (no 0, O, I, l)
        if not address or len(address) < 32 or len(address) > 44:
            logger.warning(f"Invalid token address length: {address}")
            return address
        
        # Remove any invalid characters for URLs
        # Base58 characters are URL-safe, but double-check
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
            logger.warning(f"Token address contains invalid characters: {address}")
            # Clean it (remove invalid chars)
            address = re.sub(r'[^1-9A-HJ-NP-Za-km-z]', '', address)
        
        return address
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format and ensure it's safe for Telegram buttons
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        # First check basic URL structure
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False
        
        # Additional check: Telegram buttons don't accept URLs with certain special chars
        # that could break HTML/XML parsing: <, >, &, ", '
        invalid_chars = ['<', '>', '"', "'"]
        for char in invalid_chars:
            if char in url:
                logger.debug(f"URL contains invalid character '{char}': {url}")
                return False
        
        return True
    
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
