"""
获取钱包地址脚本
从服务器获取数据列表，对于 n 字段为空的记录：
1. 获取代理配置
2. 使用代理请求 contract-creator API
3. 更新 n 字段到服务器
"""

import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 服务器API配置
SERVER_BASE_URL = "https://sg.bicoin.com.cn/99l"
CONTRACT_CREATOR_API_URL = "http://opinion.api.predictscan.dev:10001/api/user/contract-creator"

def log_print(*args, **kwargs):
    """带时间戳的打印函数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)


def get_proxy_config(browser_id, timeout=15):
    """
    获取浏览器代理配置
    
    Args:
        browser_id: 浏览器编号
        timeout: 请求超时时间（秒）
        
    Returns:
        dict: 代理配置信息，包含 ip, port, username, password, type，失败返回None
    """
    try:
        log_print(f"[{browser_id}] 调用获取新IP接口（超时: {timeout}秒）...")
        
        url = f"{SERVER_BASE_URL}/bro/getIp"
        payload = {"number": browser_id}
        
        response = requests.post(url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] 获取IP接口返回: {result}")
            
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                ip = data.get("ip")
                is_main = data.get("isMain", 0)
                
                if not ip:
                    log_print(f"[{browser_id}] ⚠ 返回数据中没有IP字段")
                    return None
                
                # 根据 isMain 字段决定如何构建代理配置
                if is_main == 1:
                    port = data.get("port")
                    username = data.get("username")
                    password = data.get("password")
                    
                    if ip and port and username and password:
                        proxy_config = {
                            "ip": ip,
                            "port": str(port),
                            "username": username,
                            "password": password,
                            "type": "http",
                            "isMain": is_main
                        }
                        log_print(f"[{browser_id}] ✓ 成功获取新代理配置 (isMain=1): IP={ip}, Port={port}, Type=http")
                        return proxy_config
                    else:
                        log_print(f"[{browser_id}] ⚠ isMain=1 但返回数据中缺少必要字段")
                        return None
                else:
                    # isMain != 1 时，使用固定配置
                    proxy_config = {
                        "ip": ip,
                        "port": "50100",  # 固定端口
                        "username": data.get("username", "nolanwang"),  # 如果有则使用，否则使用默认值
                        "password": data.get("password", "HFVsyegfeyigrfkjb"),  # 如果有则使用，否则使用默认值
                        "type": "SOCKS5",  # 固定类型
                        "isMain": is_main
                    }
                    log_print(f"[{browser_id}] ✓ 成功获取新代理配置 (isMain={is_main}): IP={ip}, Port=50100, Type=SOCKS5")
                    return proxy_config
            else:
                log_print(f"[{browser_id}] ⚠ 获取IP失败: code={code}, msg={result.get('msg')}")
                return None
        else:
            log_print(f"[{browser_id}] ✗ 获取IP请求失败: HTTP状态码 {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        log_print(f"[{browser_id}] ✗ 获取IP请求超时（{timeout}秒）")
        return None
    except requests.exceptions.RequestException as e:
        log_print(f"[{browser_id}] ✗ 获取IP网络请求失败: {str(e)}")
        return None
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取新IP异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return None


def get_contract_creator_with_proxy(address, proxy_config):
    """
    使用代理配置请求 contract-creator API
    
    Args:
        address: 钱包地址
        proxy_config: 代理配置字典，包含 ip, port, username, password, type
        
    Returns:
        str: contractCreator 地址，失败返回 None
    """
    try:
        url = f"{CONTRACT_CREATOR_API_URL}/{address}"
        
        log_print(f"[代理请求] 地址: {address}, 代理: {proxy_config['ip']}:{proxy_config['port']} ({proxy_config['type']})")
        
        # 构建代理配置
        if proxy_config['type'].upper() == 'HTTP':
            proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        elif proxy_config['type'].upper() == 'SOCKS5':
            # 使用 SOCKS5 代理
            # 格式: socks5://username:password@host:port
            proxy_url = f"socks5://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            # 注意：需要安装 requests[socks] 或 PySocks
            # pip install requests[socks] 或 pip install PySocks
        else:
            log_print(f"⚠ 不支持的代理类型: {proxy_config['type']}")
            proxies = None
        
        # 发送请求
        response = requests.get(url, proxies=proxies, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data') and result['data'].get('contractCreator'):
                contract_creator = result['data']['contractCreator']
                log_print(f"✓ 成功获取 contractCreator: {contract_creator}")
                return contract_creator
            else:
                log_print(f"⚠ API 返回数据格式不正确: {result}")
                return None
        else:
            log_print(f"✗ 请求失败: HTTP状态码 {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        log_print(f"✗ 请求超时")
        return None
    except requests.exceptions.RequestException as e:
        log_print(f"✗ 网络请求失败: {str(e)}")
        return None
    except Exception as e:
        log_print(f"✗ 请求异常: {str(e)}")
        import traceback
        log_print(f"错误详情:\n{traceback.format_exc()}")
        return None


def load_data():
    """
    从服务器加载数据列表
    
    Returns:
        list: 数据列表，失败返回空列表
    """
    try:
        url = f"{SERVER_BASE_URL}/boost/findAccountConfigCache"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # API 返回结构: { "data": [...] } 或 { "data": { "data": [...] } }
            # 检查数据结构
            if result.get('data'):
                data = result['data']
                # 如果 data 是字典，尝试获取内部的 data 字段
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                # 如果 data 是列表，直接使用
                if isinstance(data, list):
                    log_print(f"✓ 成功加载 {len(data)} 条数据")
                    return data
                else:
                    log_print(f"⚠ 服务器返回数据格式不正确: data 不是列表类型")
                    log_print(f"   数据类型: {type(data)}, 内容: {data}")
                    return []
            else:
                log_print("⚠ 服务器返回数据中没有 'data' 字段")
                log_print(f"   返回内容: {result}")
                return []
        else:
            log_print(f"✗ 加载数据失败: HTTP状态码 {response.status_code}")
            return []
    except Exception as e:
        log_print(f"✗ 加载数据异常: {str(e)}")
        import traceback
        log_print(f"错误详情:\n{traceback.format_exc()}")
        return []


def save_row_data(row_data):
    """
    保存单行数据到服务器
    
    Args:
        row_data: 行数据字典
        
    Returns:
        bool: 保存成功返回 True，失败返回 False
    """
    try:
        url = f"{SERVER_BASE_URL}/boost/addAccountConfig"
        
        # 准备要保存的数据
        save_data = {**row_data}
        # 平台值保存到 e 字段
        if 'platform' in save_data:
            save_data['e'] = save_data['platform']
        
        response = requests.post(url, json=save_data, timeout=10)
        
        if response.status_code == 200:
            log_print(f"✓ 数据保存成功: fingerprintNo={row_data.get('fingerprintNo')}")
            return True
        else:
            log_print(f"✗ 数据保存失败: HTTP状态码 {response.status_code}")
            return False
    except Exception as e:
        log_print(f"✗ 保存数据异常: {str(e)}")
        return False


def process_single_row(row, index, total, counters_lock):
    """
    处理单条记录
    
    Args:
        row: 行数据字典
        index: 当前索引
        total: 总记录数
        counters_lock: 线程锁，用于保护计数器
        
    Returns:
        tuple: (success, skipped, fail) 处理结果
    """
    fingerprint_no = row.get('fingerprintNo')
    row_index = row.get('index')
    
    log_print(f"[{index}/{total}] 处理记录: fingerprintNo={fingerprint_no}, index={row_index}")
    
    # 检查 h 字段
    address_to_use = row.get('h', '').strip() if row.get('h') else ''
    if not address_to_use:
        with counters_lock:
            log_print(f"[{fingerprint_no}] ⚠ 跳过：h 字段为空")
        return (False, True, False)  # (success, skipped, fail)
    
    # 检查浏览器编号
    browser_id = row.get('fingerprintNo')
    if not browser_id:
        with counters_lock:
            log_print(f"[{fingerprint_no}] ⚠ 跳过：缺少浏览器编号")
        return (False, True, False)
    
    # 1. 获取代理配置
    proxy_config = get_proxy_config(browser_id)
    if not proxy_config:
        with counters_lock:
            log_print(f"[{fingerprint_no}] ✗ 获取代理配置失败，跳过")
        return (False, False, True)
    
    # 2. 使用代理请求 contract-creator
    contract_creator = get_contract_creator_with_proxy(address_to_use, proxy_config)
    if not contract_creator:
        with counters_lock:
            log_print(f"[{fingerprint_no}] ✗ 获取 contractCreator 失败，跳过")
        return (False, False, True)
    
    # 3. 更新 n 字段
    row['n'] = contract_creator
    
    # 4. 保存到服务器
    if save_row_data(row):
        with counters_lock:
            log_print(f"[{fingerprint_no}] ✓ 成功处理并保存: contractCreator={contract_creator}")
        return (True, False, False)
    else:
        # 即使保存失败，也记录为成功获取（因为已经获取到了）
        with counters_lock:
            log_print(f"[{fingerprint_no}] ⚠ 获取成功但保存失败: contractCreator={contract_creator}")
        return (True, False, False)


def get_wallet_addresses():
    """
    主函数：获取钱包地址（使用多线程并发处理）
    """
    log_print("=" * 60)
    log_print("开始获取钱包地址（使用10个线程并发处理）...")
    log_print("=" * 60)
    
    # 1. 加载数据
    data = load_data()
    if not data:
        log_print("没有数据或加载失败，退出")
        return
    
    # 2. 找出 n 字段为空的记录
    rows_to_process = []
    for row in data:
        n_value = row.get('n')
        if not n_value or (isinstance(n_value, str) and not n_value.strip()):
            rows_to_process.append(row)
    
    if not rows_to_process:
        log_print("没有需要处理的记录（所有记录的 n 字段都已填写）")
        return
    
    log_print(f"找到 {len(rows_to_process)} 条需要处理的记录")
    log_print(f"使用 10 个线程并发处理...")
    
    # 3. 使用线程池并发处理
    success_count = 0
    fail_count = 0
    skipped_count = 0
    counters_lock = threading.Lock()
    
    # 创建线程池，最多10个线程
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有任务
        futures = []
        for i, row in enumerate(rows_to_process, 1):
            future = executor.submit(process_single_row, row, i, len(rows_to_process), counters_lock)
            futures.append(future)
        
        # 等待所有任务完成并收集结果
        for future in as_completed(futures):
            try:
                success, skipped, fail = future.result()
                with counters_lock:
                    if success:
                        success_count += 1
                    elif skipped:
                        skipped_count += 1
                    elif fail:
                        fail_count += 1
            except Exception as e:
                with counters_lock:
                    fail_count += 1
                    log_print(f"✗ 处理任务异常: {str(e)}")
    
    # 4. 显示结果
    log_print("\n" + "=" * 60)
    log_print("处理完成！")
    log_print(f"成功: {success_count} 个")
    log_print(f"失败: {fail_count} 个")
    log_print(f"跳过: {skipped_count} 个")
    log_print("=" * 60)


if __name__ == "__main__":
    try:
        get_wallet_addresses()
    except KeyboardInterrupt:
        log_print("\n用户中断，退出")
    except Exception as e:
        log_print(f"\n程序异常: {str(e)}")
        import traceback
        log_print(traceback.format_exc())

