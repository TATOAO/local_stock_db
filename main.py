#!/usr/bin/env python3
"""
A-Share Stock Monitoring System
A local database system for monitoring Chinese A-share stocks with real-time price updates,
alerts, and web dashboard.

Author: AI Assistant
Date: 2024
"""

import sys
import os
import signal
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database.models import DatabaseManager
from data_fetcher.akshare_client import AKShareClient
from data_fetcher.scheduler import DataScheduler
from web_app.app import create_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class StockMonitoringSystem:
    """Main application class for the stock monitoring system"""
    
    def __init__(self):
        self.db_manager = None
        self.akshare_client = None
        self.scheduler = None
        self.app = None
        
    def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing A-Share Stock Monitoring System...")
        
        try:
            # Initialize database
            logger.info("Initializing database...")
            self.db_manager = DatabaseManager()
            
            # Initialize AKShare client
            logger.info("Initializing AKShare client...")
            self.akshare_client = AKShareClient()
            
            # Test AKShare connection
            if not self.akshare_client.check_connection():
                logger.warning("AKShare connection failed - continuing anyway")
            else:
                logger.info("AKShare connection successful")
            
            # Initialize scheduler
            logger.info("Initializing data scheduler...")
            self.scheduler = DataScheduler()
            
            # Create Flask app
            logger.info("Creating Flask application...")
            self.app = create_app()
            
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {str(e)}")
            raise
    
    def start(self):
        """Start the monitoring system"""
        logger.info("Starting A-Share Stock Monitoring System...")
        
        try:
            # Start the scheduler
            logger.info("Starting data scheduler...")
            self.scheduler.start()
            
            # Start the web application
            logger.info(f"Starting web server on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
            self.app.run(
                host=Config.FLASK_HOST,
                port=Config.FLASK_PORT,
                debug=Config.FLASK_DEBUG,
                threaded=True
            )
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.shutdown()
        except Exception as e:
            logger.error(f"Error starting system: {str(e)}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """Shutdown the monitoring system"""
        logger.info("Shutting down A-Share Stock Monitoring System...")
        
        try:
            if self.scheduler:
                logger.info("Stopping data scheduler...")
                self.scheduler.stop()
            
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
    
    def check_system_health(self):
        """Check system health and dependencies"""
        logger.info("Checking system health...")
        
        health_checks = {
            'database': False,
            'akshare': False,
            'scheduler': False
        }
        
        try:
            # Check database
            if self.db_manager:
                symbols = self.db_manager.get_stock_symbols()
                health_checks['database'] = True
                logger.info(f"Database: OK ({len(symbols)} symbols)")
            
            # Check AKShare
            if self.akshare_client:
                health_checks['akshare'] = self.akshare_client.check_connection()
                logger.info(f"AKShare: {'OK' if health_checks['akshare'] else 'FAILED'}")
            
            # Check scheduler
            if self.scheduler:
                status = self.scheduler.get_scheduler_status()
                health_checks['scheduler'] = status['is_running']
                logger.info(f"Scheduler: {'OK' if health_checks['scheduler'] else 'FAILED'}")
            
            return health_checks
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return health_checks

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if hasattr(signal_handler, 'system'):
        signal_handler.system.shutdown()
    sys.exit(0)

def main():
    """Main entry point"""
    print("=" * 60)
    print("A-Share Stock Monitoring System")
    print("=" * 60)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {Config.DATABASE_PATH}")
    print(f"Web Interface: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print("=" * 60)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and initialize system
    system = StockMonitoringSystem()
    signal_handler.system = system
    
    try:
        system.initialize()
        
        # Check system health
        health = system.check_system_health()
        
        # Display health status
        print("\nSystem Health Check:")
        for component, status in health.items():
            status_text = "✓ OK" if status else "✗ FAILED"
            print(f"  {component.capitalize()}: {status_text}")
        
        print("\nStarting services...")
        print("Web dashboard will be available at:")
        print(f"  http://localhost:{Config.FLASK_PORT}")
        print(f"  http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
        print("\nPress Ctrl+C to stop the system")
        print("=" * 60)
        
        # Start the system
        system.start()
        
    except Exception as e:
        logger.error(f"Failed to start system: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Please check the logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 