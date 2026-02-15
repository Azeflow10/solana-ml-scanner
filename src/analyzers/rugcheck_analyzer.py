"""
RugCheck Analyzer - Integrates with RugCheck.xyz API for security analysis
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.models.token_data import RugCheckResult

logger = get_logger(__name__)


class RugCheckAnalyzer:
    """Analyze token security using RugCheck.xyz API"""
    
    BASE_URL = "https://api.rugcheck.xyz/v1"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize RugCheck analyzer"""
        self.config = config or {}
        self.timeout = self.config.get('timeout', 10)
        self.max_retries = self.config.get('max_retries', 3)
        self.cache = {}  # Simple cache for 30 seconds
        self.cache_ttl = 30
        
        logger.info("RugCheck Analyzer initialized")
    
    async def analyze(self, token_address: str) -> RugCheckResult:
        """
        Get comprehensive security analysis from RugCheck.xyz
        
        Returns RugCheckResult with:
        - Overall score (0-10)
        - Mint authority status
        - Freeze authority status
        - Top holders distribution
        - Liquidity lock status
        - Known risks
        """
        
        try:
            # Check cache
            cache_key = f"rugcheck_{token_address}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (asyncio.get_event_loop().time() - cached_time) < self.cache_ttl:
                    logger.debug(f"Using cached RugCheck data for {token_address}")
                    return cached_data
            
            # Fetch from API with retries
            data = await self._fetch_with_retry(token_address)
            
            # Parse the response
            result = self._parse_response(data, token_address)
            
            # Cache the result
            self.cache[cache_key] = (result, asyncio.get_event_loop().time())
            
            logger.info(f"RugCheck analysis complete for {token_address}: score={result.overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"RugCheck analysis failed for {token_address}: {e}")
            # Return conservative defaults on error
            return RugCheckResult(
                overall_score=5.0,
                mint_authority_frozen=False,
                freeze_authority_revoked=False,
                top_10_holders_percent=100.0,
                lp_locked=False,
                lp_burned=False,
                known_risks=["Analysis failed"],
                raw_data={}
            )
    
    async def _fetch_with_retry(self, token_address: str) -> Dict[str, Any]:
        """Fetch data from API with exponential backoff retry"""
        
        url = f"{self.BASE_URL}/tokens/{token_address}/report"
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        
                        if response.status == 200:
                            return await response.json()
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            wait_time = (2 ** attempt) * 1
                            logger.warning(f"RugCheck rate limit hit, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        elif response.status == 404:
                            logger.warning(f"Token {token_address} not found on RugCheck")
                            return {}
                        
                        else:
                            logger.warning(f"RugCheck API returned status {response.status}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return {}
                            
            except asyncio.TimeoutError:
                logger.warning(f"RugCheck API timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
            except Exception as e:
                logger.error(f"RugCheck API error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        return {}
    
    def _parse_response(self, data: Dict[str, Any], token_address: str) -> RugCheckResult:
        """Parse RugCheck API response into RugCheckResult"""
        
        if not data:
            # No data - return conservative defaults
            return RugCheckResult(
                overall_score=5.0,
                mint_authority_frozen=False,
                freeze_authority_revoked=False,
                top_10_holders_percent=100.0,
                lp_locked=False,
                lp_burned=False,
                known_risks=["No data available"],
                raw_data={}
            )
        
        try:
            # Extract security score (0-10 scale)
            # RugCheck returns various risk scores - we normalize to 0-10
            risk_score = data.get('risks', {})
            overall_score = 10.0  # Start with perfect score
            
            # Deduct points for risks
            if isinstance(risk_score, dict):
                for risk_type, risk_data in risk_score.items():
                    if isinstance(risk_data, dict):
                        severity = risk_data.get('level', 0)
                        if severity == 'danger':
                            overall_score -= 2.0
                        elif severity == 'warning':
                            overall_score -= 0.5
            
            overall_score = max(0.0, min(10.0, overall_score))
            
            # Extract token metadata
            token_meta = data.get('tokenMeta', {})
            mint_data = token_meta.get('mint', {})
            
            # Check authorities
            mint_authority_frozen = mint_data.get('mintAuthority') is None
            freeze_authority_revoked = mint_data.get('freezeAuthority') is None
            
            # Extract holder distribution
            top_holders = data.get('topHolders', [])
            top_10_percent = 0.0
            if top_holders:
                # Sum up top 10 holders percentage
                top_10_percent = sum(
                    holder.get('pct', 0) for holder in top_holders[:10]
                )
            
            # Extract LP info
            markets = data.get('markets', [])
            lp_locked = False
            lp_burned = False
            
            for market in markets:
                lp_info = market.get('lp', {})
                if lp_info.get('lpLockedPct', 0) > 0:
                    lp_locked = True
                if lp_info.get('lpBurnPct', 0) > 0:
                    lp_burned = True
            
            # Extract known risks
            known_risks = []
            if 'risks' in data:
                for risk_type, risk_data in data['risks'].items():
                    if isinstance(risk_data, dict) and risk_data.get('level') in ['danger', 'warning']:
                        known_risks.append(risk_data.get('description', risk_type))
            
            # Check for honeypot
            is_honeypot = any('honeypot' in str(risk).lower() for risk in known_risks)
            can_sell = not is_honeypot
            
            return RugCheckResult(
                overall_score=overall_score,
                mint_authority_frozen=mint_authority_frozen,
                freeze_authority_revoked=freeze_authority_revoked,
                top_10_holders_percent=top_10_percent,
                lp_locked=lp_locked,
                lp_burned=lp_burned,
                known_risks=known_risks,
                is_honeypot=is_honeypot,
                can_sell=can_sell,
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Error parsing RugCheck response: {e}")
            return RugCheckResult(
                overall_score=5.0,
                mint_authority_frozen=False,
                freeze_authority_revoked=False,
                top_10_holders_percent=100.0,
                lp_locked=False,
                lp_burned=False,
                known_risks=["Parse error"],
                raw_data=data
            )
