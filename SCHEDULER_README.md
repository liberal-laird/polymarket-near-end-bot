# 自动交易调度器使用说明

## 📋 概述

本项目提供了三种自动交易调度器，可以每5分钟自动运行一次交易程序：

1. **Python调度器** (`auto_trader_scheduler.py`) - 基础版本
2. **Shell脚本** (`run_auto_trader.sh`) - 简单版本
3. **高级调度器** (`advanced_scheduler.py`) - 功能完整版本

## 🚀 使用方法

### 1. 基础Python调度器

```bash
python auto_trader_scheduler.py
```

**特点：**
- 每5分钟执行一次交易
- 显示执行状态和结果
- 支持Ctrl+C停止

### 2. Shell脚本调度器

```bash
./run_auto_trader.sh
```

**特点：**
- 简单易用
- 每5分钟执行一次交易
- 显示执行次数和状态

### 3. 高级调度器（推荐）

```bash
python advanced_scheduler.py
```

**特点：**
- 📊 完整的日志记录
- 📈 执行统计信息
- ⚙️ 配置文件支持
- 🔄 自动重试机制
- 📁 状态持久化

## ⚙️ 配置说明

### 高级调度器配置 (`scheduler_config.json`)

```json
{
  "interval_minutes": 5,        // 执行间隔（分钟）
  "max_trades": 1,              // 最大交易次数
  "scan_minutes": 5,            // 扫描时间范围（分钟）
  "test_mode": true,            // 测试模式（不执行实际交易）
  "log_level": "INFO",          // 日志级别
  "max_retries": 3,             // 最大重试次数
  "retry_delay": 30             // 重试延迟（秒）
}
```

### 配置参数说明

- **interval_minutes**: 调度器执行间隔，默认5分钟
- **max_trades**: 每次执行的最大交易次数，默认1次
- **scan_minutes**: 扫描多少分钟内结束的市场，默认5分钟
- **test_mode**: 是否启用测试模式，默认true（不执行实际交易）
- **log_level**: 日志级别（DEBUG, INFO, WARNING, ERROR）
- **max_retries**: 执行失败时的最大重试次数
- **retry_delay**: 重试之间的延迟时间

## 📊 监控和日志

### 高级调度器生成的文件

- **scheduler.log**: 详细的执行日志
- **scheduler_stats.json**: 执行统计信息
- **scheduler_config.json**: 配置文件

### 统计信息包括

- 运行时间
- 执行次数
- 成功/失败次数
- 最后执行时间
- 最后成功/失败时间

## 🛠️ 自定义命令

如果需要修改执行的命令，可以编辑相应的脚本文件：

### 基础调度器
修改 `auto_trader_scheduler.py` 中的 `cmd` 变量：

```python
cmd = [
    "uv", "run", "main.py", 
    "--minutes", "5", 
    "--auto-trade", 
    "--max-trades", "1"
]
```

### Shell脚本
修改 `run_auto_trader.sh` 中的命令：

```bash
uv run main.py --minutes 5 --auto-trade --max-trades 1
```

### 高级调度器
修改 `scheduler_config.json` 配置文件，或编辑 `advanced_scheduler.py` 中的命令构建逻辑。

## 🔧 系统服务（可选）

### 使用systemd创建系统服务

1. 创建服务文件：

```bash
sudo nano /etc/systemd/system/polymarket-trader.service
```

2. 添加以下内容：

```ini
[Unit]
Description=Polymarket Auto Trader
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/polymarket
ExecStart=/usr/bin/python3 /path/to/polymarket/advanced_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. 启用并启动服务：

```bash
sudo systemctl enable polymarket-trader.service
sudo systemctl start polymarket-trader.service
```

4. 查看服务状态：

```bash
sudo systemctl status polymarket-trader.service
```

## 📝 注意事项

1. **测试模式**: 默认启用测试模式，不会执行实际交易
2. **网络连接**: 确保网络连接稳定
3. **资源监控**: 定期检查日志和统计信息
4. **安全**: 确保私钥和配置文件的安全
5. **备份**: 定期备份配置和日志文件

## 🆘 故障排除

### 常见问题

1. **命令执行失败**
   - 检查uv是否正确安装
   - 检查main.py是否存在
   - 检查网络连接

2. **权限问题**
   - 确保脚本有执行权限：`chmod +x run_auto_trader.sh`
   - 检查文件路径是否正确

3. **配置问题**
   - 检查scheduler_config.json格式是否正确
   - 检查环境变量是否设置

### 日志查看

```bash
# 查看实时日志
tail -f scheduler.log

# 查看最近的错误
grep ERROR scheduler.log

# 查看执行统计
cat scheduler_stats.json
```

## 📞 支持

如果遇到问题，请检查：
1. 日志文件中的错误信息
2. 配置文件是否正确
3. 网络连接是否正常
4. 依赖是否安装完整
