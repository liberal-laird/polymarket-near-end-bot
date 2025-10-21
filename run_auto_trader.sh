#!/bin/bash

# 自动交易调度器 - 每5分钟运行一次交易程序
# 使用方法: ./run_auto_trader.sh

echo "🚀 自动交易调度器启动"
echo "📅 每5分钟执行一次交易"
echo "🛑 按 Ctrl+C 停止"
echo "=================================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

execution_count=0

# 捕获中断信号
trap 'echo -e "\n🛑 调度器已停止"; echo "📊 总执行次数: $execution_count"; echo "👋 再见！"; exit 0' INT

while true; do
    execution_count=$((execution_count + 1))
    echo ""
    echo "🔄 第 $execution_count 次执行"
    echo "🕐 $(date '+%Y-%m-%d %H:%M:%S') - 开始执行交易..."
    echo "📋 命令: uv run main.py --minutes 5 --auto-trade --max-trades 1"
    
    # 执行交易命令
    if uv run main.py --minutes 5 --auto-trade --max-trades 1; then
        echo "✅ 交易执行成功"
    else
        echo "❌ 交易执行失败"
    fi
    
    # 计算下次执行时间
    next_run=$(date -d '+5 minutes' '+%Y-%m-%d %H:%M:%S')
    echo "⏰ 下次执行时间: $next_run"
    echo "😴 等待5分钟..."
    
    # 等待5分钟
    sleep 300
done
