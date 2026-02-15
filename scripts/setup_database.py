#!/usr/bin/env python3
"""
Database Setup Script
Creates database schema and prepares for pre-trained models
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger

def main():
    """Setup database and initial data"""
    logger = setup_logger()
    
    print("\n🔧 Solana ML Scanner - Database Setup")
    print("=" * 50)
    
    # Create necessary directories
    print("\n[1/5] Creating directories...")
    directories = ['data', 'models', 'logs']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ {dir_name}/ created")
    
    # Create database
    print("\n[2/5] Creating database...")
    db = DatabaseManager()
    print("✅ Database created: data/scanner.db")
    
    print("\n[3/5] Creating tables...")
    db.create_tables()
    print("✅ Tables created successfully")
    
    print("\n[4/5] Pre-trained models...")
    print("ℹ️  Models will be downloaded when you run download_pretrained_models.py")
    print("ℹ️  Or the bot will train its own models from scratch")
    
    print("\n[5/5] Configuration...")
    print("✅ Configuration templates ready")
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\n📚 Next steps:")
    print("1. Copy .env.example to .env and add your API keys")
    print("2. Copy config.yaml.example to config.yaml")
    print("3. (Optional) Run: python scripts/download_pretrained_models.py")
    print("4. Run: python main.py")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
