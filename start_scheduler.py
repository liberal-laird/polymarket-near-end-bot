#!/usr/bin/env python3
"""
启动调度器 - 提供简单的启动界面
"""

import os
import sys
import subprocess
from pathlib import Path

def show_menu():
    """显示菜单"""
    print("🚀 Polymarket自动交易调度器")
    print("=" * 40)
    print("1. 基础调度器 (简单版本)")
    print("2. 高级调度器 (推荐)")
    print("3. Shell脚本调度器")
    print("4. 单次执行测试")
    print("5. 查看配置")
    print("6. 退出")
    print("=" * 40)

def run_basic_scheduler():
    """运行基础调度器"""
    print("🚀 启动基础调度器...")
    subprocess.run([sys.executable, "auto_trader_scheduler.py"])

def run_advanced_scheduler():
    """运行高级调度器"""
    print("🚀 启动高级调度器...")
    subprocess.run([sys.executable, "advanced_scheduler.py"])

def run_shell_scheduler():
    """运行Shell脚本调度器"""
    print("🚀 启动Shell脚本调度器...")
    subprocess.run(["./run_auto_trader.sh"])

def run_single_test():
    """单次执行测试"""
    print("🧪 执行单次测试...")
    result = subprocess.run([
        "uv", "run", "main.py", 
        "--minutes", "5", 
        "--auto-trade", 
        "--max-trades", "1"
    ])
    print(f"执行完成，退出码: {result.returncode}")

def show_config():
    """显示配置"""
    config_file = Path("scheduler_config.json")
    if config_file.exists():
        print("📋 当前配置:")
        with open(config_file, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("❌ 配置文件不存在")

def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("请选择 (1-6): ").strip()
        
        if choice == "1":
            run_basic_scheduler()
        elif choice == "2":
            run_advanced_scheduler()
        elif choice == "3":
            run_shell_scheduler()
        elif choice == "4":
            run_single_test()
        elif choice == "5":
            show_config()
        elif choice == "6":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main()
