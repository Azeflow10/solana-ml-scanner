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
from src.core.config import Config

async def main():
    print("🔍 Scanner & Analyzer Test")
    print("=" * 60)
    
    # Test with a known token (e.g., popular Solana token)
    test_token_address = "So11111111111111111111111111111111111111112"  # Wrapped SOL
    
    print(f"\n📍 Testing with token: {test_token_address}")
    print()
    
    # Initialize components
    config = Config()
    dex_scanner = DexScreenerScanner(config)
    rugcheck = RugCheckAnalyzer(config)
    liquidity = LiquidityAnalyzer(config)
    holder = HolderAnalyzer(config)
    scoring = ScoringEngine(config)
    pattern = PatternDetector(config)
    
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
    rugcheck_result = await rugcheck.analyze(test_token_address)
    if rugcheck_result:
        print(f"✅ RugCheck score: {rugcheck_result.get('score', 'N/A')}/10")
    else:
        print("⚠️  RugCheck analysis failed (may be rate limited)")
    print()
    
    # Test Liquidity Analysis
    print("💧 Step 3: Analyzing liquidity...")
    liquidity_result = await liquidity.analyze(test_token_address)
    if liquidity_result:
        print(f"✅ Liquidity: ${liquidity_result.get('total_usd', 0):,.0f}")
    else:
        print("⚠️  Liquidity analysis failed")
    print()
    
    # Test Holder Analysis
    print("👥 Step 4: Analyzing holders...")
    holder_result = await holder.analyze(test_token_address)
    if holder_result:
        print(f"✅ Holders: {holder_result.get('total_holders', 'N/A')}")
    else:
        print("⚠️  Holder analysis failed")
    print()
    
    # Combine results and calculate score
    print("🎯 Step 5: Calculating scores...")
    combined_data = {
        'token_info': token_info,
        'rugcheck': rugcheck_result,
        'liquidity': liquidity_result,
        'holders': holder_result
    }
    
    scores = scoring.calculate_score(combined_data)
    print(f"✅ Combined Score: {scores.get('score_combined', 0)}/100")
    print(f"   ├─ Rule Score: {scores.get('score_rules', 0)}/100")
    print(f"   └─ ML Score: {scores.get('score_ml', 0)}/100")
    print()
    
    # Detect pattern
    print("🔍 Step 6: Detecting pattern...")
    detected_pattern = pattern.detect_pattern(combined_data)
    print(f"✅ Pattern: {detected_pattern}")
    print()
    
    print("=" * 60)
    print("🎉 Test complete!")

if __name__ == "__main__":
    asyncio.run(main())
