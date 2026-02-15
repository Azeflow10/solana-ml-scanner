#!/usr/bin/env python3
"""
Test Scanner - Validate the token detection and analysis system
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.logger import setup_logger, get_logger
from src.models.token_data import TokenData
from src.analyzers.rugcheck_analyzer import RugCheckAnalyzer
from src.analyzers.liquidity_analyzer import LiquidityAnalyzer
from src.analyzers.holder_analyzer import HolderAnalyzer
from src.scoring.scoring_engine import ScoringEngine
from src.pattern_detection.pattern_detector import PatternDetector


class ScannerTester:
    """Test the scanner components"""
    
    def __init__(self):
        """Initialize tester"""
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.rugcheck_analyzer = RugCheckAnalyzer()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.holder_analyzer = HolderAnalyzer()
        self.scoring_engine = ScoringEngine()
        self.pattern_detector = PatternDetector()
        
        self.logger.info("Scanner Tester initialized")
    
    async def test_analyzers(self, token_address: str):
        """Test all analyzers with a real token"""
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Testing Analyzers with token: {token_address}")
        self.logger.info(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Test RugCheck analyzer
        self.logger.info("Testing RugCheck Analyzer...")
        try:
            rugcheck_result = await self.rugcheck_analyzer.analyze(token_address)
            self.logger.info(f"✅ RugCheck Score: {rugcheck_result.overall_score}/10")
            self.logger.info(f"   - Mint Authority Frozen: {rugcheck_result.mint_authority_frozen}")
            self.logger.info(f"   - Freeze Authority Revoked: {rugcheck_result.freeze_authority_revoked}")
            self.logger.info(f"   - Top 10 Holders: {rugcheck_result.top_10_holders_percent:.1f}%")
            self.logger.info(f"   - LP Locked: {rugcheck_result.lp_locked}")
            self.logger.info(f"   - LP Burned: {rugcheck_result.lp_burned}")
            if rugcheck_result.known_risks:
                self.logger.info(f"   - Risks: {', '.join(rugcheck_result.known_risks[:3])}")
        except Exception as e:
            self.logger.error(f"❌ RugCheck failed: {e}")
            rugcheck_result = None
        
        # Test Liquidity analyzer
        self.logger.info("\nTesting Liquidity Analyzer...")
        try:
            liquidity_result = await self.liquidity_analyzer.analyze(token_address)
            self.logger.info(f"✅ Liquidity: ${liquidity_result.total_liquidity_usd:,.2f}")
            self.logger.info(f"   - Liquidity SOL: {liquidity_result.liquidity_sol:.2f}")
            self.logger.info(f"   - LP Locked: {liquidity_result.lp_locked_percent:.1f}%")
            self.logger.info(f"   - LP Burned: {liquidity_result.lp_burned_percent:.1f}%")
            self.logger.info(f"   - Stability Score: {liquidity_result.liquidity_stability_score:.1f}/100")
        except Exception as e:
            self.logger.error(f"❌ Liquidity analysis failed: {e}")
            liquidity_result = None
        
        # Test Holder analyzer
        self.logger.info("\nTesting Holder Analyzer...")
        try:
            holder_result = await self.holder_analyzer.analyze(token_address)
            self.logger.info(f"✅ Holders: {holder_result.total_holders}")
            self.logger.info(f"   - Top 10 Concentration: {holder_result.top_10_concentration:.1f}%")
            self.logger.info(f"   - Distribution Score: {holder_result.distribution_score:.1f}/100")
            self.logger.info(f"   - Growth Rate: {holder_result.growth_rate_per_min:.1f}/min")
        except Exception as e:
            self.logger.error(f"❌ Holder analysis failed: {e}")
            holder_result = None
        
        elapsed = time.time() - start_time
        self.logger.info(f"\n⏱️  Analysis completed in {elapsed:.2f}s")
        
        return rugcheck_result, liquidity_result, holder_result
    
    async def test_scoring(self, token_data: TokenData, rugcheck, liquidity, holders):
        """Test scoring engine"""
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("Testing Scoring Engine")
        self.logger.info(f"{'='*60}\n")
        
        try:
            scoring_result = self.scoring_engine.calculate_score(
                token=token_data,
                rugcheck=rugcheck,
                liquidity=liquidity,
                holders=holders,
                ml_score=0.0,
                ml_confidence=0.0
            )
            
            self.logger.info(f"✅ Scoring Complete:")
            self.logger.info(f"   - Combined Score: {scoring_result.score_combined:.1f}/100")
            self.logger.info(f"   - Rule-based Score: {scoring_result.score_rules:.1f}/100")
            self.logger.info(f"   - Category: {scoring_result.category}")
            self.logger.info(f"   - Risk Level: {scoring_result.risk_level}")
            self.logger.info(f"\n   Component Scores:")
            self.logger.info(f"   - Security: {scoring_result.security_score*100:.1f}/100")
            self.logger.info(f"   - Liquidity: {scoring_result.liquidity_score*100:.1f}/100")
            self.logger.info(f"   - Holders: {scoring_result.holder_score*100:.1f}/100")
            self.logger.info(f"   - Momentum: {scoring_result.momentum_score*100:.1f}/100")
            self.logger.info(f"   - Social: {scoring_result.social_score*100:.1f}/100")
            self.logger.info(f"   - Age: {scoring_result.age_score*100:.1f}/100")
            
            return scoring_result
            
        except Exception as e:
            self.logger.error(f"❌ Scoring failed: {e}")
            return None
    
    async def test_pattern_detection(self, token_data: TokenData, rugcheck, liquidity, holders):
        """Test pattern detector"""
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("Testing Pattern Detection")
        self.logger.info(f"{'='*60}\n")
        
        try:
            pattern = self.pattern_detector.detect_pattern(
                token=token_data,
                rugcheck=rugcheck,
                liquidity=liquidity,
                holders=holders
            )
            
            risk_level = self.pattern_detector.get_risk_level(pattern, rugcheck)
            
            self.logger.info(f"✅ Pattern Detected: {pattern}")
            self.logger.info(f"   - Risk Level: {risk_level}")
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"❌ Pattern detection failed: {e}")
            return None
    
    async def test_full_pipeline(self, token_address: str, token_symbol: str = "TEST"):
        """Test the complete analysis pipeline"""
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"FULL PIPELINE TEST")
        self.logger.info(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Create sample token data
        token_data = TokenData(
            address=token_address,
            symbol=token_symbol,
            name=f"{token_symbol} Token",
            liquidity_usd=50000.0,
            market_cap=200000.0,
            price_usd=0.001,
            volume_24h=25000.0,
            holders=150,
            age_seconds=180,
            price_change_5min=25.0,
            price_change_1h=50.0,
            volume_change_2min=150.0,
            holder_growth_rate=12.0,
            source="test"
        )
        
        # Run analyzers
        rugcheck, liquidity, holders = await self.test_analyzers(token_address)
        
        # Run scoring
        scoring = await self.test_scoring(token_data, rugcheck, liquidity, holders)
        
        # Run pattern detection
        pattern = await self.test_pattern_detection(token_data, rugcheck, liquidity, holders)
        
        elapsed = time.time() - start_time
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"PIPELINE COMPLETE")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"⏱️  Total Time: {elapsed:.2f}s")
        
        if scoring:
            self.logger.info(f"🎯 Final Score: {scoring.score_combined:.1f}/100")
            self.logger.info(f"📊 Pattern: {pattern}")
            self.logger.info(f"⚠️  Risk: {scoring.risk_level}")
            
            if scoring.score_combined >= 70:
                self.logger.info(f"🚨 ALERT WORTHY: This token would trigger an alert!")
            else:
                self.logger.info(f"✋ Below threshold: Score too low for alert")
        
        return {
            'token': token_data,
            'rugcheck': rugcheck,
            'liquidity': liquidity,
            'holders': holders,
            'scoring': scoring,
            'pattern': pattern,
            'elapsed': elapsed
        }
    
    async def run_performance_benchmark(self):
        """Run performance benchmarks"""
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("Performance Benchmark")
        self.logger.info(f"{'='*60}\n")
        
        # Test with known Solana token addresses
        test_tokens = [
            "So11111111111111111111111111111111111111112",  # Wrapped SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        ]
        
        total_time = 0
        successful_tests = 0
        
        for token_address in test_tokens:
            try:
                self.logger.info(f"\nTesting {token_address}...")
                start = time.time()
                
                await self.test_analyzers(token_address)
                
                elapsed = time.time() - start
                total_time += elapsed
                successful_tests += 1
                
                self.logger.info(f"✅ Completed in {elapsed:.2f}s")
                
            except Exception as e:
                self.logger.error(f"❌ Test failed: {e}")
        
        if successful_tests > 0:
            avg_time = total_time / successful_tests
            self.logger.info(f"\n📊 Benchmark Results:")
            self.logger.info(f"   - Tests: {successful_tests}/{len(test_tokens)}")
            self.logger.info(f"   - Average Time: {avg_time:.2f}s")
            self.logger.info(f"   - Total Time: {total_time:.2f}s")
            
            # Check against requirements
            if avg_time < 5.0:
                self.logger.info(f"   - ✅ PASS: Under 5s requirement")
            else:
                self.logger.info(f"   - ❌ FAIL: Exceeds 5s requirement")


async def main():
    """Main test function"""
    
    # Setup logger
    logger = setup_logger()
    
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║       SOLANA ML SCANNER - TEST SUITE                   ║
    ║       Token Detection & Analysis System Tests          ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    tester = ScannerTester()
    
    # Test with a known Solana token
    test_token_address = "So11111111111111111111111111111111111111112"  # Wrapped SOL
    test_token_symbol = "SOL"
    
    try:
        # Run full pipeline test
        result = await tester.test_full_pipeline(test_token_address, test_token_symbol)
        
        # Run performance benchmark
        await tester.run_performance_benchmark()
        
        logger.info("\n✅ All tests completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
