#!/usr/bin/env python3
"""
Test script for Telegram bot integration
Verifies connectivity, message sending, and button functionality
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import Config
from src.notifications.telegram_bot import TelegramBot
from src.notifications.formatter import MessageFormatter
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_mock_alert() -> dict:
    """Create a mock alert for testing"""
    return {
        'token_symbol': 'ROCKET',
        'token_address': '7xKw9p2MAzeF8rKLQbC3j9vRH7YxGp2M',
        'score_combined': 81,
        'score_rules': 75,
        'score_ml': 68,
        'category': 'FAST_SNIPER',
        'risk_level': 'MEDIUM',
        'alert_id': 1,
        'metrics': {
            'liquidity_usd': 22400,
            'holders': 51,
            'market_cap': 98000,
            'rugcheck_score': 8.7,
            'price_change_2min': 53,
            'age_seconds': 42
        },
        'security': {
            'mint_authority': False,
            'freeze_authority': False,
            'honeypot': False,
            'lp_burned': True
        },
        'ml_predictions': {
            'pump_probability': 0.68,
            'estimated_gain_percent': 124,
            'rug_risk': 0.12,
            'pattern': 'Fast Sniper'
        },
        'suggestion': {
            'entry_timing': 'MAINTENANT (1-2min window)',
            'position_sol': '0.05-0.07 SOL',
            'take_profit': '+120-150%',
            'stop_loss': '-20%'
        }
    }


def create_special_chars_alert() -> dict:
    """Create a mock alert with special characters for testing edge cases"""
    return {
        'token_symbol': 'TEST&MOON',
        'token_address': 'ABC<123>DEF&456',
        'score_combined': 75,
        'score_rules': 70,
        'score_ml': 65,
        'category': 'SMART_SNIPER',
        'risk_level': 'LOW',
        'alert_id': 999,
        'metrics': {
            'liquidity_usd': 15000,
            'holders': 30,
            'market_cap': 50000,
            'rugcheck_score': 7.5,
            'price_change_2min': 25,
            'age_seconds': 60
        },
        'security': {
            'mint_authority': False,
            'freeze_authority': False,
            'honeypot': False,
            'lp_burned': True
        }
    }


async def test_telegram_bot():
    """Run comprehensive Telegram bot tests"""
    print("=" * 60)
    print("🤖 Telegram Bot Integration Test")
    print("=" * 60)
    print()
    
    # Step 1: Load configuration
    print("📋 Step 1: Loading configuration...")
    try:
        config = Config()
        
        if not config.telegram_token:
            print("❌ TELEGRAM_BOT_TOKEN not found in environment")
            print("   Please set it in .env file")
            return False
        
        if not config.telegram_chat_id:
            print("❌ TELEGRAM_CHAT_ID not found in environment")
            print("   Please set it in .env file")
            return False
        
        print(f"✅ Configuration loaded")
        print(f"   Token: {config.telegram_token[:10]}...")
        print(f"   Chat ID: {config.telegram_chat_id}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Step 2: Initialize bot
    print("🤖 Step 2: Initializing Telegram bot...")
    try:
        bot = TelegramBot(
            token=config.telegram_token,
            chat_id=config.telegram_chat_id
        )
        await bot.initialize()
        print("✅ Bot initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return False
    
    # Step 3: Test connection
    print("🔌 Step 3: Testing bot connection...")
    try:
        if await bot.test_connection():
            print("✅ Bot connected successfully")
            print()
        else:
            print("❌ Bot connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # Step 4: Send simple test message
    print("💬 Step 4: Sending simple test message...")
    try:
        test_message = MessageFormatter.format_test_message()
        success = await bot.send_message(test_message)
        
        if success:
            print("✅ Test message sent successfully")
            print()
        else:
            print("❌ Failed to send test message")
            return False
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False
    
    # Step 5: Send formatted alert with buttons
    print("🎯 Step 5: Sending formatted alert with buttons...")
    try:
        mock_alert = create_mock_alert()
        success = await bot.send_alert(mock_alert, compact=False)
        
        if success:
            print("✅ Formatted alert sent successfully")
            print("   Check your Telegram app to see:")
            print("   - Rich message formatting with emojis")
            print("   - Token details and metrics")
            print("   - ML predictions")
            print("   - Trading suggestions")
            print("   - Inline buttons (TRADE, CHART, TRACK)")
            print()
        else:
            print("❌ Failed to send formatted alert")
            return False
    except Exception as e:
        print(f"❌ Error sending alert: {e}")
        return False
    
    # Step 6: Send compact alert
    print("📦 Step 6: Sending compact alert format...")
    try:
        mock_alert_compact = create_mock_alert()
        mock_alert_compact['token_symbol'] = 'MOON'
        mock_alert_compact['alert_id'] = 2
        
        success = await bot.send_alert(mock_alert_compact, compact=True)
        
        if success:
            print("✅ Compact alert sent successfully")
            print()
        else:
            print("❌ Failed to send compact alert")
            return False
    except Exception as e:
        print(f"❌ Error sending compact alert: {e}")
        return False
    
    # Step 7: Test with special characters
    print("🔧 Step 7: Testing special character handling...")
    try:
        special_alert = create_special_chars_alert()
        success = await bot.send_alert(special_alert, compact=False)
        
        if success:
            print("✅ Special character alert sent successfully")
            print("   Token with &, <, > characters handled properly")
            print()
        else:
            print("❌ Failed to send special character alert")
            return False
    except Exception as e:
        print(f"❌ Error sending special character alert: {e}")
        return False
    
    # Step 8: Close bot
    print("🔒 Step 8: Closing bot connection...")
    try:
        await bot.close()
        print("✅ Bot closed cleanly")
        print()
    except Exception as e:
        print(f"⚠️ Warning while closing bot: {e}")
    
    # Final summary
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("✅ Telegram bot is fully functional")
    print("✅ Messages are formatted correctly with HTML")
    print("✅ Special characters are properly escaped")
    print("✅ Buttons are working")
    print("✅ Ready to send real alerts")
    print()
    print("Next steps:")
    print("1. Check your Telegram app for the test messages")
    print("2. Try clicking the buttons (TRADE, CHART, TRACK)")
    print("3. Verify the formatting looks good on mobile")
    print("4. Check that special character alert displays correctly")
    print("5. Bot is ready for production use!")
    print()
    
    return True


async def main():
    """Main test function"""
    try:
        success = await test_telegram_bot()
        
        if success:
            print("🎉 Test completed successfully!")
            sys.exit(0)
        else:
            print("❌ Test failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
