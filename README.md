# Polymarket 自动交易系统

这是一个专为Polymarket设计的智能自动交易系统，专注于扫描即将结束的市场并执行自动化交易策略。还没有实现redeem 功能需要自己去claim 奖金。

## 🚀 核心功能

- 🔍 **智能市场扫描**: 扫描1-6分钟内结束的市场
- ⏰ **精确时间调度**: 每小时在10、25、40、55分钟执行（15、30、45、0分钟前5分钟）
- 🎯 **保守交易策略**: 只在0.90-0.98价格范围内交易
- 🤖 **全自动交易**: 无需人工干预的自动化交易
- 📊 **实时监控**: 完整的交易日志和统计信息
- 🔒 **安全配置**: 环境变量管理，保护私钥安全

## 📋 系统要求

- Python 3.8+
- uv 包管理器（推荐）
- 有效的Polymarket账户
- USDC余额用于交易


## 🛠️ 快速开始

### 1. 安装依赖

```bash
# 使用uv（推荐）
uv sync

# 或使用pip
pip install -r requirements.txt
```

### 2. 配置环境

复制配置文件并设置您的参数：

```bash
cp config.example.env .env
```

编辑 `.env` 文件：

```bash
# 必需配置
PRIVATE_KEY=your_private_key_here
FUNDER=your_funder_address_here
RPC_URL=https://polygon-rpc.com

# 交易配置
MIN_PRICE_RANGE=0.90
MAX_PRICE_RANGE=0.98
TRADE_AMOUNT=2.0
MAX_ORDER_SIZE=2.0
MIN_ORDER_SIZE=0.1
```

### 3. 运行系统

```bash
# 启动自动交易调度器
python advanced_scheduler.py

# 或手动测试交易
uv run main.py --start-minutes 1 --end-minutes 6 --auto-trade --test-only
```

## ⚙️ 配置说明
### 测试的时候请开一个新evm钱包 充值少量的金额
### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PRIVATE_KEY` | 钱包私钥（必需） | - |
| `FUNDER` | 资金地址（必需）这是polymarket 的钱包地址点击头像获得 | - |
| `RPC_URL` | Polygon RPC端点 | https://polygon-rpc.com |
| `MIN_PRICE_RANGE` | 最小价格范围 | 0.90 |
| `MAX_PRICE_RANGE` | 最大价格范围 | 0.98 |
| `TRADE_AMOUNT` | 每笔交易金额 | 2.0 |
| `MAX_ORDER_SIZE` | 最大订单金额 | 2.0 |
| `MIN_ORDER_SIZE` | 最小订单金额 | 0.1 |

### 调度器配置

编辑 `scheduler_config.json`：

```json
{
  "interval_minutes": 5,
  "max_trades": 1,
  "scan_start_minutes": 1,
  "scan_end_minutes": 6,
  "min_time_remaining": 1,
  "test_mode": false
}
```

## 🎯 交易策略

### 扫描策略
- **时间窗口**: 扫描1-6分钟内结束的市场
- **执行时间**: 每小时10、25、40、55分钟执行
- **市场类型**: 专注于Up/Down类型的短期市场

### 交易策略
- **价格范围**: 只在0.90-0.98价格范围内交易
- **交易金额**: 每笔2.0 USDC
- **滑点设置**: 1%滑点容忍度
- **风险控制**: 保守策略，确保高成功率

## 📊 使用方法

### 自动交易模式

```bash
# 启动自动调度器
python advanced_scheduler.py

# 手动执行一次扫描
uv run main.py --start-minutes 1 --end-minutes 6 --auto-trade --max-trades 1

# 测试模式（不执行实际交易）
uv run main.py --start-minutes 1 --end-minutes 6 --auto-trade --test-only
```

### 手动交易模式

```bash
# 启用手动交易
uv run main.py --manual-trade --start-minutes 1 --end-minutes 6
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--start-minutes` | 扫描开始时间（分钟） | `--start-minutes 1` |
| `--end-minutes` | 扫描结束时间（分钟） | `--end-minutes 6` |
| `--auto-trade` | 启用自动交易 | `--auto-trade` |
| `--manual-trade` | 启用手动交易 | `--manual-trade` |
| `--test-only` | 测试模式 | `--test-only` |
| `--max-trades` | 最大交易次数 | `--max-trades 1` |

## 📁 项目结构

```
polymarket/
├── main.py                    # 主程序入口
├── advanced_scheduler.py      # 高级调度器
├── scheduler_config.json      # 调度器配置
├── config.example.env         # 环境配置示例
├── src/
│   ├── polymarket_scanner.py  # 市场扫描器
│   ├── polymarket_trader.py   # 交易器
│   ├── auto_trader.py         # 自动交易器
│   ├── manual_trader.py       # 手动交易器
│   ├── balance_checker.py     # 余额检查器
│   └── polymarket_tokenid.py  # Token ID处理
├── QUICK_START.md            # 快速开始指南
└── README.md                 # 项目说明
```

## 🔧 核心组件

### PolymarketScanner
- 扫描即将结束的市场
- 获取市场交易数据
- 时间窗口过滤

### PolymarketTrader
- 执行市价单交易
- 余额和授权管理
- 订单状态监控

### AutoTrader
- 智能交易决策
- 风险控制
- 自动化执行

### AdvancedScheduler
- 精确时间调度
- 自动重试机制
- 统计信息记录

## 📈 输出示例

```
=== 扫描1-6分钟内结束的市场 ===
策略: 在交易结束前4分钟开始分析

找到 2 个在1-6分钟内结束的市场:
 1. btc-updown-15m-1761011100 - Bitcoin Up or Down
   结束时间: 2025-10-21T02:00:00Z (还有 3分钟22秒)
 2. eth-updown-15m-1761011100 - Ethereum Up or Down
   结束时间: 2025-10-21T02:00:00Z (还有 3分钟22秒)

找到 1 个市场机会:
1. btc-updown-15m-1761011100 - Bitcoin Up or Down
   建议: BUY_YES
   原因: YES价格0.94在0.90-0.98范围内，买入Up，剩余时间3.2分钟
   ✅ 交易执行成功
```

## ⚠️ 重要注意事项

### 安全要求
1. **私钥安全**: 妥善保管私钥，不要泄露给他人
2. **资金管理**: 建议使用专门的交易账户
3. **测试先行**: 先在测试模式下验证策略

### 风险提示
1. **交易风险**: 所有交易都有风险，请谨慎使用
2. **市场波动**: 短期市场波动较大，可能造成损失
3. **技术风险**: 网络延迟、API故障等可能影响交易

### 常见问题

**Q: 为什么没有找到交易机会？**
A: 系统只在0.90-0.98价格范围内交易，如果市场价格不在这个范围内，就不会执行交易。

**Q: 如何调整交易策略？**
A: 修改 `.env` 文件中的 `MIN_PRICE_RANGE` 和 `MAX_PRICE_RANGE` 参数。

**Q: 如何停止自动交易？**
A: 按 `Ctrl+C` 停止调度器，或设置 `test_mode: true` 启用测试模式。

## 📞 技术支持

如遇到问题，请检查：
1. 网络连接是否正常
2. 私钥和地址是否正确
3. 余额是否充足
4. 配置参数是否正确

## 📄 许可证

MIT License

---

**免责声明**: 本工具仅供学习和研究使用，交易有风险，使用前请充分了解相关风险。