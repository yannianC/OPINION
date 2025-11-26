"""
OPINION 交易脚本
用于通过 OPINION CLOB SDK 进行预测市场交易和仓位管理
"""

import os
from dotenv import load_dotenv
from opinion_clob_sdk import Client
from opinion_clob_sdk.model import TopicStatusFilter, TopicType
from opinion_clob_sdk.chain.py_order_utils.model.order import PlaceOrderDataInput
from opinion_clob_sdk.chain.py_order_utils.model.sides import OrderSide
from opinion_clob_sdk.chain.py_order_utils.model.order_type import OrderType
from decimal import Decimal
import json


class OpinionTrader:
    """OPINION 交易客户端类"""
    
    def __init__(self):
        """初始化交易客户端"""
        # 加载环境变量
        load_dotenv()
        
        # 初始化客户端
        self.client = Client(
            host=os.getenv('OPINION_HOST', 'https://proxy.opinion.trade:8443'),
            apikey=os.getenv('OPINION_API_KEY'),
            chain_id=int(os.getenv('CHAIN_ID', '56')),  # BNB Chain mainnet
            rpc_url=os.getenv('RPC_URL'),
            private_key=os.getenv('PRIVATE_KEY'),
            multi_sig_addr=os.getenv('MULTI_SIG_ADDRESS'),
            conditional_tokens_addr=os.getenv('CONDITIONAL_TOKEN_ADDR', '0xAD1a38cEc043e70E83a3eC30443dB285ED10D774'),
            multisend_addr=os.getenv('MULTISEND_ADDR', '0x998739BFdAAdde7C933B942a68053933098f9EDa'),
            market_cache_ttl=300,  # 缓存市场数据5分钟
            quote_tokens_cache_ttl=3600  # 缓存报价代币1小时
        )
        
        print("✓ OPINION 交易客户端初始化成功!")
    
    def get_active_markets(self, limit=20):
        """
        获取活跃的市场列表
        
        Args:
            limit: 返回市场数量限制
            
        Returns:
            市场列表
        """
        print(f"\n📊 获取活跃市场 (限制: {limit})...")
        
        try:
            response = self.client.get_markets(
                status=TopicStatusFilter.ACTIVATED,
                page=1,
                limit=limit
            )
            
            if response.errno == 0:
                markets = response.result.list
                print(f"✓ 找到 {len(markets)} 个活跃市场")
                
                # 显示市场摘要
                for i, market in enumerate(markets, 1):
                    print(f"\n{i}. 市场ID: {market.id}")
                    print(f"   标题: {market.title}")
                    print(f"   类型: {market.type}")
                    print(f"   创建时间: {market.created_at}")
                    if hasattr(market, 'tokens') and market.tokens:
                        print(f"   代币数量: {len(market.tokens)}")
                
                return markets
            else:
                print(f"✗ 获取市场失败: {response.errmsg}")
                return []
                
        except Exception as e:
            print(f"✗ 获取市场异常: {str(e)}")
            return []
    
    def get_market_detail(self, market_id):
        """
        获取市场详情
        
        Args:
            market_id: 市场ID
            
        Returns:
            市场详情
        """
        print(f"\n🔍 获取市场详情 (ID: {market_id})...")
        
        try:
            response = self.client.get_market(market_id=market_id)
            
            if response.errno == 0:
                market = response.result
                print(f"✓ 市场: {market.title}")
                print(f"   描述: {market.description[:100]}..." if len(market.description) > 100 else f"   描述: {market.description}")
                print(f"   状态: {market.status}")
                print(f"   类型: {market.type}")
                
                if hasattr(market, 'tokens') and market.tokens:
                    print(f"\n   可交易代币:")
                    for token in market.tokens:
                        print(f"   - {token.name}: {token.token_id}")
                
                return market
            else:
                print(f"✗ 获取市场详情失败: {response.errmsg}")
                return None
                
        except Exception as e:
            print(f"✗ 获取市场详情异常: {str(e)}")
            return None
    
    def get_orderbook(self, token_id):
        """
        获取订单簿
        
        Args:
            token_id: 代币ID
            
        Returns:
            订单簿数据
        """
        print(f"\n📖 获取订单簿 (代币ID: {token_id})...")
        
        try:
            response = self.client.get_orderbook(token_id=token_id)
            
            if response.errno == 0:
                orderbook = response.result
                
                # 显示最佳买卖价
                if orderbook.bids:
                    best_bid = orderbook.bids[0]
                    print(f"✓ 最佳买价: {best_bid['price']} (数量: {best_bid['size']})")
                else:
                    print("  无买单")
                
                if orderbook.asks:
                    best_ask = orderbook.asks[0]
                    print(f"✓ 最佳卖价: {best_ask['price']} (数量: {best_ask['size']})")
                else:
                    print("  无卖单")
                
                return orderbook
            else:
                print(f"✗ 获取订单簿失败: {response.errmsg}")
                return None
                
        except Exception as e:
            print(f"✗ 获取订单簿异常: {str(e)}")
            return None
    
    def place_limit_order(self, market_id, token_id, side, price, amount):
        """
        下限价单
        
        Args:
            market_id: 市场ID
            token_id: 代币ID
            side: 订单方向 ('BUY' 或 'SELL')
            price: 价格 (字符串)
            amount: 数量 (以报价代币计算)
            
        Returns:
            订单结果
        """
        print(f"\n📝 下限价单...")
        print(f"   市场ID: {market_id}")
        print(f"   代币ID: {token_id}")
        print(f"   方向: {side}")
        print(f"   价格: {price}")
        print(f"   数量: {amount}")
        
        try:
            # 构建订单数据
            order_side = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            order_data = PlaceOrderDataInput(
                marketId=market_id,
                tokenId=token_id,
                side=order_side,
                orderType=OrderType.LIMIT_ORDER,
                price=str(price),
                makerAmountInQuoteToken=amount
            )
            
            # 下单
            result = self.client.place_order(order_data)
            
            if result.errno == 0:
                print(f"✓ 订单已提交")
                print(f"   订单ID: {result.result.order_id if hasattr(result.result, 'order_id') else 'N/A'}")
                return result
            else:
                print(f"✗ 下单失败: {result.errmsg}")
                return None
                
        except Exception as e:
            print(f"✗ 下单异常: {str(e)}")
            return None
    
    def place_market_order(self, market_id, token_id, side, amount):
        """
        下市价单
        
        Args:
            market_id: 市场ID
            token_id: 代币ID
            side: 订单方向 ('BUY' 或 'SELL')
            amount: 数量
            
        Returns:
            订单结果
        """
        print(f"\n📝 下市价单...")
        print(f"   市场ID: {market_id}")
        print(f"   代币ID: {token_id}")
        print(f"   方向: {side}")
        print(f"   数量: {amount}")
        
        try:
            order_side = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            order_data = PlaceOrderDataInput(
                marketId=market_id,
                tokenId=token_id,
                side=order_side,
                orderType=OrderType.MARKET_ORDER,
                makerAmountInQuoteToken=amount
            )
            
            result = self.client.place_order(order_data)
            
            if result.errno == 0:
                print(f"✓ 市价单已提交")
                return result
            else:
                print(f"✗ 下单失败: {result.errmsg}")
                return None
                
        except Exception as e:
            print(f"✗ 下单异常: {str(e)}")
            return None
    
    def get_my_positions(self, limit=50):
        """
        获取我的持仓
        
        Args:
            limit: 返回持仓数量限制
            
        Returns:
            持仓列表
        """
        print(f"\n💼 获取我的持仓 (限制: {limit})...")
        
        try:
            response = self.client.get_my_positions(limit=limit)
            
            if response.errno == 0:
                positions = response.result.list
                print(f"✓ 找到 {len(positions)} 个持仓")
                
                # 显示持仓摘要
                for i, pos in enumerate(positions, 1):
                    print(f"\n{i}. 市场ID: {pos.market_id}")
                    print(f"   代币ID: {pos.token_id}")
                    print(f"   持仓数量: {pos.position}")
                    if hasattr(pos, 'avg_price'):
                        print(f"   平均价格: {pos.avg_price}")
                    if hasattr(pos, 'unrealized_pnl'):
                        print(f"   未实现盈亏: {pos.unrealized_pnl}")
                
                return positions
            else:
                print(f"✗ 获取持仓失败: {response.errmsg}")
                return []
                
        except Exception as e:
            print(f"✗ 获取持仓异常: {str(e)}")
            return []
    
    def get_my_balances(self):
        """
        获取我的余额
        
        Returns:
            余额信息
        """
        print(f"\n💰 获取我的余额...")
        
        try:
            response = self.client.get_my_balances()
            
            if response.errno == 0:
                balances = response.result
                print(f"✓ 余额信息:")
                
                # 显示余额详情
                if hasattr(balances, 'available'):
                    print(f"   可用余额: {balances.available}")
                if hasattr(balances, 'locked'):
                    print(f"   锁定余额: {balances.locked}")
                if hasattr(balances, 'total'):
                    print(f"   总余额: {balances.total}")
                
                return balances
            else:
                print(f"✗ 获取余额失败: {response.errmsg}")
                return None
                
        except Exception as e:
            print(f"✗ 获取余额异常: {str(e)}")
            return None
    
    def get_my_trades(self, market_id=None, limit=50):
        """
        获取我的交易历史
        
        Args:
            market_id: 市场ID (可选，不填则获取所有市场)
            limit: 返回交易数量限制
            
        Returns:
            交易历史列表
        """
        print(f"\n📜 获取交易历史 (限制: {limit})...")
        
        try:
            response = self.client.get_my_trades(market_id=market_id, limit=limit)
            
            if response.errno == 0:
                trades = response.result.list
                print(f"✓ 找到 {len(trades)} 笔交易")
                
                # 显示交易摘要
                for i, trade in enumerate(trades, 1):
                    print(f"\n{i}. 交易ID: {trade.trade_id}")
                    print(f"   市场ID: {trade.market_id}")
                    print(f"   方向: {trade.side}")
                    print(f"   价格: {trade.price}")
                    print(f"   数量: {trade.size}")
                    print(f"   时间: {trade.timestamp}")
                
                return trades
            else:
                print(f"✗ 获取交易历史失败: {response.errmsg}")
                return []
                
        except Exception as e:
            print(f"✗ 获取交易历史异常: {str(e)}")
            return []
    
    def get_my_orders(self, market_id=None, status=None, limit=50):
        """
        获取我的订单
        
        Args:
            market_id: 市场ID (可选)
            status: 订单状态 (可选)
            limit: 返回订单数量限制
            
        Returns:
            订单列表
        """
        print(f"\n📋 获取我的订单 (限制: {limit})...")
        
        try:
            response = self.client.get_my_orders(
                market_id=market_id,
                status=status,
                limit=limit
            )
            
            if response.errno == 0:
                orders = response.result.list
                print(f"✓ 找到 {len(orders)} 个订单")
                
                # 显示订单摘要
                for i, order in enumerate(orders, 1):
                    print(f"\n{i}. 订单ID: {order.order_id}")
                    print(f"   市场ID: {order.market_id}")
                    print(f"   方向: {order.side}")
                    print(f"   类型: {order.order_type}")
                    print(f"   价格: {order.price}")
                    print(f"   状态: {order.status}")
                
                return orders
            else:
                print(f"✗ 获取订单失败: {response.errmsg}")
                return []
                
        except Exception as e:
            print(f"✗ 获取订单异常: {str(e)}")
            return []
    
    def cancel_order(self, order_id):
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            取消结果
        """
        print(f"\n❌ 取消订单 (ID: {order_id})...")
        
        try:
            result = self.client.cancel_order(order_id=order_id)
            
            if result.errno == 0:
                print(f"✓ 订单已取消")
                return result
            else:
                print(f"✗ 取消订单失败: {result.errmsg}")
                return None
                
        except Exception as e:
            print(f"✗ 取消订单异常: {str(e)}")
            return None
    
    def split_tokens(self, market_id, amount):
        """
        分割代币 (将报价代币分割成结果代币)
        
        Args:
            market_id: 市场ID
            amount: 分割数量 (单位: wei, 18位小数)
            
        Returns:
            交易哈希和收据
        """
        print(f"\n✂️ 分割代币...")
        print(f"   市场ID: {market_id}")
        print(f"   数量: {amount}")
        
        try:
            tx_hash, receipt, event = self.client.split(
                market_id=market_id,
                amount=amount
            )
            
            print(f"✓ 代币已分割")
            print(f"   交易哈希: {tx_hash.hex()}")
            return tx_hash, receipt, event
            
        except Exception as e:
            print(f"✗ 分割代币异常: {str(e)}")
            return None, None, None
    
    def merge_tokens(self, market_id, amount):
        """
        合并代币 (将结果代币合并回报价代币)
        
        Args:
            market_id: 市场ID
            amount: 合并数量 (单位: wei, 18位小数)
            
        Returns:
            交易哈希和收据
        """
        print(f"\n🔗 合并代币...")
        print(f"   市场ID: {market_id}")
        print(f"   数量: {amount}")
        
        try:
            tx_hash, receipt, event = self.client.merge(
                market_id=market_id,
                amount=amount
            )
            
            print(f"✓ 代币已合并")
            print(f"   交易哈希: {tx_hash.hex()}")
            return tx_hash, receipt, event
            
        except Exception as e:
            print(f"✗ 合并代币异常: {str(e)}")
            return None, None, None
    
    def redeem_winnings(self, market_id):
        """
        赎回获胜代币 (市场结算后)
        
        Args:
            market_id: 市场ID
            
        Returns:
            交易哈希和收据
        """
        print(f"\n🎁 赎回获胜代币...")
        print(f"   市场ID: {market_id}")
        
        try:
            tx_hash, receipt, event = self.client.redeem(market_id=market_id)
            
            print(f"✓ 代币已赎回")
            print(f"   交易哈希: {tx_hash.hex()}")
            return tx_hash, receipt, event
            
        except Exception as e:
            print(f"✗ 赎回代币异常: {str(e)}")
            return None, None, None


def main():
    """主函数 - 示例用法"""
    print("=" * 60)
    print("OPINION 交易脚本")
    print("=" * 60)
    
    # 创建交易客户端
    trader = OpinionTrader()
    
    # 示例1: 获取活跃市场
    markets = trader.get_active_markets(limit=5)
    
    # 示例2: 获取余额
    balances = trader.get_my_balances()
    
    # 示例3: 获取持仓
    positions = trader.get_my_positions(limit=20)
    
    # 示例4: 获取交易历史
    trades = trader.get_my_trades(limit=10)
    
    # 示例5: 获取订单
    orders = trader.get_my_orders(limit=10)
    
    # 如果有市场，获取第一个市场的详情
    if markets:
        market = markets[0]
        market_detail = trader.get_market_detail(market.id)
        
        # 如果有代币，获取订单簿
        if market_detail and hasattr(market_detail, 'tokens') and market_detail.tokens:
            token = market_detail.tokens[0]
            orderbook = trader.get_orderbook(token.token_id)
    
    # 示例6: 下限价单 (需要取消注释并设置正确参数)
    # result = trader.place_limit_order(
    #     market_id=813,
    #     token_id='token_yes',
    #     side='BUY',
    #     price='0.55',
    #     amount=10
    # )
    
    # 示例7: 分割代币 (需要取消注释并设置正确参数)
    # trader.split_tokens(market_id=813, amount=1000000000000000000)  # 1 USDT
    
    print("\n" + "=" * 60)
    print("✓ 示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

