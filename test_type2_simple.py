"""
Type 2 任务简单测试程序
直接测试浏览器 4001 的 Type 2 任务
"""

from auto_trader import (
    process_type2_mission,
    initialize_fingerprint_mapping,
    log_print,
    FINGERPRINT_TO_USERID
)


def test_browser_4001_op():
    """
    测试浏览器 4001 - OP 交易所
    """
    log_print("\n" + "="*80)
    log_print("测试浏览器 4001 - OP 交易所")
    log_print("="*80 + "\n")
    
    # 初始化映射
    initialize_fingerprint_mapping()
    
    # 检查映射
    browser_id = "4001"
    if browser_id in FINGERPRINT_TO_USERID:
        log_print(f"[系统] ✓ 浏览器 {browser_id} 已映射到: {FINGERPRINT_TO_USERID[browser_id]}")
    else:
        log_print(f"[系统] ⚠ 浏览器 {browser_id} 未找到映射，可能需要手动添加")
    
    # 构造任务数据（按照 auto_trader.py 期望的格式）
    task_data = {
        "mission": {
            "id": "test_4001_op",
            "type": 2,
            "numberList": "4001",
            "exchangeName": "OP"
        }
    }
    
    log_print(f"\n[测试] 执行任务: {task_data}\n")
    
    # 执行任务
    success, failure_reason, collected_data = process_type2_mission(task_data)
    
    # 打印结果
    log_print("\n" + "="*80)
    log_print("测试结果 - OP")
    log_print("="*80)
    log_print(f"✓ 成功: {success}")
    if not success:
        log_print(f"✗ 失败原因: {failure_reason}")
    
    if collected_data:
        log_print(f"\n收集到的数据:")
        log_print(f"  Portfolio: {collected_data.get('portfolio', 'N/A')}")
        log_print(f"  Balance: {collected_data.get('balance', 'N/A')}")
        
        positions = collected_data.get('positions', [])
        log_print(f"\n  Positions ({len(positions)} 项):")
        for i, pos in enumerate(positions, 1):
            log_print(f"    {i}. {pos['title']}, {pos['amount']:+.2f}")
        
        open_orders = collected_data.get('open_orders', [])
        log_print(f"\n  Open Orders ({len(open_orders)} 项):")
        for i, order in enumerate(open_orders, 1):
            log_print(f"    {i}. {order['title']}, {order['price']}, {order['progress']}")
    
    log_print("\n" + "="*80 + "\n")


def test_browser_4001_ploy():
    """
    测试浏览器 4001 - Polymarket 交易所
    """
    log_print("\n" + "="*80)
    log_print("测试浏览器 4001 - Polymarket 交易所")
    log_print("="*80 + "\n")
    
    # 初始化映射
    initialize_fingerprint_mapping()
    
    # 检查映射
    browser_id = "4001"
    if browser_id in FINGERPRINT_TO_USERID:
        log_print(f"[系统] ✓ 浏览器 {browser_id} 已映射到: {FINGERPRINT_TO_USERID[browser_id]}")
    else:
        log_print(f"[系统] ⚠ 浏览器 {browser_id} 未找到映射，可能需要手动添加")
    
    # 构造任务数据（按照 auto_trader.py 期望的格式）
    task_data = {
        "mission": {
            "id": "test_4001_ploy",
            "type": 2,
            "numberList": "4001",
            "exchangeName": "Ploy"
        }
    }
    
    log_print(f"\n[测试] 执行任务: {task_data}\n")
    
    # 执行任务
    success, failure_reason, collected_data = process_type2_mission(task_data)
    
    # 打印结果
    log_print("\n" + "="*80)
    log_print("测试结果")
    log_print("="*80)
    log_print(f"✓ 成功: {success}")
    if not success:
        log_print(f"✗ 失败原因: {failure_reason}")
    
    if collected_data:
        log_print(f"\n收集到的数据:")
        log_print(f"  Portfolio: {collected_data.get('portfolio', 'N/A')}")
        log_print(f"  Cash: {collected_data.get('cash', 'N/A')}")
        
        positions = collected_data.get('positions', [])
        log_print(f"\n  Positions ({len(positions)} 项):")
        for i, pos in enumerate(positions, 1):
            log_print(f"    {i}. {pos['title']}, {pos['amount']:+.2f}")
        
        open_orders = collected_data.get('open_orders', [])
        log_print(f"\n  Open Orders ({len(open_orders)} 项):")
        for i, order in enumerate(open_orders, 1):
            log_print(f"    {i}. {order['title']}, {order['price']}, {order['progress']}")
    
    log_print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    log_print("\n" + "="*80)
    log_print("Type 2 任务测试 - 浏览器 4001")
    log_print("="*80)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        exchange = sys.argv[1].upper()
        if exchange in ["OP", "PLOY"]:
            log_print(f"\n测试交易所: {exchange}\n")
            if exchange == "OP":
                test_browser_4001_op()
            else:
                test_browser_4001_ploy()
        else:
            log_print(f"\n⚠ 不支持的交易所: {sys.argv[1]}")
            log_print("支持的交易所: OP, Ploy")
    else:
        # 默认测试 Polymarket
        log_print("\n默认测试 Polymarket 交易所")
        log_print("提示: 使用 'python test_type2_simple.py OP' 测试 OP 交易所")
        log_print("提示: 使用 'python test_type2_simple.py Ploy' 测试 Polymarket 交易所\n")
        
        test_browser_4001_ploy()

