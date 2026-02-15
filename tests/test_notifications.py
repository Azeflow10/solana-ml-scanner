"""Tests for notification modules"""

import pytest
from src.notifications.formatter import MessageFormatter


def test_format_number():
    """Test number formatting with K, M, B suffixes"""
    assert MessageFormatter.format_number(500) == "$500.00"
    assert MessageFormatter.format_number(1500) == "$1.50K"
    assert MessageFormatter.format_number(1500000) == "$1.50M"
    assert MessageFormatter.format_number(1500000000) == "$1.50B"


def test_format_percentage():
    """Test percentage formatting"""
    assert MessageFormatter.format_percentage(45.5) == "+45.5%"
    assert MessageFormatter.format_percentage(-20.3) == "-20.3%"
    assert MessageFormatter.format_percentage(0) == "0.0%"  # Zero has no sign
    assert MessageFormatter.format_percentage(45.5, show_sign=False) == "45.5%"


def test_truncate_address():
    """Test blockchain address truncation"""
    address = "7xKw9p2MAzeF8rKLQbC3j9vRH7YxGp2M"
    truncated = MessageFormatter.truncate_address(address, 5, 3)
    assert truncated == "7xKw9...p2M"
    
    short_address = "ABC123"
    assert MessageFormatter.truncate_address(short_address, 5, 3) == "ABC123"


def test_format_time_ago():
    """Test time ago formatting"""
    assert "42 secondes" in MessageFormatter.format_time_ago(42)
    assert "5 minutes" in MessageFormatter.format_time_ago(300)
    assert "2 heures" in MessageFormatter.format_time_ago(7200)


def test_format_telegram_alert_detailed():
    """Test detailed alert formatting"""
    alert_data = {
        'token_symbol': 'TEST',
        'token_address': '7xKw9p2MAzeF8rKLQbC3j9vRH7YxGp2M',
        'score_combined': 85,
        'score_ml': 70,
        'category': 'FAST_SNIPER',
        'risk_level': 'LOW',
        'alert_id': 1,
        'metrics': {
            'liquidity_usd': 25000,
            'holders': 60,
            'market_cap': 100000,
            'rugcheck_score': 9.0,
        },
        'security': {
            'mint_authority': False,
            'freeze_authority': False,
            'honeypot': False,
            'lp_burned': True
        }
    }
    
    message = MessageFormatter.format_telegram_alert(alert_data, compact=False)
    
    # Check that key elements are in the message
    assert "SNIPER ALERT" in message
    assert "$TEST" in message
    assert "85/100" in message
    assert "70%" in message
    assert "FAST_SNIPER" in message
    assert "LOW" in message
    assert "🟢" in message  # LOW risk emoji


def test_format_telegram_alert_compact():
    """Test compact alert formatting"""
    alert_data = {
        'token_symbol': 'MOON',
        'token_address': 'ABC123DEF456GHI789',
        'score_combined': 90,
        'category': 'SMART_SNIPER',
        'risk_level': 'MEDIUM',
        'metrics': {
            'liquidity_usd': 50000,
            'holders': 100
        }
    }
    
    message = MessageFormatter.format_telegram_alert(alert_data, compact=True)
    
    # Check that key elements are in the compact message
    assert "$MOON" in message
    assert "90/100" in message
    assert "MEDIUM" in message
    assert "🟡" in message  # MEDIUM risk emoji
    assert "🎯" in message  # SMART_SNIPER emoji


def test_format_test_message():
    """Test message formatting"""
    message = MessageFormatter.format_test_message()
    
    assert "Test Message" in message
    assert "✅" in message
    assert "Timestamp:" in message


def test_category_emojis():
    """Test category emoji mappings"""
    assert MessageFormatter.CATEGORY_EMOJIS['FAST_SNIPER'] == '⚡️'
    assert MessageFormatter.CATEGORY_EMOJIS['SMART_SNIPER'] == '🎯'
    assert MessageFormatter.CATEGORY_EMOJIS['MOMENTUM'] == '📈'
    assert MessageFormatter.CATEGORY_EMOJIS['SAFE'] == '🛡️'


def test_risk_emojis():
    """Test risk level emoji mappings"""
    assert MessageFormatter.RISK_EMOJIS['LOW'] == '🟢'
    assert MessageFormatter.RISK_EMOJIS['MEDIUM'] == '🟡'
    assert MessageFormatter.RISK_EMOJIS['HIGH'] == '🔴'
    assert MessageFormatter.RISK_EMOJIS['CRITICAL'] == '🔴⚠️'
