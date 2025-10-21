#!/usr/bin/env python3
"""
自动交易调度器 - 每5分钟运行一次交易程序
"""

import subprocess
import time
import datetime
import os
import sys
from pathlib import Path

def run_trading_command():
    """运行交易命令"""
    try:
        # 获取当前脚本所在目录
        script_dir = Path(__file__).parent
        
        # 构建命令
        cmd = [
            "uv", "run", "main.py", 
            "--minutes", "5", 
            "--auto-trade", 
            "--max-trades", "1"
        ]
        
        print(f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始执行交易...")
        print(f"📋 命令: {' '.join(cmd)}")
        
        # 执行命令
        result = subprocess.run(
            cmd,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 输出结果
        if result.stdout:
            print("📤 输出:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  错误:")
            print(result.stderr)
        
        print(f"✅ 执行完成，退出码: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ 命令执行超时（5分钟）")
        return False
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 自动交易调度器启动")
    print("📅 每5分钟执行一次交易")
    print("🛑 按 Ctrl+C 停止")
    print("=" * 50)
    
    # 记录开始时间
    start_time = datetime.datetime.now()
    execution_count = 0
    
    try:
        while True:
            execution_count += 1
            print(f"\n🔄 第 {execution_count} 次执行")
            
            # 运行交易命令
            success = run_trading_command()
            
            if success:
                print("✅ 交易执行成功")
            else:
                print("❌ 交易执行失败")
            
            # 计算下次执行时间
            next_run = datetime.datetime.now() + datetime.timedelta(minutes=5)
            print(f"⏰ 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 等待5分钟
            print("😴 等待5分钟...")
            time.sleep(300)  # 300秒 = 5分钟
            
    except KeyboardInterrupt:
        print(f"\n🛑 调度器已停止")
        print(f"📊 总执行次数: {execution_count}")
        print(f"⏱️  运行时间: {datetime.datetime.now() - start_time}")
        print("👋 再见！")

if __name__ == "__main__":
    main()
