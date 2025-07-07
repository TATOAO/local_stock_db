from fastapi import FastAPI, Request, HTTPException, Query, Path, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
from typing import Dict, List, Optional
import uvicorn

from config import Config
from database.models import DatabaseManager
from data_fetcher.akshare_client import AKShareClient
from data_fetcher.scheduler import DataScheduler

app = FastAPI(title="Stock Data API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

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
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stocks/prices")
async def get_stock_prices(symbols: Optional[List[str]] = Query(None)):
    """Get latest stock prices"""
    try:
        prices = db_manager.get_latest_prices(symbols)
        
        return {
            'success': True,
            'data': prices,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting stock prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/info/{symbol}")
async def get_stock_info(symbol: str = Path(...)):
    """Get stock information"""
    try:
        stock_info = db_manager.get_stock_info(symbol)
        
        if not stock_info:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        return {
            'success': True,
            'data': stock_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/history/{symbol}")
async def get_stock_history(symbol: str = Path(...), limit: int = Query(100)):
    """Get stock price history"""
    try:
        history = db_manager.get_price_history(symbol, limit)
        
        return {
            'success': True,
            'data': history
        }
    
    except Exception as e:
        logger.error(f"Error getting stock history for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/search")
async def search_stocks(q: str = Query(..., description="Search keyword")):
    """Search stocks by keyword"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Search keyword is required")
        
        results = akshare_client.search_stocks(q)
        
        return {
            'success': True,
            'data': results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching stocks with keyword '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/hot")
async def get_hot_stocks(market: str = Query("all")):
    """Get hot/active stocks"""
    try:
        hot_stocks = akshare_client.get_hot_stocks(market)
        
        return {
            'success': True,
            'data': hot_stocks
        }
    
    except Exception as e:
        logger.error(f"Error getting hot stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts(limit: int = Query(50)):
    """Get recent price alerts"""
    try:
        alerts = db_manager.get_recent_alerts(limit)
        
        return {
            'success': True,
            'data': alerts
        }
    
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        status = scheduler.get_scheduler_status()
        
        return {
            'success': True,
            'data': status
        }
    
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scheduler/symbols")
async def get_monitored_symbols():
    """Get list of monitored symbols"""
    try:
        symbols = scheduler.get_monitored_symbols()
        
        return {
            'success': True,
            'data': symbols
        }
    
    except Exception as e:
        logger.error(f"Error getting monitored symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/symbols")
async def add_monitored_symbol(data: Dict[str, str] = Body(...)):
    """Add a symbol to monitoring"""
    try:
        symbol = data.get('symbol')
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        scheduler.add_symbol(symbol)
        
        return {
            'success': True,
            'message': f'Symbol {symbol} added to monitoring'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding symbol to monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/scheduler/symbols/{symbol}")
async def remove_monitored_symbol(symbol: str = Path(...)):
    """Remove a symbol from monitoring"""
    try:
        scheduler.remove_symbol(symbol)
        
        return {
            'success': True,
            'message': f'Symbol {symbol} removed from monitoring'
        }
    
    except Exception as e:
        logger.error(f"Error removing symbol from monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
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
        
        return {
            'success': True,
            'data': stats
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_symbols = db_manager.get_stock_symbols()
        
        # Check AKShare connection
        akshare_status = akshare_client.check_connection()
        
        return {
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'akshare': 'connected' if akshare_status else 'disconnected',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        })

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            'success': False,
            'error': 'Endpoint not found'
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'error': 'Internal server error'
        }
    )

def create_app():
    """Application factory"""
    return app

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    
    try:
        # Run the FastAPI app with uvicorn
        uvicorn.run(
            app,
            host=Config.SERVER_HOST,
            port=Config.SERVER_PORT,
            log_level="info"
        )
    finally:
        # Stop scheduler on exit
        scheduler.stop() 