# 🚀 快速启动指南

## 📋 每5分钟自动交易

### 方法1: 使用启动脚本（推荐）

```bash
python start_scheduler.py
```

然后选择：
- `2` - 高级调度器（推荐）
- `4` - 单次执行测试

### 方法2: 直接运行高级调度器

```bash
python advanced_scheduler.py
```

### 方法3: 使用Shell脚本

```bash
./run_auto_trader.sh
```

### 方法4: 基础Python调度器

```bash
python auto_trader_scheduler.py
```

## ⚙️ 配置说明

### 环境变量配置

在 `.env` 文件中配置以下参数：

```env
# 交易策略配置
MIN_PRICE_RANGE=0.85    # 最小价格范围
MAX_PRICE_RANGE=0.99    # 最大价格范围
TRADE_AMOUNT=1.0        # 每笔交易金额 (USD)
```

### 默认配置（实际交易模式）
- 每5分钟执行一次
- 扫描5分钟内结束的市场
- 最多交易1次
- 实际交易模式（会执行真实交易）

### 修改配置

编辑 `scheduler_config.json`：

```json
{
  "interval_minutes": 5,        // 执行间隔（必须被5整除）
  "max_trades": 1,              // 最大交易次数
  "scan_minutes": 5,            // 扫描时间范围（兼容旧版本）
  "scan_start_minutes": 5,      // 扫描开始时间（分钟，必须被5整除）
  "scan_end_minutes": 10,       // 扫描结束时间（分钟，必须被5整除）
  "min_time_remaining": 1,      // 最少剩余时间（分钟）
  "test_mode": false,           // 实际交易模式（执行真实交易）
  "log_level": "INFO",          // 日志级别
  "max_retries": 3,             // 最大重试次数
  "retry_delay": 30             // 重试延迟
}
```

## 📊 监控

### 查看日志
```bash
tail -f scheduler.log
```

### 查看统计
```bash
cat scheduler_stats.json
```

### 查看配置
```bash
cat scheduler_config.json
```

## 🛑 停止调度器

按 `Ctrl+C` 停止调度器

## ⚠️ 重要提醒

1. **现在是实际交易模式** - 会执行真实交易
2. **确保策略正确** - 检查交易策略和配置
3. **监控日志** - 定期检查执行状态
4. **备份配置** - 保存重要的配置文件
5. **资金安全** - 确保有足够的USDC余额

## 🎯 交易策略

### 扫描策略
**前5分钟开始分析策略**：
- 扫描5-10分钟内结束的市场
- 在交易结束前5分钟开始分析
- 给分析留出足够时间，避免过早交易
- 所有时间参数必须被5整除，与交易周期对齐

### 交易策略
**价格范围策略**：只购买价格在配置范围内的一方 (默认85-99)

- YES价格在配置范围内 → 买入Up
- NO价格在配置范围内 → 买入Down
- 两个价格都在范围内 → 选择价格更高的一方
- 都不在范围内 → 不交易

**可配置参数**：
- `MIN_PRICE_RANGE`: 最小价格范围 (默认0.85)
- `MAX_PRICE_RANGE`: 最大价格范围 (默认0.99)
- `TRADE_AMOUNT`: 每笔交易金额 (默认1.0 USD)
