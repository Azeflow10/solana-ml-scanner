"""
Pump.fun Scanner - Monitors new token launches on Pump.fun
"""

import asyncio
import websockets
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from src.utils.logger import get_logger
from src.models.token_data import TokenData

logger = get_logger(__name__)


class PumpFunScanner:
    """Real-time WebSocket scanner for Pump.fun new token launches"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Pump.fun scanner"""
        self.config = config
        self.min_liquidity = config.get('min_liquidity_sol', 3)
        self.websocket_url = config.get('websocket_url', 'wss://api.helius.xyz')
        
        # Pre-filters from config
        self.liquidity_min = config.get('liquidity_min', 10000)
        self.liquidity_max = config.get('liquidity_max', 300000)
        self.age_max_seconds = config.get('age_max_seconds', 300)
        self.holders_min = config.get('holders_min', 15)
        self.market_cap_max = config.get('market_cap_max', 500000)
        
        self.ws = None
        self.running = False
        self.callback = None
        
        logger.info(f"PumpFun Scanner initialized (min liquidity: {self.min_liquidity} SOL)")
    
    def set_callback(self, callback: Callable):
        """Set callback function to receive detected tokens"""
        self.callback = callback
    
    async def connect(self):
        """Connect to Pump.fun WebSocket"""
        try:
            logger.info(f"Connecting to Pump.fun WebSocket: {self.websocket_url}")
            
            # Connect to WebSocket
            # Note: Actual Pump.fun WebSocket URL would be different
            # This is a placeholder implementation
            self.ws = await websockets.connect(self.websocket_url)
            
            # Subscribe to new token events
            subscribe_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    {
                        "mentions": ["6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"]  # Pump.fun program
                    },
                    {
                        "commitment": "confirmed"
                    }
                ]
            }
            
            await self.ws.send(json.dumps(subscribe_msg))
            logger.info("✅ Connected to Pump.fun WebSocket")
            
        except Exception as e:
            logger.error(f"Failed to connect to Pump.fun WebSocket: {e}")
            raise
    
    async def start(self):
        """Start scanning Pump.fun"""
        logger.info("Starting Pump.fun scanner...")
        self.running = True
        
        try:
            await self.connect()
            await self.scan()
        except Exception as e:
            logger.error(f"Pump.fun scanner error: {e}")
            self.running = False
    
    async def scan(self) -> List[TokenData]:
        """Scan for new tokens"""
        try:
            # If not connected or not running, return empty list
            if not self.ws or not self.running:
                return []
            
            # Listen for tokens (with short timeout for polling)
            detected_tokens = []
            
            try:
                # Try to receive message with short timeout (non-blocking scan)
                message = await asyncio.wait_for(
                    self.ws.recv(),
                    timeout=1.0
                )
                
                # Parse the message
                data = json.loads(message)
                
                # Check if it's a new token event
                if self._is_new_token_event(data):
                    token_data = await self.parse_token_data(data)
                    
                    if token_data and self.apply_prefilters(token_data):
                        detected_tokens.append(token_data)
                
            except asyncio.TimeoutError:
                # No message received, return empty list
                pass
            
            return detected_tokens
            
        except Exception as e:
            logger.error(f"PumpFun scan error: {e}")
            return []
    
    def _is_new_token_event(self, data: Dict[str, Any]) -> bool:
        """Check if the WebSocket message is a new token event"""
        
        # This is a simplified check
        # Actual implementation would parse the logs for Pump.fun token creation
        
        if 'params' in data:
            result = data.get('params', {}).get('result', {})
            if result and 'value' in result:
                logs = result['value'].get('logs', [])
                # Look for token creation signature
                return any('initialize' in log.lower() for log in logs if isinstance(log, str))
        
        return False
    
    async def parse_token_data(self, event: Dict[str, Any]) -> Optional[TokenData]:
        """Parse raw event data into TokenData object"""
        
        try:
            # Extract token information from event
            # This is a placeholder - actual parsing would be more complex
            
            result = event.get('params', {}).get('result', {})
            value = result.get('value', {})
            
            # Extract transaction info
            # In real implementation, we'd parse the transaction data
            # to extract token address, symbol, name, etc.
            
            # For now, return None as we can't parse without real event data
            # In production, this would extract all necessary fields
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing token data: {e}")
            return None
    
    def apply_prefilters(self, token_data: TokenData) -> bool:
        """
        Apply initial filters (liquidity, age, etc.)
        
        Pre-scan Filters:
        - liquidity_min: 10000  # $10k
        - liquidity_max: 300000  # $300k
        - age_max_seconds: 300  # 5 minutes
        - holders_min: 15
        - market_cap_max: 500000  # $500k
        """
        
        # Liquidity check
        if token_data.liquidity_usd < self.liquidity_min:
            logger.debug(f"Filtered: Liquidity too low (${token_data.liquidity_usd})")
            return False
        
        if token_data.liquidity_usd > self.liquidity_max:
            logger.debug(f"Filtered: Liquidity too high (${token_data.liquidity_usd})")
            return False
        
        # Age check
        if token_data.age_seconds > self.age_max_seconds:
            logger.debug(f"Filtered: Token too old ({token_data.age_seconds}s)")
            return False
        
        # Holders check
        if token_data.holders > 0 and token_data.holders < self.holders_min:
            logger.debug(f"Filtered: Not enough holders ({token_data.holders})")
            return False
        
        # Market cap check
        if token_data.market_cap > self.market_cap_max:
            logger.debug(f"Filtered: Market cap too high (${token_data.market_cap})")
            return False
        
        return True
    
    async def stop(self):
        """Stop the scanner"""
        logger.info("Stopping Pump.fun scanner...")
        self.running = False
        if self.ws:
            await self.ws.close()
    
    async def disconnect(self):
        """Disconnect from WebSocket (alias for stop)"""
        await self.stop()
