import asyncio
import aiohttp
from typing import Dict, Any, Tuple, List
import json
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BookParams


class AsyncPolymarketClient:
    """异步Polymarket客户端"""
    
    def __init__(self, base_url: str = "https://clob.polymarket.com"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def get_midpoint(self, token_id: str) -> Dict[str, Any]:
        """异步获取中间价"""
        url = f"{self.base_url}/midpoint"
        params = {"token_id": token_id}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to get midpoint: {response.status}")
    
    async def get_price(self, token_id: str, side: str = "BUY") -> Dict[str, Any]:
        """异步获取价格"""
        url = f"{self.base_url}/price"
        params = {"token_id": token_id, "side": side}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to get price: {response.status}")
    
    async def get_order_book(self, token_id: str) -> Dict[str, Any]:
        """异步获取订单簿"""
        url = f"{self.base_url}/book"
        params = {"token_id": token_id}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to get order book: {response.status}")
    
    async def get_order_books(self, token_ids: List[str]) -> List[Dict[str, Any]]:
        """异步批量获取订单簿"""
        url = f"{self.base_url}/books"
        params = {"token_ids": ",".join(token_ids)}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to get order books: {response.status}")


async def get_midpoint_async(client: AsyncPolymarketClient, token_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], int]:
    """异步获取单个token的所有数据"""
    try:
        # 并行获取所有数据
        mid_task = client.get_midpoint(token_id)
        price_task = client.get_price(token_id, side="BUY")
        book_task = client.get_order_book(token_id)
        
        # 等待所有任务完成
        mid, price, book = await asyncio.gather(mid_task, price_task, book_task)
        
        # 获取订单簿数量
        books = await client.get_order_books([token_id])
        
        return mid, price, book, len(books)
    except Exception as e:
        print(f"Async API failed for token {token_id}: {e}")
        # 回退到同步客户端
        try:
            sync_client = ClobClient("https://clob.polymarket.com")
            mid = sync_client.get_midpoint(token_id)
            price = sync_client.get_price(token_id, side="BUY")
            book = sync_client.get_order_book(token_id)
            books = sync_client.get_order_books([BookParams(token_id=token_id)])
            return mid, price, book.market, len(books)
        except Exception as sync_e:
            print(f"Sync fallback also failed for token {token_id}: {sync_e}")
            # 返回默认值
            return {"mid": "0"}, {"price": "0"}, {"market": "0"}, 0


async def get_all_midpoints_async(yes_token_id: str, no_token_id: str) -> Tuple:
    """异步获取yes和no token的所有数据"""
    async with AsyncPolymarketClient() as client:
        # 并行获取yes和no token的数据
        yes_task = get_midpoint_async(client, yes_token_id)
        no_task = get_midpoint_async(client, no_token_id)
        
        # 等待两个任务完成
        (yes_mid, yes_price, yes_book, yes_books), (no_mid, no_price, no_book, no_books) = await asyncio.gather(yes_task, no_task)
        
        return yes_mid, no_mid, yes_price, no_price, yes_book, no_book, yes_books, no_books


def get_all_midpoints(yes_token_id: str, no_token_id: str) -> Tuple:
    """同步接口，直接使用同步客户端（更稳定）"""
    try:
        client = ClobClient("https://clob.polymarket.com")
        
        # 获取yes token数据
        yes_mid = client.get_midpoint(yes_token_id)
        yes_price = client.get_price(yes_token_id, side="BUY")
        yes_book = client.get_order_book(yes_token_id)
        yes_books = client.get_order_books([BookParams(token_id=yes_token_id)])
        
        # 获取no token数据
        no_mid = client.get_midpoint(no_token_id)
        no_price = client.get_price(no_token_id, side="BUY")
        no_book = client.get_order_book(no_token_id)
        no_books = client.get_order_books([BookParams(token_id=no_token_id)])
        
        return yes_mid, no_mid, yes_price, no_price, yes_book.market, no_book.market, len(yes_books), len(no_books)
    except Exception as e:
        print(f"Error getting market data: {e}")
        # 返回默认值
        return (
            {"mid": "0"}, {"mid": "0"}, 
            {"price": "0"}, {"price": "0"}, 
            {"market": "0"}, {"market": "0"}, 
            0, 0
        )


async def get_multiple_markets_async(market_tokens: List[Tuple[str, str]]) -> List[Tuple]:
    """异步批量获取多个市场的数据"""
    async with AsyncPolymarketClient() as client:
        tasks = []
        for yes_token_id, no_token_id in market_tokens:
            task = get_all_midpoints_async(yes_token_id, no_token_id)
            tasks.append(task)
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing market {i}: {result}")
                # 返回默认值
                processed_results.append((
                    {"mid": "0"}, {"mid": "0"}, 
                    {"price": "0"}, {"price": "0"}, 
                    {"market": "0"}, {"market": "0"}, 
                    0, 0
                ))
            else:
                processed_results.append(result)
        
        return processed_results


def get_multiple_markets(market_tokens: List[Tuple[str, str]]) -> List[Tuple]:
    """同步接口，批量获取多个市场数据"""
    results = []
    client = ClobClient("https://clob.polymarket.com")
    
    for yes_token_id, no_token_id in market_tokens:
        try:
            # 获取yes token数据
            yes_mid = client.get_midpoint(yes_token_id)
            yes_price = client.get_price(yes_token_id, side="BUY")
            yes_book = client.get_order_book(yes_token_id)
            yes_books = client.get_order_books([BookParams(token_id=yes_token_id)])
            
            # 获取no token数据
            no_mid = client.get_midpoint(no_token_id)
            no_price = client.get_price(no_token_id, side="BUY")
            no_book = client.get_order_book(no_token_id)
            no_books = client.get_order_books([BookParams(token_id=no_token_id)])
            
            results.append((yes_mid, no_mid, yes_price, no_price, yes_book.market, no_book.market, len(yes_books), len(no_books)))
        except Exception as e:
            print(f"Error getting data for market {yes_token_id}/{no_token_id}: {e}")
            # 添加默认值
            results.append((
                {"mid": "0"}, {"mid": "0"}, 
                {"price": "0"}, {"price": "0"}, 
                {"market": "0"}, {"market": "0"}, 
                0, 0
            ))
    
    return results


async def main():
    """测试异步功能"""
    yes_token_id = "3213896807609151356983200973907978744783690841747971638399173106356363051321"
    no_token_id = "10600610012239123092489783310300542814410069056808404652512661555366785875656"
    
    print("测试单个市场异步获取:")
    start_time = asyncio.get_event_loop().time()
    
    yes_mid, no_mid, yes_price, no_price, yes_book, no_book, yes_books, no_books = await get_all_midpoints_async(yes_token_id, no_token_id)
    
    end_time = asyncio.get_event_loop().time()
    print(f"单个市场获取耗时: {end_time - start_time:.2f}秒")
    
    # 计算价格
    yes_price_calc = 1.0 - float(yes_price['price'])
    no_price_calc = 1.0 - float(no_price['price'])
    
    print(f"yes : mid:{yes_mid['mid']} {yes_price_calc} {yes_book} {yes_books}")
    print(f"no : mid:{no_mid['mid']} {no_price_calc} {no_book} {no_books}")
    
    print("\n测试批量市场异步获取:")
    # 测试批量获取
    market_tokens = [
        (yes_token_id, no_token_id),
        (yes_token_id, no_token_id),  # 重复测试
    ]
    
    start_time = asyncio.get_event_loop().time()
    results = await get_multiple_markets_async(market_tokens)
    end_time = asyncio.get_event_loop().time()
    
    print(f"批量获取{len(market_tokens)}个市场耗时: {end_time - start_time:.2f}秒")
    print(f"成功获取 {len(results)} 个市场数据")


if __name__ == "__main__":
    asyncio.run(main())
