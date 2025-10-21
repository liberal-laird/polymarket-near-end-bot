#!/usr/bin/env python3
"""
高级自动交易调度器 - 每5分钟运行一次交易程序
支持日志记录、错误处理和配置管理
"""

import subprocess
import time
import datetime
import os
import sys
import json
import logging
from pathlib import Path

class AutoTraderScheduler:
    """自动交易调度器"""
    
    def __init__(self, config_file="scheduler_config.json"):
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / config_file
        self.log_file = self.script_dir / "scheduler.log"
        self.stats_file = self.script_dir / "scheduler_stats.json"
        
        # 默认配置
        self.config = {
            "interval_minutes": 5,
            "max_trades": 1,
            "scan_minutes": 5,
            "scan_start_minutes": 1,
            "scan_end_minutes": 6,
            "min_time_remaining": 1,
            "test_mode": False,
            "log_level": "INFO",
            "max_retries": 3,
            "retry_delay": 30
        }
        
        # 统计信息
        self.stats = {
            "start_time": None,
            "execution_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "last_execution": None,
            "last_success": None,
            "last_failure": None
        }
        
        self.setup_logging()
        self.load_config()
        self.load_stats()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, self.config["log_level"]),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_time_config(self, config):
        """验证时间配置是否被5整除"""
        # 只对调度间隔和扫描间隔要求被5整除，扫描时间窗口允许更灵活
        strict_time_params = ['interval_minutes', 'scan_minutes']
        flexible_time_params = ['scan_start_minutes', 'scan_end_minutes']
        
        # 严格验证调度相关参数
        for param in strict_time_params:
            if param in config and config[param] % 5 != 0:
                self.logger.warning(f"⚠️  {param} = {config[param]} 不被5整除，建议修改为5的倍数")
                # 自动调整为最接近的5的倍数
                adjusted_value = (config[param] // 5) * 5
                if adjusted_value == 0:
                    adjusted_value = 5
                config[param] = adjusted_value
                self.logger.info(f"✅ 已自动调整 {param} 为 {adjusted_value}")
        
        # 对扫描时间窗口只给出建议，不强制调整
        for param in flexible_time_params:
            if param in config and config[param] % 5 != 0:
                self.logger.info(f"ℹ️  {param} = {config[param]} 不是5的倍数，但扫描时间窗口允许灵活设置")
        
        return config

    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                # 验证时间配置
                self.config = self.validate_time_config(self.config)
                self.logger.info(f"配置已加载: {self.config_file}")
            except Exception as e:
                self.logger.warning(f"配置加载失败: {e}")
        else:
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置已保存: {self.config_file}")
        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")
    
    def load_stats(self):
        """加载统计信息"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats.update(json.load(f))
            except Exception as e:
                self.logger.warning(f"统计信息加载失败: {e}")
    
    def save_stats(self):
        """保存统计信息"""
        try:
            # 创建可序列化的统计信息副本
            serializable_stats = {}
            for key, value in self.stats.items():
                if isinstance(value, datetime.datetime):
                    serializable_stats[key] = value.isoformat()
                elif isinstance(value, datetime.timedelta):
                    serializable_stats[key] = str(value)
                else:
                    serializable_stats[key] = value
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"统计信息保存失败: {e}")
    
    def run_trading_command(self):
        """运行交易命令"""
        try:
            # 构建命令 - 使用新的时间范围参数
            cmd = [
                "uv", "run", "main.py", 
                "--start-minutes", str(self.config["scan_start_minutes"]), 
                "--end-minutes", str(self.config["scan_end_minutes"]), 
                "--auto-trade", 
                "--max-trades", str(self.config["max_trades"])
            ]
            
            if self.config["test_mode"]:
                cmd.append("--test-only")
            
            self.logger.info(f"执行命令: {' '.join(cmd)}")
            
            # 设置环境变量
            env = os.environ.copy()
            env['MIN_TIME_REMAINING_MINUTES'] = str(self.config['min_time_remaining'])
            
            # 执行命令
            result = subprocess.run(
                cmd,
                cwd=self.script_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 记录输出
            if result.stdout:
                self.logger.info(f"输出: {result.stdout}")
            
            if result.stderr:
                self.logger.warning(f"错误: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            self.logger.error("命令执行超时（5分钟）")
            return False
        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            return False
    
    def run_with_retry(self):
        """带重试的执行"""
        for attempt in range(self.config["max_retries"]):
            if attempt > 0:
                self.logger.info(f"第 {attempt + 1} 次尝试...")
                time.sleep(self.config["retry_delay"])
            
            success = self.run_trading_command()
            if success:
                return True
        
        return False
    
    def should_execute_now(self):
        """检查是否应该在当前时间执行"""
        now = datetime.datetime.now()
        minute = now.minute
        
        # 在15、30、45、0分钟的前4分钟执行
        target_minutes = [11, 26, 41, 56]  # 15-4=11, 30-4=26, 45-4=41, 60-4=56
        
        return minute in target_minutes
    
    def get_next_execution_time(self):
        """获取下次执行时间"""
        now = datetime.datetime.now()
        minute = now.minute
        
        # 目标执行分钟
        target_minutes = [11, 26, 41, 56]
        
        # 找到下一个目标时间
        for target in target_minutes:
            if minute < target:
                next_time = now.replace(minute=target, second=0, microsecond=0)
                return next_time
        
        # 如果当前时间已过所有目标，则等到下一个小时的11分钟
        next_hour = now.replace(hour=now.hour + 1, minute=11, second=0, microsecond=0)
        return next_hour

    def print_status(self):
        """打印状态信息"""
        print("\n" + "="*50)
        print("📊 调度器状态")
        print("="*50)
        print(f"⏰ 运行时间: {datetime.datetime.now() - self.stats['start_time']}")
        print(f"🔄 执行次数: {self.stats['execution_count']}")
        print(f"✅ 成功次数: {self.stats['success_count']}")
        print(f"❌ 失败次数: {self.stats['failure_count']}")
        if self.stats['last_execution']:
            print(f"🕐 上次执行: {self.stats['last_execution']}")
        if self.stats['last_success']:
            print(f"✅ 上次成功: {self.stats['last_success']}")
        if self.stats['last_failure']:
            print(f"❌ 上次失败: {self.stats['last_failure']}")
        print("="*50)
    
    def run(self):
        """运行调度器"""
        self.stats['start_time'] = datetime.datetime.now()
        self.save_stats()
        
        self.logger.info("🚀 自动交易调度器启动")
        self.logger.info("📅 执行时间: 每小时11、26、41、56分钟（15、30、45、0分钟前4分钟）")
        self.logger.info("🛑 按 Ctrl+C 停止")
        
        try:
            while True:
                # 检查是否应该执行
                if self.should_execute_now():
                    self.stats['execution_count'] += 1
                    self.stats['last_execution'] = datetime.datetime.now().isoformat()
                    
                    self.logger.info(f"🔄 第 {self.stats['execution_count']} 次执行")
                    
                    # 执行交易命令
                    success = self.run_with_retry()
                    
                    if success:
                        self.stats['success_count'] += 1
                        self.stats['last_success'] = datetime.datetime.now().isoformat()
                        self.logger.info("✅ 交易执行成功")
                    else:
                        self.stats['failure_count'] += 1
                        self.stats['last_failure'] = datetime.datetime.now().isoformat()
                        self.logger.error("❌ 交易执行失败")
                    
                    self.save_stats()
                    
                    # 执行后等待1分钟，避免重复执行
                    time.sleep(60)
                else:
                    # 等待到下次执行时间
                    next_time = self.get_next_execution_time()
                    wait_seconds = (next_time - datetime.datetime.now()).total_seconds()
                    
                    if wait_seconds > 0:
                        self.logger.info(f"⏰ 下次执行时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        self.logger.info(f"😴 等待 {wait_seconds/60:.1f} 分钟...")
                        time.sleep(wait_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 调度器已停止")
            self.print_status()
            self.logger.info("👋 再见！")

def main():
    """主函数"""
    scheduler = AutoTraderScheduler()
    scheduler.run()

if __name__ == "__main__":
    main()
