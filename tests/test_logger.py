"""
Test logger with emoji support
"""

import logging
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger


def test_logger_basic():
    """Test basic logger functionality"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logger("test_basic", log_file=str(log_file))
        
        # Test basic logging
        logger.info("Test message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Verify log file was created
        assert log_file.exists()
        
        # Verify content
        content = log_file.read_text(encoding='utf-8')
        assert "Test message" in content
        assert "Warning message" in content
        assert "Error message" in content


def test_logger_with_emojis():
    """Test logger with emoji characters"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_emoji.log"
        logger = setup_logger("test_emoji", log_file=str(log_file))
        
        # Test emoji logging (should not crash)
        try:
            logger.info("✅ Configuration loaded")
            logger.info("🚀 Bot is starting...")
            logger.info("🤖 Bot is running!")
            logger.info("🔍 Scanning for new tokens...")
            logger.info("📊 Status update")
            logger.info("⏸️ Waiting...")
            logger.info("🚨 Alert!")
            logger.info("✨ Success!")
            success = True
        except UnicodeEncodeError:
            success = False
        
        assert success, "Logger should handle emojis without crashing"
        
        # Verify file contains emojis
        assert log_file.exists()
        content = log_file.read_text(encoding='utf-8')
        
        # Check that at least some messages made it to the file
        assert "Configuration loaded" in content
        assert "Bot is starting" in content


def test_logger_no_file():
    """Test logger without file output"""
    logger = setup_logger("test_no_file", log_file=None)
    
    # Should work without file
    try:
        logger.info("✅ Test without file")
        logger.info("🚀 This should work")
        success = True
    except Exception:
        success = False
    
    assert success, "Logger should work without file handler"


def test_logger_windows_encoding():
    """Test logger handles Windows encoding properly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_windows.log"
        
        # Test setup (should not crash on any platform)
        try:
            logger = setup_logger("test_windows", log_file=str(log_file))
            
            # Test various emojis that commonly cause issues on Windows
            emojis = [
                "✅",  # Check mark
                "🚀",  # Rocket
                "🤖",  # Robot
                "🔍",  # Magnifying glass
                "📊",  # Chart
                "⏸️",  # Pause
                "🚨",  # Siren
                "✨",  # Sparkles
                "⏳",  # Hourglass
                "👋",  # Wave
                "❌",  # Cross mark
            ]
            
            for emoji in emojis:
                logger.info(f"{emoji} Testing emoji")
            
            success = True
        except UnicodeEncodeError:
            success = False
        
        assert success, "Logger should handle all emojis without UnicodeEncodeError"


def test_multiple_logger_setup():
    """Test that calling setup_logger multiple times doesn't cause issues"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file1 = Path(tmpdir) / "test1.log"
        log_file2 = Path(tmpdir) / "test2.log"
        
        # Setup logger multiple times
        logger1 = setup_logger("test_multi_1", log_file=str(log_file1))
        logger2 = setup_logger("test_multi_2", log_file=str(log_file2))
        
        # Both should work without issues
        try:
            logger1.info("✅ First logger with emoji")
            logger2.info("🚀 Second logger with emoji")
            success = True
        except Exception:
            success = False
        
        assert success, "Multiple logger setups should work correctly"


if __name__ == "__main__":
    print("Running logger tests...")
    
    print("\n1. Testing basic logger...")
    test_logger_basic()
    print("✅ Basic logger test passed")
    
    print("\n2. Testing logger with emojis...")
    test_logger_with_emojis()
    print("✅ Emoji logger test passed")
    
    print("\n3. Testing logger without file...")
    test_logger_no_file()
    print("✅ No-file logger test passed")
    
    print("\n4. Testing Windows encoding...")
    test_logger_windows_encoding()
    print("✅ Windows encoding test passed")
    
    print("\n5. Testing multiple logger setups...")
    test_multiple_logger_setup()
    print("✅ Multiple logger setup test passed")
    
    print("\n✅ All tests passed!")
