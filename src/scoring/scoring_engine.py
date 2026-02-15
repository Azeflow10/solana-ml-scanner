"""
Scoring Engine - Combines rule-based and ML scores
"""

from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ScoringEngine:
    """Main scoring engine combining multiple scoring methods"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize scoring engine"""
        self.config = config
        self.ml_weight = config.get('ml_weight', 0.40)
        self.rule_weight = config.get('rule_weight', 0.60)
        
        logger.info(f"Scoring Engine initialized (ML: {self.ml_weight}, Rules: {self.rule_weight})")
    
    def calculate_final_score(
        self,
        rule_score: float,
        ml_score: float
    ) -> Dict[str, Any]:
        """Calculate final weighted score"""
        final_score = (rule_score * self.rule_weight) + (ml_score * self.ml_weight)
        
        return {
            'final_score': final_score,
            'rule_component': rule_score * self.rule_weight,
            'ml_component': ml_score * self.ml_weight,
            'category': self._categorize_score(final_score)
        }
    
    def _categorize_score(self, score: float) -> str:
        """Categorize score into alert type"""
        if score >= 80:
            return 'FAST_SNIPER'
        elif score >= 70:
            return 'SMART_SNIPER'
        elif score >= 60:
            return 'MOMENTUM'
        else:
            return 'SAFE'
