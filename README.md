# A股实时监控系统 (A-Share Stock Monitoring System)

一个基于 Python 的本地股票数据库系统，用于监控中国A股市场的实时价格、价格变动和趋势分析。

## 系统特性

### 📊 实时数据监控
- 实时获取A股股票价格数据
- 支持上海证券交易所和深圳证券交易所
- 自动识别市场交易时间，调整数据获取频率
- 基于AKShare的可靠数据源

### 🔔 价格警报系统
- 可配置的价格变动阈值警报
- 支持涨跌幅警报
- 历史警报记录和查询
- 实时警报通知

### 💾 本地数据库
- SQLite数据库，轻量级且可靠
- 股票信息、实时价格、历史数据存储
- 自动数据清理和优化
- 快速查询和索引

### 🌐 Web控制面板
- 现代化的响应式Web界面
- 实时股价表格显示
- 股票搜索和添加功能
- 价格趋势图表
- 系统状态监控

### ⚡ 后台调度系统
- 自动定时数据更新
- 市场时间感知调度
- 可配置的更新间隔
- 系统健康检查

## 系统架构

```
local_stock_database/
├── config.py                    # 配置文件
├── main.py                     # 主程序入口
├── requirements.txt            # 依赖包列表
├── database/
│   └── models.py              # 数据库模型
├── data_fetcher/
│   ├── akshare_client.py      # AKShare客户端
│   └── scheduler.py           # 调度器
├── web_app/
│   └── app.py                 # Flask Web应用
├── templates/
│   └── index.html             # 主页模板
└── static/
    ├── css/
    │   └── style.css          # 样式文件
    └── js/
        └── app.js             # 前端JavaScript
```

## 安装要求

- Python 3.8+
- 稳定的互联网连接
- 8GB+ 可用磁盘空间（用于数据存储）

## 安装步骤

### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 2. 安装依赖包

```bash
# 使用 uv 安装依赖（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 3. 配置系统（可选）

创建 `.env` 文件来自定义配置：

```bash
# 数据库路径
DATABASE_PATH=stock_database.db

# 更新间隔（秒）
REALTIME_UPDATE_INTERVAL=10
STOCK_INFO_UPDATE_INTERVAL=3600

# Web服务器配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# 价格变动警报阈值（百分比）
PRICE_CHANGE_THRESHOLD=5.0

# 日志级别
LOG_LEVEL=INFO
```

### 4. 运行系统

```bash
python main.py
```

## 使用说明

### 启动系统

运行主程序后，系统会自动：
1. 初始化SQLite数据库
2. 检查AKShare连接
3. 启动后台调度器
4. 启动Web服务器

### 访问Web界面

打开浏览器访问：
- `http://localhost:5000`
- 或配置的其他地址

### 主要功能

#### 1. 实时股价监控
- 查看当前监控的股票列表
- 实时价格、涨跌幅、成交量
- 价格变动趋势指示

#### 2. 股票搜索和添加
- 搜索框输入股票代码或名称
- 点击搜索结果添加到监控列表
- 支持移除不需要的股票

#### 3. 价格图表
- 点击表格中的图表按钮
- 查看股票的历史价格走势
- 基于Chart.js的交互式图表

#### 4. 系统状态监控
- 查看调度器运行状态
- 监控数据源连接状态
- 系统健康检查

#### 5. 价格警报
- 自动监控价格变动
- 超过阈值时触发警报
- 查看历史警报记录

## 配置选项

### 默认监控股票

在 `config.py` 中的 `DEFAULT_STOCK_SYMBOLS` 列表中修改：

```python
DEFAULT_STOCK_SYMBOLS = [
    '000001',  # 平安银行
    '000002',  # 万科A
    '600519',  # 贵州茅台
    '000858',  # 五粮液
    # 添加更多股票代码...
]
```

### 更新频率

- `REALTIME_UPDATE_INTERVAL`: 实时价格更新间隔（秒）
- `STOCK_INFO_UPDATE_INTERVAL`: 股票信息更新间隔（秒）

### 警报设置

- `PRICE_CHANGE_THRESHOLD`: 价格变动警报阈值（百分比）

## API接口

系统提供RESTful API接口：

### 股票数据
- `GET /api/stocks/prices` - 获取最新股价
- `GET /api/stocks/info/<symbol>` - 获取股票信息
- `GET /api/stocks/history/<symbol>` - 获取历史数据
- `GET /api/stocks/search?q=<keyword>` - 搜索股票
- `GET /api/stocks/hot` - 获取热门股票

### 监控管理
- `GET /api/scheduler/symbols` - 获取监控列表
- `POST /api/scheduler/symbols` - 添加监控股票
- `DELETE /api/scheduler/symbols/<symbol>` - 移除监控股票

### 系统状态
- `GET /api/stats` - 获取系统统计
- `GET /api/health` - 系统健康检查
- `GET /api/alerts` - 获取警报列表

## 数据库结构

### 主要表格

1. **stock_info**: 股票基本信息
2. **stock_prices**: 实时价格数据
3. **price_history**: 价格历史记录
4. **price_alerts**: 价格警报记录

### 数据保留策略

- 价格历史：保留30天
- 警报记录：保留7天
- 每日凌晨3点自动清理

## 系统监控

### 日志文件

- `stock_monitor.log`: 系统运行日志
- 日志级别：INFO, WARNING, ERROR
- 包含所有系统活动记录

### 性能指标

- 内存使用量
- 数据库大小
- API响应时间
- 数据获取成功率

## 故障排除

### 常见问题

1. **AKShare连接失败**
   - 检查网络连接
   - 确认防火墙设置
   - 验证AKShare库版本

2. **数据库错误**
   - 检查磁盘空间
   - 验证数据库文件权限
   - 重新初始化数据库

3. **Web界面无法访问**
   - 确认端口未被占用
   - 检查防火墙设置
   - 验证Flask配置

4. **数据更新停止**
   - 检查调度器状态
   - 查看错误日志
   - 重启系统

### 重置系统

如需重置系统：

```bash
# 停止程序
Ctrl+C

# 删除数据库文件
rm stock_database.db

# 删除日志文件
rm stock_monitor.log

# 重新启动
python main.py
```

## 性能优化

### 推荐配置

- **生产环境**: 使用较长的更新间隔（30-60秒）
- **开发环境**: 使用较短的更新间隔（5-10秒）
- **监控股票数量**: 建议不超过100只股票

### 系统资源

- **内存**: 建议512MB以上
- **CPU**: 单核心即可满足需求
- **存储**: 每月约50-100MB数据增长

## 扩展功能

### 可扩展特性

1. **邮件通知**: 添加SMTP配置发送警报邮件
2. **技术指标**: 计算MA、RSI、MACD等指标
3. **数据导出**: 支持CSV、Excel格式导出
4. **多市场支持**: 扩展到港股、美股等市场
5. **移动端适配**: 响应式设计支持移动设备

### 集成建议

- **数据库**: 升级到PostgreSQL或MySQL
- **消息队列**: 使用Redis或RabbitMQ
- **缓存**: 添加Redis缓存层
- **监控**: 集成Prometheus + Grafana
- **部署**: Docker容器化部署


### REFERENCE
https://tushare.pro/document/2?doc_id=315


## 免责声明

本系统仅用于学习和研究目的。股票投资存在风险，请谨慎决策。本系统提供的数据和分析不构成投资建议。

## 技术支持

如有技术问题，请查看：
1. 系统日志文件
2. 错误信息和堆栈跟踪
3. 网络连接状态
4. 依赖包版本兼容性

---

**注意**: 请确保遵守相关法律法规和数据提供商的使用条款。 