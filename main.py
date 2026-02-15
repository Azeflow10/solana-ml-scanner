#!/usr/bin/env python3
"""
Solana ML Scanner - Main Entry Point
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.orchestrator import Orchestrator
from src.utils.logger import setup_logger

def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║     🚀 SOLANA ML SCANNER v1.0                ║
    ║     Smart Memecoin Opportunity Detection      ║
    ╚═══════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Main function"""
    print_banner()
    
    # Setup logger
    logger = setup_logger()
    logger.info("Starting Solana ML Scanner...")
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Start bot
        await orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
