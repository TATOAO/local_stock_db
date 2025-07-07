import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'stock_database.db')
    
    # Update intervals (in seconds)
    REALTIME_UPDATE_INTERVAL = int(os.getenv('REALTIME_UPDATE_INTERVAL', 10))  # 10 seconds
    STOCK_INFO_UPDATE_INTERVAL = int(os.getenv('STOCK_INFO_UPDATE_INTERVAL', 3600))  # 1 hour
    
    # Flask settings
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Default stock symbols to monitor (popular A-share stocks)
    DEFAULT_STOCK_SYMBOLS = [
        '000001',  # 平安银行
        '000002',  # 万科A
        '000858',  # 五粮液
        '002415',  # 海康威视
        '600036',  # 招商银行
        '600519',  # 贵州茅台
        '600887',  # 伊利股份
        '000858',  # 五粮液
        '002142',  # 宁波银行
        '300750',  # 宁德时代
    ]
    
    # Price change thresholds for alerts
    PRICE_CHANGE_THRESHOLD = float(os.getenv('PRICE_CHANGE_THRESHOLD', 5.0))  # 5% change
    
    # Data source settings
    DATA_SOURCE = 'akshare'
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))  # 10 seconds
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO') 