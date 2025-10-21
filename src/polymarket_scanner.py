from datetime import timedelta, datetime, timezone
import requests
import json
from .polymarket_tokenid import get_all_midpoints, get_multiple_markets
from .balance_checker import BalanceChecker
from typing import Optional, List


class PolymarketScanner:
    def __init__(self, trader: Optional[object] = None):
        self.base_url = "https://gamma-api.polymarket.com"
        self.trader = trader  # 可选的交易器实例，用于显示余额
        self.balance_checker = BalanceChecker()  # 初始化余额查询器
        
    def fetch_markets(self, limit=500):
        """获取所有活跃市场数据"""
        # 根据官方文档，使用events端点获取所有活跃市场，按ID排序获取最新的
        url = f"{self.base_url}/events?order=id&ascending=false&closed=false&limit={limit}"
        response = requests.get(url)
        data = response.json()

        # 同时获取体育赛事，因为体育赛事通常有更短的结束时间
        sports_url = f"{self.base_url}/events?closed=false&limit=200"
        sports_response = requests.get(sports_url)
        sports_data = sports_response.json()

        # 合并数据并去重
        all_markets = data + sports_data
        unique_markets = []
        seen_ids = set()
        for market in all_markets:
            if market['id'] not in seen_ids:
                unique_markets.append(market)
                seen_ids.add(market['id'])

        return unique_markets

    def get_markets_with_time(self, markets):
        """获取带有时间信息的市场列表"""
        markets_with_time = []
        current_time_utc = datetime.now(timezone.utc)
        
        for market in markets:
            try:
                # 使用UTC时间进行比较
                end_time_utc = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                
                if end_time_utc > current_time_utc:  # 只考虑未来的market
                    time_diff = end_time_utc - current_time_utc
                    markets_with_time.append((market, time_diff))
            except Exception as e:
                continue
                
        # 按时间差排序
        markets_with_time.sort(key=lambda x: x[1])
        return markets_with_time

    def format_time_difference(self, time_diff):
        """格式化时间差为可读格式"""
        total_seconds = time_diff.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟{seconds}秒"


    def get_short_term_markets(self, markets_with_time, max_hours=1):
        """获取短期结束的市场"""
        short_term_markets = []
        for market, time_diff in markets_with_time:
            if time_diff <= timedelta(hours=max_hours):
                short_term_markets.append((market, time_diff))
        return short_term_markets

    def get_market_data(self, market):
        """获取市场交易数据"""
        if 'markets' in market and market['markets']:
            try:
                tokenids = json.loads(market['markets'][0]['clobTokenIds'])
                no_token_id = tokenids[0]
                yes_token_id = tokenids[1]
                yes_mid, no_mid, yes_price, no_price, yes_book, no_book, yes_books, no_books = get_all_midpoints(yes_token_id, no_token_id)
                # 计算网站显示的价格 (1 - API价格)
                yes_price_display = 1.0 - float(yes_price['price'])
                no_price_display = 1.0 - float(no_price['price'])
                
                return {
                    'yes': {
                        'mid': yes_mid['mid'],
                        'price': yes_price_display,
                        'book': yes_book,
                        'books': yes_books
                    },
                    'no': {
                        'mid': no_mid['mid'],
                        'price': no_price_display,
                        'book': no_book,
                        'books': no_books
                    }
                }
            except Exception as e:
                return None
        return None

    def get_multiple_markets_data(self, markets):
        """批量获取多个市场的交易数据"""
        market_tokens = []
        valid_markets = []
        
        for market in markets:
            if 'markets' in market and market['markets']:
                try:
                    tokenids = json.loads(market['markets'][0]['clobTokenIds'])
                    no_token_id = tokenids[0]
                    yes_token_id = tokenids[1]
                    market_tokens.append((yes_token_id, no_token_id))
                    valid_markets.append(market)
                except Exception as e:
                    continue
        
        if not market_tokens:
            return []
        
        # 批量获取数据
        results = get_multiple_markets(market_tokens)
        
        # 组合结果
        market_data_list = []
        for i, (market, result) in enumerate(zip(valid_markets, results)):
            yes_mid, no_mid, yes_price, no_price, yes_book, no_book, yes_books, no_books = result
            
            # 计算网站显示的价格 (1 - API价格)
            yes_price_display = 1.0 - float(yes_price['price'])
            no_price_display = 1.0 - float(no_price['price'])
            
            market_data = {
                'market': market,
                'data': {
                    'yes': {
                        'mid': yes_mid['mid'],
                        'price': yes_price_display,
                        'book': yes_book,
                        'books': yes_books
                    },
                    'no': {
                        'mid': no_mid['mid'],
                        'price': no_price_display,
                        'book': no_book,
                        'books': no_books
                    }
                }
            }
            market_data_list.append(market_data)
        
        return market_data_list

    def scan_short_term_markets(self, max_hours=1, show_top_n=20):
        """扫描短期结束的市场"""
        print(f"当前时间: {datetime.now().isoformat()}")
        print(f"{max_hours}小时后: {(datetime.now() + timedelta(hours=max_hours)).isoformat()}")
        
        # 获取市场数据
        markets = self.fetch_markets()
        print(f"总共有 {len(markets)} 个market")
        

        
        # 获取带时间信息的市场
        markets_with_time = self.get_markets_with_time(markets)

        # 显示前N个最近结束的市场
        print(f"\n前{show_top_n}个最近结束的market:")
        for i, (market, time_diff) in enumerate(markets_with_time[:show_top_n]):
            time_str = self.format_time_difference(time_diff)
            print(f"{i+1}. {market['ticker']} - {market['title']}")
            print(f"   结束时间: {market['endDate']} (还有 {time_str})")
        
        # 查找短期市场
        print(f"\n查找{max_hours}小时内结束的market:")
        short_term_markets = self.get_short_term_markets(markets_with_time, max_hours)
        
        if short_term_markets:
            # 提取市场列表用于批量获取
            markets_list = [market for market, time_diff in short_term_markets]
            
            # 批量获取市场数据
            print(f"批量获取 {len(markets_list)} 个市场的交易数据...")
            market_data_list = self.get_multiple_markets_data(markets_list)
            
            # 创建市场数据映射
            market_data_map = {data['market']['ticker']: data['data'] for data in market_data_list}
            
            for market, time_diff in short_term_markets:
                time_str = self.format_time_difference(time_diff)
                print(f"找到{max_hours}小时内结束的market: {market['ticker']} - {market['title']}")
                print(f"结束时间: {market['endDate']} (还有 {time_str})")
                
                # 从批量获取的数据中获取市场数据
                market_data = market_data_map.get(market['ticker'])
                if market_data:
                    
                    print(f"yes : mid:{market_data['yes']['mid']} {market_data['yes']['price']} {market_data['yes']['book']} {market_data['yes']['books']}")
                    print(f"no : mid:{market_data['no']['mid']} {market_data['no']['price']} {market_data['no']['book']} {market_data['no']['books']}")
                else:
                    print("无法获取市场数据")
        else:
            print(f"没有找到{max_hours}小时内结束的market")
            if markets_with_time:
                time_str = self.format_time_difference(markets_with_time[0][1])
                print(f"最近的market将在 {time_str} 后结束")
            else:
                print("没有找到任何未来的market")
        
        # 显示账户余额信息
        if self.trader and hasattr(self.trader, 'funder'):
            print(f"\n=== 账户余额信息 ===")
            self.balance_checker.print_balance_info(self.trader.funder, 1.0)
            print("==================")
        
        return short_term_markets
    
    def scan_near_end_markets(self, start_minutes: int = 4, end_minutes: int = 6, show_top_n: int = 20) -> List[tuple]:
        """
        扫描在指定时间范围内结束的市场（前4分钟开始分析策略）
        
        Args:
            start_minutes: 开始扫描的时间（分钟），默认4分钟
            end_minutes: 结束扫描的时间（分钟），默认6分钟
            show_top_n: 显示前N个市场
            
        Returns:
            在指定时间范围内结束的市场列表
        """
        print(f"=== 扫描{start_minutes}-{end_minutes}分钟内结束的市场 ===")
        print(f"策略: 在交易结束前4分钟开始分析")
        
        # 获取所有市场
        markets = self.fetch_markets()
        markets_with_time = self.get_markets_with_time(markets)
        
        # 筛选在指定时间范围内结束的市场
        near_end_markets = []
        
        # 如果开始和结束时间相同，使用一个合理的时间窗口
        if start_minutes == end_minutes:
            # 使用 ±1分钟的时间窗口
            time_window = 1
            actual_start = max(0, start_minutes - time_window)
            actual_end = start_minutes + time_window
            print(f"⚠️  开始和结束时间相同({start_minutes}分钟)，使用时间窗口: {actual_start}-{actual_end}分钟")
        else:
            actual_start = start_minutes
            actual_end = end_minutes
        
        for market, time_diff in markets_with_time:
            minutes_remaining = time_diff.total_seconds() / 60
            if actual_start <= minutes_remaining <= actual_end:
                near_end_markets.append((market, time_diff))
        
        # 显示结果
        if start_minutes == end_minutes:
            print(f"\n找到 {len(near_end_markets)} 个在{actual_start}-{actual_end}分钟内结束的市场:")
        else:
            print(f"\n找到 {len(near_end_markets)} 个在{start_minutes}-{end_minutes}分钟内结束的市场:")
        for i, (market, time_diff) in enumerate(near_end_markets[:show_top_n], 1):
            time_str = self.format_time_difference(time_diff)
            print(f"{i:2d}. {market['ticker']} - {market['title']}")
            print(f"   结束时间: {market['endDate']} (还有 {time_str})")
        
        # 显示账户余额信息
        if self.trader and hasattr(self.trader, 'funder'):
            print(f"\n=== 账户余额信息 ===")
            self.balance_checker.print_balance_info(self.trader.funder, 1.0)
            print("==================")
        
        return near_end_markets

    def scan_all_markets(self, show_top_n: int = 50) -> List[tuple]:
        """
        扫描所有未结束的市场

        Args:
            show_top_n: 显示前N个最近结束的市场

        Returns:
            所有未结束的市场列表
        """
        print("=== 扫描所有未结束的市场 ===")

        # 获取所有市场
        markets = self.fetch_markets()
        markets_with_time = self.get_markets_with_time(markets)

        # 显示前N个最近结束的市场
        print(f"\n前{show_top_n}个最近结束的market:")
        for i, (market, time_diff) in enumerate(markets_with_time[:show_top_n], 1):
            time_str = self.format_time_difference(time_diff)
            print(f"{i:2d}. {market['ticker']} - {market['title']}")
            print(f"   结束时间: {market['endDate']} (还有 {time_str})")

        # 显示账户余额信息
        if self.trader and hasattr(self.trader, 'funder'):
            print(f"\n=== 账户余额信息 ===")
            self.balance_checker.print_balance_info(self.trader.funder, 1.0)
            print("==================")

        return markets_with_time
