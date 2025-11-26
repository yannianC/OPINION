"""
Opinion Trade 自动化测试脚本
用于测试 Type 1 任务逻辑
"""

import sys
import os

# 导入主模块
from opinion_auto import (
    log_print,
    initialize_fingerprint_mapping,
    process_type1_mission
)


def test_type1_task():
    """
    测试 Type 1 任务
    """
    log_print("\n" + "="*80)
    log_print("开始测试 Type 1 任务")
    log_print("="*80 + "\n")
    
    # 初始化浏览器映射
    log_print("[测试] 初始化浏览器映射...")
    initialize_fingerprint_mapping()
    
    # 构建测试任务数据
    mission_data = {
        "id": "test_mission_001",
        "type": 1,
        "browserId": "4001",
        "tradeType": "Buy",
        "priceType": "Limit",
        "optionType": "NO",  # 默认使用YES，如需NO请修改此处
        "topicId": "1274",
        "price": "97",
        "amount": "10"
    }
    
    log_print("\n[测试] 任务数据：")
    for key, value in mission_data.items():
        log_print(f"  {key}: {value}")
    log_print("")
    
    # 执行任务
    log_print("[测试] 开始执行任务...\n")
    success, failure_reason = process_type1_mission(mission_data)
    
    # 输出结果
    log_print("\n" + "="*80)
    if success:
        log_print("✓✓✓ 测试成功！任务执行完成")
    else:
        log_print(f"✗✗✗ 测试失败！失败原因: {failure_reason}")
    log_print("="*80 + "\n")
    
    return success


if __name__ == "__main__":
    try:
        success = test_type1_task()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_print("\n[测试] 收到中断信号，测试终止")
        sys.exit(1)
    except Exception as e:
        log_print(f"\n[测试] ✗ 测试过程中发生异常: {str(e)}")
        import traceback
        log_print(f"[测试] 错误详情:\n{traceback.format_exc()}")
        sys.exit(1)

