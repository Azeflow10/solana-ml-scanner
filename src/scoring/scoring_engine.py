"""
Scoring Engine - Combines rule-based and ML scores with professional weights
"""

from typing import Dict, Any, Optional
import numpy as np
from src.utils.logger import get_logger
from src.models.token_data import (
    TokenData, RugCheckResult, LiquidityResult, 
    HolderResult, ScoringResult
)

logger = get_logger(__name__)


class ScoringEngine:
    """Main scoring engine combining multiple scoring methods"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize scoring engine"""
        self.config = config or {}
        self.ml_weight = self.config.get('ml_weight', 0.40)
        self.rule_weight = self.config.get('rule_weight', 0.60)
        
        logger.info(f"Scoring Engine initialized (ML: {self.ml_weight}, Rules: {self.rule_weight})")
    
    def calculate_score(
        self,
        token: TokenData,
        rugcheck: Optional[RugCheckResult] = None,
        liquidity: Optional[LiquidityResult] = None,
        holders: Optional[HolderResult] = None,
        ml_score: float = 0.0,
        ml_confidence: float = 0.0
    ) -> ScoringResult:
        """
        Calculate comprehensive opportunity scores
        
        Returns ScoringResult with:
        - score_combined (0-100)
        - score_rules (0-100) - rule-based
        - score_ml (0-100) - ML prediction
        - risk_level (LOW/MEDIUM/HIGH)
        - category (FAST_SNIPER/SMART_SNIPER/MOMENTUM/SAFE)
        """
        
        # Calculate individual component scores
        security_score = self._calculate_security_score(rugcheck)
        liquidity_score = self._calculate_liquidity_score(liquidity, token)
        holder_score = self._calculate_holder_score(holders)
        momentum_score = self._calculate_momentum_score(token)
        social_score = self._calculate_social_score(token)
        age_score = self._calculate_age_score(token)
        
        # Calculate rule-based score with professional weights
        rule_score = self._calculate_rule_score(
            security_score=security_score,
            liquidity_score=liquidity_score,
            holder_score=holder_score,
            momentum_score=momentum_score,
            social_score=social_score,
            age_score=age_score
        )
        
        # Calculate combined score
        if ml_score > 0 and ml_confidence >= 0.50:
            # Use ML score if available and confident
            combined_score = (rule_score * self.rule_weight) + (ml_score * self.ml_weight)
        else:
            # Use only rule-based score
            combined_score = rule_score
            ml_score = 0.0
            ml_confidence = 0.0
        
        # Determine category and risk level
        category = self._categorize_score(combined_score, token, rugcheck)
        risk_level = self._determine_risk_level(category, rugcheck, security_score)
        
        return ScoringResult(
            score_combined=combined_score,
            score_rules=rule_score,
            score_ml=ml_score,
            security_score=security_score,
            liquidity_score=liquidity_score,
            holder_score=holder_score,
            momentum_score=momentum_score,
            social_score=social_score,
            age_score=age_score,
            risk_level=risk_level,
            category=category,
            pattern=category,
            ml_confidence=ml_confidence
        )
    
    def _calculate_rule_score(
        self,
        security_score: float,
        liquidity_score: float,
        holder_score: float,
        momentum_score: float,
        social_score: float,
        age_score: float
    ) -> float:
        """
        Rule-based scoring with professional weights
        
        Formula:
        score_rules = (
            security_score * 0.30 +      # 30% - Security is critical
            liquidity_score * 0.20 +     # 20% - Adequate liquidity
            holder_score * 0.15 +        # 15% - Distribution
            momentum_score * 0.20 +      # 20% - Price action
            social_score * 0.10 +        # 10% - Social signals
            age_score * 0.05             # 5% - Not too old/new
        ) * 100
        """
        
        score = (
            security_score * 0.30 +
            liquidity_score * 0.20 +
            holder_score * 0.15 +
            momentum_score * 0.20 +
            social_score * 0.10 +
            age_score * 0.05
        ) * 100
        
        return min(100.0, max(0.0, score))
    
    def _calculate_security_score(self, rugcheck: Optional[RugCheckResult]) -> float:
        """Calculate security score (0-1)"""
        
        if not rugcheck:
            return 0.5  # Neutral if no data
        
        # Start with RugCheck score (0-10) normalized to 0-1
        score = rugcheck.overall_score / 10.0
        
        # Apply bonuses/penalties
        if rugcheck.mint_authority_frozen:
            score += 0.1
        else:
            score -= 0.2
        
        if rugcheck.freeze_authority_revoked:
            score += 0.1
        else:
            score -= 0.2
        
        if rugcheck.lp_locked or rugcheck.lp_burned:
            score += 0.15
        else:
            score -= 0.3
        
        if rugcheck.top_10_holders_percent < 35:
            score += 0.1
        elif rugcheck.top_10_holders_percent > 50:
            score -= 0.2
        
        if rugcheck.is_honeypot:
            score = 0.0  # Instant fail
        
        return min(1.0, max(0.0, score))
    
    def _calculate_liquidity_score(
        self,
        liquidity: Optional[LiquidityResult],
        token: TokenData
    ) -> float:
        """Calculate liquidity score (0-1)"""
        
        liquidity_usd = token.liquidity_usd
        if liquidity:
            liquidity_usd = max(liquidity_usd, liquidity.total_liquidity_usd)
        
        score = 0.0
        
        # Liquidity amount score
        if 10000 <= liquidity_usd <= 300000:
            # Sweet spot range
            score += 0.5
            
            # Bonus for being in optimal range ($30k-$150k)
            if 30000 <= liquidity_usd <= 150000:
                score += 0.2
        elif liquidity_usd < 10000:
            score += 0.2  # Too low
        else:
            score += 0.3  # High but outside sweet spot
        
        # LP locked/burned bonus
        if liquidity:
            total_secured = liquidity.lp_locked_percent + liquidity.lp_burned_percent
            score += (total_secured / 100) * 0.3
        
        return min(1.0, max(0.0, score))
    
    def _calculate_holder_score(self, holders: Optional[HolderResult]) -> float:
        """Calculate holder distribution score (0-1)"""
        
        if not holders:
            return 0.5  # Neutral if no data
        
        score = 0.0
        
        # Number of holders
        if holders.total_holders >= 200:
            score += 0.4
        elif holders.total_holders >= 100:
            score += 0.3
        elif holders.total_holders >= 50:
            score += 0.2
        elif holders.total_holders >= 15:
            score += 0.1
        else:
            score += 0.0  # Too few holders
        
        # Top 10 concentration (lower is better)
        if holders.top_10_concentration < 25:
            score += 0.3
        elif holders.top_10_concentration < 35:
            score += 0.2
        elif holders.top_10_concentration < 50:
            score += 0.1
        
        # Growth rate bonus
        if holders.growth_rate_per_min >= 20:
            score += 0.3
        elif holders.growth_rate_per_min >= 10:
            score += 0.2
        elif holders.growth_rate_per_min >= 5:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_momentum_score(self, token: TokenData) -> float:
        """Calculate momentum score (0-1)"""
        
        score = 0.0
        
        # Volume spike (most important)
        if token.volume_change_2min >= 300:
            score += 0.4
        elif token.volume_change_2min >= 200:
            score += 0.3
        elif token.volume_change_2min >= 100:
            score += 0.2
        elif token.volume_change_2min >= 50:
            score += 0.1
        
        # Price momentum 5min
        if token.price_change_5min >= 40:
            score += 0.3
        elif token.price_change_5min >= 20:
            score += 0.2
        elif token.price_change_5min >= 10:
            score += 0.1
        elif token.price_change_5min < 0:
            score -= 0.2  # Penalty for negative momentum
        
        # Price momentum 1h
        if token.price_change_1h >= 100:
            score += 0.3
        elif token.price_change_1h >= 50:
            score += 0.2
        elif token.price_change_1h >= 25:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_social_score(self, token: TokenData) -> float:
        """Calculate social signals score (0-1)"""
        
        # TODO: Implement social metrics (Twitter, Telegram, etc.)
        # For now, use volume as a proxy for social interest
        
        score = 0.5  # Default neutral
        
        if token.volume_24h > 100000:
            score += 0.3
        elif token.volume_24h > 50000:
            score += 0.2
        elif token.volume_24h > 10000:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_age_score(self, token: TokenData) -> float:
        """Calculate age score (0-1) - prefer ultra-early tokens"""
        
        age_seconds = token.age_seconds
        
        # Optimal: 1-5 minutes (60-300 seconds)
        if age_seconds <= 120:
            return 1.0  # Ultra early
        elif age_seconds <= 300:
            return 0.9  # Very early
        elif age_seconds <= 600:
            return 0.7  # Early
        elif age_seconds <= 1800:
            return 0.5  # Still early
        elif age_seconds <= 3600:
            return 0.3  # Getting old
        else:
            return 0.1  # Too old
    
    def _categorize_score(
        self,
        score: float,
        token: TokenData,
        rugcheck: Optional[RugCheckResult]
    ) -> str:
        """Categorize score into alert type based on characteristics"""
        
        # High security + high score = SAFE
        if rugcheck and rugcheck.overall_score >= 9.0 and score >= 70:
            if rugcheck.lp_locked or rugcheck.lp_burned:
                return 'SAFE'
        
        # Ultra early + good score = FAST_SNIPER
        if token.age_seconds <= 120 and score >= 70:
            return 'FAST_SNIPER'
        
        # Good security + medium early = SMART_SNIPER
        if 120 < token.age_seconds <= 300 and score >= 75:
            if rugcheck and rugcheck.overall_score >= 8.5:
                return 'SMART_SNIPER'
        
        # Strong momentum = MOMENTUM
        if token.price_change_5min >= 40 and score >= 70:
            return 'MOMENTUM'
        
        # Default categorization by score
        if score >= 80:
            return 'FAST_SNIPER'
        elif score >= 70:
            return 'SMART_SNIPER'
        elif score >= 60:
            return 'MOMENTUM'
        else:
            return 'SAFE'
    
    def _determine_risk_level(
        self,
        category: str,
        rugcheck: Optional[RugCheckResult],
        security_score: float
    ) -> str:
        """Determine risk level"""
        
        # SAFE category is always LOW risk
        if category == 'SAFE':
            return 'LOW'
        
        # Check security score
        if security_score >= 0.8:
            risk = 'LOW'
        elif security_score >= 0.6:
            risk = 'MEDIUM'
        else:
            risk = 'HIGH'
        
        # FAST_SNIPER has higher base risk
        if category == 'FAST_SNIPER' and risk == 'LOW':
            risk = 'MEDIUM'
        
        # Additional checks
        if rugcheck:
            if rugcheck.is_honeypot:
                return 'HIGH'
            
            if not rugcheck.mint_authority_frozen or not rugcheck.freeze_authority_revoked:
                if risk == 'LOW':
                    risk = 'MEDIUM'
            
            if rugcheck.top_10_holders_percent > 50:
                if risk != 'HIGH':
                    risk = 'MEDIUM'
        
        return risk
