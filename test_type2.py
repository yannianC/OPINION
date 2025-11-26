"""
Type 2 任务测试程序
用于测试 auto_trader.py 中的 Type 2 任务逻辑
"""

from auto_trader import (
    process_type2_mission,
    initialize_fingerprint_mapping,
    log_print,
    FINGERPRINT_TO_USERID
)


def test_type2_op():
    """
    测试 Type 2 任务 - OP 交易所
    """
    log_print("\n" + "="*80)
    log_print("开始测试 Type 2 任务 - OP 交易所")
    log_print("="*80 + "\n")
    
    # 构造任务数据（按照 auto_trader.py 期望的格式）
    task_data = {
        "mission": {
            "id": "test_mission_001",
            "type": 2,
            "numberList": "4001",
            "exchangeName": "OP"
        }
    }
    
    log_print(f"[测试] 任务数据: {task_data}\n")
    
    # 执行任务
    success, failure_reason, collected_data = process_type2_mission(task_data)
    
    # 打印结果
    log_print("\n" + "="*80)
    log_print("测试结果 - OP")
    log_print("="*80)
    log_print(f"成功: {success}")
    log_print(f"失败原因: {failure_reason if failure_reason else '无'}")
    
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
    
    log_print("="*80 + "\n")
    
    return success, collected_data


def test_type2_ploy():
    """
    测试 Type 2 任务 - Polymarket 交易所
    """
    log_print("\n" + "="*80)
    log_print("开始测试 Type 2 任务 - Polymarket 交易所")
    log_print("="*80 + "\n")
    
    # 构造任务数据（按照 auto_trader.py 期望的格式）
    task_data = {
        "mission": {
            "id": "test_mission_002",
            "type": 2,
            "numberList": "4001",
            "exchangeName": "Ploy"
        }
    }
    
    log_print(f"[测试] 任务数据: {task_data}\n")
    
    # 执行任务
    success, failure_reason, collected_data = process_type2_mission(task_data)
    
    # 打印结果
    log_print("\n" + "="*80)
    log_print("测试结果")
    log_print("="*80)
    log_print(f"成功: {success}")
    log_print(f"失败原因: {failure_reason if failure_reason else '无'}")
    log_print(f"收集到的数据:")
    log_print("="*80)
    
    # 详细打印收集到的数据
    if collected_data:
        log_print(f"\nPortfolio: {collected_data.get('portfolio', 'N/A')}")
        log_print(f"Cash: {collected_data.get('cash', 'N/A')}")
        
        positions = collected_data.get('positions', [])
        log_print(f"\nPositions 数据 ({len(positions)} 个 tr):")
        for i, tr_data in enumerate(positions, 1):
            log_print(f"\n  TR {i} ({len(tr_data)} 个 td):")
            for j, td_data in enumerate(tr_data, 1):
                log_print(f"    TD {j} ({len(td_data)} 项):")
                for k, item in enumerate(td_data, 1):
                    # 确保 item 是字典
                    if isinstance(item, dict):
                        log_print(f"      {k}. [{item.get('tag', '?')}] {item.get('content', '')}")
                    else:
                        log_print(f"      {k}. [unknown] {item}")
    
    log_print("\n" + "="*80 + "\n")
    
    return success, collected_data


def main():
    """
    主函数 - 提供菜单选择测试类型
    """
    # 初始化浏览器映射
    log_print("[系统] 初始化浏览器映射...")
    initialize_fingerprint_mapping()
    
    # 检查浏览器 4001 的映射
    browser_id = "4001"
    if browser_id in FINGERPRINT_TO_USERID:
        log_print(f"[系统] ✓ 浏览器 {browser_id} 映射到用户ID: {FINGERPRINT_TO_USERID[browser_id]}")
    else:
        log_print(f"[系统] ⚠ 浏览器 {browser_id} 没有映射，需要手动添加")
        # 手动添加映射（如果需要）
        # FINGERPRINT_TO_USERID[browser_id] = "your_user_id_here"
    
    log_print("\n" + "="*80)
    log_print("Type 2 任务测试程序")
    log_print("="*80)
    log_print("\n请选择要测试的交易所:")
    log_print("1. OP (Opinion.trade)")
    log_print("2. Ploy (Polymarket)")
    log_print("3. 全部测试")
    log_print("0. 退出")
    log_print("\n" + "="*80)
    
    while True:
        try:
            choice = input("\n请输入选项 (0-3): ").strip()
            
            if choice == "0":
                log_print("\n退出测试程序")
                break
            elif choice == "1":
                test_type2_op()
            elif choice == "2":
                test_type2_ploy()
            elif choice == "3":
                log_print("\n开始全部测试...\n")
                
                # 测试 OP
                test_type2_op()
                
                # 等待用户确认
                input("\n按回车继续测试 Polymarket...")
                
                # 测试 Ploy
                test_type2_ploy()
                
                log_print("\n✓ 全部测试完成")
            else:
                log_print("⚠ 无效选项，请重新输入")
                
        except KeyboardInterrupt:
            log_print("\n\n收到中断信号，退出程序")
            break
        except Exception as e:
            log_print(f"\n✗ 测试过程发生错误: {str(e)}")
            import traceback
            log_print(f"错误详情:\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
