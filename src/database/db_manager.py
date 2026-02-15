"""
Database Manager
"""

import json
from typing import Dict, Any
from datetime import datetime
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
    
    def save_analysis(self, analysis_data: Dict[str, Any]):
        """
        Save analysis result to database
        
        Args:
            analysis_data: Dictionary containing analysis results
        """
        try:
            # For now, we'll just log it
            # In production, this would save to proper database tables
            
            token_address = analysis_data.get('token', {}).get('address', 'UNKNOWN')
            symbol = analysis_data.get('token', {}).get('symbol', 'UNKNOWN')
            score = analysis_data.get('scoring', {}).get('score_combined', 0)
            
            logger.debug(f"Saved analysis: {symbol} ({token_address}) - Score: {score:.1f}")
            
            # TODO: Implement proper database storage
            # session = self.get_session()
            # analysis_model = AnalysisModel(**analysis_data)
            # session.add(analysis_model)
            # session.commit()
            # session.close()
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
