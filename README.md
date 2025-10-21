# Polymarket 短期市场扫描器

这是一个用于扫描Polymarket短期结束市场的Python工具，可以帮助您找到即将结束的交易机会。

## 功能特性

- 🔍 扫描指定时间内结束的市场
- ⏰ 精确到分钟和秒的时间显示
- 📊 显示市场交易数据（中间价、价格、订单簿）
- 🎯 支持按小时或分钟筛选
- 📈 实时获取市场数据
- ⚡ 异步架构设计，支持批量获取（提高性能）
- 🔄 自动回退机制，确保稳定性
- 💰 自动交易功能，支持市价单下单
- 🤖 智能交易策略（保守、中等、激进）
- 📋 环境变量配置，安全便捷

## 安装依赖

```bash
# 使用uv（推荐）
uv add requests py-clob-client aiohttp python-dotenv

# 或使用pip
pip install requests py-clob-client aiohttp python-dotenv
```

## 使用方法

### 基本用法

```bash
# 扫描1小时内结束的市场（默认）
python main.py

# 扫描2小时内结束的市场
python main.py --hours 2

# 扫描30分钟内结束的市场
python main.py --minutes 30

# 显示前50个最近结束的市场
python main.py --top 50

# 组合使用
python main.py --minutes 15 --top 10

# 自动交易模式
python main.py --auto-trade --minutes 15 --max-trades 3

# 手动交易模式
python main.py --manual-trade --minutes 15

# 使用激进策略
python main.py --auto-trade --strategy aggressive --max-trades 5
```

### 命令行参数

- `--hours`: 扫描多少小时内结束的市场（默认: 1.0）
- `--minutes`: 扫描多少分钟内结束的市场（优先级高于hours）
- `--top`: 显示前N个最近结束的市场（默认: 20）
- `--auto-trade`: 启用自动交易模式
- `--manual-trade`: 启用手动交易模式
- `--max-trades`: 最大交易次数（默认: 3）
- `--strategy`: 交易策略（conservative/moderate/aggressive，默认: moderate）
- `--help`: 显示帮助信息

## 输出示例

```
当前时间: 2025-10-19T15:40:17.151836
0.5小时后: 2025-10-19T16:10:17.151857
总共有 700 个market

Solana市场信息:
Solana Up or Down on October 19: 还有 8.3 小时结束

前20个最近结束的market:
1. btc-updown-15m-1760859000 - Bitcoin Up or Down - October 19, 3:30AM-3:45AM ET
   结束时间: 2025-10-19T07:45:00Z (还有 4分钟38秒)

查找0.5小时内结束的market:
找到0.5小时内结束的market: btc-updown-15m-1760859000 - Bitcoin Up or Down - October 19, 3:30AM-3:45AM ET
结束时间: 2025-10-19T07:45:00Z (还有 4分钟38秒)
yes : mid:0.91 {'price': '0.9'} 0xeadc94e09b11eff6dfbc4046749c5cf34c7668957f33fff7ba0f9b1879572319 1
no : mid:0.09 {'price': '0.06'} 0xeadc94e09b11eff6dfbc4046749c5cf34c7668957f33fff7ba0f9b1879572319 1

总结: 找到 10 个0.5小时内结束的市场
```

## 项目结构

```
polymarket/
├── main.py                    # 主程序入口
├── src/
│   ├── polymarket_scanner.py  # 市场扫描器类
│   ├── polymarket_tokenid.py  # 异步Token ID处理模块
│   ├── polymarket_trader.py   # 交易器类
│   ├── auto_trader.py         # 自动交易器
│   └── manual_trader.py       # 手动交易器
├── config.example.env         # 配置示例文件
├── pyproject.toml            # 项目配置
└── README.md                 # 说明文档
```

## 核心类说明

### PolymarketScanner

主要的市场扫描器类，提供以下方法：

- `fetch_markets()`: 获取所有活跃市场数据
- `get_markets_with_time()`: 获取带有时间信息的市场列表
- `get_short_term_markets()`: 获取短期结束的市场
- `get_market_data()`: 获取单个市场交易数据
- `get_multiple_markets_data()`: 批量获取多个市场交易数据
- `scan_short_term_markets()`: 扫描短期市场的完整流程

### PolymarketTokenID

异步Token ID处理模块，提供以下功能：

- `AsyncPolymarketClient`: 异步HTTP客户端
- `get_all_midpoints()`: 获取单个市场的所有数据
- `get_multiple_markets()`: 批量获取多个市场数据
- 自动回退机制：异步API失败时自动使用同步客户端

### PolymarketTrader

交易器类，提供以下功能：

- `place_market_order()`: 下市价单
- `place_yes_no_orders()`: 同时下YES和NO订单
- `get_balance()`: 获取余额
- `cancel_order()`: 取消订单
- `get_open_orders()`: 获取未成交订单

### AutoTrader

自动交易器，结合扫描器和交易器：

- `analyze_market_opportunity()`: 分析市场机会
- `scan_and_analyze()`: 扫描并分析市场
- `execute_trade()`: 执行交易
- `auto_trade_loop()`: 自动交易循环

### ManualTrader

手动交易器，提供交互式交易界面：

- `scan_markets()`: 扫描可交易市场
- `display_markets()`: 显示市场列表
- `manual_trade()`: 手动执行交易
- `interactive_trading()`: 交互式交易界面

## 配置说明

### 环境变量配置

复制 `config.example.env` 为 `.env` 并配置以下参数：

```bash
# 必需配置
PRIVATE_KEY=your_private_key_here
FUNDER=your_funder_address_here
RPC_URL=https://polygon-rpc.com

# 可选配置
CHAIN_ID=137
SIGNATURE_TYPE=0
DEFAULT_SLIPPAGE=0.01
MAX_ORDER_SIZE=1.0
MIN_ORDER_SIZE=1.0
ORDER_EXPIRATION=86400

# 自动交易配置
AUTO_TRADE_ENABLED=false
DEFAULT_TRADE_SIZE=1.0
MAX_TRADE_SIZE=10.0
TRADE_SLIPPAGE=0.02
MIN_TIME_REMAINING_MINUTES=5
TRADE_STRATEGY=moderate
```

### 交易策略说明

- **conservative（保守）**: 固定订单1USD，滑点1%，最少剩余10分钟
- **moderate（中等）**: 固定订单1USD，滑点1%，最少剩余5分钟
- **aggressive（激进）**: 固定订单1USD，滑点1%，最少剩余2分钟

**注意**: 所有策略都固定每笔交易1USD和1%滑点，确保风险可控

### 签名类型说明

系统支持三种签名类型，根据您的钱包类型选择：

- **SIGNATURE_TYPE=0 (默认)**: Standard EOA签名
  - 适用于：MetaMask、硬件钱包、任何直接控制私钥的钱包
  - 最常用的签名类型

- **SIGNATURE_TYPE=1**: Email/Magic钱包签名
  - 适用于：使用委托签名的Magic钱包
  - 需要特殊的签名流程

- **SIGNATURE_TYPE=2**: Browser钱包代理签名
  - 适用于：使用代理合约的浏览器钱包
  - 不是直接的钱包连接

### 手动交易模式

手动交易模式提供交互式界面，让您手动选择市场进行交易：

```bash
# 启用手动交易模式
python main.py --manual-trade --minutes 15
```

**手动交易流程**：
1. 扫描并显示可交易的市场列表
2. 选择市场编号
3. 选择交易方向（YES/NO）
4. 确认交易参数
5. 执行交易

**交互式命令**：
- 输入市场编号：选择要交易的市场
- 输入 `q`：退出程序
- 输入 `r`：刷新市场列表

## 注意事项

1. 该工具基于Polymarket官方API，请遵守API使用限制
2. 市场数据实时更新，时间显示基于UTC时间
3. 交易数据包含中间价、价格和订单簿信息
4. 建议在交易前仔细分析市场数据
5. **交易有风险，请谨慎使用自动交易功能**
6. 请确保私钥安全，不要泄露给他人
7. 建议先在测试环境验证策略效果

### 余额和授权要求

在开始交易前，请确保：

1. **USDC余额充足**: 账户需要有足够的USDC来执行交易
2. **授权额度**: 系统会自动检查并尝试授权USDC使用额度
3. **Gas费用**: 确保账户有足够的MATIC来支付交易Gas费用

**常见问题**：
- `not enough balance`: 余额不足，请充值USDC
- `not enough allowance`: 授权不足，系统会自动尝试授权
- 如果自动授权失败，请手动在钱包中授权USDC使用额度

## 许可证

MIT License
