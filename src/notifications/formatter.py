"""
Message Formatter for notifications
Formats alerts into rich, readable messages for different channels

Note: French language strings are used intentionally as per project requirements.
The target audience is French-speaking traders. To make this configurable,
consider implementing a localization system in future versions.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class MessageFormatter:
    """Formats alert data into readable messages"""
    
    # Emoji mappings for various elements
    RISK_EMOJIS = {
        'LOW': '🟢',
        'MEDIUM': '🟡',
        'HIGH': '🔴',
        'CRITICAL': '🔴⚠️'
    }
    
    CATEGORY_EMOJIS = {
        'FAST_SNIPER': '⚡️',
        'SMART_SNIPER': '🎯',
        'MOMENTUM': '📈',
        'SAFE': '🛡️'
    }
    
    @staticmethod
    def format_number(value: float, decimals: int = 2) -> str:
        """Format number with K, M, B suffixes"""
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.{decimals}f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.{decimals}f}M"
        elif value >= 1_000:
            return f"${value/1_000:.{decimals}f}K"
        else:
            return f"${value:.{decimals}f}"
    
    @staticmethod
    def format_time_ago(seconds: int) -> str:
        """Format time ago in human readable format"""
        if seconds < 60:
            return f"il y a {seconds} secondes"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            hours = seconds // 3600
            return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    
    @staticmethod
    def format_percentage(value: float, show_sign: bool = True) -> str:
        """
        Format percentage with sign
        
        Args:
            value: Percentage value
            show_sign: If True, adds '+' for positive values (negative values always show '-')
        """
        sign = '+' if value > 0 and show_sign else ''
        return f"{sign}{value:.1f}%"
    
    @staticmethod
    def truncate_address(address: str, start: int = 5, end: int = 3) -> str:
        """Truncate blockchain address for display"""
        if len(address) <= start + end:
            return address
        return f"{address[:start]}...{address[-end:]}"
    
    @classmethod
    def format_telegram_alert(cls, alert_data: Dict[str, Any], compact: bool = False) -> str:
        """
        Format alert data into rich Telegram message
        
        Args:
            alert_data: Alert data dictionary
            compact: If True, returns compact format
            
        Returns:
            Formatted message string
        """
        if compact:
            return cls._format_compact_alert(alert_data)
        return cls._format_detailed_alert(alert_data)
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape special HTML characters for Telegram HTML parse mode"""
        text = str(text)
        # Important: Escape & first to avoid double-escaping
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
    
    @classmethod
    def _format_detailed_alert(cls, data: Dict[str, Any]) -> str:
        """Format detailed alert message using HTML"""
        # Extract data with defaults
        token_symbol = data.get('token_symbol', 'UNKNOWN')
        token_address = data.get('token_address', '')
        score_combined = data.get('score_combined', 0)
        score_ml = data.get('score_ml', 0)
        category = data.get('category', 'UNKNOWN')
        risk_level = data.get('risk_level', 'UNKNOWN')
        
        metrics = data.get('metrics', {})
        security = data.get('security', {})
        ml_predictions = data.get('ml_predictions', {})
        suggestion = data.get('suggestion', {})
        
        # Get emojis
        category_emoji = cls.CATEGORY_EMOJIS.get(category, '🎯')
        risk_emoji = cls.RISK_EMOJIS.get(risk_level, '⚪️')
        
        # Escape any user-provided text (token symbols and addresses)
        token_symbol_safe = cls.escape_html(token_symbol)
        token_address_safe = cls.escape_html(token_address)
        
        # Build message using HTML formatting
        lines = []
        
        # Header
        lines.append(f"🎯 <b>SNIPER ALERT</b> - Score: {score_combined}/100")
        lines.append(f"🤖 ML Confidence: {score_ml}%")
        lines.append("")
        
        # Token info
        lines.append(f"🪙 Token: <b>${token_symbol_safe}</b>")
        lines.append(f"📍 CA: <code>{token_address_safe}</code>")
        
        # Age
        age_seconds = metrics.get('age_seconds', 0)
        if age_seconds:
            lines.append(f"⏰ Lancé: {cls.format_time_ago(age_seconds)}")
        lines.append("")
        
        # Metrics
        lines.append("📊 <b>Métriques:</b>")
        liquidity = metrics.get('liquidity_usd', 0)
        holders = metrics.get('holders', 0)
        market_cap = metrics.get('market_cap', 0)
        rugcheck_score = metrics.get('rugcheck_score', 0)
        
        lines.append(f"├─ Liquidité: {cls.format_number(liquidity)}")
        lines.append(f"├─ Holders: {holders}")
        lines.append(f"├─ MC: {cls.format_number(market_cap, 0)}")
        lines.append(f"└─ RugCheck: {rugcheck_score:.1f}/10")
        lines.append("")
        
        # Security
        lines.append("✅ <b>Sécurité:</b>")
        mint_auth = security.get('mint_authority', True)
        freeze_auth = security.get('freeze_authority', True)
        honeypot = security.get('honeypot', True)
        lp_burned = security.get('lp_burned', False)
        
        lines.append(f"├─ {'✅' if not mint_auth else '❌'} {'Pas mint authority' if not mint_auth else 'Mint authority présente'}")
        lines.append(f"├─ {'✅' if not freeze_auth else '❌'} {'Pas freeze authority' if not freeze_auth else 'Freeze authority présente'}")
        lines.append(f"├─ {'✅' if not honeypot else '❌'} Honeypot: {'Safe' if not honeypot else 'DANGER'}")
        lines.append(f"└─ {'✅' if lp_burned else '❌'} LP {'burned' if lp_burned else 'NOT burned'}")
        lines.append("")
        
        # Momentum
        price_change = metrics.get('price_change_2min', 0)
        if price_change != 0:
            lines.append(f"📈 Momentum: {cls.format_percentage(price_change)} (2min)")
            lines.append("")
        
        # ML Analysis
        if ml_predictions:
            lines.append("🤖 <b>ML ANALYSIS:</b>")
            pump_prob = ml_predictions.get('pump_probability', 0)
            estimated_gain = ml_predictions.get('estimated_gain_percent', 0)
            rug_risk = ml_predictions.get('rug_risk', 0)
            pattern = ml_predictions.get('pattern', 'Unknown')
            
            lines.append(f"├─ Pump probability: {int(pump_prob * 100)}%")
            lines.append(f"├─ Estimated gain: {cls.format_percentage(estimated_gain)}")
            
            rug_risk_pct = int(rug_risk * 100)
            rug_level = 'LOW' if rug_risk < 0.3 else 'MEDIUM' if rug_risk < 0.6 else 'HIGH'
            lines.append(f"├─ Rug risk: {rug_risk_pct}% ({rug_level})")
            lines.append(f"└─ Pattern: {pattern}")
            lines.append("")
        
        # Suggestion
        if suggestion:
            lines.append("🎯 <b>SUGGESTION:</b>")
            entry_timing = cls.escape_html(suggestion.get('entry_timing', 'N/A'))
            position_sol = cls.escape_html(suggestion.get('position_sol', 'N/A'))
            take_profit = cls.escape_html(suggestion.get('take_profit', 'N/A'))
            stop_loss = cls.escape_html(suggestion.get('stop_loss', 'N/A'))
            
            lines.append(f"Entry: {entry_timing}")
            lines.append(f"Position: {position_sol}")
            lines.append(f"TP: {take_profit} | SL: {stop_loss}")
            lines.append("")
        
        # Footer
        alert_id = data.get('alert_id', 1)
        lines.append(f"{category_emoji} {category} • Risk: {risk_level} {risk_emoji}")
        lines.append(f"Alert #{alert_id}")
        
        return "\n".join(lines)
    
    @classmethod
    def _format_compact_alert(cls, data: Dict[str, Any]) -> str:
        """Format compact alert message using HTML"""
        token_symbol = data.get('token_symbol', 'UNKNOWN')
        token_address = data.get('token_address', '')
        score_combined = data.get('score_combined', 0)
        category = data.get('category', 'UNKNOWN')
        risk_level = data.get('risk_level', 'UNKNOWN')
        
        metrics = data.get('metrics', {})
        
        category_emoji = cls.CATEGORY_EMOJIS.get(category, '🎯')
        risk_emoji = cls.RISK_EMOJIS.get(risk_level, '⚪️')
        
        # Escape user-provided content
        token_symbol_safe = cls.escape_html(token_symbol)
        token_address_safe = cls.escape_html(token_address)
        
        liquidity = cls.format_number(metrics.get('liquidity_usd', 0))
        holders = metrics.get('holders', 0)
        
        lines = [
            f"{category_emoji} <b>${token_symbol_safe}</b> - Score: {score_combined}/100",
            f"📍 <code>{cls.truncate_address(token_address_safe, 6, 4)}</code>",
            f"💰 Liq: {liquidity} | 👥 {holders} holders",
            f"Risk: {risk_level} {risk_emoji}"
        ]
        
        return "\n".join(lines)
    
    @classmethod
    def format_test_message(cls) -> str:
        """Generate a test message using HTML formatting"""
        return (
            "🤖 <b>Test Message from Solana ML Scanner</b>\n"
            "\n"
            "✅ Bot is connected and working!\n"
            "✅ Message formatting works\n"
            "✅ Ready to send alerts\n"
            "\n"
            f"⏰ Timestamp: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
