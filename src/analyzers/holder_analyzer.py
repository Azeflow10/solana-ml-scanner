"""
Holder Analyzer - Analyzes token holder distribution
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.models.token_data import HolderResult

logger = get_logger(__name__)


class HolderAnalyzer:
    """Analyzes token holder distribution"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize holder analyzer"""
        self.config = config or {}
        self.timeout = self.config.get('timeout', 10)
        self.cache = {}
        self.cache_ttl = 30
        
        logger.info("Holder Analyzer initialized")
    
    async def analyze(self, token_address: str, token_data: Optional[Dict[str, Any]] = None) -> HolderResult:
        """
        Analyze holder distribution
        
        Returns HolderResult with:
        - Total holders
        - Top 10 concentration %
        - Dev wallet %
        - Growth rate
        - Distribution score
        """
        
        try:
            # Check cache
            cache_key = f"holders_{token_address}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (asyncio.get_event_loop().time() - cached_time) < self.cache_ttl:
                    logger.debug(f"Using cached holder data for {token_address}")
                    return cached_data
            
            # Fetch holder data
            # Note: This would typically come from Helius RPC or similar
            # For now, we'll use data from token_data or DexScreener
            result = await self._analyze_holders(token_address, token_data)
            
            # Cache the result
            self.cache[cache_key] = (result, asyncio.get_event_loop().time())
            
            logger.info(f"Holder analysis complete for {token_address}: {result.total_holders} holders")
            return result
            
        except Exception as e:
            logger.error(f"Holder analysis failed for {token_address}: {e}")
            # Return defaults on error
            return HolderResult(
                total_holders=0,
                top_10_concentration=100.0,
                distribution_score=0.0
            )
    
    async def _analyze_holders(
        self,
        token_address: str,
        token_data: Optional[Dict[str, Any]] = None
    ) -> HolderResult:
        """Analyze holder distribution"""
        
        # Start with defaults
        total_holders = 0
        top_10_concentration = 100.0
        top_20_concentration = 100.0
        dev_wallet_percent = 0.0
        growth_rate = 0.0
        
        # Try to get data from token_data first
        if token_data:
            total_holders = token_data.get('holders', 0)
            growth_rate = token_data.get('holder_growth_rate', 0.0)
        
        # Try to fetch from DexScreener for additional info
        try:
            dex_data = await self._fetch_dexscreener_data(token_address)
            
            if dex_data and 'pairs' in dex_data and dex_data['pairs']:
                pair = dex_data['pairs'][0]
                
                # Some pairs have holder info
                if 'info' in pair:
                    info = pair['info']
                    if 'holders' in info:
                        total_holders = max(total_holders, int(info['holders']))
                
                # Try to get holder concentration from pair data
                # This is an estimate as DexScreener doesn't always provide this
                if total_holders > 0:
                    # Estimate based on typical distributions
                    # More holders = better distribution
                    if total_holders > 1000:
                        top_10_concentration = 15.0
                        top_20_concentration = 25.0
                    elif total_holders > 500:
                        top_10_concentration = 25.0
                        top_20_concentration = 40.0
                    elif total_holders > 200:
                        top_10_concentration = 35.0
                        top_20_concentration = 50.0
                    elif total_holders > 50:
                        top_10_concentration = 50.0
                        top_20_concentration = 70.0
                    else:
                        top_10_concentration = 70.0
                        top_20_concentration = 90.0
                
        except Exception as e:
            logger.warning(f"Could not fetch additional holder data: {e}")
        
        # Calculate distribution score (0-100)
        distribution_score = self._calculate_distribution_score(
            total_holders,
            top_10_concentration,
            dev_wallet_percent
        )
        
        return HolderResult(
            total_holders=total_holders,
            top_10_concentration=top_10_concentration,
            top_20_concentration=top_20_concentration,
            dev_wallet_percent=dev_wallet_percent,
            growth_rate_per_min=growth_rate,
            distribution_score=distribution_score
        )
    
    async def _fetch_dexscreener_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch data from DexScreener API"""
        
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
                        return {}
                        
        except Exception as e:
            logger.debug(f"DexScreener fetch error: {e}")
            return {}
    
    def _calculate_distribution_score(
        self,
        total_holders: int,
        top_10_concentration: float,
        dev_wallet_percent: float
    ) -> float:
        """Calculate holder distribution score (0-100)"""
        
        score = 0.0
        
        # Number of holders (40 points)
        if total_holders >= 1000:
            score += 40
        elif total_holders >= 500:
            score += 35
        elif total_holders >= 200:
            score += 30
        elif total_holders >= 100:
            score += 25
        elif total_holders >= 50:
            score += 20
        elif total_holders >= 20:
            score += 10
        
        # Top 10 concentration (40 points)
        # Lower is better
        if top_10_concentration <= 20:
            score += 40
        elif top_10_concentration <= 30:
            score += 30
        elif top_10_concentration <= 40:
            score += 20
        elif top_10_concentration <= 50:
            score += 10
        
        # Dev wallet (20 points)
        # Lower is better
        if dev_wallet_percent <= 5:
            score += 20
        elif dev_wallet_percent <= 10:
            score += 15
        elif dev_wallet_percent <= 15:
            score += 10
        elif dev_wallet_percent <= 20:
            score += 5
        
        return min(100.0, score)
