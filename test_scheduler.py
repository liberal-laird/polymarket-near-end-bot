#!/usr/bin/env python3
"""
测试调度器修复
"""

import json
import datetime
from advanced_scheduler import AutoTraderScheduler

def test_json_serialization():
    """测试JSON序列化"""
    print("🧪 测试JSON序列化...")
    
    scheduler = AutoTraderScheduler()
    
    # 添加一些测试数据
    scheduler.stats['start_time'] = datetime.datetime.now()
    scheduler.stats['execution_count'] = 1
    scheduler.stats['success_count'] = 1
    scheduler.stats['failure_count'] = 0
    
    try:
        scheduler.save_stats()
        print("✅ JSON序列化测试通过")
        
        # 验证文件内容
        with open('scheduler_stats.json', 'r') as f:
            data = json.load(f)
            print(f"📊 保存的统计信息: {data}")
        
    except Exception as e:
        print(f"❌ JSON序列化测试失败: {e}")

def test_config():
    """测试配置"""
    print("\n🧪 测试配置...")
    
    scheduler = AutoTraderScheduler()
    
    print(f"📋 当前配置:")
    for key, value in scheduler.config.items():
        print(f"  {key}: {value}")
    
    if scheduler.config['test_mode'] == False:
        print("✅ 测试模式已关闭")
    else:
        print("❌ 测试模式仍然开启")

def test_command_building():
    """测试命令构建"""
    print("\n🧪 测试命令构建...")
    
    scheduler = AutoTraderScheduler()
    
    # 模拟命令构建
    cmd = [
        "uv", "run", "main.py", 
        "--minutes", str(scheduler.config["scan_minutes"]), 
        "--auto-trade", 
        "--max-trades", str(scheduler.config["max_trades"])
    ]
    
    if scheduler.config["test_mode"]:
        cmd.append("--test-only")
    
    print(f"📋 构建的命令: {' '.join(cmd)}")
    
    if "--test-only" not in cmd:
        print("✅ 命令中不包含--test-only参数")
    else:
        print("❌ 命令中仍然包含--test-only参数")

def main():
    """主函数"""
    print("🚀 调度器修复测试")
    print("=" * 40)
    
    test_json_serialization()
    test_config()
    test_command_building()
    
    print("\n✅ 所有测试完成")

if __name__ == "__main__":
    main()
