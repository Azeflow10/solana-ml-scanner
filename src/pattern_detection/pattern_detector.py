"""
Pattern Detector - Detect successful token launch patterns
"""

from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.models.token_data import TokenData, RugCheckResult, LiquidityResult, HolderResult

logger = get_logger(__name__)


class PatternDetector:
    """Detect successful token launch patterns"""
    
    def __init__(self):
        """Initialize pattern detector"""
        logger.info("Pattern Detector initialized")
    
    def detect_pattern(
        self,
        token: TokenData,
        rugcheck: Optional[RugCheckResult] = None,
        liquidity: Optional[LiquidityResult] = None,
        holders: Optional[HolderResult] = None
    ) -> str:
        """
        Identify pattern type based on token characteristics
        
        Patterns:
        - FAST_SNIPER: Ultra early, low liquidity, growing fast
        - SMART_SNIPER: Good security, medium liquidity, solid fundamentals
        - MOMENTUM: Established momentum, higher liquidity, proven growth
        - SAFE: High security, locked LP, low risk
        - WHALE_ACCUMULATION: Big buys detected
        """
        
        # Check for FAST_SNIPER pattern
        if self._is_fast_sniper(token, liquidity, holders):
            return "FAST_SNIPER"
        
        # Check for SMART_SNIPER pattern
        if self._is_smart_sniper(token, rugcheck, liquidity):
            return "SMART_SNIPER"
        
        # Check for MOMENTUM pattern
        if self._is_momentum(token, holders):
            return "MOMENTUM"
        
        # Check for SAFE pattern
        if self._is_safe(rugcheck, liquidity):
            return "SAFE"
        
        # Check for WHALE_ACCUMULATION pattern
        if self._is_whale_accumulation(token, holders):
            return "WHALE_ACCUMULATION"
        
        return "UNKNOWN"
    
    def _is_fast_sniper(
        self,
        token: TokenData,
        liquidity: Optional[LiquidityResult],
        holders: Optional[HolderResult]
    ) -> bool:
        """
        FAST_SNIPER:
        - Age < 2 minutes (120 seconds)
        - Liquidity: $10k-$50k
        - Holders growing fast (+15/min)
        - Volume spike > 200%
        """
        
        # Age check
        if token.age_seconds > 120:
            return False
        
        # Liquidity range check
        if not (10000 <= token.liquidity_usd <= 50000):
            return False
        
        # Holder growth rate check
        if holders and holders.growth_rate_per_min >= 15:
            return True
        
        # Volume spike check
        if token.volume_change_2min >= 200:
            return True
        
        return False
    
    def _is_smart_sniper(
        self,
        token: TokenData,
        rugcheck: Optional[RugCheckResult],
        liquidity: Optional[LiquidityResult]
    ) -> bool:
        """
        SMART_SNIPER:
        - Age: 2-5 minutes (120-300 seconds)
        - Liquidity: $30k-$150k
        - RugCheck > 8.5
        - LP locked/burned
        """
        
        # Age check
        if not (120 < token.age_seconds <= 300):
            return False
        
        # Liquidity range check
        if not (30000 <= token.liquidity_usd <= 150000):
            return False
        
        # Security checks
        if rugcheck:
            if rugcheck.overall_score < 8.5:
                return False
            
            if not (rugcheck.lp_locked or rugcheck.lp_burned):
                return False
            
            return True
        
        return False
    
    def _is_momentum(
        self,
        token: TokenData,
        holders: Optional[HolderResult]
    ) -> bool:
        """
        MOMENTUM:
        - Age: 5-30 minutes (300-1800 seconds)
        - Strong price momentum (+40% in 5min)
        - Volume increasing
        - Holder growth steady
        """
        
        # Age check
        if not (300 < token.age_seconds <= 1800):
            return False
        
        # Price momentum check
        if token.price_change_5min < 40:
            return False
        
        # Holder growth check (steady growth)
        if holders and holders.growth_rate_per_min >= 10:
            return True
        
        # Volume check
        if token.volume_change_2min > 0:
            return True
        
        return False
    
    def _is_safe(
        self,
        rugcheck: Optional[RugCheckResult],
        liquidity: Optional[LiquidityResult]
    ) -> bool:
        """
        SAFE:
        - RugCheck > 9.0
        - LP 100% locked/burned
        - No mint/freeze authority
        - Top 10 < 25%
        """
        
        if not rugcheck:
            return False
        
        # High security score
        if rugcheck.overall_score < 9.0:
            return False
        
        # LP fully locked or burned
        if liquidity:
            total_lp_secured = liquidity.lp_locked_percent + liquidity.lp_burned_percent
            if total_lp_secured < 100:
                return False
        
        # Authority checks
        if not rugcheck.mint_authority_frozen:
            return False
        
        if not rugcheck.freeze_authority_revoked:
            return False
        
        # Top 10 concentration check
        if rugcheck.top_10_holders_percent >= 25:
            return False
        
        return True
    
    def _is_whale_accumulation(
        self,
        token: TokenData,
        holders: Optional[HolderResult]
    ) -> bool:
        """
        WHALE_ACCUMULATION:
        - Large volume spike
        - Low holder concentration increasing
        - Significant price movement
        """
        
        # Large volume spike
        if token.volume_change_2min < 300:
            return False
        
        # Significant price movement
        if token.price_change_5min < 20:
            return False
        
        # Check holder concentration
        if holders:
            # Whales accumulating but not too concentrated
            if 20 <= holders.top_10_concentration <= 40:
                return True
        
        return False
    
    def get_risk_level(self, pattern: str, rugcheck: Optional[RugCheckResult] = None) -> str:
        """
        Determine risk level based on pattern and security analysis
        
        Returns: LOW, MEDIUM, or HIGH
        """
        
        # SAFE pattern is always LOW risk
        if pattern == "SAFE":
            return "LOW"
        
        # FAST_SNIPER is MEDIUM-HIGH risk
        if pattern == "FAST_SNIPER":
            if rugcheck and rugcheck.overall_score >= 8.0:
                return "MEDIUM"
            return "HIGH"
        
        # SMART_SNIPER is MEDIUM risk
        if pattern == "SMART_SNIPER":
            return "MEDIUM"
        
        # MOMENTUM is MEDIUM risk
        if pattern == "MOMENTUM":
            # Lower risk if high security score
            if rugcheck and rugcheck.overall_score >= 8.5:
                return "LOW"
            return "MEDIUM"
        
        # WHALE_ACCUMULATION is MEDIUM-HIGH risk
        if pattern == "WHALE_ACCUMULATION":
            if rugcheck and rugcheck.overall_score >= 8.0:
                return "MEDIUM"
            return "HIGH"
        
        # Default to HIGH for unknown patterns
        return "HIGH"
