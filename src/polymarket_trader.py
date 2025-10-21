import os
import json
from typing import Dict, Any, Optional, List
from decimal import Decimal
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, OpenOrderParams, MarketOrderArgs, BalanceAllowanceParams
from py_clob_client.order_builder.constants import BUY, SELL
from dotenv import load_dotenv

# 导入余额查询器
from .balance_checker import BalanceChecker

# 加载环境变量
load_dotenv()


class PolymarketTrader:
    """Polymarket交易器"""
    
    def __init__(self, private_key: Optional[str] = None, funder: Optional[str] = None, signature_type: Optional[int] = None):
        """
        初始化交易器
        
        Args:
            private_key: 私钥，如果为None则从环境变量读取
            funder: 资金地址，如果为None则从环境变量读取
            signature_type: 签名类型，如果为None则从环境变量读取
                           0: Standard EOA (MetaMask, 硬件钱包等)
                           1: Email/Magic wallet signatures (委托签名)
                           2: Browser wallet proxy signatures (代理合约)
        """
        self.private_key = private_key or os.getenv('PRIVATE_KEY')
        self.funder = funder or os.getenv('FUNDER')
        self.signature_type = signature_type or int(os.getenv('SIGNATURE_TYPE', '0'))
        
        if not self.private_key:
            raise ValueError("私钥未设置，请设置PRIVATE_KEY环境变量或传入private_key参数")
        
        if not self.funder:
            raise ValueError("资金地址未设置，请设置FUNDER环境变量或传入funder参数")
        
        # 验证签名类型
        if self.signature_type not in [0, 1, 2]:
            raise ValueError("签名类型必须是0、1或2")
        
        # 初始化客户端
        self.client = ClobClient(
            host="https://clob.polymarket.com",
            key=self.private_key,
            chain_id=int(os.getenv('CHAIN_ID', '137')),  # Polygon主网
            signature_type=self.signature_type,
            funder=self.funder  # Address that holds your funds
        )
        
        # 设置API凭据
        try:
            api_creds = self.client.create_or_derive_api_creds()
            # 直接传入ApiCreds对象
            self.client.set_api_creds(api_creds)
        except Exception as e:
            print(f"警告: 设置API凭据失败: {e}")
            print("某些功能可能不可用")
        
        # 从环境变量读取配置
        self.default_slippage = float(os.getenv('DEFAULT_SLIPPAGE', '0.01'))  # 从环境变量读取滑点
        self.max_order_size = float(os.getenv('MAX_ORDER_SIZE', '1.0'))  # 从环境变量读取最大订单大小
        self.min_order_size = float(os.getenv('MIN_ORDER_SIZE', '1.0'))  # 从环境变量读取最小订单大小
        
        # 初始化余额查询器
        self.balance_checker = BalanceChecker()
        
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            address = self.client.get_address()
            return {'address': address}
        except Exception as e:
            print(f"获取账户信息失败: {e}")
            return {}
    
    def get_usdc_balance(self) -> float:
        """获取USDC余额"""
        return self.balance_checker.get_balance_simple(self.funder)
    
    
    def approve_token(self, token_id: str, amount: float) -> bool:
        """授权token使用额度"""
        try:
            print(f"正在授权token {token_id}，金额: {amount}")
            result = self.client.approve_token(token_id, amount)
            print(f"授权成功: {result}")
            return True
        except Exception as e:
            print(f"授权失败: {e}")
            return False
    
    def get_usdc_token_id(self) -> str:
        """获取USDC token ID"""
        # 对于Polymarket，USDC通常使用特定的token ID
        # 这里返回一个更通用的USDC token ID
        return "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Polygon USDC
    
    def get_collateral_token_id(self) -> str:
        """获取抵押品token ID（通常是USDC）"""
        try:
            # 尝试从客户端获取抵押品地址
            collateral_address = self.client.get_collateral_address()
            return collateral_address
        except Exception as e:
            print(f"获取抵押品地址失败: {e}")
            # 尝试使用不同的USDC token ID
            try:
                # 使用Polymarket的USDC token ID (作为字符串)
                return "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            except:
                # 如果还是失败，返回一个通用的token ID
                return "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    
    def get_market_price(self, token_id: str, side: str = "BUY") -> Optional[float]:
        """获取市场价格"""
        try:
            price_data = self.client.get_price(token_id, side=side)
            if price_data and 'price' in price_data:
                # API返回的价格需要 1 - price 才是网站上显示的价格
                api_price = float(price_data['price'])
                website_price = 1.0 - api_price
                return website_price
            return None
        except Exception as e:
            print(f"获取市场价格失败 (token: {token_id}): {e}")
            return None
    
    def place_market_order(
        self,
        token_id: str,
        side: str,
        size: float,
        slippage: Optional[float] = None,
        token_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        下市价单
        
        Args:
            token_id: Token ID
            side: 买卖方向 ("BUY" 或 "SELL")
            size: 订单大小
            slippage: 滑点容忍度，如果为None则使用默认值
            token_type: Token类型 ("YES" 或 "NO")，用于显示方向
            
        Returns:
            订单结果字典，失败时返回None
        """
        try:
            # 验证参数
            if side not in ["BUY", "SELL"]:
                raise ValueError("side必须是'BUY'或'SELL'")
            
            if size < self.min_order_size:
                raise ValueError(f"订单大小 {size} 小于最小订单大小 {self.min_order_size}")
            
            if size > self.max_order_size:
                raise ValueError(f"订单大小 {size} 大于最大订单大小 {self.max_order_size}")
            
            # 使用默认滑点
            if slippage is None:
                slippage = self.default_slippage
            
            
            # 转换side为常量
            side_constant = BUY if side == "BUY" else SELL
            
            # 先检查订单簿是否有足够的流动性
            try:
                # 获取当前价格
                current_price = self.get_market_price(token_id, side)
                if current_price is None:
                    raise ValueError("无法获取市场价格，可能订单簿为空")
                
                print(f"当前市场价格: {current_price:.3f}")
            except Exception as e:
                print(f"⚠️ 价格检查失败: {e}")
                # 继续尝试下单，但记录警告
            
            # 创建市价单参数
            market_order_args = MarketOrderArgs(
                token_id=token_id,
                amount=size,
                side=side_constant,
                order_type=OrderType.FOK  # Fill or Kill - 立即成交或取消
            )
            
            # 创建签名订单
            signed_order = self.client.create_market_order(market_order_args)
            
            # 下订单
            result = self.client.post_order(signed_order, OrderType.FOK)
            
            # 确定交易方向显示
            # 在Polymarket的"Up or Down"市场中：
            # - 买入价格高的token通常显示为"Up"方向
            # - 买入价格低的token通常显示为"Down"方向
            if token_type:
                if side == "BUY":
                    if token_type == "YES":
                        direction_display = "买入Up"  # YES token
                    elif token_type == "NO":
                        direction_display = "买入Up"  # NO token，但显示为Up方向
                    else:
                        direction_display = f"买入{token_type}"
                else:
                    if token_type == "YES":
                        direction_display = "卖出Up"
                    elif token_type == "NO":
                        direction_display = "卖出Up"
                    else:
                        direction_display = f"卖出{token_type}"
            else:
                direction_display = side
            
            print(f"市价单下单成功:")
            print(f"  Token ID: {token_id}")
            print(f"  方向: {side} ({direction_display})")
            print(f"  大小: {size} USD")
            print(f"  滑点: {slippage*100:.1f}%")
            print(f"  订单类型: FOK (立即成交或取消)")
            print(f"  订单ID: {result.get('id', 'N/A')}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"下市价单失败: {error_msg}")
            
            # 提供更详细的错误信息
            if "no match" in error_msg.lower():
                print("💡 可能原因: 订单簿中没有足够的流动性或价格变化太快")
                print("💡 建议: 尝试稍后重试或检查市场是否仍然活跃")
            elif "insufficient balance" in error_msg.lower():
                print("💡 可能原因: 账户余额不足")
                print("💡 建议: 检查USDC余额和授权额度")
            elif "invalid signature" in error_msg.lower():
                print("💡 可能原因: 签名验证失败")
                print("💡 建议: 检查私钥和签名类型配置")
            elif "not enough balance" in error_msg.lower():
                print("💡 可能原因: 余额或授权不足")
                print("💡 建议: 检查USDC余额和token授权")
            
            return None
    
    
    def cancel_order(self, order_id: str) -> bool:
        """取消指定订单"""
        try:
            result = self.client.cancel(order_id)
            print(f"订单 {order_id} 取消成功: {result}")
            return True
        except Exception as e:
            print(f"取消订单失败: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """取消所有未成交订单"""
        try:
            result = self.client.cancel_all()
            print(f"取消所有订单成功: {result}")
            return True
        except Exception as e:
            print(f"取消所有订单失败: {e}")
            return False
    
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """获取所有未成交订单"""
        try:
            open_orders = self.client.get_orders(OpenOrderParams())
            return open_orders
        except Exception as e:
            print(f"获取未成交订单失败: {e}")
            return []
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态"""
        try:
            return self.client.get_order(order_id)
        except Exception as e:
            print(f"获取订单状态失败: {e}")
            return None
    
    def auto_trade_market(
        self, 
        market_data: Dict[str, Any], 
        trade_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据市场数据自动交易
        
        Args:
            market_data: 市场数据，包含token_id等信息
            trade_config: 交易配置，包含交易大小、方向等
            
        Returns:
            交易结果
        """
        try:
            token_id = market_data.get('token_id')
            side = trade_config.get('side', 'BUY')
            size = trade_config.get('size', 1.0)
            slippage = trade_config.get('slippage')
            
            if not token_id:
                raise ValueError("市场数据中缺少token_id")
            
            # 检查余额
            balance = self.get_balance(token_id)
            print(f"当前余额: {balance}")
            
            if side == "BUY" and balance < size:
                print(f"余额不足，需要 {size}，当前余额 {balance}")
                return {'success': False, 'error': '余额不足'}
            
            # 下订单
            result = self.place_market_order(token_id, side, size, slippage)
            
            return {
                'success': result is not None,
                'order': result,
                'market_data': market_data,
                'trade_config': trade_config
            }
            
        except Exception as e:
            print(f"自动交易失败: {e}")
            return {'success': False, 'error': str(e)}
    

    def print_trader_status(self):
        """打印交易器状态和配置"""
        print("\n=== 交易器状态 ===")
        account_info = self.get_account_info()
        print(f"账户地址: {account_info.get('address', 'N/A')}")
        print(f"资金地址: {self.funder}")
        
        # 显示签名类型说明
        signature_type_names = {
            0: "Standard EOA (MetaMask, 硬件钱包等)",
            1: "Email/Magic wallet (委托签名)",
            2: "Browser wallet proxy (代理合约)"
        }
        print(f"签名类型: {self.signature_type} - {signature_type_names.get(self.signature_type, '未知')}")

        # 显示USDC余额
        try:
            usdc_balance = self.get_usdc_balance()
            print(f"USDC余额: {usdc_balance:.6f} USD")
        except Exception as e:
            print(f"USDC余额: 查询失败 ({e})")

        print(f"默认滑点: {self.default_slippage*100:.1f}%")
        print(f"最大订单大小: {self.max_order_size} USD")
        print(f"最小订单大小: {self.min_order_size} USD")
        print(f"链ID: {os.getenv('CHAIN_ID', '137')}")
        print("====================")
    
    def print_balance_info(self):
        """打印余额信息"""
        self.balance_checker.print_balance_info(self.funder, self.min_order_size)


def main():
    """测试交易器功能"""
    try:
        # 初始化交易器
        trader = PolymarketTrader()
        
        # 打印交易器状态
        trader.print_trader_status()
        
        # 获取未成交订单
        print("\n=== 未成交订单 ===")
        open_orders = trader.get_open_orders()
        print(f"未成交订单数量: {len(open_orders)}")
        
        # 示例：获取市场数据并交易（需要有效的token_id）
        print("\n=== 交易示例 ===")
        print("注意：这是示例代码，需要有效的token_id才能实际交易")
        
        # 示例配置
        example_market_data = {
            'token_id': 'example_token_id',
            'ticker': 'example-market',
            'title': 'Example Market'
        }
        
        example_trade_config = {
            'side': 'BUY',
            'size': 1.0,
            'slippage': 0.01
        }
        
        print("示例交易配置:")
        print(f"  市场: {example_market_data['title']}")
        print(f"  方向: {example_trade_config['side']}")
        print(f"  大小: {example_trade_config['size']}")
        print(f"  滑点: {example_trade_config['slippage']*100:.1f}%")
        
    except Exception as e:
        print(f"初始化交易器失败: {e}")
        print("请检查.env文件中的配置")


if __name__ == "__main__":
    main()
