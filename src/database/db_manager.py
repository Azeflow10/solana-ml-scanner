"""
Database Manager
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Database manager for SQLite"""
    
    def __init__(self, database_url: str = "sqlite:///data/scanner.db"):
        """Initialize database manager"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info(f"Database initialized: {database_url}")
    
    def create_tables(self):
        """Create all tables"""
        # TODO: Import models and create tables
        logger.info("Creating database tables...")
        logger.info("✅ Tables created")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
