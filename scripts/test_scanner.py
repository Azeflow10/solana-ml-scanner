#!/usr/bin/env python3
"""Test scanner functionality"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now imports will work
from src.scanners.dexscreener_scanner import DexScreenerScanner
from src.analyzers.rugcheck_analyzer import RugCheckAnalyzer
from src.analyzers.liquidity_analyzer import LiquidityAnalyzer
from src.analyzers.holder_analyzer import HolderAnalyzer
from src.scoring.scoring_engine import ScoringEngine
from src.pattern_detection.pattern_detector import PatternDetector
from src.models.token_data import TokenData

async def main():
    print("🔍 Scanner & Analyzer Test")
    print("=" * 60)
    
    # Test with a known token (e.g., popular Solana token)
    test_token_address = "So11111111111111111111111111111111111111112"  # Wrapped SOL
    
    print(f"\n📍 Testing with token: {test_token_address}")
    print()
    
    # Initialize components with minimal config
    config = {
        'poll_interval': 10,
        'liquidity_min': 10000,
        'timeout': 10
    }
    
    dex_scanner = DexScreenerScanner(config)
    rugcheck = RugCheckAnalyzer(config)
    liquidity = LiquidityAnalyzer(config)
    holder = HolderAnalyzer(config)
    scoring = ScoringEngine(config)
    pattern = PatternDetector()  # Note: PatternDetector uses no config by design
    
    print("✅ Components initialized")
    print()
    
    # Test DexScreener
    print("📊 Step 1: Fetching token info from DexScreener...")
    token_info = await dex_scanner.get_token_info(test_token_address)
    if token_info:
        print(f"✅ Token info retrieved: {token_info.get('symbol', 'Unknown')}")
    else:
        print("❌ Failed to get token info")
    print()
    
    # Test RugCheck
    print("🔒 Step 2: Running RugCheck analysis...")
    try:
        rugcheck_result = await rugcheck.analyze(test_token_address)
        if rugcheck_result:
            print(f"✅ RugCheck score: {rugcheck_result.overall_score}/10")
        else:
            print("⚠️  RugCheck analysis failed (may be rate limited)")
    except Exception as e:
        print(f"⚠️  RugCheck analysis failed: {e}")
        rugcheck_result = None
    print()
    
    # Test Liquidity Analysis
    print("💧 Step 3: Analyzing liquidity...")
    try:
        liquidity_result = await liquidity.analyze(test_token_address)
        if liquidity_result:
            print(f"✅ Liquidity: ${liquidity_result.total_liquidity_usd:,.0f}")
        else:
            print("⚠️  Liquidity analysis failed")
    except Exception as e:
        print(f"⚠️  Liquidity analysis failed: {e}")
        liquidity_result = None
    print()
    
    # Test Holder Analysis
    print("👥 Step 4: Analyzing holders...")
    try:
        holder_result = await holder.analyze(test_token_address)
        if holder_result:
            print(f"✅ Holders: {holder_result.total_holders}")
        else:
            print("⚠️  Holder analysis failed")
    except Exception as e:
        print(f"⚠️  Holder analysis failed: {e}")
        holder_result = None
    print()
    
    # Create a TokenData object for scoring
    print("🎯 Step 5: Calculating scores...")
    if token_info:
        token_data = TokenData(
            address=test_token_address,
            symbol=token_info.get('symbol', 'SOL'),
            name=token_info.get('name', 'Wrapped SOL'),
            liquidity_usd=token_info.get('liquidity', 0),
            market_cap=token_info.get('market_cap', 0),
            price_usd=token_info.get('price', 0),
            volume_24h=token_info.get('volume_24h', 0),
            holders=token_info.get('holders', 0),
            age_seconds=token_info.get('age_seconds', 0),
            source='dexscreener'
        )
        
        scores = scoring.calculate_score(
            token=token_data,
            rugcheck=rugcheck_result,
            liquidity=liquidity_result,
            holders=holder_result
        )
        print(f"✅ Combined Score: {scores.score_combined:.0f}/100")
        print(f"   ├─ Rule Score: {scores.score_rules:.0f}/100")
        print(f"   └─ ML Score: {scores.score_ml:.0f}/100")
        print()
        
        # Detect pattern
        print("🔍 Step 6: Detecting pattern...")
        detected_pattern = pattern.detect_pattern(
            token=token_data,
            rugcheck=rugcheck_result,
            liquidity=liquidity_result,
            holders=holder_result
        )
        print(f"✅ Pattern: {detected_pattern}")
        print()
    else:
        print("⚠️  Skipping scoring and pattern detection (no token info)")
        print()
    
    print("=" * 60)
    print("🎉 Test complete!")

if __name__ == "__main__":
    asyncio.run(main())
