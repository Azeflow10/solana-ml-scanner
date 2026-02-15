"""
Core Orchestrator - Coordinates all bot components
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.logger import get_logger, setup_logger
from src.core.config import Config
from src.database.db_manager import DatabaseManager
from src.ml.inference.predictor import MLPredictor
from src.notifications.notification_manager import NotificationManager

from src.scanners.pumpfun_scanner import PumpFunScanner
from src.scanners.dexscreener_scanner import DexScreenerScanner
from src.analyzers.rugcheck_analyzer import RugCheckAnalyzer
from src.analyzers.liquidity_analyzer import LiquidityAnalyzer
from src.analyzers.holder_analyzer import HolderAnalyzer
from src.scoring.scoring_engine import ScoringEngine
from src.pattern_detection.pattern_detector import PatternDetector

from src.models.token_data import TokenData, AnalysisResult


class Orchestrator:
    """Main orchestrator for the scanner bot"""
    
    def __init__(self):
        """Initialize orchestrator"""
        logger = get_logger(__name__)
        logger.info("Initializing Orchestrator...")
        
        # Load configuration
        self.config = Config()
        logger.info("✅ Configuration loaded")
        
        # Initialize database
        self.db = DatabaseManager(self.config.database_url)
        logger.info("✅ Database connected")
        
        # Initialize ML predictor
        self.ml_predictor = MLPredictor()
        logger.info("✅ ML models loaded")
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(self.config)
        logger.info("✅ Notification manager ready")
        
        # Initialize scanners
        scanner_config = self._get_scanner_config()
        self.pumpfun_scanner = PumpFunScanner(scanner_config)
        self.dexscreener_scanner = DexScreenerScanner(scanner_config)
        logger.info("✅ Scanners initialized")
        
        # Initialize analyzers
        analyzer_config = self._get_analyzer_config()
        self.rugcheck_analyzer = RugCheckAnalyzer(analyzer_config)
        self.liquidity_analyzer = LiquidityAnalyzer(analyzer_config)
        self.holder_analyzer = HolderAnalyzer(analyzer_config)
        logger.info("✅ Analyzers initialized")
        
        # Initialize scoring and pattern detection
        scoring_config = self._get_scoring_config()
        self.scoring_engine = ScoringEngine(scoring_config)
        self.pattern_detector = PatternDetector()
        logger.info("✅ Scoring engine and pattern detector ready")
        
        # Alert tracking
        self.alerts_sent_today = 0
        self.last_alert_reset = datetime.utcnow()
        self.max_alerts_per_day = self.config.get_nested('alerts', 'max_alerts_per_day', 15)
        self.min_alert_score = self.config.get_nested('alerts', 'min_score', 70)
        
        logger.info("Orchestrator initialization complete!")
    
    def _get_scanner_config(self) -> Dict[str, Any]:
        """Get scanner configuration with professional settings"""
        return {
            'liquidity_min': 10000,  # $10k
            'liquidity_max': 300000,  # $300k
            'age_max_seconds': 300,  # 5 minutes
            'holders_min': 15,
            'market_cap_max': 500000,  # $500k
            'poll_interval': 10,
            'websocket_url': self.config.get_nested('scanners', 'pumpfun', 'websocket_url', 'wss://api.helius.xyz')
        }
    
    def _get_analyzer_config(self) -> Dict[str, Any]:
        """Get analyzer configuration"""
        return {
            'timeout': 10,
            'max_retries': 3
        }
    
    def _get_scoring_config(self) -> Dict[str, Any]:
        """Get scoring configuration"""
        return {
            'ml_weight': self.config.get_nested('machine_learning', 'ml_weight', 0.40),
            'rule_weight': self.config.get_nested('machine_learning', 'rule_weight', 0.60)
        }
    
    async def start(self):
        """Start the bot"""
        logger = get_logger(__name__)
        logger.info("🚀 Bot is starting...")
        
        # Set up callbacks for scanners
        self.pumpfun_scanner.set_callback(self.process_token)
        self.dexscreener_scanner.set_callback(self.process_token)
        
        # Start all scanners
        scanner_tasks = []
        
        if self.config.get_nested('scanners', 'pumpfun', 'enabled', True):
            scanner_tasks.append(asyncio.create_task(self.pumpfun_scanner.start()))
            logger.info("✅ Pump.fun scanner started")
        
        if self.config.get_nested('scanners', 'dexscreener', 'enabled', True):
            scanner_tasks.append(asyncio.create_task(self.dexscreener_scanner.start()))
            logger.info("✅ DexScreener scanner started")
        
        logger.info("🤖 Bot is running! Waiting for opportunities...")
        
        # Keep running
        try:
            # Wait for all scanner tasks
            await asyncio.gather(*scanner_tasks)
        except asyncio.CancelledError:
            logger.info("Bot shutdown requested")
            await self.shutdown()
    
    async def process_token(self, token_data: TokenData):
        """
        Full analysis pipeline for detected token
        
        Pipeline:
        1. Pre-filter (already done by scanner)
        2. Run all analyzers in parallel
        3. Calculate scores
        4. Detect patterns
        5. If score >= threshold: send alert
        """
        
        logger = get_logger(__name__)
        start_time = time.time()
        
        logger.info(f"Processing token: {token_data.symbol} ({token_data.address})")
        
        try:
            # Run all analyzers in parallel
            analyzer_results = await self._run_analyzers(token_data.address, token_data.to_dict())
            
            # Calculate ML score if available
            ml_score = 0.0
            ml_confidence = 0.0
            
            try:
                if self.config.get_nested('machine_learning', 'enabled', True):
                    ml_result = await self._get_ml_score(token_data, analyzer_results)
                    ml_score = ml_result.get('score', 0.0)
                    ml_confidence = ml_result.get('confidence', 0.0)
            except Exception as e:
                logger.warning(f"ML scoring failed: {e}")
            
            # Calculate comprehensive scores
            scoring_result = self.scoring_engine.calculate_score(
                token=token_data,
                rugcheck=analyzer_results.get('rugcheck'),
                liquidity=analyzer_results.get('liquidity'),
                holders=analyzer_results.get('holders'),
                ml_score=ml_score,
                ml_confidence=ml_confidence
            )
            
            # Detect pattern
            pattern = self.pattern_detector.detect_pattern(
                token=token_data,
                rugcheck=analyzer_results.get('rugcheck'),
                liquidity=analyzer_results.get('liquidity'),
                holders=analyzer_results.get('holders')
            )
            
            # Update scoring result with detected pattern
            scoring_result.pattern = pattern
            scoring_result.risk_level = self.pattern_detector.get_risk_level(
                pattern,
                analyzer_results.get('rugcheck')
            )
            
            # Create analysis result
            analysis_duration_ms = (time.time() - start_time) * 1000
            
            analysis = AnalysisResult(
                token=token_data,
                rugcheck=analyzer_results.get('rugcheck'),
                liquidity=analyzer_results.get('liquidity'),
                holders=analyzer_results.get('holders'),
                scoring=scoring_result,
                analysis_duration_ms=analysis_duration_ms
            )
            
            logger.info(
                f"Analysis complete: {token_data.symbol} | "
                f"Score: {scoring_result.score_combined:.1f} | "
                f"Pattern: {pattern} | "
                f"Risk: {scoring_result.risk_level} | "
                f"Time: {analysis_duration_ms:.0f}ms"
            )
            
            # Save to database
            try:
                await self._save_analysis(analysis)
            except Exception as e:
                logger.error(f"Failed to save analysis: {e}")
            
            # Check if should alert
            if self._should_alert(scoring_result):
                await self._send_alert(analysis)
            else:
                logger.info(f"Token does not meet alert threshold: {scoring_result.score_combined:.1f} < {self.min_alert_score}")
            
        except Exception as e:
            logger.error(f"Error processing token {token_data.address}: {e}", exc_info=True)
    
    async def _run_analyzers(
        self,
        token_address: str,
        token_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run all analyzers in parallel"""
        
        logger = get_logger(__name__)
        logger.debug(f"Running analyzers for {token_address}")
        
        # Run analyzers in parallel
        results = await asyncio.gather(
            self.rugcheck_analyzer.analyze(token_address),
            self.liquidity_analyzer.analyze(token_address, token_data),
            self.holder_analyzer.analyze(token_address, token_data),
            return_exceptions=True
        )
        
        # Unpack results
        rugcheck_result = results[0] if not isinstance(results[0], Exception) else None
        liquidity_result = results[1] if not isinstance(results[1], Exception) else None
        holder_result = results[2] if not isinstance(results[2], Exception) else None
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                analyzer_name = ['RugCheck', 'Liquidity', 'Holder'][i]
                logger.error(f"{analyzer_name} analyzer failed: {result}")
        
        return {
            'rugcheck': rugcheck_result,
            'liquidity': liquidity_result,
            'holders': holder_result
        }
    
    async def _get_ml_score(
        self,
        token_data: TokenData,
        analyzer_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Get ML prediction score"""
        
        try:
            # Build feature vector
            features = self._build_feature_vector(token_data, analyzer_results)
            
            # Get prediction
            prediction = await asyncio.get_event_loop().run_in_executor(
                None,
                self.ml_predictor.predict,
                features
            )
            
            return {
                'score': prediction.get('score', 0.0) * 100,
                'confidence': prediction.get('confidence', 0.0)
            }
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.warning(f"ML prediction failed: {e}")
            return {'score': 0.0, 'confidence': 0.0}
    
    def _build_feature_vector(
        self,
        token_data: TokenData,
        analyzer_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Build feature vector for ML model"""
        
        features = {
            'liquidity_usd': token_data.liquidity_usd,
            'market_cap': token_data.market_cap,
            'holders': token_data.holders,
            'age_seconds': token_data.age_seconds,
            'price_change_5min': token_data.price_change_5min,
            'volume_24h': token_data.volume_24h
        }
        
        if analyzer_results.get('rugcheck'):
            features['rugcheck_score'] = analyzer_results['rugcheck'].overall_score
            features['top_10_concentration'] = analyzer_results['rugcheck'].top_10_holders_percent
        
        if analyzer_results.get('liquidity'):
            features['liquidity_stability'] = analyzer_results['liquidity'].liquidity_stability_score
        
        if analyzer_results.get('holders'):
            features['distribution_score'] = analyzer_results['holders'].distribution_score
        
        return features
    
    def _should_alert(self, scoring_result: ScoringResult) -> bool:
        """Determine if token qualifies for alert"""
        
        # Check daily limit
        self._reset_alert_counter_if_needed()
        
        if self.alerts_sent_today >= self.max_alerts_per_day:
            logger = get_logger(__name__)
            logger.info(f"Daily alert limit reached ({self.max_alerts_per_day})")
            return False
        
        # Check score threshold
        if scoring_result.score_combined < self.min_alert_score:
            return False
        
        # Check ML confidence if ML is used
        min_ml_confidence = self.config.get_nested('alerts', 'min_ml_confidence', 0.65)
        if scoring_result.ml_confidence > 0 and scoring_result.ml_confidence < min_ml_confidence:
            return False
        
        # Check category filters
        category_filters = self.config.get_nested('alerts', 'categories', {})
        if category_filters:
            category_enabled = category_filters.get(
                scoring_result.category.lower().replace('_', '_'),
                True
            )
            if not category_enabled:
                return False
        
        return True
    
    def _reset_alert_counter_if_needed(self):
        """Reset alert counter if new day"""
        current_date = datetime.utcnow().date()
        last_reset_date = self.last_alert_reset.date()
        
        if current_date > last_reset_date:
            self.alerts_sent_today = 0
            self.last_alert_reset = datetime.utcnow()
    
    async def _send_alert(self, analysis: AnalysisResult):
        """Send alert for qualified token"""
        
        logger = get_logger(__name__)
        
        try:
            await self.notification_manager.send_alert(analysis.to_dict())
            
            self.alerts_sent_today += 1
            
            logger.info(
                f"🚨 ALERT SENT: {analysis.token.symbol} | "
                f"Score: {analysis.scoring.score_combined:.1f} | "
                f"Pattern: {analysis.scoring.pattern} | "
                f"Alerts today: {self.alerts_sent_today}/{self.max_alerts_per_day}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _save_analysis(self, analysis: AnalysisResult):
        """Save analysis result to database"""
        
        try:
            # Convert to dict and save
            analysis_dict = analysis.to_dict()
            
            # Save to database
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.db.save_analysis,
                analysis_dict
            )
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to save analysis: {e}")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger = get_logger(__name__)
        logger.info("Shutting down gracefully...")
        
        # Stop scanners
        try:
            await self.pumpfun_scanner.stop()
        except Exception:
            pass
        
        try:
            await self.dexscreener_scanner.stop()
        except Exception:
            pass
        
        logger.info("✅ Shutdown complete")
