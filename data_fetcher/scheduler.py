import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import Config
from database.models import DatabaseManager
from data_fetcher.akshare_client import AKShareClient

class DataScheduler:
    """Scheduler for periodic data updates and monitoring"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.akshare_client = AKShareClient()
        self.scheduler = BackgroundScheduler()
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.symbols_to_monitor = Config.DEFAULT_STOCK_SYMBOLS.copy()
        
        # Setup scheduler jobs
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        # Real-time price updates (every 10 seconds during market hours)
        self.scheduler.add_job(
            func=self._update_realtime_prices,
            trigger=IntervalTrigger(seconds=Config.REALTIME_UPDATE_INTERVAL),
            id='realtime_price_update',
            name='Update Real-time Prices',
            replace_existing=True
        )
        
        # Stock info updates (every hour)
        self.scheduler.add_job(
            func=self._update_stock_info,
            trigger=IntervalTrigger(seconds=Config.STOCK_INFO_UPDATE_INTERVAL),
            id='stock_info_update',
            name='Update Stock Info',
            replace_existing=True
        )
        
        # Alert monitoring (every 30 seconds)
        self.scheduler.add_job(
            func=self._monitor_alerts,
            trigger=IntervalTrigger(seconds=30),
            id='alert_monitoring',
            name='Monitor Price Alerts',
            replace_existing=True
        )
        
        # Market hours check (every minute)
        self.scheduler.add_job(
            func=self._check_market_hours,
            trigger=CronTrigger(second=0),  # Every minute
            id='market_hours_check',
            name='Check Market Hours',
            replace_existing=True
        )
        
        # Daily cleanup (at 3 AM)
        self.scheduler.add_job(
            func=self._daily_cleanup,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_cleanup',
            name='Daily Database Cleanup',
            replace_existing=True
        )
    
    def start(self):
        """Start the scheduler"""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                self.logger.info("Data scheduler started successfully")
                
                # Initialize stock info for default symbols
                self._initial_stock_info_update()
                
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {str(e)}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                self.logger.info("Data scheduler stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {str(e)}")
    
    def add_symbol(self, symbol: str):
        """Add a symbol to monitoring list"""
        if symbol not in self.symbols_to_monitor:
            self.symbols_to_monitor.append(symbol)
            self.logger.info(f"Added symbol {symbol} to monitoring list")
            
            # Get stock info for the new symbol
            stock_info = self.akshare_client.get_stock_info(symbol)
            if stock_info:
                self.db_manager.insert_stock_info(
                    symbol=stock_info['symbol'],
                    name=stock_info['name'],
                    market=stock_info['market'],
                    sector=stock_info.get('sector'),
                    industry=stock_info.get('industry')
                )
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol from monitoring list"""
        if symbol in self.symbols_to_monitor:
            self.symbols_to_monitor.remove(symbol)
            self.logger.info(f"Removed symbol {symbol} from monitoring list")
    
    def get_monitored_symbols(self) -> List[str]:
        """Get list of currently monitored symbols"""
        return self.symbols_to_monitor.copy()
    
    def _initial_stock_info_update(self):
        """Initial update of stock information"""
        self.logger.info("Performing initial stock info update...")
        
        for symbol in self.symbols_to_monitor:
            try:
                stock_info = self.akshare_client.get_stock_info(symbol)
                if stock_info:
                    self.db_manager.insert_stock_info(
                        symbol=stock_info['symbol'],
                        name=stock_info['name'],
                        market=stock_info['market'],
                        sector=stock_info.get('sector'),
                        industry=stock_info.get('industry')
                    )
                    self.logger.info(f"Updated stock info for {symbol}")
                else:
                    self.logger.warning(f"Could not get stock info for {symbol}")
                    
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error updating stock info for {symbol}: {str(e)}")
    
    def _update_realtime_prices(self):
        """Update real-time prices for monitored symbols"""
        if not self._is_market_hours():
            return
        
        try:
            # Get real-time prices for all monitored symbols
            prices = self.akshare_client.get_realtime_prices(self.symbols_to_monitor)
            
            if not prices:
                self.logger.warning("No real-time price data received")
                return
            
            # Store prices in database
            for price_data in prices:
                try:
                    self.db_manager.insert_price_data(price_data['symbol'], price_data)
                    
                    # Also update price history
                    self._update_price_history(price_data)
                    
                except Exception as e:
                    self.logger.error(f"Error storing price data for {price_data['symbol']}: {str(e)}")
            
            self.logger.debug(f"Updated real-time prices for {len(prices)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error in real-time price update: {str(e)}")
    
    def _update_stock_info(self):
        """Update stock information periodically"""
        try:
            for symbol in self.symbols_to_monitor:
                stock_info = self.akshare_client.get_stock_info(symbol)
                if stock_info:
                    self.db_manager.insert_stock_info(
                        symbol=stock_info['symbol'],
                        name=stock_info['name'],
                        market=stock_info['market'],
                        sector=stock_info.get('sector'),
                        industry=stock_info.get('industry')
                    )
                
                # Add delay to avoid rate limiting
                time.sleep(1)
            
            self.logger.info("Stock info update completed")
            
        except Exception as e:
            self.logger.error(f"Error in stock info update: {str(e)}")
    
    def _update_price_history(self, price_data: Dict):
        """Update price history table"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO price_history (symbol, price, change_percent, volume)
                VALUES (?, ?, ?, ?)
            ''', (
                price_data['symbol'],
                price_data['current_price'],
                price_data['change_percent'],
                price_data['volume']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating price history: {str(e)}")
    
    def _monitor_alerts(self):
        """Monitor price changes and create alerts"""
        try:
            # Get latest prices
            latest_prices = self.db_manager.get_latest_prices(self.symbols_to_monitor)
            
            for price_data in latest_prices:
                change_percent = abs(price_data['change_percent'])
                
                # Check if change exceeds threshold
                if change_percent >= Config.PRICE_CHANGE_THRESHOLD:
                    alert_type = 'gain' if price_data['change_percent'] > 0 else 'loss'
                    
                    # Insert alert
                    self.db_manager.insert_price_alert(
                        symbol=price_data['symbol'],
                        alert_type=alert_type,
                        threshold=Config.PRICE_CHANGE_THRESHOLD,
                        current_change=price_data['change_percent']
                    )
                    
                    self.logger.info(f"Price alert triggered for {price_data['symbol']}: {price_data['change_percent']:.2f}%")
        
        except Exception as e:
            self.logger.error(f"Error in alert monitoring: {str(e)}")
    
    def _check_market_hours(self):
        """Check if market is open and adjust update frequency"""
        is_market_open = self._is_market_hours()
        
        # Get current job
        job = self.scheduler.get_job('realtime_price_update')
        if job:
            if is_market_open:
                # Normal update interval during market hours
                if job.trigger.interval.total_seconds() != Config.REALTIME_UPDATE_INTERVAL:
                    job.modify(trigger=IntervalTrigger(seconds=Config.REALTIME_UPDATE_INTERVAL))
                    self.logger.info("Switched to market hours update frequency")
            else:
                # Slower updates outside market hours
                if job.trigger.interval.total_seconds() != 300:  # 5 minutes
                    job.modify(trigger=IntervalTrigger(seconds=300))
                    self.logger.info("Switched to off-market hours update frequency")
    
    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        # Chinese stock market hours: 9:30-11:30, 13:00-15:00, Monday-Friday
        # Skip weekends
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Morning session: 9:30-11:30
        morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0).time()
        morning_end = now.replace(hour=11, minute=30, second=0, microsecond=0).time()
        
        # Afternoon session: 13:00-15:00
        afternoon_start = now.replace(hour=13, minute=0, second=0, microsecond=0).time()
        afternoon_end = now.replace(hour=15, minute=0, second=0, microsecond=0).time()
        
        return (morning_start <= current_time <= morning_end) or (afternoon_start <= current_time <= afternoon_end)
    
    def _daily_cleanup(self):
        """Daily database cleanup"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Delete old price history (keep last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute(
                'DELETE FROM price_history WHERE timestamp < ?',
                (thirty_days_ago,)
            )
            
            # Delete old alerts (keep last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            cursor.execute(
                'DELETE FROM price_alerts WHERE triggered_at < ?',
                (seven_days_ago,)
            )
            
            conn.commit()
            conn.close()
            
            self.logger.info("Daily database cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in daily cleanup: {str(e)}")
    
    def get_scheduler_status(self) -> Dict:
        """Get scheduler status information"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return {
            'is_running': self.is_running,
            'monitored_symbols': len(self.symbols_to_monitor),
            'jobs': jobs,
            'market_hours': self._is_market_hours()
        } 