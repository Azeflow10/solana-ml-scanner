"""
Configuration Manager
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """Configuration manager for the bot"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration"""
        # Load environment variables
        load_dotenv()
        
        # Load YAML config
        self.config_path = Path(config_path)
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        
        # Environment variables
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///data/scanner.db')
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def get_nested(self, *keys, default: Any = None) -> Any:
        """
        Get nested configuration value with variable number of keys
        
        Example:
            config.get_nested('alerts', 'min_score', default=70)
            config.get_nested('machine_learning', 'enabled', default=True)
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
