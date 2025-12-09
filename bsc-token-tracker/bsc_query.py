"""
BSC Token Transfers 查询工具
纯 Python 脚本版本，直接在命令行运行
"""
import sys
from web3 import Web3
from web3.middleware import geth_poa_middleware
from datetime import datetime
import json
import time

# BSC RPC 节点配置
DEFAULT_RPC_URL = 'https://public-bsc-mainnet.fastnode.io/'

# ERC20 Transfer 事件签名
# 这是 ERC20 Token 标准定义的 Transfer 事件的签名哈希值
# Transfer(address indexed from, address indexed to, uint256 value)
# 当 Token 转账时，会发出这个事件，我们通过查询这个事件来获取 Token 转账记录
# 这是查询 Token Transfers 的核心，类似 BscScan 的 Token Transfers 功能
TRANSFER_EVENT_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

# ERC20 标准 ABI（简化版）
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


def init_web3(rpc_url=None):
    """初始化 Web3 连接"""
    if rpc_url is None:
        rpc_url = DEFAULT_RPC_URL
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise Exception("无法连接到 BSC 节点")
        
        return w3
    except Exception as e:
        print(f"❌ Web3 初始化失败: {str(e)}")
        print(f"   请检查网络连接或 RPC 节点地址: {rpc_url}")
        return None


def get_token_info(w3, contract_address):
    """获取 Token 信息"""
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=ERC20_ABI)
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        return {'name': name, 'symbol': symbol, 'decimals': decimals}
    except Exception as e:
        return {'name': 'Unknown', 'symbol': 'Unknown', 'decimals': 18}


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


def get_token_transfers(w3, address, start_block=0, end_block=None, limit=1000, max_block_range=100000):
    """查询 Token 转账记录"""
    try:
        address = Web3.to_checksum_address(address)
        
        if end_block is None:
            end_block = w3.eth.block_number
        
        # 限制查询范围，避免超过 RPC 节点限制
        if end_block - start_block > max_block_range:
            print(f"⚠️  查询范围过大 ({end_block - start_block} 个区块)，已限制为最近 {max_block_range} 个区块")
            print(f"   💡 公共 RPC 节点限制较严，建议使用付费节点查询更多历史数据")
            start_block = max(0, end_block - max_block_range)
        
        print(f"📡 正在查询 Token 转账记录...")
        print(f"   地址: {address}")
        print(f"   区块范围: {start_block} - {end_block} (共 {end_block - start_block} 个区块)")
        
        # 如果范围仍然很大，分批查询
        block_range = end_block - start_block
        # 公共 RPC 节点限制非常严格，使用很小的批次
        batch_size = 100  # 每批最多 100 个区块（公共节点限制很严格）
        
        if block_range > batch_size:
            print(f"   查询范围较大，将分批查询（每批 {batch_size} 个区块）...")
            print(f"   ⚠️  注意：公共 RPC 节点有查询限制，如果频繁失败，建议使用付费 RPC 节点")
            all_from_logs = []
            all_to_logs = []
            
            current_start = start_block
            batch_num = 1
            total_batches = (block_range + batch_size - 1) // batch_size
            failed_batches = 0
            max_failed = 3  # 最多允许连续失败3次
            
            while current_start < end_block:
                current_end = min(current_start + batch_size - 1, end_block)
                
                print(f"   批次 {batch_num}/{total_batches}: 区块 {current_start} - {current_end}...", end='', flush=True)
                
                try:
                    # 将地址转换为 32 字节格式（补齐到 64 个十六进制字符）
                    # 某些 RPC 节点（如 llamaRPC）要求地址必须是 32 字节格式
                    address_hex = address[2:].lower()  # 去掉 0x 前缀并转小写
                    address_32bytes = '0x' + '0' * (64 - len(address_hex)) + address_hex
                    
                    from_filter = {
                        'fromBlock': hex(current_start),
                        'toBlock': hex(current_end),
                        'topics': [
                            TRANSFER_EVENT_TOPIC,
                            address_32bytes,
                            None
                        ]
                    }
                    
                    to_filter = {
                        'fromBlock': hex(current_start),
                        'toBlock': hex(current_end),
                        'topics': [
                            TRANSFER_EVENT_TOPIC,
                            None,
                            address_32bytes
                        ]
                    }
                    
                    from_logs = w3.eth.get_logs(from_filter)
                    to_logs = w3.eth.get_logs(to_filter)
                    
                    all_from_logs.extend(from_logs)
                    all_to_logs.extend(to_logs)
                    failed_batches = 0  # 重置失败计数
                    
                    print(f" ✓ 找到 {len(from_logs)} 条 from 事件，{len(to_logs)} 条 to 事件")
                    
                    # 添加延迟，避免请求过快
                    if batch_num < total_batches:
                        time.sleep(0.5)  # 每批之间延迟 0.5 秒
                    
                except Exception as e:
                    error_msg = str(e)
                    if 'limit exceeded' in error_msg.lower() or '-32005' in error_msg:
                        failed_batches += 1
                        print(f" ✗ 查询失败（RPC 限制）")
                        
                        if failed_batches >= max_failed:
                            print(f"\n   ❌ 连续 {max_failed} 次查询失败，公共 RPC 节点限制过严")
                            print(f"   💡 解决方案：")
                            print(f"      1. 【推荐】使用付费 RPC 节点：")
                            print(f"         - Infura: https://bsc-mainnet.infura.io/v3/YOUR_API_KEY")
                            print(f"         - Alchemy: https://bsc-mainnet.g.alchemy.com/v2/YOUR_API_KEY")
                            print(f"         - QuickNode: 你的 QuickNode 端点")
                            print(f"      2. 只查询最近的数据（默认模式，约3-4天）")
                            print(f"      3. 等待 5-10 分钟后重试")
                            print(f"      4. 尝试其他公共 RPC 节点")
                            print(f"\n   ⚠️  公共节点限制：")
                            print(f"      - 查询范围限制：通常只能查询最近几千个区块")
                            print(f"      - 请求频率限制：需要较长的延迟")
                            print(f"      - 结果集限制：如果地址交易太多，可能无法查询")
                            return []  # 直接返回空结果，不再继续
                        
                        # 如果失败，尝试更小的批次
                        if batch_size > 50:
                            batch_size = max(50, batch_size // 2)
                            print(f"      尝试使用更小的批次大小: {batch_size} 个区块")
                            time.sleep(5)  # 失败后等待更长时间（5秒）
                            continue
                        else:
                            # 批次已经很小了，说明这个 RPC 节点无法查询
                            print(f"      批次已最小（{batch_size}），公共节点限制过严")
                            print(f"      💡 建议使用付费 RPC 节点或只查询最近数据")
                            return []  # 直接返回空结果
                    else:
                        print(f" ✗ 查询失败: {error_msg}")
                        failed_batches += 1
                        if failed_batches >= max_failed:
                            break
                
                current_start = current_end + 1
                batch_num += 1
            
            from_logs = all_from_logs
            to_logs = all_to_logs
        else:
            # 范围较小，直接查询
            print("   正在获取事件日志...")
            try:
                # 将地址转换为 32 字节格式
                address_hex = address[2:].lower()
                address_32bytes = '0x' + '0' * (64 - len(address_hex)) + address_hex
                
                from_filter = {
                    'fromBlock': hex(start_block),
                    'toBlock': hex(end_block),
                    'topics': [
                        TRANSFER_EVENT_TOPIC,
                        address_32bytes,
                        None
                    ]
                }
                
                to_filter = {
                    'fromBlock': hex(start_block),
                    'toBlock': hex(end_block),
                    'topics': [
                        TRANSFER_EVENT_TOPIC,
                        None,
                        address_32bytes
                    ]
                }
                
                from_logs = w3.eth.get_logs(from_filter)
                to_logs = w3.eth.get_logs(to_filter)
            except Exception as e:
                error_msg = str(e)
                if 'limit exceeded' in error_msg.lower() or '-32005' in error_msg:
                    print(f"   ❌ RPC 节点限制：{error_msg}")
                    print(f"   💡 即使查询范围很小（{block_range} 个区块）仍然失败")
                    print(f"   💡 建议：")
                    print(f"      1. 使用付费 RPC 节点（Infura、Alchemy 等）")
                    print(f"      2. 或该地址交易记录太多，公共节点无法处理")
                    return []
                else:
                    raise
        
        # 合并并去重
        seen_hashes = set()
        logs = []
        for log in from_logs + to_logs:
            tx_hash = log['transactionHash'].hex()
            if tx_hash not in seen_hashes:
                seen_hashes.add(tx_hash)
                logs.append(log)
        
        print(f"   找到 {len(logs)} 条事件日志，正在处理...")
        
        transfers = []
        token_info_cache = {}
        
        for i, log in enumerate(logs[:limit]):
            if (i + 1) % 50 == 0:
                print(f"   已处理 {i + 1}/{min(len(logs), limit)} 条...")
            
            try:
                from_address = '0x' + log['topics'][1].hex()[26:]
                to_address = '0x' + log['topics'][2].hex()[26:]
                value = log['data']
                contract_address = log['address']
                
                if from_address.lower() != address.lower() and to_address.lower() != address.lower():
                    continue
                
                # 获取 Token 信息（带缓存）
                if contract_address not in token_info_cache:
                    token_info_cache[contract_address] = get_token_info(w3, contract_address)
                
                token_info = token_info_cache[contract_address]
                
                # 获取交易详情
                tx_hash = log['transactionHash'].hex()
                tx = w3.eth.get_transaction(tx_hash)
                tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
                block = w3.eth.get_block(log['blockNumber'])
                
                transfers.append({
                    'blockNumber': log['blockNumber'],
                    'timeStamp': block['timestamp'],
                    'hash': tx_hash,
                    'from': from_address,
                    'to': to_address,
                    'value': value.hex(),
                    'contractAddress': contract_address,
                    'tokenName': token_info['name'],
                    'tokenSymbol': token_info['symbol'],
                    'tokenDecimal': token_info['decimals'],
                    'type': 'token'
                })
            except Exception as e:
                continue
        
        transfers.sort(key=lambda x: x['timeStamp'], reverse=True)
        return transfers
    except Exception as e:
        print(f"❌ 查询 Token 转账失败: {str(e)}")
        return []


def get_bnb_transfers(w3, address, limit=100):
    """查询 BNB 转账记录"""
    try:
        address = Web3.to_checksum_address(address)
        latest_block = w3.eth.block_number
        start_block = max(0, latest_block - 10000)  # 只查询最近 10000 个区块
        
        print(f"📡 正在查询 BNB 转账记录...")
        print(f"   地址: {address}")
        print(f"   区块范围: {start_block} - {latest_block} (最近 10000 个区块)")
        
        transactions = []
        checked_blocks = 0
        max_blocks = 5000
        
        print("   正在遍历区块...")
        for block_num in range(latest_block, start_block - 1, -1):
            if len(transactions) >= limit or checked_blocks >= max_blocks:
                break
            
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                if not block or not block.transactions:
                    continue
                
                for tx in block.transactions:
                    if len(transactions) >= limit:
                        break
                    
                    if tx['from'] and tx['from'].lower() == address.lower():
                        tx_receipt = w3.eth.get_transaction_receipt(tx['hash'])
                        transactions.append({
                            'blockNumber': tx['blockNumber'],
                            'timeStamp': block['timestamp'],
                            'hash': tx['hash'].hex(),
                            'from': tx['from'],
                            'to': tx['to'] if tx['to'] else '',
                            'value': str(tx['value']),
                            'type': 'bnb'
                        })
                    elif tx['to'] and tx['to'].lower() == address.lower() and tx['value'] > 0:
                        tx_receipt = w3.eth.get_transaction_receipt(tx['hash'])
                        transactions.append({
                            'blockNumber': tx['blockNumber'],
                            'timeStamp': block['timestamp'],
                            'hash': tx['hash'].hex(),
                            'from': tx['from'],
                            'to': tx['to'],
                            'value': str(tx['value']),
                            'type': 'bnb'
                        })
                
                checked_blocks += 1
                if checked_blocks % 500 == 0:
                    print(f"   已检查 {checked_blocks} 个区块，找到 {len(transactions)} 条交易...")
            except Exception as e:
                continue
        
        transactions.sort(key=lambda x: x['timeStamp'], reverse=True)
        return transactions
    except Exception as e:
        print(f"❌ 查询 BNB 转账失败: {str(e)}")
        return []


def print_transactions(transactions, address):
    """打印交易记录"""
    if not transactions:
        print("\n❌ 未找到交易记录")
        return
    
    print(f"\n{'='*100}")
    print(f"📊 找到 {len(transactions)} 条交易记录")
    print(f"{'='*100}\n")
    
    # 统计信息
    token_count = sum(1 for tx in transactions if tx['type'] == 'token')
    bnb_count = sum(1 for tx in transactions if tx['type'] == 'bnb')
    
    print(f"📈 统计信息:")
    print(f"   Token 转账: {token_count} 条")
    print(f"   BNB 转账: {bnb_count} 条")
    print()
    
    # 打印表格
    print(f"{'时间':<20} {'类型':<8} {'方向':<6} {'Token/BNB':<15} {'数量':<25} {'交易哈希':<20}")
    print("-" * 100)
    
    for tx in transactions[:50]:  # 只显示前50条
        timestamp = format_time(tx['timeStamp'])
        tx_type = 'Token' if tx['type'] == 'token' else 'BNB'
        
        is_outgoing = tx['from'].lower() == address.lower()
        direction = '转出' if is_outgoing else '转入'
        
        if tx['type'] == 'token':
            token_symbol = tx.get('tokenSymbol', 'Unknown')
            decimals = int(tx.get('tokenDecimal', 18))
            value_hex = tx['value']
            if value_hex.startswith('0x'):
                value_int = int(value_hex, 16)
            else:
                value_int = int(value_hex)
            amount = format_amount(value_int, decimals, token_symbol)
        else:
            value_int = int(tx['value'])
            amount = format_amount(value_int, 18, 'BNB')
        
        tx_hash_short = shorten_address(tx['hash'])
        
        print(f"{timestamp:<20} {tx_type:<8} {direction:<6} {token_symbol if tx['type'] == 'token' else 'BNB':<15} {amount:<25} {tx_hash_short:<20}")
    
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
    print("🔍 BSC Token Transfers 查询工具 (Python 版本)")
    print("=" * 100)
    print()
    
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
    
    # 询问是否查询全部历史数据
    query_all = False
    if len(sys.argv) <= 2:  # 如果没有通过命令行参数指定
        query_all_input = input("是否查询全部历史数据? (y/N，默认只查询最近1个月): ").strip().lower()
        query_all = query_all_input == 'y'
    
    # 获取 RPC URL（可选）
    rpc_url = None
    if len(sys.argv) > 2:
        rpc_url = sys.argv[2].strip()
    else:
        use_custom = input("是否使用自定义 RPC 节点? (y/N): ").strip().lower()
        if use_custom == 'y':
            rpc_url = input("请输入 RPC 节点地址: ").strip()
    
    # 初始化 Web3
    w3 = init_web3(rpc_url)
    if not w3:
        return
    
    latest_block = w3.eth.block_number
    print(f"✅ 已连接到 BSC 节点")
    print(f"   最新区块: {latest_block}")
    print()
    
    # 查询交易
    all_transactions = []
    
    # 查询 Token 转账
    try:
        if query_all:
            # 查询全部历史数据（分批查询）
            print(f"📌 将查询全部历史数据（从区块 0 到 {latest_block}）")
            print(f"   ⚠️  警告：公共 RPC 节点通常无法查询全部历史数据")
            print(f"   💡 强烈建议使用付费 RPC 节点（Infura、Alchemy 等）")
            print(f"   💡 或只查询最近的数据（默认模式，约 4-5 小时）\n")
            token_transfers = get_token_transfers(w3, address, start_block=0, limit=1000, max_block_range=5000)
        else:
            # 默认只查询最近 5000 个区块（约 2-3 天），避免超过 RPC 限制
            default_start = max(0, latest_block - 5000)
            print(f"📌 将查询最近 5000 个区块（约 2-3 天）的数据")
            print(f"   💡 这是公共 RPC 节点通常能支持的最大范围")
            print(f"   💡 如需查询更多历史数据，请使用付费 RPC 节点\n")
            token_transfers = get_token_transfers(w3, address, start_block=default_start, limit=1000, max_block_range=5000)
        
        all_transactions.extend(token_transfers)
        print(f"✅ Token 转账查询完成，找到 {len(token_transfers)} 条记录\n")
    except Exception as e:
        print(f"⚠️  Token 转账查询出错: {str(e)}\n")
    
    # 查询 BNB 转账
    try:
        bnb_transfers = get_bnb_transfers(w3, address, limit=100)
        all_transactions.extend(bnb_transfers)
        print(f"✅ BNB 转账查询完成，找到 {len(bnb_transfers)} 条记录\n")
    except Exception as e:
        print(f"⚠️  BNB 转账查询出错: {str(e)}\n")
    
    # 排序
    all_transactions.sort(key=lambda x: x['timeStamp'], reverse=True)
    
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

