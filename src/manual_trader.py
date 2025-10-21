#!/usr/bin/env python3
"""
手动交易器 - 提供交互式交易界面
"""

import os
import json
from typing import Dict, Any, List
from datetime import timedelta
from src.polymarket_scanner import PolymarketScanner
from src.polymarket_trader import PolymarketTrader
from src.balance_checker import BalanceChecker


class ManualTrader:
    """手动交易器"""
    
    def __init__(self):
        """初始化手动交易器"""
        self.trader = PolymarketTrader()
        self.scanner = PolymarketScanner(trader=self.trader)  # 传递trader给scanner
        self.balance_checker = BalanceChecker()  # 初始化余额查询器
        
        # 从环境变量读取配置
        self.trade_size = float(os.getenv('TRADE_AMOUNT', '1.0'))  # 从环境变量读取交易金额
        self.slippage = 0.01   # 固定1%滑点
        self.test_only = False  # 测试模式标志
        
        # 价格范围配置
        self.min_price_range = float(os.getenv('MIN_PRICE_RANGE', '0.90'))  # 最小价格范围
        self.max_price_range = float(os.getenv('MAX_PRICE_RANGE', '0.98'))  # 最大价格范围
    
    def interactive_trading(self, max_hours: float = 1.0):
        """交互式交易界面"""
        if self.test_only:
            print("=== 手动交易模式 (测试模式) ===")
            print("🧪 测试模式: 将检查余额和授权，但不执行实际交易")
        else:
            print("=== 手动交易模式 ===")
        print(f"每笔交易固定: {self.trade_size}USD, 滑点: {self.slippage*100:.1f}%")
        print(f"策略: 只购买价格在{self.min_price_range}-{self.max_price_range}范围内的一方")
        print("输入 'q' 退出, 'r' 刷新市场列表")
        print("-" * 50)
        
        while True:
            try:
                # 扫描市场
                if max_hours is None:
                    print("扫描所有未结束的市场...")
                    markets = self.scanner.scan_all_markets(show_top_n=20)
                else:
                    print(f"扫描 {max_hours} 小时内的市场...")
                    markets = self.scanner.scan_short_term_markets(max_hours=max_hours, show_top_n=10)
                
                if not markets:
                    print("没有找到合适的市场")
                    continue
                
                # 显示账户余额信息
                print(f"\n=== 账户余额信息 ===")
                self.balance_checker.print_balance_info(self.trader.funder, self.trade_size)
                print("==================")
                
                # 显示市场列表
                self.display_markets(markets)
                
                # 获取用户输入
                choice = input("\n请选择市场编号 (1-{}), 或输入 'q' 退出, 'r' 刷新: ".format(len(markets)))
                
                if choice.lower() == 'q':
                    print("退出手动交易模式")
                    break
                elif choice.lower() == 'r':
                    continue
                
                try:
                    market_index = int(choice) - 1
                    if 0 <= market_index < len(markets):
                        market, time_diff = markets[market_index]
                        self.trade_market(market, time_diff)
                    else:
                        print("无效的市场编号")
                except ValueError:
                    print("请输入有效的数字")
                    
            except KeyboardInterrupt:
                print("\n退出手动交易模式")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
    
    def display_markets(self, markets: List[tuple]):
        """显示市场列表"""
        print("\n=== 可交易市场列表 ===")
        print(f"每笔交易: {self.trade_size}USD, 滑点: {self.slippage*100:.1f}%")
        print("-" * 80)
        
        for i, (market, time_diff) in enumerate(markets, 1):
            # 获取市场数据
            market_data = self.scanner.get_market_data(market)
            
            # 格式化时间
            total_seconds = time_diff.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            if hours > 0:
                time_str = f"{hours}小时{minutes}分钟"
            else:
                time_str = f"{minutes}分钟{seconds}秒"
            
            print(f"{i:2d}. {market['ticker']}")
            print(f"    标题: {market['title']}")
            print(f"    剩余时间: {time_str}")
            
            if market_data:
                yes_mid = float(market_data['yes']['mid'])
                no_mid = float(market_data['no']['mid'])
                
                print(f"    YES价格: {yes_mid:.3f} | NO价格: {no_mid:.3f}")
                
            # 简化的交易策略：检查价格是否在配置的范围内
            yes_in_range = self.min_price_range <= yes_mid <= self.max_price_range
            no_in_range = self.min_price_range <= no_mid <= self.max_price_range
            
            if yes_in_range and not no_in_range:
                print(f"    🎯 建议: 买入Up (YES价格在{self.min_price_range}-{self.max_price_range}范围内)")
            elif no_in_range and not yes_in_range:
                print(f"    🎯 建议: 买入Down (NO价格在{self.min_price_range}-{self.max_price_range}范围内)")
            elif yes_in_range and no_in_range:
                if yes_mid >= no_mid:
                    print(f"    🎯 建议: 买入Up (YES和NO都在范围内，YES价格更高)")
                else:
                    print(f"    🎯 建议: 买入Down (YES和NO都在范围内，NO价格更高)")
            else:
                print(f"    ⏸️  建议: 不交易 (价格不在{self.min_price_range}-{self.max_price_range}范围内)")
        else:
            print(f"    市场数据: 无法获取")
        
        print()
    
    
    def trade_market(self, market: Dict[str, Any], time_diff: timedelta) -> Dict[str, Any]:
        """
        交易指定市场
        
        Args:
            market: 市场信息
            time_diff: 剩余时间
            
        Returns:
            交易结果
        """
        try:
            # 获取token ID
            if 'markets' not in market or not market['markets']:
                return {'success': False, 'error': '无法获取token ID'}
            
            tokenids = json.loads(market['markets'][0]['clobTokenIds'])
            yes_token_id = tokenids[1]
            no_token_id = tokenids[0]
            
            # 获取用户选择
            side = input("选择交易方向 (YES/NO): ").strip().upper()
            
            if side not in ["YES", "NO"]:
                return {'success': False, 'error': '交易方向必须是YES或NO'}
            
            # 确定token ID和交易方向
            if side.upper() == "YES":
                token_id = yes_token_id
                side_str = "BUY"
            elif side.upper() == "NO":
                token_id = no_token_id
                side_str = "BUY"
            else:
                return {'success': False, 'error': '交易方向必须是YES或NO'}
            
            # 确定方向显示
            if side.upper() == "YES":
                direction_display = "Up"
            elif side.upper() == "NO":
                direction_display = "Down"
            else:
                direction_display = side
            
            if self.test_only:
                print(f"\n🧪 测试模式: 模拟交易:")
                print(f"  市场: {market['ticker']}")
                print(f"  方向: {side} (买入{direction_display})")
                print(f"  金额: {self.trade_size}USD")
                print(f"  滑点: {self.slippage*100:.1f}%")
                
                # 测试模式
                print(f"  ✅ 测试通过: 可以交易")
                result = {'test_mode': True, 'success': True, 'message': '测试通过'}
            else:
                print(f"\n执行交易:")
                print(f"  市场: {market['ticker']}")
                print(f"  方向: {side} (买入{direction_display})")
                print(f"  金额: {self.trade_size}USD")
                print(f"  滑点: {self.slippage*100:.1f}%")
                
                # 执行交易
                result = self.trader.place_market_order(
                    token_id, 
                    side_str, 
                    self.trade_size, 
                    self.slippage,
                    side.upper()  # 传递YES或NO作为token_type
                )
            
            return {
                'success': result is not None,
                'order': result,
                'market': market,
                'side': side
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """测试手动交易器"""
    try:
        manual_trader = ManualTrader()
        manual_trader.interactive_trading(max_hours=1.0)
    except Exception as e:
        print(f"手动交易器运行失败: {e}")


if __name__ == "__main__":
    main()
