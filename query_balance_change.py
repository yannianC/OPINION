#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询账户余额变化脚本
从 org,txt 读取浏览器编号和初始金额，查询接口获取当前余额，计算变化值并排序输出
"""

import requests
import json
from typing import List, Dict, Optional
import time

# API接口地址
API_URL = "https://sg.bicoin.com.cn/99l/boost/findAccountConfigCache"

def read_org_file(file_path: str) -> List[Dict[str, str]]:
    """读取 org,txt 文件，返回浏览器编号和初始金额的列表"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # 跳过空行
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                # 尝试用空格分割
                parts = line.split()
                if len(parts) < 2:
                    print(f"警告: 第 {line_num} 行格式不正确，跳过: {line}")
                    continue
            
            browser_no = parts[0].strip()
            initial_amount_str = parts[1].strip()
            
            # 处理金额中的逗号（如 "10,059.15"）
            initial_amount_str = initial_amount_str.replace(',', '')
            
            try:
                initial_amount = float(initial_amount_str)
                data.append({
                    'browser_no': browser_no,
                    'initial_amount': initial_amount
                })
            except ValueError:
                print(f"警告: 第 {line_num} 行金额格式不正确，跳过: {initial_amount_str}")
                continue
    
    return data

def fetch_account_data() -> Optional[List[Dict]]:
    """请求API获取账户数据"""
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get('msg') is None and 'data' in result:
            return result['data']
        else:
            print(f"API返回错误: {result.get('msg', '未知错误')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求API失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析JSON失败: {e}")
        return None

def find_account_by_fingerprint(data: List[Dict], fingerprint_no: str) -> Optional[Dict]:
    """根据 fingerprintNo 查找账户数据"""
    for account in data:
        if str(account.get('fingerprintNo', '')) == str(fingerprint_no):
            return account
    return None

def calculate_current_balance(account: Dict) -> float:
    """计算当前余额 = balance + c字段的值"""
    balance = float(account.get('balance', 0) or 0)
    c_value = account.get('c', '0')
    if c_value:
        try:
            c_value = float(str(c_value).replace(',', ''))
        except (ValueError, TypeError):
            c_value = 0
    else:
        c_value = 0
    
    return balance + c_value

def process_accounts(org_data: List[Dict[str, str]]) -> List[Dict]:
    """处理所有账户，计算余额变化"""
    print("正在请求API获取账户数据...")
    account_data = fetch_account_data()
    
    if not account_data:
        print("无法获取账户数据，程序退出")
        return []
    
    print(f"成功获取 {len(account_data)} 条账户数据")
    print("正在处理账户余额变化...")
    
    results = []
    not_found_count = 0
    
    for item in org_data:
        browser_no = item['browser_no']
        initial_amount = item['initial_amount']
        
        account = find_account_by_fingerprint(account_data, browser_no)
        
        if account:
            current_balance = calculate_current_balance(account)
            change = current_balance - initial_amount
            
            results.append({
                'browser_no': browser_no,
                'initial_amount': initial_amount,
                'current_balance': current_balance,
                'change': change
            })
        else:
            not_found_count += 1
            print(f"警告: 未找到浏览器编号 {browser_no} 的账户数据")
    
    if not_found_count > 0:
        print(f"\n共有 {not_found_count} 个浏览器编号未找到对应的账户数据")
    
    # 按变化值从大到小排序
    results.sort(key=lambda x: x['change'], reverse=True)
    
    return results

def write_output_file(results: List[Dict], output_file: str):
    """将结果写入输出文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入表头
        f.write("浏览器编号\t初始金额\t现余额\t变化值\n")
        
        # 写入数据
        total_initial = 0
        total_current = 0
        total_change = 0
        
        for result in results:
            f.write(f"{result['browser_no']}\t"
                   f"{result['initial_amount']:.2f}\t"
                   f"{result['current_balance']:.2f}\t"
                   f"{result['change']:.2f}\n")
            
            total_initial += result['initial_amount']
            total_current += result['current_balance']
            total_change += result['change']
        
        # 写入汇总行
        f.write("\n")
        f.write("合计\t"
               f"{total_initial:.2f}\t"
               f"{total_current:.2f}\t"
               f"{total_change:.2f}\n")
    
    print(f"\n结果已保存到: {output_file}")
    print(f"共处理 {len(results)} 条记录")
    print(f"总变化值: {sum(r['change'] for r in results):.2f}")

def main():
    input_file = "org,txt"
    output_file = "balance_change_result.txt"
    
    print("=" * 60)
    print("账户余额变化查询脚本")
    print("=" * 60)
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print()
    
    # 读取原始数据
    print(f"正在读取 {input_file}...")
    org_data = read_org_file(input_file)
    print(f"成功读取 {len(org_data)} 条记录")
    print()
    
    # 处理账户数据
    results = process_accounts(org_data)
    
    if not results:
        print("没有可处理的数据")
        return
    
    # 写入输出文件
    write_output_file(results, output_file)
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("统计信息:")
    print(f"总记录数: {len(results)}")
    if results:
        positive_count = sum(1 for r in results if r['change'] > 0)
        negative_count = sum(1 for r in results if r['change'] < 0)
        zero_count = sum(1 for r in results if r['change'] == 0)
        total_change = sum(r['change'] for r in results)
        
        print(f"正变化: {positive_count} 条")
        print(f"负变化: {negative_count} 条")
        print(f"无变化: {zero_count} 条")
        print(f"总变化值: {total_change:.2f}")
        print(f"最大变化值: {results[0]['change']:.2f} (浏览器编号: {results[0]['browser_no']})")
        print(f"最小变化值: {results[-1]['change']:.2f} (浏览器编号: {results[-1]['browser_no']})")
    print("=" * 60)

if __name__ == "__main__":
    main()
