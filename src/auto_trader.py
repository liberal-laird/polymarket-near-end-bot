import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import timedelta, datetime, timezone
from .polymarket_scanner import PolymarketScanner
from .polymarket_trader import PolymarketTrader
from .balance_checker import BalanceChecker


class AutoTrader:
    """自动交易器 - 结合扫描器和交易器"""
    
    def __init__(self, trader: Optional[PolymarketTrader] = None):
        """
        初始化自动交易器
        
        Args:
            trader: 交易器实例，如果为None则自动创建
        """
        self.trader = trader or PolymarketTrader()
        self.scanner = PolymarketScanner(trader=self.trader)  # 传递trader给scanner
        self.balance_checker = BalanceChecker()  # 初始化余额查询器
        
        # 从环境变量读取交易配置
        self.auto_trade_enabled = os.getenv('AUTO_TRADE_ENABLED', 'false').lower() == 'true'
        self.default_trade_size = float(os.getenv('TRADE_AMOUNT', '1.0'))  # 从环境变量读取交易金额
        self.max_trade_size = float(os.getenv('TRADE_AMOUNT', '1.0'))      # 最大交易大小
        self.trade_slippage = 0.01  # 固定1%滑点
        self.min_time_remaining = int(os.getenv('MIN_TIME_REMAINING_MINUTES', '1'))  # 最少剩余1分钟
        
        # 价格范围配置
        self.min_price_range = float(os.getenv('MIN_PRICE_RANGE', '0.90'))  # 最小价格范围
        self.max_price_range = float(os.getenv('MAX_PRICE_RANGE', '0.98'))  # 最大价格范围
        
        # 交易配置 - 固定1USD和1%滑点
        self.current_strategy = os.getenv('TRADE_STRATEGY', 'moderate')
        self.test_only = False  # 测试模式标志
    
    def analyze_market_opportunity(self, market: Dict[str, Any], time_diff: timedelta) -> Dict[str, Any]:
        """
        分析市场机会
        
        Args:
            market: 市场数据
            time_diff: 剩余时间
            
        Returns:
            分析结果
        """
        analysis = {
            'market': market,
            'time_remaining': time_diff,
            'opportunity_score': 0,
            'recommendation': 'HOLD',
            'trade_size': 0,
            'reason': ''
        }
        
        try:
            # 计算剩余时间（分钟）
            minutes_remaining = time_diff.total_seconds() / 60
            
            # 获取市场数据
            market_data = self.scanner.get_market_data(market)
            if not market_data:
                analysis['reason'] = '无法获取市场数据'
                return analysis
            
            yes_mid = float(market_data['yes']['mid'])
            no_mid = float(market_data['no']['mid'])
            
            # 简化的交易策略：只检查价格是否在配置的范围内
            analysis['opportunity_score'] = 0  # 不再使用复杂的机会分数
            
            # 检查是否有价格在配置的范围内
            yes_in_range = self.min_price_range <= yes_mid <= self.max_price_range
            no_in_range = self.min_price_range <= no_mid <= self.max_price_range
            
            # 生成建议 - 只购买价格在配置范围内的一方
            if minutes_remaining >= self.min_time_remaining:
                if yes_in_range and not no_in_range:
                    # 只有YES价格在范围内，买入YES (Up)
                    analysis['recommendation'] = 'BUY_YES'
                    analysis['trade_size'] = self.default_trade_size
                    analysis['reason'] = f'YES价格{yes_mid:.3f}在{self.min_price_range}-{self.max_price_range}范围内，买入Up，剩余时间{minutes_remaining:.1f}分钟'
                elif no_in_range and not yes_in_range:
                    # 只有NO价格在范围内，买入NO (Down)
                    analysis['recommendation'] = 'BUY_NO'
                    analysis['trade_size'] = self.default_trade_size
                    analysis['reason'] = f'NO价格{no_mid:.3f}在{self.min_price_range}-{self.max_price_range}范围内，买入Down，剩余时间{minutes_remaining:.1f}分钟'
                elif yes_in_range and no_in_range:
                    # 两个价格都在范围内，选择价格更高的
                    if yes_mid >= no_mid:
                        analysis['recommendation'] = 'BUY_YES'
                        analysis['trade_size'] = self.default_trade_size
                        analysis['reason'] = f'YES价格{yes_mid:.3f}和NO价格{no_mid:.3f}都在{self.min_price_range}-{self.max_price_range}范围内，YES价格更高，买入Up，剩余时间{minutes_remaining:.1f}分钟'
                    else:
                        analysis['recommendation'] = 'BUY_NO'
                        analysis['trade_size'] = self.default_trade_size
                        analysis['reason'] = f'YES价格{yes_mid:.3f}和NO价格{no_mid:.3f}都在{self.min_price_range}-{self.max_price_range}范围内，NO价格更高，买入Down，剩余时间{minutes_remaining:.1f}分钟'
                else:
                    # 没有价格在范围内
                    analysis['reason'] = f'YES价格{yes_mid:.3f}和NO价格{no_mid:.3f}都不在{self.min_price_range}-{self.max_price_range}范围内'
            else:
                analysis['reason'] = f'剩余时间不足({minutes_remaining:.1f}分钟 < {self.min_time_remaining}分钟)'
            
        except Exception as e:
            analysis['reason'] = f'分析失败: {e}'
        
        return analysis
    
    def scan_and_analyze(self, max_hours: float = 1.0, start_minutes: Optional[int] = None, end_minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        扫描并分析市场机会
        
        Args:
            max_hours: 扫描的最大时间范围，None表示扫描所有市场
            start_minutes: 开始扫描时间（分钟）
            end_minutes: 结束扫描时间（分钟）
            
        Returns:
            分析结果列表
        """
        if start_minutes is not None and end_minutes is not None:
            print(f"扫描 {start_minutes}-{end_minutes} 分钟内结束的市场机会...")
            # 使用新的时间范围扫描
            target_markets = self.scanner.scan_near_end_markets(start_minutes, end_minutes)
        elif max_hours is None:
            print("扫描所有未结束的市场机会...")
            # 获取所有市场
            markets = self.scanner.fetch_markets()
            markets_with_time = self.scanner.get_markets_with_time(markets)
            target_markets = markets_with_time
        else:
            print(f"扫描 {max_hours} 小时内的市场机会...")
            # 获取短期市场
            markets = self.scanner.fetch_markets()
            markets_with_time = self.scanner.get_markets_with_time(markets)
            target_markets = self.scanner.get_short_term_markets(markets_with_time, max_hours)
        
        opportunities = []
        
        for market, time_diff in target_markets:
            try:
                analysis = self.analyze_market_opportunity(market, time_diff)
                opportunities.append(analysis)
            except Exception as e:
                print(f"⚠️ 分析市场失败 {market.get('ticker', 'Unknown')}: {e}")
                # 添加一个失败的分析结果
                opportunities.append({
                    'market': market,
                    'time_remaining': time_diff,
                    'opportunity_score': 0,
                    'recommendation': 'HOLD',
                    'trade_size': 0,
                    'reason': f'分析失败: {e}'
                })
        
        # 按机会分数排序
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        # 显示账户余额信息
        print(f"\n=== 账户余额信息 ===")
        self.balance_checker.print_balance_info(self.trader.funder, self.default_trade_size)
        print("==================")
        
        return opportunities
    
    def execute_trade(self, analysis: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """
        执行交易（带重试机制）
        
        Args:
            analysis: 市场分析结果
            max_retries: 最大重试次数
            
        Returns:
            交易结果
        """
        if not self.auto_trade_enabled:
            return {'success': False, 'error': '自动交易未启用'}
        
        market = analysis['market']
        recommendation = analysis['recommendation']
        trade_size = analysis['trade_size']
        
        if recommendation == 'HOLD':
            return {'success': False, 'error': '不建议交易'}
        
        for attempt in range(max_retries + 1):
            try:
                # 获取token ID
                if 'markets' not in market or not market['markets']:
                    return {'success': False, 'error': '无法获取token ID'}
                
                tokenids = json.loads(market['markets'][0]['clobTokenIds'])
                # 注意：Polymarket的token ID映射可能与预期相反
                # tokenids[0] 通常是 NO token (Down)
                # tokenids[1] 通常是 YES token (Up)
                no_token_id = tokenids[0]   # Down token
                yes_token_id = tokenids[1]  # Up token
                
                # 执行交易
                result = None
                if recommendation == 'BUY_YES':
                    result = self.trader.place_market_order(
                        yes_token_id, 
                        "BUY", 
                        trade_size, 
                        self.trade_slippage,
                        "YES"
                    )
                elif recommendation == 'BUY_NO':
                    result = self.trader.place_market_order(
                        no_token_id, 
                        "BUY", 
                        trade_size, 
                        self.trade_slippage,
                        "NO"
                    )
                else:
                    return {'success': False, 'error': f'未知交易建议: {recommendation}'}
                
                # 如果交易成功，返回结果
                if result is not None:
                    return {
                        'success': True,
                        'order': result,
                        'analysis': analysis,
                        'attempts': attempt + 1
                    }
                
                # 如果交易失败且还有重试机会
                if attempt < max_retries:
                    print(f"⚠️ 交易失败，2秒后重试 (第{attempt + 1}次尝试)...")
                    time.sleep(2)  # 等待2秒后重试
                else:
                    return {
                        'success': False,
                        'error': '交易失败，已达到最大重试次数',
                        'attempts': attempt + 1
                    }
                
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries and "no match" in error_msg.lower():
                    print(f"⚠️ 交易失败: {error_msg}")
                    print(f"⚠️ 2秒后重试 (第{attempt + 1}次尝试)...")
                    time.sleep(2)  # 等待2秒后重试
                else:
                    return {
                        'success': False,
                        'error': error_msg,
                        'attempts': attempt + 1
                    }
        
        return {'success': False, 'error': '交易失败，已达到最大重试次数'}
    
    def auto_trade_loop(self, max_hours: float = 1.0, max_trades: int = 5, start_minutes: Optional[int] = None, end_minutes: Optional[int] = None):
        """
        自动交易循环
        
        Args:
            max_hours: 扫描的最大时间范围
            max_trades: 最大交易次数
            start_minutes: 开始扫描时间（分钟）
            end_minutes: 结束扫描时间（分钟）
        """
        print("=== 自动交易循环开始 ===")
        print(f"策略: 简化策略 - 只购买价格在{self.min_price_range}-{self.max_price_range}范围内的一方")
        print(f"交易金额: {self.default_trade_size} USD")
        print(f"自动交易: {'启用' if self.auto_trade_enabled else '禁用'}")
        print(f"测试模式: {'启用' if self.test_only else '禁用'}")
        
        if not self.auto_trade_enabled:
            print("自动交易未启用，仅进行分析")
        elif self.test_only:
            print("🧪 测试模式启用 - 将检查余额和授权，但不执行实际交易")
        
        # 扫描和分析机会
        opportunities = self.scan_and_analyze(max_hours, start_minutes, end_minutes)
        
        print(f"\n找到 {len(opportunities)} 个市场机会:")
        
        trades_executed = 0
        
        for i, analysis in enumerate(opportunities[:10]):  # 只显示前10个
            market = analysis['market']
            recommendation = analysis['recommendation']
            reason = analysis['reason']
            
            print(f"\n{i+1}. {market['ticker']} - {market['title']}")
            print(f"   建议: {recommendation}")
            print(f"   原因: {reason}")
            
            # 如果启用自动交易且有机会
            if (self.auto_trade_enabled and 
                recommendation != 'HOLD' and 
                trades_executed < max_trades):
                
                if self.test_only:
                    print(f"   🧪 测试模式: 模拟交易...")
                    print(f"   ✅ 测试通过: 可以交易")
                else:
                    print(f"   执行交易...")
                    trade_result = self.execute_trade(analysis)
                    
                    if trade_result['success']:
                        attempts = trade_result.get('attempts', 1)
                        if attempts > 1:
                            print(f"   ✅ 交易成功! (经过{attempts}次尝试)")
                        else:
                            print(f"   ✅ 交易成功!")
                        trades_executed += 1
                    else:
                        attempts = trade_result.get('attempts', 1)
                        print(f"   ❌ 交易失败: {trade_result['error']} (尝试{attempts}次)")
        
        print(f"\n=== 交易总结 ===")
        print(f"执行交易: {trades_executed}/{max_trades}")
        print(f"分析机会: {len(opportunities)}")


def main():
    """测试自动交易器"""
    try:
        # 初始化自动交易器
        auto_trader = AutoTrader()
        
        # 运行自动交易循环
        auto_trader.auto_trade_loop(max_hours=0.5, max_trades=3)
        
    except Exception as e:
        print(f"自动交易器运行失败: {e}")


if __name__ == "__main__":
    main()
