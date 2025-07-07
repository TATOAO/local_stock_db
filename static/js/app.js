// A-Share Stock Monitoring Dashboard - JavaScript
class StockMonitorApp {
    constructor() {
        this.apiBase = '/api';
        this.updateInterval = 10000; // 10 seconds
        this.priceChart = null;
        this.updateTimer = null;
        this.isConnected = true;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startClock();
        this.loadInitialData();
        this.startAutoUpdate();
    }
    
    setupEventListeners() {
        // Search functionality
        document.getElementById('search-btn').addEventListener('click', () => {
            this.performSearch();
        });
        
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadStockPrices();
        });
        
        // Modal events
        document.getElementById('chartModal').addEventListener('shown.bs.modal', (e) => {
            const symbol = e.relatedTarget.getAttribute('data-symbol');
            this.loadStockChart(symbol);
        });
    }
    
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeString = now.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            document.getElementById('current-time').textContent = timeString;
        };
        
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadSystemStats(),
                this.loadStockPrices(),
                this.loadHotStocks(),
                this.loadAlerts()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data');
        }
    }
    
    startAutoUpdate() {
        this.updateTimer = setInterval(() => {
            this.loadStockPrices();
            this.loadSystemStats();
        }, this.updateInterval);
    }
    
    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }
    
    async apiRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'API request failed');
            }
            
            this.setConnectionStatus(true);
            return data;
            
        } catch (error) {
            console.error('API request failed:', error);
            this.setConnectionStatus(false);
            throw error;
        }
    }
    
    setConnectionStatus(connected) {
        this.isConnected = connected;
        const statusEl = document.getElementById('connection-status');
        
        if (connected) {
            statusEl.textContent = '连接正常';
            statusEl.className = 'badge bg-success';
        } else {
            statusEl.textContent = '连接失败';
            statusEl.className = 'badge bg-danger';
        }
    }
    
    async loadSystemStats() {
        try {
            const response = await this.apiRequest('/stats');
            const stats = response.data;
            
            // Update stats cards
            document.getElementById('monitored-count').textContent = stats.monitored_symbols;
            document.getElementById('alert-count').textContent = stats.recent_alerts;
            
            // Update system status
            document.getElementById('scheduler-status').textContent = stats.scheduler_running ? '运行中' : '已停止';
            document.getElementById('scheduler-status').className = stats.scheduler_running ? 'badge bg-success' : 'badge bg-danger';
            
            document.getElementById('akshare-status').textContent = stats.akshare_connected ? '已连接' : '未连接';
            document.getElementById('akshare-status').className = stats.akshare_connected ? 'badge bg-success' : 'badge bg-danger';
            
            document.getElementById('last-update').textContent = new Date(stats.last_update).toLocaleTimeString('zh-CN');
            
            // Update market status
            const marketStatus = document.getElementById('market-status');
            if (stats.market_hours) {
                marketStatus.textContent = '开市';
                marketStatus.className = 'badge market-open';
            } else {
                marketStatus.textContent = '休市';
                marketStatus.className = 'badge market-closed';
            }
            
        } catch (error) {
            console.error('Error loading system stats:', error);
        }
    }
    
    async loadStockPrices() {
        try {
            const response = await this.apiRequest('/stocks/prices');
            const prices = response.data;
            
            this.updateStockTable(prices);
            this.updateStatsCards(prices);
            
        } catch (error) {
            console.error('Error loading stock prices:', error);
            this.showError('Failed to load stock prices');
        }
    }
    
    updateStockTable(prices) {
        const tbody = document.getElementById('stock-table-body');
        tbody.innerHTML = '';
        
        prices.forEach(stock => {
            const row = document.createElement('tr');
            row.className = 'fade-in';
            
            const changeClass = stock.change_percent > 0 ? 'price-positive' : 
                              stock.change_percent < 0 ? 'price-negative' : 'price-neutral';
            
            const trendClass = stock.change_percent > 0 ? 'trend-up' : 
                             stock.change_percent < 0 ? 'trend-down' : 'trend-flat';
            
            row.innerHTML = `
                <td><strong>${stock.symbol}</strong></td>
                <td>${stock.name}</td>
                <td><strong>¥${stock.current_price.toFixed(2)}</strong></td>
                <td class="${changeClass}">${stock.change_amount > 0 ? '+' : ''}${stock.change_amount.toFixed(2)}</td>
                <td class="${changeClass} ${trendClass}">${stock.change_percent > 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%</td>
                <td>${this.formatVolume(stock.volume)}</td>
                <td>${new Date(stock.timestamp).toLocaleTimeString('zh-CN')}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="app.showChart('${stock.symbol}', '${stock.name}')">
                        <i class="fas fa-chart-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger ms-1" onclick="app.removeStock('${stock.symbol}')">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    updateStatsCards(prices) {
        let gainCount = 0;
        let lossCount = 0;
        
        prices.forEach(stock => {
            if (stock.change_percent > 5) gainCount++;
            if (stock.change_percent < -5) lossCount++;
        });
        
        document.getElementById('gain-count').textContent = gainCount;
        document.getElementById('loss-count').textContent = lossCount;
    }
    
    async loadHotStocks() {
        try {
            const response = await this.apiRequest('/stocks/hot');
            const hotStocks = response.data;
            
            const container = document.getElementById('hot-stocks-list');
            container.innerHTML = '';
            
            hotStocks.slice(0, 10).forEach(stock => {
                const item = document.createElement('div');
                item.className = 'hot-stock-item';
                
                const changeClass = stock.change_percent > 0 ? 'price-positive' : 
                                  stock.change_percent < 0 ? 'price-negative' : 'price-neutral';
                
                item.innerHTML = `
                    <div>
                        <div class="hot-stock-symbol">${stock.symbol}</div>
                        <div class="hot-stock-name">${stock.name}</div>
                    </div>
                    <div class="hot-stock-price">
                        <div><strong>¥${stock.current_price.toFixed(2)}</strong></div>
                        <div class="${changeClass}">${stock.change_percent > 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%</div>
                    </div>
                `;
                
                container.appendChild(item);
            });
            
        } catch (error) {
            console.error('Error loading hot stocks:', error);
        }
    }
    
    async loadAlerts() {
        try {
            const response = await this.apiRequest('/alerts');
            const alerts = response.data;
            
            const container = document.getElementById('alerts-list');
            container.innerHTML = '';
            
            if (alerts.length === 0) {
                container.innerHTML = '<div class="text-muted">暂无警报</div>';
                return;
            }
            
            alerts.slice(0, 10).forEach(alert => {
                const item = document.createElement('div');
                item.className = 'alert-item';
                
                const icon = alert.alert_type === 'gain' ? 'fa-arrow-up text-success' : 'fa-arrow-down text-danger';
                const changeText = alert.alert_type === 'gain' ? '上涨' : '下跌';
                
                item.innerHTML = `
                    <div>
                        <i class="fas ${icon} alert-icon"></i>
                        <strong>${alert.symbol}</strong> ${alert.name}
                        <div class="alert-time">${changeText} ${Math.abs(alert.current_change).toFixed(2)}%</div>
                    </div>
                    <div class="alert-time">
                        ${new Date(alert.triggered_at).toLocaleTimeString('zh-CN')}
                    </div>
                `;
                
                container.appendChild(item);
            });
            
        } catch (error) {
            console.error('Error loading alerts:', error);
        }
    }
    
    async performSearch() {
        const keyword = document.getElementById('search-input').value.trim();
        if (!keyword) return;
        
        try {
            const response = await this.apiRequest(`/stocks/search?q=${encodeURIComponent(keyword)}`);
            const results = response.data;
            
            this.displaySearchResults(results);
            
        } catch (error) {
            console.error('Error performing search:', error);
            this.showError('搜索失败');
        }
    }
    
    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        container.innerHTML = '';
        
        if (results.length === 0) {
            container.innerHTML = '<div class="text-muted">未找到相关股票</div>';
            return;
        }
        
        results.forEach(stock => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            
            const changeClass = stock.change_percent > 0 ? 'price-positive' : 
                              stock.change_percent < 0 ? 'price-negative' : 'price-neutral';
            
            item.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div>
                        <strong>${stock.symbol}</strong> ${stock.name}
                    </div>
                    <div>
                        <strong>¥${stock.current_price.toFixed(2)}</strong>
                        <span class="${changeClass} ms-2">${stock.change_percent > 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%</span>
                    </div>
                </div>
            `;
            
            item.addEventListener('click', () => {
                this.addStock(stock.symbol);
            });
            
            container.appendChild(item);
        });
    }
    
    async addStock(symbol) {
        try {
            await this.apiRequest('/scheduler/symbols', {
                method: 'POST',
                body: JSON.stringify({ symbol: symbol })
            });
            
            this.showSuccess(`已添加股票 ${symbol} 到监控列表`);
            this.loadStockPrices();
            
        } catch (error) {
            console.error('Error adding stock:', error);
            this.showError('添加股票失败');
        }
    }
    
    async removeStock(symbol) {
        if (!confirm(`确定要移除股票 ${symbol} 吗？`)) return;
        
        try {
            await this.apiRequest(`/scheduler/symbols/${symbol}`, {
                method: 'DELETE'
            });
            
            this.showSuccess(`已移除股票 ${symbol}`);
            this.loadStockPrices();
            
        } catch (error) {
            console.error('Error removing stock:', error);
            this.showError('移除股票失败');
        }
    }
    
    showChart(symbol, name) {
        const modal = new bootstrap.Modal(document.getElementById('chartModal'));
        document.getElementById('chartModalLabel').textContent = `${symbol} ${name} - 股价走势`;
        modal.show();
    }
    
    async loadStockChart(symbol) {
        try {
            const response = await this.apiRequest(`/stocks/history/${symbol}?limit=50`);
            const history = response.data;
            
            this.renderChart(history);
            
        } catch (error) {
            console.error('Error loading stock chart:', error);
            this.showError('加载图表失败');
        }
    }
    
    renderChart(history) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Destroy existing chart
        if (this.priceChart) {
            this.priceChart.destroy();
        }
        
        const labels = history.map(item => new Date(item.timestamp).toLocaleDateString('zh-CN'));
        const prices = history.map(item => item.price);
        
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.reverse(),
                datasets: [{
                    label: '股价',
                    data: prices.reverse(),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    formatVolume(volume) {
        if (volume >= 100000000) {
            return (volume / 100000000).toFixed(2) + '亿';
        } else if (volume >= 10000) {
            return (volume / 10000).toFixed(2) + '万';
        } else {
            return volume.toString();
        }
    }
    
    showError(message) {
        this.showNotification(message, 'danger');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    destroy() {
        this.stopAutoUpdate();
        if (this.priceChart) {
            this.priceChart.destroy();
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new StockMonitorApp();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.app) {
        window.app.destroy();
    }
}); 