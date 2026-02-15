"""
DexScreener Scanner - Monitors trending tokens on DexScreener
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from src.utils.logger import get_logger
from src.models.token_data import TokenData

logger = get_logger(__name__)


class DexScreenerScanner:
    """API polling scanner for new tokens and momentum plays"""
    
    BASE_URL = "https://api.dexscreener.com/latest/dex"
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize DexScreener scanner"""
        self.config = config
        self.poll_interval = config.get('poll_interval', 10)
        
        # Pre-filters
        self.liquidity_min = config.get('liquidity_min', 10000)
        self.liquidity_max = config.get('liquidity_max', 300000)
        self.age_max_seconds = config.get('age_max_seconds', 300)
        self.holders_min = config.get('holders_min', 15)
        self.market_cap_max = config.get('market_cap_max', 500000)
        
        # Rate limiting
        self.max_requests_per_minute = 300
        self.request_count = 0
        self.request_window_start = datetime.utcnow()
        
        self.running = False
        self.callback = None
        self.seen_tokens = set()
        
        logger.info(f"DexScreener Scanner initialized (poll interval: {self.poll_interval}s)")
    
    def set_callback(self, callback: Callable):
        """Set callback function to receive detected tokens"""
        self.callback = callback
    
    async def start(self):
        """Start scanning DexScreener"""
        logger.info("Starting DexScreener scanner...")
        self.running = True
        
        # Start both scanning tasks
        await asyncio.gather(
            self._scan_new_pairs_loop(),
            self._scan_trending_loop()
        )
    
    async def _scan_new_pairs_loop(self):
        """Poll for newly created pairs"""
        
        while self.running:
            try:
                await self.scan_new_pairs()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in new pairs scan: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _scan_trending_loop(self):
        """Poll for trending tokens"""
        
        # Poll less frequently for trending
        trending_interval = self.poll_interval * 3
        
        while self.running:
            try:
                await self.scan_trending()
                await asyncio.sleep(trending_interval)
            except Exception as e:
                logger.error(f"Error in trending scan: {e}")
                await asyncio.sleep(trending_interval)
    
    async def scan_new_pairs(self) -> List[TokenData]:
        """Poll for newly created pairs"""
        
        try:
            # Check rate limit
            await self._check_rate_limit()
            
            # Fetch latest pairs for Solana
            url = f"{self.BASE_URL}/search?q=solana"
            
            data = await self._fetch_with_retry(url)
            
            if not data or 'pairs' not in data:
                return []
            
            detected_tokens = []
            
            for pair in data['pairs']:
                try:
                    # Parse pair data into TokenData
                    token_data = self._parse_pair_data(pair)
                    
                    if not token_data:
                        continue
                    
                    # Skip if already seen
                    if token_data.address in self.seen_tokens:
                        continue
                    
                    # Apply pre-filters
                    if self.apply_prefilters(token_data):
                        logger.info(f"✨ New pair detected: {token_data.symbol} ({token_data.address})")
                        detected_tokens.append(token_data)
                        self.seen_tokens.add(token_data.address)
                        
                        # Call callback if set
                        if self.callback:
                            asyncio.create_task(self.callback(token_data))
                    
                except Exception as e:
                    logger.error(f"Error parsing pair: {e}")
                    continue
            
            return detected_tokens
            
        except Exception as e:
            logger.error(f"Error scanning new pairs: {e}")
            return []
    
    async def scan_trending(self) -> List[TokenData]:
        """Find trending/momentum tokens"""
        
        try:
            # Check rate limit
            await self._check_rate_limit()
            
            # Fetch trending tokens
            # Note: DexScreener doesn't have a direct trending endpoint
            # We'll use the search with momentum filters
            url = f"{self.BASE_URL}/search?q=solana"
            
            data = await self._fetch_with_retry(url)
            
            if not data or 'pairs' not in data:
                return []
            
            trending_tokens = []
            
            for pair in data['pairs']:
                try:
                    token_data = self._parse_pair_data(pair)
                    
                    if not token_data:
                        continue
                    
                    # Check for momentum indicators
                    if self._has_momentum(token_data):
                        if token_data.address not in self.seen_tokens:
                            logger.info(f"📈 Trending token detected: {token_data.symbol}")
                            trending_tokens.append(token_data)
                            self.seen_tokens.add(token_data.address)
                            
                            if self.callback:
                                asyncio.create_task(self.callback(token_data))
                
                except Exception as e:
                    logger.error(f"Error parsing trending pair: {e}")
                    continue
            
            return trending_tokens
            
        except Exception as e:
            logger.error(f"Error scanning trending: {e}")
            return []
    
    async def get_token_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get detailed token info from DexScreener API"""
        
        try:
            await self._check_rate_limit()
            
            url = f"{self.BASE_URL}/tokens/{address}"
            data = await self._fetch_with_retry(url)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching token info: {e}")
            return None
    
    async def _fetch_with_retry(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Fetch data from API with retry logic"""
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        self.request_count += 1
                        
                        if response.status == 200:
                            return await response.json()
                        
                        elif response.status == 429:
                            # Rate limited
                            wait_time = (2 ** attempt) * 2
                            logger.warning(f"DexScreener rate limit, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            logger.warning(f"DexScreener API status {response.status}")
                            return {}
                            
            except asyncio.TimeoutError:
                logger.warning(f"DexScreener timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"DexScreener API error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return {}
    
    async def _check_rate_limit(self):
        """Check and enforce rate limits (300 requests/min)"""
        
        current_time = datetime.utcnow()
        elapsed = (current_time - self.request_window_start).total_seconds()
        
        if elapsed >= 60:
            # Reset window
            self.request_count = 0
            self.request_window_start = current_time
        elif self.request_count >= self.max_requests_per_minute:
            # Wait until window resets
            wait_time = 60 - elapsed
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            self.request_count = 0
            self.request_window_start = datetime.utcnow()
    
    def _parse_pair_data(self, pair: Dict[str, Any]) -> Optional[TokenData]:
        """Parse DexScreener pair data into TokenData"""
        
        try:
            # Extract token info
            base_token = pair.get('baseToken', {})
            quote_token = pair.get('quoteToken', {})
            
            # Use base token (the actual token, not SOL)
            token_address = base_token.get('address', '')
            symbol = base_token.get('symbol', 'UNKNOWN')
            name = base_token.get('name', symbol)
            
            # Price and market data
            price_usd = float(pair.get('priceUsd', 0))
            liquidity_usd = float(pair.get('liquidity', {}).get('usd', 0))
            market_cap = float(pair.get('fdv', 0))  # Fully diluted valuation
            volume_24h = float(pair.get('volume', {}).get('h24', 0))
            
            # Price changes
            price_change = pair.get('priceChange', {})
            price_change_5min = float(price_change.get('m5', 0))
            price_change_1h = float(price_change.get('h1', 0))
            
            # Calculate age (if pairCreatedAt is available)
            created_at = pair.get('pairCreatedAt', 0)
            age_seconds = 0
            if created_at:
                age_seconds = int((datetime.utcnow().timestamp() - created_at / 1000))
            
            # Volume change (approximate from 24h data)
            volume_change_2min = 0.0  # Not available in DexScreener
            
            return TokenData(
                address=token_address,
                symbol=symbol,
                name=name,
                liquidity_usd=liquidity_usd,
                market_cap=market_cap,
                price_usd=price_usd,
                volume_24h=volume_24h,
                holders=0,  # Not available in DexScreener
                age_seconds=age_seconds,
                price_change_5min=price_change_5min,
                price_change_1h=price_change_1h,
                volume_change_2min=volume_change_2min,
                source='dexscreener',
                raw_data=pair
            )
            
        except Exception as e:
            logger.error(f"Error parsing pair data: {e}")
            return None
    
    def apply_prefilters(self, token_data: TokenData) -> bool:
        """Apply initial filters (liquidity, age, etc.)"""
        
        # Liquidity check
        if token_data.liquidity_usd < self.liquidity_min:
            return False
        
        if token_data.liquidity_usd > self.liquidity_max:
            return False
        
        # Age check (if available)
        if token_data.age_seconds > 0 and token_data.age_seconds > self.age_max_seconds:
            return False
        
        # Market cap check
        if token_data.market_cap > self.market_cap_max:
            return False
        
        return True
    
    def _has_momentum(self, token_data: TokenData) -> bool:
        """Check if token has momentum indicators"""
        
        # Price momentum check
        if token_data.price_change_5min >= 40:
            return True
        
        # Volume check
        if token_data.volume_24h > 50000:
            return True
        
        return False
    
    async def stop(self):
        """Stop the scanner"""
        logger.info("Stopping DexScreener scanner...")
        self.running = False
