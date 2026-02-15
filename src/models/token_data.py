"""
Token Data Models - Core data structures for token analysis
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class TokenData:
    """Token data structure for analysis"""
    
    # Basic info
    address: str
    symbol: str
    name: str
    
    # Market data
    liquidity_usd: float
    market_cap: float
    price_usd: float
    volume_24h: float = 0.0
    
    # Holder data
    holders: int = 0
    
    # Age
    age_seconds: int = 0
    created_at: Optional[datetime] = None
    
    # Price momentum
    price_change_5min: float = 0.0
    price_change_1h: float = 0.0
    volume_change_2min: float = 0.0
    
    # Additional metrics
    holder_growth_rate: float = 0.0  # holders per minute
    liquidity_sol: float = 0.0
    
    # Source info
    source: str = "unknown"  # pumpfun, raydium, dexscreener
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'address': self.address,
            'symbol': self.symbol,
            'name': self.name,
            'liquidity_usd': self.liquidity_usd,
            'market_cap': self.market_cap,
            'price_usd': self.price_usd,
            'volume_24h': self.volume_24h,
            'holders': self.holders,
            'age_seconds': self.age_seconds,
            'price_change_5min': self.price_change_5min,
            'price_change_1h': self.price_change_1h,
            'volume_change_2min': self.volume_change_2min,
            'holder_growth_rate': self.holder_growth_rate,
            'liquidity_sol': self.liquidity_sol,
            'source': self.source
        }


@dataclass
class RugCheckResult:
    """Results from RugCheck.xyz analysis"""
    
    overall_score: float  # 0-10
    mint_authority_frozen: bool
    freeze_authority_revoked: bool
    top_10_holders_percent: float
    lp_locked: bool
    lp_burned: bool
    known_risks: List[str] = field(default_factory=list)
    is_honeypot: bool = False
    can_sell: bool = True
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LiquidityResult:
    """Results from liquidity analysis"""
    
    total_liquidity_usd: float
    liquidity_sol: float
    lp_locked_percent: float
    lp_burned_percent: float
    price_impact_1k_usd: float = 0.0
    price_impact_5k_usd: float = 0.0
    liquidity_stability_score: float = 0.0  # 0-100
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HolderResult:
    """Results from holder distribution analysis"""
    
    total_holders: int
    top_10_concentration: float  # percentage
    top_20_concentration: float = 0.0
    dev_wallet_percent: float = 0.0
    growth_rate_per_min: float = 0.0
    distribution_score: float = 0.0  # 0-100
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringResult:
    """Results from scoring engine"""
    
    # Final scores
    score_combined: float  # 0-100
    score_rules: float  # 0-100
    score_ml: float = 0.0  # 0-100
    
    # Component scores
    security_score: float = 0.0
    liquidity_score: float = 0.0
    holder_score: float = 0.0
    momentum_score: float = 0.0
    social_score: float = 0.0
    age_score: float = 0.0
    
    # Classification
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    category: str = "UNKNOWN"  # FAST_SNIPER, SMART_SNIPER, MOMENTUM, SAFE
    pattern: str = "UNKNOWN"
    
    # ML confidence
    ml_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'score_combined': self.score_combined,
            'score_rules': self.score_rules,
            'score_ml': self.score_ml,
            'security_score': self.security_score,
            'liquidity_score': self.liquidity_score,
            'holder_score': self.holder_score,
            'momentum_score': self.momentum_score,
            'social_score': self.social_score,
            'age_score': self.age_score,
            'risk_level': self.risk_level,
            'category': self.category,
            'pattern': self.pattern,
            'ml_confidence': self.ml_confidence
        }


@dataclass
class AnalysisResult:
    """Complete analysis result for a token"""
    
    token: TokenData
    rugcheck: Optional[RugCheckResult] = None
    liquidity: Optional[LiquidityResult] = None
    holders: Optional[HolderResult] = None
    scoring: Optional[ScoringResult] = None
    
    # Metadata
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    analysis_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        """Check if all analyses completed successfully"""
        return all([
            self.rugcheck is not None,
            self.liquidity is not None,
            self.holders is not None,
            self.scoring is not None
        ])
    
    def should_alert(self, min_score: float = 70.0) -> bool:
        """Determine if this token should trigger an alert"""
        if not self.is_complete() or self.scoring is None:
            return False
        
        return self.scoring.score_combined >= min_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'token': self.token.to_dict(),
            'rugcheck': self.rugcheck.__dict__ if self.rugcheck else None,
            'liquidity': self.liquidity.__dict__ if self.liquidity else None,
            'holders': self.holders.__dict__ if self.holders else None,
            'scoring': self.scoring.to_dict() if self.scoring else None,
            'analyzed_at': self.analyzed_at.isoformat(),
            'analysis_duration_ms': self.analysis_duration_ms,
            'errors': self.errors
        }
