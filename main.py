import argparse
import os
from src.polymarket_scanner import PolymarketScanner
from src.auto_trader import AutoTrader
from src.manual_trader import ManualTrader


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Polymarket短期市场扫描器和自动交易器')
    parser.add_argument('--hours', type=float, default=1.0, help='扫描多少小时内结束的市场 (默认: 1.0)')
    parser.add_argument('--top', type=int, default=20, help='显示前N个最近结束的市场 (默认: 20)')
    parser.add_argument('--minutes', type=int, help='扫描多少分钟内结束的市场 (优先级高于hours)')
    parser.add_argument('--start-minutes', type=int, help='扫描开始时间（分钟）')
    parser.add_argument('--end-minutes', type=int, help='扫描结束时间（分钟）')
    parser.add_argument('--all-markets', action='store_true', help='扫描所有未结束的市场')
    parser.add_argument('--auto-trade', action='store_true', help='启用自动交易模式')
    parser.add_argument('--manual-trade', action='store_true', help='启用手动交易模式')
    parser.add_argument('--max-trades', type=int, default=3, help='最大交易次数 (默认: 3)')
    parser.add_argument('--strategy', choices=['conservative', 'moderate', 'aggressive'], 
                       default='moderate', help='交易策略 (默认: moderate)')
    parser.add_argument('--test-only', action='store_true', help='仅测试模式，不执行实际交易')
    
    args = parser.parse_args()
    
    # 确定扫描范围
    if args.all_markets:
        max_hours = None  # None表示扫描所有市场
        print("扫描所有未结束的市场...")
    elif args.start_minutes and args.end_minutes:
        # 使用新的时间范围参数
        max_hours = None  # 特殊标记，使用scan_near_end_markets
        print(f"扫描 {args.start_minutes}-{args.end_minutes} 分钟内结束的市场...")
    elif args.minutes:
        max_hours = args.minutes / 60.0
        print(f"扫描 {args.minutes} 分钟内结束的市场...")
    else:
        max_hours = args.hours
        print(f"扫描 {max_hours} 小时内结束的市场...")
    
    if args.auto_trade:
        # 自动交易模式
        if args.test_only:
            print("=== 自动交易模式 (测试模式) ===")
            print("🧪 测试模式: 将检查余额和授权，但不执行实际交易")
        else:
            print("=== 自动交易模式 ===")

        # 检查是否配置了私钥
        if not os.getenv('PRIVATE_KEY'):
            print("❌ 自动交易需要配置PRIVATE_KEY环境变量")
            print("请复制 config.example.env 为 .env 并配置您的私钥")
            return

        try:
            auto_trader = AutoTrader()
            auto_trader.current_strategy = args.strategy
            auto_trader.auto_trade_enabled = True
            auto_trader.test_only = args.test_only  # 设置测试模式

            # 运行自动交易循环
            if args.start_minutes and args.end_minutes:
                auto_trader.auto_trade_loop(max_hours=None, max_trades=args.max_trades, start_minutes=args.start_minutes, end_minutes=args.end_minutes)
            else:
                auto_trader.auto_trade_loop(max_hours=max_hours, max_trades=args.max_trades)

        except Exception as e:
            print(f"❌ 自动交易失败: {e}")
            print("请检查您的配置和网络连接")
    
    elif args.manual_trade:
        # 手动交易模式
        if args.test_only:
            print("=== 手动交易模式 (测试模式) ===")
            print("🧪 测试模式: 将检查余额和授权，但不执行实际交易")
        else:
            print("=== 手动交易模式 ===")

        # 检查是否配置了私钥
        if not os.getenv('PRIVATE_KEY'):
            print("❌ 手动交易需要配置PRIVATE_KEY环境变量")
            print("请复制 config.example.env 为 .env 并配置您的私钥")
            return

        try:
            manual_trader = ManualTrader()
            manual_trader.test_only = args.test_only  # 设置测试模式

            # 启动交互式交易
            manual_trader.interactive_trading(max_hours=max_hours)

        except Exception as e:
            print(f"❌ 手动交易失败: {e}")
            print("请检查您的配置和网络连接")
    
    else:
        # 扫描模式
        print("=== 扫描模式 ===")
        scanner = PolymarketScanner()
        
        if max_hours is None:
            # 扫描所有市场
            all_markets = scanner.scan_all_markets(show_top_n=args.top)
            print(f"\n总结: 找到 {len(all_markets)} 个未结束的市场")
        else:
            # 扫描短期市场
            short_term_markets = scanner.scan_short_term_markets(
                max_hours=max_hours, 
                show_top_n=args.top
            )
            print(f"\n总结: 找到 {len(short_term_markets)} 个{max_hours}小时内结束的市场")
        
        if not args.auto_trade and not args.manual_trade:
            print("\n💡 提示:")
            print("  - 使用 --auto-trade 参数启用自动交易模式")
            print("  - 使用 --manual-trade 参数启用手动交易模式")
            print("  - 使用 --all-markets 参数扫描所有未结束的市场")


if __name__ == "__main__":
    main()
