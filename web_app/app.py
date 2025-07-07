from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime
from typing import Dict, List

from config import Config
from database.models import DatabaseManager
from data_fetcher.akshare_client import AKShareClient
from data_fetcher.scheduler import DataScheduler

app = Flask(__name__)
CORS(app)

# Initialize components
db_manager = DatabaseManager()
akshare_client = AKShareClient()
scheduler = DataScheduler()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/stocks/prices')
def get_stock_prices():
    """Get latest stock prices"""
    try:
        symbols = request.args.getlist('symbols')
        if not symbols:
            symbols = None
        
        prices = db_manager.get_latest_prices(symbols)
        
        return jsonify({
            'success': True,
            'data': prices,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting stock prices: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/info/<symbol>')
def get_stock_info(symbol):
    """Get stock information"""
    try:
        stock_info = db_manager.get_stock_info(symbol)
        
        if not stock_info:
            return jsonify({
                'success': False,
                'error': 'Stock not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stock_info
        })
    
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/history/<symbol>')
def get_stock_history(symbol):
    """Get stock price history"""
    try:
        limit = int(request.args.get('limit', 100))
        history = db_manager.get_price_history(symbol, limit)
        
        return jsonify({
            'success': True,
            'data': history
        })
    
    except Exception as e:
        logger.error(f"Error getting stock history for {symbol}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/search')
def search_stocks():
    """Search stocks by keyword"""
    try:
        keyword = request.args.get('q', '')
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'Search keyword is required'
            }), 400
        
        results = akshare_client.search_stocks(keyword)
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Error searching stocks with keyword '{keyword}': {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/hot')
def get_hot_stocks():
    """Get hot/active stocks"""
    try:
        market = request.args.get('market', 'all')
        hot_stocks = akshare_client.get_hot_stocks(market)
        
        return jsonify({
            'success': True,
            'data': hot_stocks
        })
    
    except Exception as e:
        logger.error(f"Error getting hot stocks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts')
def get_alerts():
    """Get recent price alerts"""
    try:
        limit = int(request.args.get('limit', 50))
        alerts = db_manager.get_recent_alerts(limit)
        
        return jsonify({
            'success': True,
            'data': alerts
        })
    
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scheduler/status')
def get_scheduler_status():
    """Get scheduler status"""
    try:
        status = scheduler.get_scheduler_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
    
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scheduler/symbols', methods=['GET'])
def get_monitored_symbols():
    """Get list of monitored symbols"""
    try:
        symbols = scheduler.get_monitored_symbols()
        
        return jsonify({
            'success': True,
            'data': symbols
        })
    
    except Exception as e:
        logger.error(f"Error getting monitored symbols: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scheduler/symbols', methods=['POST'])
def add_monitored_symbol():
    """Add a symbol to monitoring"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400
        
        scheduler.add_symbol(symbol)
        
        return jsonify({
            'success': True,
            'message': f'Symbol {symbol} added to monitoring'
        })
    
    except Exception as e:
        logger.error(f"Error adding symbol to monitoring: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scheduler/symbols/<symbol>', methods=['DELETE'])
def remove_monitored_symbol(symbol):
    """Remove a symbol from monitoring"""
    try:
        scheduler.remove_symbol(symbol)
        
        return jsonify({
            'success': True,
            'message': f'Symbol {symbol} removed from monitoring'
        })
    
    except Exception as e:
        logger.error(f"Error removing symbol from monitoring: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        # Get database stats
        symbols = db_manager.get_stock_symbols()
        alerts = db_manager.get_recent_alerts(10)
        
        # Get scheduler status
        scheduler_status = scheduler.get_scheduler_status()
        
        # Check AKShare connection
        akshare_status = akshare_client.check_connection()
        
        stats = {
            'total_symbols': len(symbols),
            'monitored_symbols': len(scheduler.get_monitored_symbols()),
            'recent_alerts': len(alerts),
            'scheduler_running': scheduler_status['is_running'],
            'market_hours': scheduler_status['market_hours'],
            'akshare_connected': akshare_status,
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_symbols = db_manager.get_stock_symbols()
        
        # Check AKShare connection
        akshare_status = akshare_client.check_connection()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'akshare': 'connected' if akshare_status else 'disconnected',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

def create_app():
    """Application factory"""
    return app

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    
    try:
        # Run the Flask app
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    finally:
        # Stop scheduler on exit
        scheduler.stop() 