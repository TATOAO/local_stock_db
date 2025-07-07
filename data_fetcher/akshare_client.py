import akshare as ak
import pandas as pd
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
from config import Config

class AKShareClient:
    """Client for fetching A-share stock data using AKShare"""
    
    def __init__(self):
        self.timeout = Config.REQUEST_TIMEOUT
        self.logger = logging.getLogger(__name__)
        
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get basic stock information"""
        try:
            # Get stock info from AKShare
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            
            if stock_info.empty:
                self.logger.warning(f"No stock info found for symbol: {symbol}")
                return None
            
            # Convert to dict format
            info_dict = {}
            for _, row in stock_info.iterrows():
                info_dict[row['item']] = row['value']
            
            return {
                'symbol': symbol,
                'name': info_dict.get('股票名称', ''),
                'market': self._get_market_from_symbol(symbol),
                'sector': info_dict.get('所属行业', ''),
                'industry': info_dict.get('所属概念', ''),
                'total_share': info_dict.get('总股本', 0),
                'float_share': info_dict.get('流通股本', 0),
                'market_cap': info_dict.get('总市值', 0),
                'pe_ratio': info_dict.get('市盈率', 0),
                'pb_ratio': info_dict.get('市净率', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return None
    
    def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        """Get real-time price data for a single stock"""
        try:
            # Get real-time data from AKShare
            rt_data = ak.stock_zh_a_spot_em()
            
            if rt_data.empty:
                self.logger.warning("No real-time data available")
                return None
            
            # Find the stock in the data
            stock_data = rt_data[rt_data['代码'] == symbol]
            
            if stock_data.empty:
                self.logger.warning(f"No real-time data found for symbol: {symbol}")
                return None
            
            row = stock_data.iloc[0]
            
            # Calculate change amount and percentage
            current_price = float(row['最新价'])
            close_price = float(row['昨收'])
            change_amount = current_price - close_price
            change_percent = (change_amount / close_price) * 100 if close_price != 0 else 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'open_price': float(row['今开']),
                'high_price': float(row['最高']),
                'low_price': float(row['最低']),
                'close_price': close_price,
                'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
                'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                'change_amount': change_amount,
                'change_percent': change_percent,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching real-time price for {symbol}: {str(e)}")
            return None
    
    def get_realtime_prices(self, symbols: List[str]) -> List[Dict]:
        """Get real-time price data for multiple stocks"""
        try:
            # Get all real-time data at once for efficiency
            rt_data = ak.stock_zh_a_spot_em()
            
            if rt_data.empty:
                self.logger.warning("No real-time data available")
                return []
            
            results = []
            for symbol in symbols:
                stock_data = rt_data[rt_data['代码'] == symbol]
                
                if stock_data.empty:
                    self.logger.warning(f"No real-time data found for symbol: {symbol}")
                    continue
                
                row = stock_data.iloc[0]
                
                # Calculate change amount and percentage
                current_price = float(row['最新价'])
                close_price = float(row['昨收'])
                change_amount = current_price - close_price
                change_percent = (change_amount / close_price) * 100 if close_price != 0 else 0
                
                price_data = {
                    'symbol': symbol,
                    'name': row['名称'],
                    'current_price': current_price,
                    'open_price': float(row['今开']),
                    'high_price': float(row['最高']),
                    'low_price': float(row['最低']),
                    'close_price': close_price,
                    'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
                    'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                    'change_amount': change_amount,
                    'change_percent': change_percent,
                    'timestamp': datetime.now()
                }
                
                results.append(price_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching real-time prices: {str(e)}")
            return []
    
    def get_stock_hist(self, symbol: str, period: str = "daily", start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get historical stock data"""
        try:
            if start_date is None:
                start_date = "20240101"  # Default to start of 2024
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            
            # Get historical data
            hist_data = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date)
            
            return hist_data
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_hot_stocks(self, market: str = "all") -> List[Dict]:
        """Get hot/active stocks"""
        try:
            # Get real-time data sorted by volume or change
            rt_data = ak.stock_zh_a_spot_em()
            
            if rt_data.empty:
                return []
            
            # Filter by market if specified
            if market != "all":
                if market == "sh":
                    rt_data = rt_data[rt_data['代码'].str.startswith('60')]
                elif market == "sz":
                    rt_data = rt_data[rt_data['代码'].str.startswith(('00', '30'))]
            
            # Sort by volume (most active) and get top 20
            hot_stocks = rt_data.nlargest(20, '成交量')
            
            results = []
            for _, row in hot_stocks.iterrows():
                current_price = float(row['最新价'])
                close_price = float(row['昨收'])
                change_amount = current_price - close_price
                change_percent = (change_amount / close_price) * 100 if close_price != 0 else 0
                
                stock_data = {
                    'symbol': row['代码'],
                    'name': row['名称'],
                    'current_price': current_price,
                    'change_amount': change_amount,
                    'change_percent': change_percent,
                    'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
                    'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                }
                
                results.append(stock_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching hot stocks: {str(e)}")
            return []
    
    def search_stocks(self, keyword: str) -> List[Dict]:
        """Search stocks by keyword"""
        try:
            # Get all stock list
            stock_list = ak.stock_zh_a_spot_em()
            
            if stock_list.empty:
                return []
            
            # Search by name or symbol
            results = stock_list[
                (stock_list['名称'].str.contains(keyword, na=False)) |
                (stock_list['代码'].str.contains(keyword, na=False))
            ]
            
            # Convert to list of dicts
            search_results = []
            for _, row in results.head(10).iterrows():  # Limit to 10 results
                search_results.append({
                    'symbol': row['代码'],
                    'name': row['名称'],
                    'current_price': float(row['最新价']),
                    'change_percent': float(row['涨跌幅'])
                })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching stocks with keyword '{keyword}': {str(e)}")
            return []
    
    def _get_market_from_symbol(self, symbol: str) -> str:
        """Determine market from symbol"""
        if symbol.startswith('60'):
            return 'SH'  # Shanghai
        elif symbol.startswith('00') or symbol.startswith('30'):
            return 'SZ'  # Shenzhen
        elif symbol.startswith('68'):
            return 'SH'  # Shanghai STAR Market
        else:
            return 'Unknown'
    
    def check_connection(self) -> bool:
        """Check if AKShare is working"""
        try:
            # Try to get a simple data request
            data = ak.stock_zh_a_spot_em()
            return not data.empty
        except Exception as e:
            self.logger.error(f"AKShare connection failed: {str(e)}")
            return False 