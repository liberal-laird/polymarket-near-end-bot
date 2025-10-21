#!/usr/bin/env python3
"""
余额查询器 - 专门用于查询Polygon网络上的USDC余额
"""

from typing import Dict, Any, Optional
import requests

# 尝试导入web3，如果没有安装则跳过
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class BalanceChecker:
    """余额查询器"""
    
    def __init__(self):
        """初始化余额查询器"""
        self.usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Polygon USDC合约地址
        self.rpc_endpoints = [
            "https://polygon-rpc.com",
            "https://rpc-mainnet.maticvigil.com",
            "https://polygon-mainnet.chainstacklabs.com"
        ]
        
        # USDC合约ABI（只需要balanceOf方法）
        self.usdc_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
    
    def get_usdc_balance(self, address: str) -> Dict[str, Any]:
        """
        获取指定地址的USDC余额
        
        Args:
            address: 要查询的地址
            
        Returns:
            包含余额信息的字典
        """
        if not WEB3_AVAILABLE:
            return {
                "address": address,
                "balance_usdc": 0.0,
                "balance_wei": 0,
                "status": "error",
                "error": "Web3库未安装"
            }
        
        for rpc_url in self.rpc_endpoints:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                if not w3.is_connected():
                    continue
                
                # 创建合约实例
                usdc_contract_instance = w3.eth.contract(
                    address=Web3.to_checksum_address(self.usdc_contract),
                    abi=self.usdc_abi
                )
                
                # 查询余额
                balance_wei = usdc_contract_instance.functions.balanceOf(
                    Web3.to_checksum_address(address)
                ).call()
                
                balance_usdc = balance_wei / 1e6  # USDC有6位小数
                
                return {
                    "address": address,
                    "balance_usdc": balance_usdc,
                    "balance_wei": balance_wei,
                    "status": "success",
                    "method": f"Web3 ({rpc_url})",
                    "contract": self.usdc_contract
                }
                
            except Exception as e:
                continue
        
        return {
            "address": address,
            "balance_usdc": 0.0,
            "balance_wei": 0,
            "status": "error",
            "error": "所有RPC端点都失败"
        }
    
    def get_balance_simple(self, address: str) -> float:
        """
        获取USDC余额的简化版本，只返回余额数值
        
        Args:
            address: 要查询的地址
            
        Returns:
            USDC余额（float）
        """
        result = self.get_usdc_balance(address)
        if result["status"] == "success":
            return result["balance_usdc"]
        else:
            return 0.0
    
    def print_balance_info(self, address: str, min_required: float = 1.0):
        """
        打印余额信息
        
        Args:
            address: 要查询的地址
            min_required: 最小需要的余额
        """
        result = self.get_usdc_balance(address)
        
        if result["status"] == "success":
            balance = result["balance_usdc"]
            print(f"💰 当前USDC余额: {balance:.6f} USD")
            
            if balance >= min_required:
                print(f"✅ 余额充足，可以进行交易")
            else:
                print(f"❌ 余额不足，需要至少 {min_required} USD")
        else:
            print(f"⚠️  余额查询失败: {result['error']}")
    
    def check_balance_sufficient(self, address: str, required_amount: float) -> bool:
        """
        检查余额是否足够
        
        Args:
            address: 要查询的地址
            required_amount: 需要的金额
            
        Returns:
            余额是否足够
        """
        balance = self.get_balance_simple(address)
        return balance >= required_amount
    
    def get_balance_status(self, address: str, required_amount: float = 1.0) -> Dict[str, Any]:
        """
        获取余额状态信息
        
        Args:
            address: 要查询的地址
            required_amount: 需要的金额
            
        Returns:
            包含余额状态的字典
        """
        result = self.get_usdc_balance(address)
        
        if result["status"] == "success":
            balance = result["balance_usdc"]
            return {
                "address": address,
                "balance": balance,
                "required": required_amount,
                "sufficient": balance >= required_amount,
                "status": "success"
            }
        else:
            return {
                "address": address,
                "balance": 0.0,
                "required": required_amount,
                "sufficient": False,
                "status": "error",
                "error": result["error"]
            }


def main():
    """测试余额查询器"""
    print("=== 余额查询器测试 ===")
    
    checker = BalanceChecker()
    
    # 测试地址
    test_address = "0x7e86A3FC28392CA607Ee519fA41F19C02CF77a1A"
    
    print(f"测试地址: {test_address}")
    
    # 测试完整查询
    print("\n1. 完整查询:")
    result = checker.get_usdc_balance(test_address)
    print(f"结果: {result}")
    
    # 测试简化查询
    print("\n2. 简化查询:")
    balance = checker.get_balance_simple(test_address)
    print(f"余额: {balance} USD")
    
    # 测试余额信息打印
    print("\n3. 余额信息打印:")
    checker.print_balance_info(test_address)
    
    # 测试余额检查
    print("\n4. 余额检查:")
    sufficient = checker.check_balance_sufficient(test_address, 1.0)
    print(f"1 USD交易: {'✅ 足够' if sufficient else '❌ 不足'}")
    
    # 测试余额状态
    print("\n5. 余额状态:")
    status = checker.get_balance_status(test_address, 1.0)
    print(f"状态: {status}")


if __name__ == "__main__":
    main()
