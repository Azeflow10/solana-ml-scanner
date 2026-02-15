"""
Liquidity Analyzer - Analyzes token liquidity metrics
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.models.token_data import LiquidityResult

logger = get_logger(__name__)


class LiquidityAnalyzer:
    """Analyzes token liquidity depth and quality"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize liquidity analyzer"""
        self.config = config or {}
        self.timeout = self.config.get('timeout', 10)
        self.cache = {}
        self.cache_ttl = 30
        
        logger.info("Liquidity Analyzer initialized")
    
    async def analyze(self, token_address: str, token_data: Optional[Dict[str, Any]] = None) -> LiquidityResult:
        """
        Analyze liquidity metrics
        
        Returns LiquidityResult with:
        - Total liquidity USD
        - LP locked %
        - LP burn %
        - Price impact for trades
        - Liquidity stability score
        """
        
        try:
            # Check cache
            cache_key = f"liquidity_{token_address}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (asyncio.get_event_loop().time() - cached_time) < self.cache_ttl:
                    logger.debug(f"Using cached liquidity data for {token_address}")
                    return cached_data
            
            # Fetch liquidity data from DexScreener
            data = await self._fetch_dexscreener_data(token_address)
            
            # Parse the response
            result = self._parse_liquidity_data(data, token_data)
            
            # Cache the result
            self.cache[cache_key] = (result, asyncio.get_event_loop().time())
            
            logger.info(f"Liquidity analysis complete for {token_address}: ${result.total_liquidity_usd:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Liquidity analysis failed for {token_address}: {e}")
            # Return defaults on error
            return LiquidityResult(
                total_liquidity_usd=0.0,
                liquidity_sol=0.0,
                lp_locked_percent=0.0,
                lp_burned_percent=0.0,
                liquidity_stability_score=0.0
            )
    
    async def _fetch_dexscreener_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch liquidity data from DexScreener API"""
        
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"DexScreener API returned status {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"DexScreener API error: {e}")
            return {}
    
    def _parse_liquidity_data(
        self,
        data: Dict[str, Any],
        token_data: Optional[Dict[str, Any]] = None
    ) -> LiquidityResult:
        """Parse liquidity data from API response"""
        
        if not data or 'pairs' not in data or not data['pairs']:
            # Use token_data if available
            if token_data:
                return LiquidityResult(
                    total_liquidity_usd=token_data.get('liquidity_usd', 0.0),
                    liquidity_sol=token_data.get('liquidity_sol', 0.0),
                    lp_locked_percent=0.0,
                    lp_burned_percent=0.0,
                    liquidity_stability_score=50.0
                )
            
            return LiquidityResult(
                total_liquidity_usd=0.0,
                liquidity_sol=0.0,
                lp_locked_percent=0.0,
                lp_burned_percent=0.0,
                liquidity_stability_score=0.0
            )
        
        try:
            # Get the main pair (usually first one)
            pair = data['pairs'][0]
            
            # Extract liquidity data
            liquidity_usd = float(pair.get('liquidity', {}).get('usd', 0))
            
            # Estimate SOL liquidity (assuming SOL ~$100)
            sol_price = 100.0  # TODO: Get real SOL price
            liquidity_sol = liquidity_usd / (2 * sol_price)  # Divide by 2 as it's split in pair
            
            # LP lock/burn data
            lp_locked = 0.0
            lp_burned = 0.0
            
            # DexScreener may have this in different formats
            if 'liquidity' in pair:
                liq_info = pair['liquidity']
                if isinstance(liq_info, dict):
                    # Some DEXes provide lock info
                    lp_locked = float(liq_info.get('locked', 0))
                    lp_burned = float(liq_info.get('burned', 0))
            
            # Calculate price impact estimates
            # Simple heuristic: higher liquidity = lower impact
            price_impact_1k = self._estimate_price_impact(liquidity_usd, 1000)
            price_impact_5k = self._estimate_price_impact(liquidity_usd, 5000)
            
            # Calculate liquidity stability score (0-100)
            stability_score = self._calculate_stability_score(
                liquidity_usd,
                lp_locked,
                lp_burned,
                price_impact_1k
            )
            
            return LiquidityResult(
                total_liquidity_usd=liquidity_usd,
                liquidity_sol=liquidity_sol,
                lp_locked_percent=lp_locked,
                lp_burned_percent=lp_burned,
                price_impact_1k_usd=price_impact_1k,
                price_impact_5k_usd=price_impact_5k,
                liquidity_stability_score=stability_score,
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Error parsing liquidity data: {e}")
            return LiquidityResult(
                total_liquidity_usd=0.0,
                liquidity_sol=0.0,
                lp_locked_percent=0.0,
                lp_burned_percent=0.0,
                liquidity_stability_score=0.0
            )
    
    def _estimate_price_impact(self, liquidity_usd: float, trade_size_usd: float) -> float:
        """Estimate price impact for a given trade size"""
        
        if liquidity_usd <= 0:
            return 100.0  # Max impact
        
        # Simple constant product formula approximation
        # impact ≈ trade_size / liquidity
        impact_percent = (trade_size_usd / liquidity_usd) * 100
        
        return min(100.0, impact_percent)
    
    def _calculate_stability_score(
        self,
        liquidity_usd: float,
        lp_locked: float,
        lp_burned: float,
        price_impact_1k: float
    ) -> float:
        """Calculate liquidity stability score (0-100)"""
        
        score = 0.0
        
        # Liquidity amount (40 points)
        if liquidity_usd >= 100000:
            score += 40
        elif liquidity_usd >= 50000:
            score += 30
        elif liquidity_usd >= 20000:
            score += 20
        elif liquidity_usd >= 10000:
            score += 10
        
        # LP locked/burned (40 points)
        total_secured = lp_locked + lp_burned
        score += min(40, total_secured * 0.4)
        
        # Price impact (20 points)
        if price_impact_1k < 1:
            score += 20
        elif price_impact_1k < 3:
            score += 15
        elif price_impact_1k < 5:
            score += 10
        elif price_impact_1k < 10:
            score += 5
        
        return min(100.0, score)
