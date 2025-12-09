"""
BSC Token Transfers 查询工具 - BscScan API 版本
使用 BscScan API，无需分批查询，更简单直接
"""
import sys
import requests
from datetime import datetime
import json
import time

# BscScan API 配置
BSCSCAN_API_KEY = 'NFQB9EMZ23TG6BN24M3MFK8R3XT27BCISN'  # 请在 https://bscscan.com/apis 获取免费 API Key
BSCSCAN_API_URL = 'https://api.bscscan.com/api'

# API 请求限制（每秒最多5次请求）
last_request_time = 0
min_request_interval = 0.2  # 200ms


def rate_limit():
    """简单的速率限制"""
    global last_request_time
    current_time = time.time()
    elapsed = current_time - last_request_time
    if elapsed < min_request_interval:
        time.sleep(min_request_interval - elapsed)
    last_request_time = time.time()


def get_token_transfers_bscscan(address, startblock=0, endblock=99999999, page=1, offset=10000, sort='desc'):
    """
    使用 BscScan API 获取 Token 转账记录
    
    Args:
        address: 要查询的地址
        startblock: 起始区块号
        endblock: 结束区块号
        page: 页码
        offset: 每页记录数（最多10000）
        sort: 排序方式 'asc' 或 'desc'
    
    Returns:
        dict: API 响应数据
    """
    rate_limit()
    
    params = {
        'module': 'account',
        'action': 'tokentx',
        'address': address,
        'startblock': startblock,
        'endblock': endblock,
        'page': page,
        'offset': offset,
        'sort': sort,
        'apikey': BSCSCAN_API_KEY
    }
    
    try:
        response = requests.get(BSCSCAN_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1' and data.get('message') == 'OK':
            return {
                'success': True,
                'data': data.get('result', []),
                'message': 'OK'
            }
        else:
            return {
                'success': False,
                'data': [],
                'message': data.get('message', 'Unknown error')
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'data': [],
            'message': f'Request error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'message': f'Error: {str(e)}'
        }


def get_normal_transactions_bscscan(address, startblock=0, endblock=99999999, page=1, offset=10000, sort='desc'):
    """
    使用 BscScan API 获取普通交易记录（BNB 转账）
    """
    rate_limit()
    
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': startblock,
        'endblock': endblock,
        'page': page,
        'offset': offset,
        'sort': sort,
        'apikey': BSCSCAN_API_KEY
    }
    
    try:
        response = requests.get(BSCSCAN_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1' and data.get('message') == 'OK':
            return {
                'success': True,
                'data': data.get('result', []),
                'message': 'OK'
            }
        else:
            return {
                'success': False,
                'data': [],
                'message': data.get('message', 'Unknown error')
            }
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'message': f'Error: {str(e)}'
        }


def format_time(timestamp):
    """格式化时间戳"""
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')


def format_amount(value, decimals, symbol=''):
    """格式化金额"""
    amount = int(value) / (10 ** decimals)
    return f"{amount:.6f} {symbol}".strip()


def shorten_address(address):
    """缩短地址显示"""
    if not address:
        return 'N/A'
    return f"{address[:6]}...{address[-4:]}"


def print_transactions(transactions, address):
    """打印交易记录"""
    if not transactions:
        print("\n❌ 未找到交易记录")
        return
    
    print(f"\n{'='*100}")
    print(f"📊 找到 {len(transactions)} 条交易记录")
    print(f"{'='*100}\n")
    
    # 统计信息
    token_count = sum(1 for tx in transactions if tx.get('tokenSymbol'))
    bnb_count = len(transactions) - token_count
    
    print(f"📈 统计信息:")
    print(f"   Token 转账: {token_count} 条")
    print(f"   BNB 转账: {bnb_count} 条")
    print()
    
    # 打印表格
    print(f"{'时间':<20} {'类型':<8} {'方向':<6} {'Token/BNB':<15} {'数量':<25} {'交易哈希':<20}")
    print("-" * 100)
    
    for tx in transactions[:50]:  # 只显示前50条
        timestamp = format_time(tx.get('timeStamp', 0))
        tx_type = 'Token' if tx.get('tokenSymbol') else 'BNB'
        
        is_outgoing = tx.get('from', '').lower() == address.lower()
        direction = '转出' if is_outgoing else '转入'
        
        if tx.get('tokenSymbol'):
            decimals = int(tx.get('tokenDecimal', 18))
            value_int = int(tx.get('value', 0))
            amount = format_amount(value_int, decimals, tx.get('tokenSymbol', 'Token'))
            symbol = tx.get('tokenSymbol', 'Token')
        else:
            value_int = int(tx.get('value', 0))
            amount = format_amount(value_int, 18, 'BNB')
            symbol = 'BNB'
        
        tx_hash_short = shorten_address(tx.get('hash', tx.get('transactionHash', '')))
        
        print(f"{timestamp:<20} {tx_type:<8} {direction:<6} {symbol:<15} {amount:<25} {tx_hash_short:<20}")
    
    if len(transactions) > 50:
        print(f"\n... 还有 {len(transactions) - 50} 条记录未显示")
    
    print(f"\n{'='*100}")
    print(f"💡 提示: 可以在 BscScan 查看详细信息")
    print(f"   地址: https://bscscan.com/address/{address}")
    print(f"{'='*100}\n")


def save_to_json(transactions, filename):
    """保存交易记录到 JSON 文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ 交易记录已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")


def main():
    """主函数"""
    print("=" * 100)
    print("🔍 BSC Token Transfers 查询工具 (BscScan API 版本)")
    print("=" * 100)
    print()
    
    # 检查 API Key
    if BSCSCAN_API_KEY == 'YourApiKeyToken':
        print("⚠️  警告: 未配置 BscScan API Key")
        print("   请在 https://bscscan.com/apis 注册并获取免费 API Key")
        print("   然后修改脚本中的 BSCSCAN_API_KEY 变量")
        print()
        use_default = input("是否继续使用默认 Key（可能有速率限制）? (y/N): ").strip().lower()
        if use_default != 'y':
            return
    
    # 获取地址
    if len(sys.argv) > 1:
        address = sys.argv[1].strip()
    else:
        address = input("请输入 BSC 地址: ").strip()
    
    if not address:
        print("❌ 地址不能为空")
        return
    
    if not address.startswith('0x') or len(address) != 42:
        print("❌ 无效的地址格式，BSC 地址应为 0x 开头的 42 位字符串")
        return
    
    print(f"✅ 使用 BscScan API 查询（无需分批查询，更快速）")
    print(f"   地址: {address}")
    print()
    
    # 查询交易
    all_transactions = []
    
    # 查询 Token 转账
    print("📡 正在查询 Token 转账记录...")
    try:
        token_result = get_token_transfers_bscscan(address, offset=10000, sort='desc')
        if token_result['success']:
            all_transactions.extend(token_result['data'])
            print(f"✅ Token 转账查询完成，找到 {len(token_result['data'])} 条记录\n")
        else:
            print(f"⚠️  Token 转账查询失败: {token_result['message']}\n")
    except Exception as e:
        print(f"⚠️  Token 转账查询出错: {str(e)}\n")
    
    # 查询 BNB 转账
    print("📡 正在查询 BNB 转账记录...")
    try:
        bnb_result = get_normal_transactions_bscscan(address, offset=10000, sort='desc')
        if bnb_result['success']:
            all_transactions.extend(bnb_result['data'])
            print(f"✅ BNB 转账查询完成，找到 {len(bnb_result['data'])} 条记录\n")
        else:
            print(f"⚠️  BNB 转账查询失败: {bnb_result['message']}\n")
    except Exception as e:
        print(f"⚠️  BNB 转账查询出错: {str(e)}\n")
    
    # 排序
    all_transactions.sort(key=lambda x: int(x.get('timeStamp', 0)), reverse=True)
    
    # 显示结果
    print_transactions(all_transactions, address)
    
    # 保存到文件（可选）
    if all_transactions:
        save = input("是否保存到 JSON 文件? (y/N): ").strip().lower()
        if save == 'y':
            filename = f"transactions_{address[:10]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_to_json(all_transactions, filename)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

