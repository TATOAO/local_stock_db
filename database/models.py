import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import Config

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Stock information table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Real-time price data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                current_price REAL NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                change_amount REAL NOT NULL,
                change_percent REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES stock_info (symbol)
            )
        ''')
        
        # Price history table for tracking changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                change_percent REAL NOT NULL,
                volume INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES stock_info (symbol)
            )
        ''')
        
        # Price alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,  -- 'gain' or 'loss'
                threshold REAL NOT NULL,
                current_change REAL NOT NULL,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES stock_info (symbol)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_prices_timestamp ON stock_prices(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON price_history(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp)')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
    
    def insert_stock_info(self, symbol: str, name: str, market: str, sector: str = None, industry: str = None):
        """Insert or update stock information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stock_info (symbol, name, market, sector, industry, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, name, market, sector, industry, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def insert_price_data(self, symbol: str, price_data: Dict):
        """Insert current price data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stock_prices (
                symbol, current_price, open_price, high_price, low_price, 
                close_price, volume, change_amount, change_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            price_data.get('current_price', 0),
            price_data.get('open_price', 0),
            price_data.get('high_price', 0),
            price_data.get('low_price', 0),
            price_data.get('close_price', 0),
            price_data.get('volume', 0),
            price_data.get('change_amount', 0),
            price_data.get('change_percent', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_latest_prices(self, symbols: List[str] = None) -> List[Dict]:
        """Get latest prices for specified symbols or all symbols"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if symbols:
            placeholders = ','.join(['?' for _ in symbols])
            query = f'''
                SELECT sp.*, si.name
                FROM stock_prices sp
                JOIN stock_info si ON sp.symbol = si.symbol
                WHERE sp.symbol IN ({placeholders})
                AND sp.timestamp = (
                    SELECT MAX(timestamp) FROM stock_prices sp2 WHERE sp2.symbol = sp.symbol
                )
                ORDER BY sp.change_percent DESC
            '''
            cursor.execute(query, symbols)
        else:
            cursor.execute('''
                SELECT sp.*, si.name
                FROM stock_prices sp
                JOIN stock_info si ON sp.symbol = si.symbol
                WHERE sp.timestamp = (
                    SELECT MAX(timestamp) FROM stock_prices sp2 WHERE sp2.symbol = sp.symbol
                )
                ORDER BY sp.change_percent DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stock information by symbol"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stock_info WHERE symbol = ?', (symbol,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_price_history(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get price history for a symbol"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM price_history 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (symbol, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def insert_price_alert(self, symbol: str, alert_type: str, threshold: float, current_change: float):
        """Insert price alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO price_alerts (symbol, alert_type, threshold, current_change)
            VALUES (?, ?, ?, ?)
        ''', (symbol, alert_type, threshold, current_change))
        
        conn.commit()
        conn.close()
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent price alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pa.*, si.name
            FROM price_alerts pa
            JOIN stock_info si ON pa.symbol = si.symbol
            ORDER BY pa.triggered_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stock_symbols(self) -> List[str]:
        """Get all stock symbols in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT symbol FROM stock_info ORDER BY symbol')
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows] 