import time
import random
import requests
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


# ============================================================================
# 基础配置和工具函数
# ============================================================================

def log_print(*args, **kwargs):
    """带时间戳的打印函数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)


def get_browser_password(browser_id):
    """
    根据浏览器ID获取对应的密码
    
    Args:
        browser_id: 浏览器编号（int 或 str）
        
    Returns:
        str: 对应的密码
    """
    browser_id_str = str(browser_id)
    else_password = None
    
    # 遍历密码映射
    for password, browser_ids_str in PASSWORD_MAP.items():
        # 检查是否是 "else" 默认配置
        if browser_ids_str.strip().lower() == "else":
            else_password = password
            continue
        
        # 解析浏览器ID列表
        browser_ids = [bid.strip() for bid in browser_ids_str.split(',')]
        
        # 检查当前浏览器ID是否在列表中
        if browser_id_str in browser_ids:
            log_print(f"[{browser_id}] 使用特定密码配置")
            return password
    
    # 如果没有匹配，使用 "else" 密码
    if else_password:
        log_print(f"[{browser_id}] 使用 else 默认密码")
        return else_password
    
    # 最后使用全局默认密码
    log_print(f"[{browser_id}] 使用全局默认密码")
    return PWD


# 电脑组
COMPUTER_GROUP = "7"

# 密码配置（密码 -> 浏览器ID列表）
# 格式：密码: "浏览器ID1,浏览器ID2,浏览器ID3,..."
# 特殊值 "else" 表示其他所有未匹配的浏览器使用此密码
PASSWORD_MAP = {
    # 示例 1：为特定浏览器配置不同密码
    # "ywj000805*": "11,22,33,44,5566,77,88",
    # "tnpxxx": "1,2,3,4,5,6",
    # "another_password": "100,200,300",
    
    # 示例 2：所有浏览器使用同一个密码（此时 PWD 不会被使用）
    # "your_password": "else",
}

# 默认密码（仅当 PASSWORD_MAP 为空或没有 "else" 配置时使用）
# 如果您使用了 PASSWORD_MAP = {"your_password": "else"}，则此值不会被使用
PWD = "cx142359."

# 服务器API配置
SERVER_BASE_URL = "https://sg.bicoin.com.cn/99l"


def get_mission_status(mission_id):
    """
    获取任务状态
    
    Args:
        mission_id: 任务ID
        
    Returns:
        int: 任务状态码，失败返回None
    """
    try:
        url = f"{SERVER_BASE_URL}/mission/status"
        response = requests.get(url, params={"id": mission_id}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data') and data['data'].get('mission'):
                return data['data']['mission'].get('status')
        return None
    except Exception as e:
        log_print(f"[系统] 获取任务状态失败: {str(e)}")
        return None


def save_mission_result(mission_id, status, msg=""):
    """
    保存任务结果（仅更新状态）- 带重试机制
    
    Args:
        mission_id: 任务ID
        status: 任务状态
        msg: 附加消息
        
    Returns:
        bool: 成功返回True
    """
    max_retries = 5
    retry_delay = 3  # 秒
    
    for attempt in range(max_retries + 1):  # 第一次尝试 + 5次重试 = 总共6次
        try:
            if attempt > 0:
                log_print(f"[系统] 保存任务结果重试第 {attempt} 次...")
                time.sleep(retry_delay)
            
            url = f"{SERVER_BASE_URL}/mission/saveResult"
            payload = {
                "id": mission_id,
                "status": status,
                "msg": msg
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                if attempt > 0:
                    log_print(f"[系统] ✓ 保存任务结果成功（第 {attempt + 1} 次尝试）")
                return True
            else:
                log_print(f"[系统] ⚠ 保存任务结果失败，状态码: {response.status_code}")
                
        except Exception as e:
            log_print(f"[系统] ⚠ 保存任务结果失败: {str(e)}")
        
        # 如果不是最后一次尝试，继续重试
        if attempt < max_retries:
            continue
        else:
            log_print(f"[系统] ✗✗✗ 保存任务结果失败，已重试 {max_retries} 次")
    
    return False

# 全局线程池配置
MAX_WORKERS = 6
global_thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks_lock = threading.Lock()
active_tasks = {}  # {mission_id: {'futures': [], 'results': {}, 'total': 0, 'completed': 0}}

# 正在执行 type=3 任务的浏览器ID映射 {browser_id: mission_id}
active_type3_browsers = {}
active_type3_browsers_lock = threading.Lock()

# AdsPower配置
ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"

# 全局字典：存储每个浏览器最后使用的代理配置
LAST_PROXY_CONFIG = {}

# 浏览器编号到用户ID的映射
FINGERPRINT_TO_USERID = {}

# 最大重试次数
MAX_RETRIES = 3


# ============================================================================
# 代理IP管理相关函数
# ============================================================================

def get_new_ip_for_browser(browser_id, timeout=15):
    """
    获取浏览器新代理配置的接口
    
    Args:
        browser_id: 浏览器编号
        timeout: 请求超时时间（秒），默认15秒
        
    Returns:
        dict: 代理配置信息，包含 ip, port, username, password, type, isMain，失败返回None
    """
    try:
        log_print(f"[{browser_id}] 调用获取新IP接口（超时: {timeout}秒）...")
        
        url = "https://sg.bicoin.com.cn/99l/bro/getIp"
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
                    proxy_config = {
                        "ip": ip,
                        "port": "50101",
                        "username": "nolanwang",
                        "password": "HFVsyegfeyigrfkjb",
                        "type": "socks5",
                        "isMain": is_main
                    }
                    log_print(f"[{browser_id}] ✓ 成功获取新代理配置 (isMain={is_main}): IP={ip}, 其他字段使用默认值")
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


def update_adspower_proxy(browser_id, proxy_config):
    """
    更新AdsPower浏览器的代理配置
    
    Args:
        browser_id: 浏览器编号
        proxy_config: 代理配置字典，包含 ip, port, username, password, type, isMain
        
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    try:
        # 获取浏览器环境ID
        user_id = FINGERPRINT_TO_USERID.get(str(browser_id))
        if not user_id:
            log_print(f"[{browser_id}] ✗ 无法找到浏览器环境ID映射")
            return False
        
        is_main = proxy_config.get('isMain', 0)
        log_print(f"[{browser_id}] 开始更新AdsPower代理配置，环境ID: {user_id}, isMain: {is_main}")
        log_print(f"[{browser_id}] 代理配置: IP={proxy_config['ip']}, Port={proxy_config['port']}, Type={proxy_config['type']}, Username={proxy_config['username']}")
        
        # 构建请求参数
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/update"
        payload = {
            "user_id": user_id,
            "user_proxy_config": {
                "proxy_host": proxy_config['ip'],
                "proxy_port": proxy_config['port'],
                "proxy_user": proxy_config['username'],
                "proxy_password": proxy_config['password'],
                "proxy_type": proxy_config['type'],
                "proxy_soft": "other"
            }
        }
        headers = {
            'Authorization': f'Bearer {ADSPOWER_API_KEY}'
        }
        
        log_print(f"[{browser_id}] 发送更新请求到: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] 服务器响应: {result}")
            code = result.get("code")
            
            if code == 0:
                log_print(f"[{browser_id}] ✓ AdsPower代理配置更新成功")
                # 记录成功更新的代理配置
                LAST_PROXY_CONFIG[str(browser_id)] = proxy_config.copy()
                return True
            else:
                log_print(f"[{browser_id}] ✗ AdsPower代理配置更新失败: code={code}, msg={result.get('msg')}")
                return False
        else:
            log_print(f"[{browser_id}] ✗ AdsPower代理配置更新失败: HTTP状态码 {response.status_code}")
            log_print(f"[{browser_id}] 响应内容: {response.text}")
            return False
            
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 更新AdsPower代理配置异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False


def force_change_ip_for_browser(browser_id, timeout=15):
    """
    强制更换浏览器IP（用于页面加载失败时）
    
    Args:
        browser_id: 浏览器编号
        timeout: 请求超时时间（秒），默认15秒
        
    Returns:
        dict: 代理配置信息，包含 ip, port, username, password, type，失败返回None
    """
    try:
        log_print(f"[{browser_id}] 调用强制更换IP接口（超时: {timeout}秒）...")
        
        url = "https://sg.bicoin.com.cn/99l/bro/forceChangeIp"
        payload = {"number": browser_id}
        
        response = requests.post(url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] 强制更换IP接口返回: {result}")
            
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                ip = data.get("ip")
                port = data.get("port")
                
                if not ip:
                    log_print(f"[{browser_id}] ⚠ 返回数据中没有IP字段")
                    return None
                
                if not port:
                    log_print(f"[{browser_id}] ⚠ 返回数据中没有port字段")
                    return None
                
                # 使用固定的用户名和密码
                username = data.get("username", "nolanwang")
                password = data.get("password", "HFVsyegfeyigrfkjb")
                
                proxy_config = {
                    "ip": ip,
                    "port": str(port),
                    "username": username,
                    "password": password,
                    "type": "socks5",
                    "isMain": 0
                }
                log_print(f"[{browser_id}] ✓ 成功强制更换IP: IP={ip}, Port={port}")
                return proxy_config
            else:
                log_print(f"[{browser_id}] ⚠ 强制更换IP失败: code={code}, msg={result.get('msg')}")
                return None
        else:
            log_print(f"[{browser_id}] ✗ 强制更换IP请求失败: HTTP状态码 {response.status_code}")
            return None
        
    except requests.exceptions.Timeout:
        log_print(f"[{browser_id}] ✗ 强制更换IP请求超时（{timeout}秒）")
        return None
    except requests.exceptions.RequestException as e:
        log_print(f"[{browser_id}] ✗ 强制更换IP网络请求失败: {str(e)}")
        return None
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 强制更换IP异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return None


def try_update_ip_before_start(browser_id):
    """
    在打开浏览器前尝试获取并更新代理配置（8秒超时）
    
    Args:
        browser_id: 浏览器编号
        
    Returns:
        bool: 是否成功更新了代理配置
    """
    try:
        log_print(f"[{browser_id}] 尝试在打开浏览器前获取新代理配置...")
        
        proxy_config = get_new_ip_for_browser(browser_id, timeout=8)
        
        if proxy_config:
            log_print(f"[{browser_id}] 在8秒内获取到新代理配置: IP={proxy_config['ip']}, 开始更新...")
            update_success = update_adspower_proxy(browser_id, proxy_config)
            
            if update_success:
                log_print(f"[{browser_id}] ✓ 代理配置更新成功")
                return True
            else:
                log_print(f"[{browser_id}] ⚠ 代理配置更新失败")
                return False
        else:
            log_print(f"[{browser_id}] 8秒内未获取到新代理配置")
            return False
            
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 尝试更新代理配置时发生异常: {str(e)}")
        return False


# ============================================================================
# AdsPower浏览器操作函数
# ============================================================================

def check_browser_active(serial_number):
    """
    检查AdsPower浏览器是否已经启动
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (is_active: bool, browser_data: dict or None)
               - is_active: 浏览器是否已经运行
               - browser_data: 如果已运行，返回浏览器连接信息；否则返回None
    """
    try:
        # 获取浏览器环境ID
        user_id = FINGERPRINT_TO_USERID.get(str(serial_number))
        if not user_id:
            log_print(f"[{serial_number}] ⚠ 无法找到浏览器环境ID映射")
            return False, None
        
        log_print(f"[{user_id}] user_id...")
        url = f"{ADSPOWER_BASE_URL}/api/v1/browser/active"
        params = {
            "user_id": user_id
        }
        headers = {
            'Authorization': f'Bearer {ADSPOWER_API_KEY}'
        }
        
        log_print(f"[{serial_number}] 检查浏览器状态...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        data = response.json()
        
        if data.get("code") == 0:
            status = data.get("data", {}).get("status", "Inactive")
            
            if status == "Active":
                log_print(f"[{serial_number}] ✓ 浏览器已在运行中")
                browser_data = data.get("data", {})
                return True, browser_data
            else:
                log_print(f"[{serial_number}] 浏览器未运行，状态: {status}")
                return False, None
        else:
            log_print(f"[{serial_number}] ⚠ 检查浏览器状态失败: {data.get('msg')}")
            return False, None
            
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 检查浏览器状态异常: {str(e)}")
        return False, None


def start_adspower_browser(serial_number):
    """
    启动AdsPower浏览器
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        dict: 包含浏览器连接信息的字典，失败返回None
    """
    import json
    
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/start"
    params = {
        "serial_number": serial_number,
        "user_id": "",
        "open_tabs": 1
    }
    launch_args = [f"--window-size={1500},{1000}"]
    params["launch_args"] = json.dumps(launch_args)
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            log_print(f"[{serial_number}] 尝试启动浏览器 (第 {attempt + 1}/{MAX_RETRIES} 次)")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 浏览器启动成功")
                return data.get("data")
            else:
                log_print(f"[{serial_number}] ✗ 浏览器启动失败: {data.get('msg')}")
                
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 启动浏览器时发生错误: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            wait_time = random.randint(5, 10)
            log_print(f"[{serial_number}] 等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    log_print(f"[{serial_number}] ✗✗✗ 浏览器启动失败，已达到最大重试次数")
    return None


def close_adspower_browser(serial_number, max_retries=3):
    """
    关闭AdsPower浏览器
    
    Args:
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/stop"
    params = {
        "serial_number": serial_number
    }
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] 尝试关闭浏览器 (第 {attempt + 1}/{max_retries} 次)")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 浏览器关闭命令已发送")
                time.sleep(2)
                return True
            else:
                log_print(f"[{serial_number}] ✗ 关闭浏览器失败: {data.get('msg')}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 关闭浏览器时发生错误: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
    
    log_print(f"[{serial_number}] ✗ 浏览器关闭失败，已达到最大重试次数")
    return False


def create_selenium_driver(browser_data):
    """
    创建Selenium WebDriver
    
    Args:
        browser_data: AdsPower返回的浏览器数据
        
    Returns:
        WebDriver: Selenium驱动对象
    """
    chrome_driver = browser_data.get("webdriver")
    debugger_address = browser_data.get("ws", {}).get("selenium")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", debugger_address)
    
    service = Service(executable_path=chrome_driver)
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver


# ============================================================================
# 任务管理函数
# ============================================================================

def get_mission_from_server():
    """
    从服务器获取任务
    
    Returns:
        dict: 任务数据，如果没有任务或失败则返回None
    """
    try:
        url = f"{SERVER_BASE_URL}/mission/getOneMission"
        payload = {"groupNo": COMPUTER_GROUP}
        
        log_print(f"\n[系统] 请求任务: {url}")
        log_print(f"[系统] 请求参数: {payload}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[系统] 服务器响应: {result}")
            
            if result and isinstance(result, dict):
                code = result.get("code")
                msg = result.get("msg")
                data = result.get("data")
                
                if code == 0 and data:
                    mission = data.get("mission", {})
                    exchange_config = data.get("exchangeConfig", {})
                    
                    if mission:
                        log_print(f"[系统] ✓ 获取到任务 ID: {mission.get('id')}, 类型: {mission.get('type')}, 交易所: {mission.get('exchangeName')}")
                        return {
                            "mission": mission,
                            "exchangeConfig": exchange_config
                        }
                    else:
                        log_print(f"[系统] ℹ 任务数据为空")
                else:
                    log_print(f"[系统] ℹ 暂无任务 (code: {code}, msg: {msg})")
            else:
                log_print(f"[系统] ℹ 服务器返回数据格式错误")
        else:
            log_print(f"[系统] ✗ 请求失败，状态码: {response.status_code}")
        
        return None
        
    except requests.exceptions.Timeout:
        log_print(f"[系统] ✗ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        log_print(f"[系统] ✗ 无法连接到服务器: {SERVER_BASE_URL}")
        return None
    except Exception as e:
        log_print(f"[系统] ✗ 获取任务失败: {str(e)}")
        import traceback
        log_print(f"[系统] 错误详情:\n{traceback.format_exc()}")
        return None


def submit_mission_result(mission_id, success_count, failed_count, failed_info, status=2):
    """
    提交任务结果到服务器（带重试机制）
    
    Args:
        mission_id: 任务ID
        success_count: 成功数量
        failed_count: 失败数量
        failed_info: 失败的浏览器信息字典 {browser_id: failure_reason}
        status: 任务状态，2=成功，3=失败
        
    Returns:
        bool: 提交成功返回True，失败返回False
    """
    url = f"{SERVER_BASE_URL}/mission/saveResult"
    
    # 构建消息
    msg = f"成功: {success_count}个, 失败: {failed_count}个"
    if failed_info:
        msg += f", 失败的浏览器: {', '.join(failed_info.keys())}"
        reasons = []
        for bid, reason in failed_info.items():
            if reason:
                reasons.append(f"{bid}{reason}")
        if reasons:
            msg += f"，其中{'，'.join(reasons)}"
    
    payload = {
        "id": mission_id,
        "status": status,  # 2=成功，3=失败
        "msg": msg
    }
    
    log_print(f"\n[系统] 提交结果: {url}")
    log_print(f"[系统] 提交数据: {payload}")
    
    # 重试机制：最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_print(f"[系统] 第 {attempt + 1} 次尝试提交...")
                time.sleep(2)
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                log_print(f"[系统] 服务器响应: {result}")
                
                if result == {}:
                    log_print(f"[系统] ✓ 结果提交成功（服务器返回空字典）")
                    return True
                
                if result and isinstance(result, dict):
                    code = result.get("code")
                    server_msg = result.get("msg")
                    
                    if code == 0:
                        log_print(f"[系统] ✓ 结果提交成功")
                        return True
                    else:
                        log_print(f"[系统] ✗ 结果提交失败 (code: {code}, msg: {server_msg})")
                        if attempt < max_retries - 1:
                            continue
                        return False
                else:
                    log_print(f"[系统] ✗ 服务器返回数据格式错误")
                    if attempt < max_retries - 1:
                        continue
                    return False
            else:
                log_print(f"[系统] ✗ 结果提交失败，状态码: {response.status_code}")
                if attempt < max_retries - 1:
                    continue
                return False
                
        except requests.exceptions.Timeout:
            log_print(f"[系统] ✗ 提交结果超时")
            if attempt < max_retries - 1:
                continue
            return False
        except Exception as e:
            log_print(f"[系统] ✗ 提交结果失败: {str(e)}")
            if attempt < max_retries - 1:
                continue
            return False
    
    return False


# ============================================================================
# 通用浏览器操作函数
# ============================================================================

def wait_and_find_element(driver, by, value, timeout=10, serial_number=""):
    """
    在指定时间内循环查找元素
    
    Args:
        driver: Selenium WebDriver对象
        by: 查找方式 (By.TAG_NAME, By.CSS_SELECTOR等)
        value: 查找值
        timeout: 超时时间（秒），默认10秒
        serial_number: 浏览器序列号（用于日志）
        
    Returns:
        WebElement: 找到的元素，失败返回None
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            element = driver.find_element(by, value)
            if element:
                return element
        except:
            pass
        time.sleep(0.5)
    return None


def wait_and_find_elements(driver, by, value, timeout=10, serial_number=""):
    """
    在指定时间内循环查找多个元素
    
    Args:
        driver: Selenium WebDriver对象
        by: 查找方式 (By.TAG_NAME, By.CSS_SELECTOR等)
        value: 查找值
        timeout: 超时时间（秒），默认10秒
        serial_number: 浏览器序列号（用于日志）
        
    Returns:
        list: 找到的元素列表，失败返回空列表
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            elements = driver.find_elements(by, value)
            if elements:
                return elements
        except:
            pass
        time.sleep(0.5)
    return []


def open_new_tab_with_url(driver, url, serial_number):
    """
    在新标签页中打开URL
    
    Args:
        driver: Selenium WebDriver对象
        url: 要打开的URL
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        # 获取当前窗口句柄
        current_window = driver.current_window_handle
        original_window_count = len(driver.window_handles)
        
        # 方法1: 使用 driver.switch_to.new_window (Selenium 4+)
        try:
            driver.switch_to.new_window('tab')
            time.sleep(1)
            driver.get(url)
            time.sleep(2)
            log_print(f"[{serial_number}] ✓ 已在新标签页打开: {url}")
            return True
        except Exception as e1:
            log_print(f"[{serial_number}] ⚠ new_window 方法失败: {str(e1)}，尝试 Ctrl+T...")
            # 切换回原窗口
            try:
                driver.switch_to.window(current_window)
            except:
                pass
        
        # 方法2: 使用 Ctrl+T 打开新标签页，然后用 driver.get() 导航
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.CONTROL + 't')
            time.sleep(1)
            
            # 切换到新标签页
            all_windows = driver.window_handles
            if len(all_windows) > original_window_count:
                new_window = all_windows[-1]
                driver.switch_to.window(new_window)
                
                # 使用 driver.get() 导航（比JavaScript更可靠）
                driver.get(url)
                time.sleep(2)
                
                log_print(f"[{serial_number}] ✓ 已在新标签页打开 (Ctrl+T): {url}")
                return True
        except Exception as e2:
            log_print(f"[{serial_number}] ⚠ Ctrl+T 方法失败: {str(e2)}")
        
        return False
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 打开新标签页失败: {str(e)}")
        return False


def preopen_okx_wallet(driver, serial_number):
    """
    预先打开OKX钱包页面
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: 主窗口句柄
    """
    log_print(f"[{serial_number}] [预处理] 检查并预打开 OKX 钱包页面...")
    
    # 保存主窗口句柄
    main_window = driver.current_window_handle
    
    okx_extension_id = "mcohilncbfahbmgdjkbpemcciiolgcge"
    okx_popup_url = f"chrome-extension://{okx_extension_id}/popup.html"
    
    try:
        # 检查是否已经存在OKX钱包标签页
        log_print(f"[{serial_number}] → 检查是否已存在 OKX 钱包标签页...")
        all_windows = driver.window_handles
        okx_window_exists = False
        
        for window in all_windows:
            try:
                # 暂时切换到该窗口检查URL
                driver.switch_to.window(window)
                current_url = driver.current_url
                
                # 检查是否包含OKX扩展ID
                if okx_extension_id in current_url:
                    okx_window_exists = True
                    log_print(f"[{serial_number}] ✓ 已找到现有的 OKX 钱包标签页: {current_url}")
                    break
            except Exception as e:
                # 某些窗口可能无法访问，继续检查下一个
                continue
        
        # 切换回主窗口
        driver.switch_to.window(main_window)
        
        # 如果不存在OKX窗口，则打开新的
        if not okx_window_exists:
            log_print(f"[{serial_number}] → 未找到 OKX 钱包标签页，正在打开...")
            success = open_new_tab_with_url(driver, okx_popup_url, serial_number)
            
            if success:
                log_print(f"[{serial_number}] ✓ OKX 钱包页面已打开")
            else:
                log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包失败，继续执行...")
                time.sleep(3)
            
            # 切换回主窗口
            log_print(f"[{serial_number}] → 切换回主窗口")
            driver.switch_to.window(main_window)
            log_print(f"[{serial_number}] ✓ 已切换回主窗口")
        else:
            log_print(f"[{serial_number}] ✓ 跳过打开，使用现有的 OKX 钱包标签页")
        
        # 等待1秒
        time.sleep(1)
        
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包异常: {str(e)}，继续执行...")
        try:
            driver.switch_to.window(main_window)
        except:
            pass
    
    return main_window


def unlock_okx_wallet(driver, serial_number, browser_id):
    """
    检查OKX钱包是否需要解锁，如果需要则输入密码解锁
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        browser_id: 浏览器ID（用于获取密码）
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        log_print(f"[{serial_number}] 检查钱包是否需要解锁...")
        
        # 获取密码
        password = get_browser_password(browser_id)
        
        # 先尝试切换到 OKX 钱包的特定 iframe (id="ui-ses-iframe")
        try:
            log_print(f"[{serial_number}] → 查找 OKX 钱包 iframe (id='ui-ses-iframe')...")
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#ui-ses-iframe"))
            )
            driver.switch_to.frame(iframe)
            log_print(f"[{serial_number}] ✓ 已切换到 OKX 钱包 iframe")
        except TimeoutException:
            log_print(f"[{serial_number}] ℹ 未找到 ui-ses-iframe，尝试查找其他 iframe...")
            try:
                iframe = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
                )
                driver.switch_to.frame(iframe)
                log_print(f"[{serial_number}] ✓ 已切换到 iframe")
            except TimeoutException:
                log_print(f"[{serial_number}] ℹ 未找到任何 iframe，在主页面查找")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 切换 iframe 失败: {str(e)}")
        
        # 在5秒内检查是否有密码输入框 (data-testid="okd-input")
        try:
            log_print(f"[{serial_number}] → 查找密码输入框 (data-testid='okd-input')...")
            password_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='okd-input']"))
            )
            log_print(f"[{serial_number}] ✓ 发现密码输入框，钱包需要解锁")
            
            # 使用 React 兼容的方式输入密码
            try:
                log_print(f"[{serial_number}] → 使用 React 兼容方式输入密码...")
                
                # 使用特殊的方式触发 React 的 value setter
                success = driver.execute_script("""
                    try {
                        const input = arguments[0];
                        const password = arguments[1];
                        
                        // 获取 input 的原生 value setter
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 
                            'value'
                        ).set;
                        
                        // 聚焦输入框
                        input.focus();
                        
                        // 使用原生 setter 设置值（这会触发 React 的监听）
                        nativeInputValueSetter.call(input, password);
                        
                        // 触发 input 事件（React 会监听这个）
                        const inputEvent = new Event('input', { bubbles: true });
                        input.dispatchEvent(inputEvent);
                        
                        // 触发 change 事件
                        const changeEvent = new Event('change', { bubbles: true });
                        input.dispatchEvent(changeEvent);
                        
                        return true;
                    } catch (e) {
                        console.error('输入密码失败:', e);
                        return false;
                    }
                """, password_input, password)
                
                if success:
                    log_print(f"[{serial_number}] ✓ 已输入密码（React 方式）")
                else:
                    log_print(f"[{serial_number}] ⚠ JavaScript 报告输入失败，但继续尝试")
                
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 输入密码失败: {str(e)}")
                # 不抛出异常，返回 True 表示可能已解锁
                driver.switch_to.default_content()
                return True
            
            # 等待按钮从 disabled 变为可点击状态
            log_print(f"[{serial_number}] → 等待解锁按钮变为可点击状态...")
            time.sleep(1)
            
            # 在10秒内找到并等待解锁按钮变为可点击 (去掉 disabled 属性)
            try:
                log_print(f"[{serial_number}] → 查找解锁按钮 (data-testid='okd-button')...")
                # 等待按钮可点击（没有 disabled 属性）
                unlock_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
                )
                log_print(f"[{serial_number}] ✓ 解锁按钮已启用")
                
                log_print(f"[{serial_number}] → 点击解锁按钮...")
                unlock_button.click()
                log_print(f"[{serial_number}] ✓ 已点击解锁按钮")
                
                # 等待解锁完成
                time.sleep(2)
                
                # 切换回主页面
                driver.switch_to.default_content()
                log_print(f"[{serial_number}] ✓ 已切换回主页面")
                
                return True
            except TimeoutException:
                # 切换回主页面
                driver.switch_to.default_content()
                log_print(f"[{serial_number}] ✗ 未找到解锁按钮")
                return False
                
        except TimeoutException:
            # 切换回主页面
            try:
                driver.switch_to.default_content()
            except:
                pass
            log_print(f"[{serial_number}] ℹ 未发现密码输入框，钱包可能已解锁")
            return True
            
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 检查/解锁钱包时出错: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False


# ============================================================================
# Opinion Trade 特定函数
# ============================================================================

def wait_for_opinion_trade_box(driver, serial_number, max_retries=3):
    """
    等待 Opinion Trade 页面加载完成（30秒内每3秒查找一次，超时刷新重试）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
        
    Returns:
        WebElement: trade-box元素，失败返回None
    """
    for attempt in range(max_retries):
        log_print(f"[{serial_number}] [OP] 等待页面加载完成... (尝试 {attempt + 1}/{max_retries})")
        
        # 在30秒内，每隔3秒查找一次
        timeout = 120
        interval = 3
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                elapsed = int(time.time() - start_time)
                log_print(f"[{serial_number}] [OP] 查找 trade-box... ({elapsed}s/{timeout}s)")
                
                # 查找 trade-box
                trade_box = driver.find_element(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                
                if trade_box:
                    log_print(f"[{serial_number}] [OP] ✓ 页面加载成功，找到 trade-box (用时 {elapsed}s)")
                    return trade_box
                
            except Exception as e:
                elapsed = int(time.time() - start_time)
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 trade-box ({elapsed}s/{timeout}s)")
            
            # 等待3秒后重试
            if time.time() - start_time < timeout:
                time.sleep(interval)
        
        # 30秒超时
        log_print(f"[{serial_number}] [OP] ✗ 30秒内未找到 trade-box")
        
        if attempt < max_retries - 1:
            log_print(f"[{serial_number}] [OP] 刷新页面并重试...")
            driver.refresh()
            time.sleep(2)  # 刷新后等待2秒
        else:
            log_print(f"[{serial_number}] [OP] ✗ 页面加载失败，已达到最大重试次数 ({max_retries})")
            return None
    
    return None


def click_opinion_trade_type_button(trade_box, trade_type, serial_number):
    """
    点击 Opinion Trade 的买卖类型按钮
    
    Args:
        trade_box: trade-box元素
        trade_type: Buy 或 Sell
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 {trade_type} 按钮...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                buttons = trade_box.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == trade_type:
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 {trade_type} 按钮")
                        time.sleep(0.5)
                        return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 {trade_type} 按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 {trade_type} 按钮失败: {str(e)}")
        return False


def select_opinion_price_type(trade_box, price_type, serial_number):
    """
    选择 Opinion Trade 的价格类型
    
    Args:
        trade_box: trade-box元素
        price_type: Market 或 Limit
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找价格类型 {price_type}...")
        
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        
        target_p = None
        other_price_type = "Market" if price_type == "Limit" else "Limit"
        other_p = None
        
        for p in p_tags:
            text = p.text.strip()
            if text == price_type:
                target_p = p
                break
            elif text == other_price_type:
                other_p = p
        
        if target_p:
            log_print(f"[{serial_number}] [OP] ✓ 找到目标价格类型 {price_type}")
            return True
        elif other_p:
            log_print(f"[{serial_number}] [OP] 未找到 {price_type}，点击 {other_price_type} 切换...")
            parent = other_p.find_element(By.XPATH, "..")
            parent.click()
            time.sleep(0.5)
            log_print(f"[{serial_number}] [OP] ✓ 已点击切换到 {price_type}")
            return True
        else:
            log_print(f"[{serial_number}] [OP] ✗ 未找到任何价格类型标签")
            return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 选择价格类型失败: {str(e)}")
        return False


def select_opinion_option_type(trade_box, option_type, serial_number):
    """
    选择 Opinion Trade 的种类
    
    Args:
        trade_box: trade-box元素
        option_type: YES 或 NO
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并选择种类 {option_type}...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                # 查找所有具有特定属性的 button
                buttons = trade_box.find_elements(By.CSS_SELECTOR, 'button[data-sentry-element="Button"][data-sentry-source-file="BuySell.tsx"]')
                
                if len(buttons) >= 2:
                    # YES = 第一个按钮，NO = 第二个按钮
                    button_index = 0 if option_type == "YES" else 1
                    target_button = buttons[button_index]
                    
                    log_print(f"[{serial_number}] [OP] ✓ 找到 {option_type} 按钮（第 {button_index + 1} 个）")
                    
                    target_button.click()
                    log_print(f"[{serial_number}] [OP] ✓ 已点击 {option_type} 选项")
                    time.sleep(0.5)
                    
                    # 检查是否激活
                    active_attr = target_button.get_attribute("data-active")
                    if active_attr == "true":
                        log_print(f"[{serial_number}] [OP] ✓ {option_type} 选项已激活")
                        return True
                    else:
                        log_print(f"[{serial_number}] [OP] ⚠ {option_type} 选项未激活")
                        return False
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到足够的按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 选择种类失败: {str(e)}")
        return False


def click_opinion_amount_tab(trade_box, serial_number):
    """
    点击 Opinion Trade 的 Amount 标签
    
    Args:
        trade_box: trade-box元素
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 'Amount' 标签...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                p_tags = trade_box.find_elements(By.TAG_NAME, "p")
                
                for p in p_tags:
                    if p.text.strip() == "Amount":
                        parent = p.find_element(By.XPATH, "..")
                        parent.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 'Amount' 标签")
                        time.sleep(0.5)
                        return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到 'Amount' 标签，继续执行...")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ⚠ 点击 'Amount' 标签失败: {str(e)}，继续执行...")
        return False


def fill_opinion_price_and_amount(trade_box, price, amount, serial_number):
    """
    填入 Opinion Trade 的价格和数量
    
    Args:
        trade_box: trade-box元素
        price: 价格（Market模式时为None）
        amount: 数量
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        inputs = trade_box.find_elements(By.TAG_NAME, "input")
        
        log_print(f"[{serial_number}] [OP] 在 trade-box 下找到 {len(inputs)} 个 input 元素")
        
        if len(inputs) == 0:
            log_print(f"[{serial_number}] [OP] ✗ 未找到任何 input 元素")
            return False
        
        # Market模式：price为None，只填第一个input（数量）
        if price is None:
            log_print(f"[{serial_number}] [OP] Market模式，填入数量到第一个input...")
            amount_input = inputs[0]
            amount_input.clear()
            amount_input.send_keys(str(amount))
            log_print(f"[{serial_number}] [OP] ✓ 已填入数量: {amount}")
            time.sleep(0.3)
        else:
            # Limit模式：填入价格和数量到前两个input
            if len(inputs) < 2:
                log_print(f"[{serial_number}] [OP] ✗ Limit模式需要至少2个input，但只找到 {len(inputs)} 个")
                return False
            
            log_print(f"[{serial_number}] [OP] Limit模式，填入价格和数量...")
            
            # 第一个input填价格
            price_input = inputs[0]
            price_input.clear()
            price_input.send_keys(str(price))
            log_print(f"[{serial_number}] [OP] ✓ 已填入价格: {price}")
            time.sleep(0.3)
            
            # 第二个input填数量
            amount_input = inputs[1]
            amount_input.clear()
            amount_input.send_keys(str(amount))
            log_print(f"[{serial_number}] [OP] ✓ 已填入数量: {amount}")
            time.sleep(0.3)
        
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 填入价格和数量失败: {str(e)}")
        return False


def click_opinion_open_orders_tab(driver, serial_number):
    """
    点击 Opinion Trade 的 "Open Orders" 标签页
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 'Open Orders' 按钮...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Open Orders":
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 'Open Orders' 按钮")
                        time.sleep(1)
                        return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到 'Open Orders' 按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ⚠ 点击 'Open Orders' 失败: {str(e)}")
        return False


def get_opinion_table_row_count(driver, serial_number, need_click_open_orders=False, trending_part1=''):
    """
    获取 Opinion Trade 的table中tr的数量
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        need_click_open_orders: 是否需要先点击 Open Orders 按钮
        trending_part1: 子标题名称，如果有，需要检查tr内p标签内容
        
    Returns:
        int: tr数量，失败返回-1
    """
    try:
        if need_click_open_orders:
            click_opinion_open_orders_tab(driver, serial_number)
        
        # 先找到 data-scope="tabs" 且 id 中包含 "open orders" 的 div
        log_print(f"[{serial_number}] [OP] 查找 open orders 的 div 容器...")
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        
        target_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'open orders' in div_id.lower():
                target_div = div
                log_print(f"[{serial_number}] [OP] 找到目标 div，id: {div_id}")
                break
        
        if not target_div:
            log_print(f"[{serial_number}] [OP] ⚠ 未找到包含 'open orders' 的 div")
            return -1
        
        # 在目标 div 中查找 table
        table = target_div.find_element(By.TAG_NAME, 'table')
        tbody = table.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        count = len(tr_list)
        log_print(f"[{serial_number}] [OP] 当前 table 中有 {count} 个 tr")
        
        # 如果有子标题，需要进一步检查tr内p标签内容
        if trending_part1 and count > 0:
            log_print(f"[{serial_number}] [OP] 检测到子标题 '{trending_part1}'，检查tr内p标签内容...")
            matched_count = 0
            for tr in tr_list:
                try:
                    # 获取tr内所有p标签
                    p_tags = tr.find_elements(By.TAG_NAME, "p")
                    # 检查是否有p标签内容包含子标题
                    for p in p_tags:
                        p_text = p.text.strip()
                        if trending_part1 in p_text:
                            matched_count += 1
                            log_print(f"[{serial_number}] [OP] ✓ 找到匹配的订单，p标签内容: {p_text}")
                            break
                except:
                    continue
            
            log_print(f"[{serial_number}] [OP] 有子标题情况下，匹配的tr数量: {matched_count}")
            return matched_count
        
        return count
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ⚠ 获取 table 行数失败: {str(e)}")
        return -1


def submit_opinion_order(driver, trade_box, trade_type, option_type, serial_number, browser_id, task_data=None):
    """
    提交 Opinion Trade 订单
    
    Args:
        driver: Selenium WebDriver对象
        trade_box: trade-box元素
        trade_type: 买卖类型
        option_type: 种类
        serial_number: 浏览器序列号
        browser_id: 浏览器ID
        task_data: 任务数据（用于type=5的同步机制）
        
    Returns:
        tuple: (success, should_retry_or_msg)
            - (True, True): 成功
            - (False, True): 失败，可以重试
            - (False, False): 失败，不应重试（如type=5点击取消）
            - (False, "msg"): 失败，不应重试，并带有具体失败原因
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找提交订单按钮...")
        
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            text = p.text.strip()
            if trade_type in text and option_type in text:
                log_print(f"[{serial_number}] [OP] ✓ 找到提交按钮，文本: {text}")
                
                parent = p.find_element(By.XPATH, "..")
                parent.click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击提交订单按钮")
                
                time.sleep(2)
                
                # 切换到OKX页面
                log_print(f"[{serial_number}] [OP] 切换到 OKX 钱包页面...")
                all_windows = driver.window_handles
                
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                        log_print(f"[{serial_number}] [OP] ✓ 已切换到 OKX 页面")
                        
                        # 解锁
                        unlock_okx_wallet(driver, serial_number, browser_id)
                        
                        # 点击确认按钮
                        log_print(f"[{serial_number}] [OP] 查找确认按钮...")
                        time.sleep(1)
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        
                        if len(buttons) >= 2:
                            # Type 5 任务需要同步机制
                            mission = task_data.get('mission', {}) if task_data else {}
                            mission_type = mission.get('type')
                            log_print(f"[{serial_number}] [OP] 检测到任务类型: {mission_type}")
                            
                            if task_data and mission_type == 5:
                                log_print(f"[{serial_number}] [OP] Type 5 任务，启动同步机制...")
                                
                                mission_id = mission.get('id')
                                tp1 = mission.get('tp1')  # 任务一的ID
                                
                                if not tp1:
                                    # 任务一：先检查自己的状态，如果是3则直接取消
                                    log_print(f"[{serial_number}] [OP] 任务一: 检查自己的状态...")
                                    current_status = get_mission_status(mission_id)
                                    if current_status == 3:
                                        log_print(f"[{serial_number}] [OP] ✗ 任务一状态为3（任务二导致失败），点击取消按钮")
                                        buttons[0].click()  # 点击取消按钮
                                        return False, "任务二导致失败"
                                    
                                    # 任务一：先通知准备就绪，等待任务二准备就绪
                                    log_print(f"[{serial_number}] [OP] 任务一: 设置状态为5（准备就绪）...")
                                    save_result_success = save_mission_result(mission_id, 5)
                                    if not save_result_success:
                                        save_result_success = save_mission_result(mission_id, 5)
                                        if not save_result_success:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务一设置状态5失败")
                                            return False, True  # 失败，可重试
                                    
                                    log_print(f"[{serial_number}] [OP] 任务一: 等待任务二准备就绪（状态6）...")
                                    # 轮询等待状态变为6
                                    max_wait_time = 600  # 最多等待10分钟
                                    start_time = time.time()
                                    while True:
                                        if time.time() - start_time > max_wait_time:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务一等待任务二超时，点击取消按钮")
                                            buttons[0].click()  # 点击取消按钮
                                            return False, False  # 失败，不可重试
                                        
                                        status = get_mission_status(mission_id)
                                        if status == 6:
                                            log_print(f"[{serial_number}] [OP] ✓ 任务二已准备就绪（状态6）")
                                            break
                                        elif status == 3:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务一状态变为3（任务二失败），点击取消按钮")
                                            buttons[0].click()  # 点击取消按钮
                                            return False, "任务二导致失败"
                                        
                                        time.sleep(10)
                                    
                                    # 点击确认按钮
                                    log_print(f"[{serial_number}] [OP] 任务一: 点击OKX确认按钮...")
                                    buttons[1].click()
                                    log_print(f"[{serial_number}] [OP] ✓ 任务一已点击 OKX 确认按钮")
                                    
                                    # 更改状态为7（任务一已确认）
                                    log_print(f"[{serial_number}] [OP] 任务一: 设置状态为7（已确认）...")
                                    save_result_success = save_mission_result(mission_id, 7)
                                    if not save_result_success:
                                        time.sleep(2)
                                        save_result_success = save_mission_result(mission_id, 7)
                                        if not save_result_success:
                                            log_print(f"[{serial_number}] [OP] ⚠ 任务一设置状态7失败，但已点击确认")
                                    
                                    return True, True  # 成功
                                    
                                else:
                                    # 任务二：等待任务一准备就绪，然后通知任务一可以执行
                                    log_print(f"[{serial_number}] [OP] 任务二: 等待任务一准备就绪（状态5）...")
                                    # 轮询等待任务一状态为5
                                    max_wait_time = 600  # 最多等待10分钟
                                    start_time = time.time()
                                    while True:
                                        if time.time() - start_time > max_wait_time:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务二等待任务一超时")
                                            return False, True  # 失败，可重试
                                        
                                        tp1_status = get_mission_status(tp1)
                                        if tp1_status == 5:
                                            log_print(f"[{serial_number}] [OP] ✓ 任务一已准备就绪（状态5）")
                                            break
                                        elif tp1_status == 3:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务一失败，任务二也失败")
                                            return False, True  # 失败，可重试
                                        
                                        time.sleep(10)
                                    
                                    # 更改任务一状态为6（任务二也准备就绪）
                                    log_print(f"[{serial_number}] [OP] 任务二: 设置任务一状态为6（任务二就绪）...")
                                    save_result_success = save_mission_result(tp1, 6)
                                    if not save_result_success:
                                        log_print(f"[{serial_number}] [OP] ✗ 任务二设置任务一状态6失败")
                                        return False, True  # 失败，可重试
                                    
                                    # 等待任务一点击确认（状态7）
                                    log_print(f"[{serial_number}] [OP] 任务二: 等待任务一点击确认（状态7）...")
                                    start_time = time.time()
                                    while True:
                                        if time.time() - start_time > max_wait_time:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务二等待任务一确认超时，点击取消按钮")
                                            buttons[0].click()  # 点击取消按钮
                                            return False, False  # 失败，不可重试
                                        
                                        tp1_status = get_mission_status(tp1)
                                        if tp1_status == 7 or tp1_status == 2:
                                            time.sleep(5)
                                            log_print(f"[{serial_number}] [OP] ✓ 任务一已点击确认（状态7）")
                                            break
                                        elif tp1_status == 3:
                                            log_print(f"[{serial_number}] [OP] ✗ 任务一失败，任务二也失败，点击取消按钮")
                                            buttons[0].click()  # 点击取消按钮
                                            return False, False  # 失败，不可重试
                                        
                                        time.sleep(10)
                                    
                                    # 点击确认按钮
                                    log_print(f"[{serial_number}] [OP] 任务二: 点击OKX确认按钮...")
                                    buttons[1].click()
                                    log_print(f"[{serial_number}] [OP] ✓ 任务二已点击 OKX 确认按钮")
                                    return True, True  # 成功
                            else:
                                # 普通任务（Type 1），直接点击确认
                                buttons[1].click()
                                log_print(f"[{serial_number}] [OP] ✓ 已点击 OKX 确认按钮")
                                return True, True  # 成功
                        else:
                            log_print(f"[{serial_number}] [OP] ⚠ OKX 按钮数量不足: {len(buttons)}")
                            return False, True  # 失败，可重试
                
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 OKX 页面")
                return False, True  # 失败，可重试
        
        log_print(f"[{serial_number}] [OP] ✗ 未找到提交订单按钮")
        return False, True  # 失败，可重试
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 提交订单失败: {str(e)}")
        return False, True  # 失败，可重试


def check_transaction_fee(driver, serial_number, task_label, is_task1):
    """
    检查 Transactions 中的交易费，判断任务是否真正成功
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        task_label: 任务标签（任务一/任务二）
        is_task1: 是否是任务一
        
    Returns:
        tuple: (transaction_fee, success)
            - transaction_fee: 交易费字符串（例如 "$0.5" 或 "-"）
            - success: 检查是否成功（任务一：交易费为0或空为成功；任务二：交易费>0为成功）
    """
    try:
        # 点击 Transactions 按钮
        log_print(f"[{serial_number}] [{task_label}] 点击 Transactions 按钮...")
        transactions_button_found = False
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if btn.text.strip() == "Transactions":
                btn.click()
                time.sleep(2)
                transactions_button_found = True
                log_print(f"[{serial_number}] [{task_label}] ✓ 已点击 Transactions 按钮")
                break
        
        time.sleep(10)
        if not transactions_button_found:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到 Transactions 按钮")
            return "-", is_task1  # 任务一找不到按钮算成功，任务二算失败
        
        # 查找 Transactions div
        log_print(f"[{serial_number}] [{task_label}] 查找 Transactions div...")
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        transactions_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'content-transactions' in div_id.lower():
                transactions_div = div
                log_print(f"[{serial_number}] [{task_label}] ✓ 找到 Transactions div，id: {div_id}")
                break
        
        if not transactions_div:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到 Transactions div")
            return "-", is_task1  # 任务一找不到div算成功，任务二算失败
        
        # 获取 tbody 和第一个 tr
        tbody = transactions_div.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        if not tr_list or len(tr_list) == 0:
            log_print(f"[{serial_number}] [{task_label}] ⚠ Transactions 中没有 tr")
            return "-", is_task1  # 任务一没有tr算成功，任务二算失败
        
        # 获取第一个 tr 的第 6 个 td 的 div 的 p 标签内容
        first_tr = tr_list[0]
        tds = first_tr.find_elements(By.TAG_NAME, "td")
        
        if len(tds) < 6:
            log_print(f"[{serial_number}] [{task_label}] ⚠ Transactions 第一个 tr 的 td 数量不足6个（实际: {len(tds)}）")
            return "-", is_task1
        
        # 第6个td（index=5）
        td6 = tds[5]
        td6_ps = td6.find_elements(By.TAG_NAME, "p")
        transaction_fee_text = td6_ps[0].text.strip() if td6_ps else "-"
        
        log_print(f"[{serial_number}] [{task_label}] Transactions 交易费: {transaction_fee_text}")
        
        # 解析交易费数字
        fee_value = 0.0
        try:
            # 移除 $ 符号和其他非数字字符，只保留数字和小数点
            import re
            fee_number_str = re.sub(r'[^\d.]', '', transaction_fee_text)
            if fee_number_str and fee_number_str != '':
                fee_value = float(fee_number_str)
            log_print(f"[{serial_number}] [{task_label}] 解析后的交易费数值: {fee_value}")
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 解析交易费失败: {str(e)}，原始文本: {transaction_fee_text}")
            fee_value = 0.0
        
        # 判断逻辑
        if is_task1:
            # 任务一：交易费为0、空、"-" 或无法解析数字 → 成功；反之失败
            if transaction_fee_text == "-" or transaction_fee_text == "" or fee_value == 0:
                log_print(f"[{serial_number}] [{task_label}] ✓ 任务一：交易费为0或空，检查通过")
                return transaction_fee_text, True
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 任务一：交易费不为0（{fee_value}），检查失败")
                return transaction_fee_text, False
        else:
            # 任务二：交易费有值且大于0 → 成功；反之失败
            if transaction_fee_text != "-" and transaction_fee_text != "" and fee_value > 0:
                log_print(f"[{serial_number}] [{task_label}] ✓ 任务二：交易费大于0（{fee_value}），检查通过")
                return transaction_fee_text, True
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 任务二：交易费为0或空，检查失败")
                return transaction_fee_text, False
        
    except Exception as e:
        log_print(f"[{serial_number}] [{task_label}] ✗ 检查 Transactions 失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [{task_label}] 错误详情:\n{traceback.format_exc()}")
        return "-", is_task1  # 异常时，任务一算成功，任务二算失败


def get_position_filled_amount(driver, serial_number, trending_part1):
    """
    获取Position中的已成交数量
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        trending_part1: 子标题（用于筛选）
        
    Returns:
        str: 已成交数量，失败返回""
    """
    try:
        # 点击Position按钮
        log_print(f"[{serial_number}] 点击Position按钮...")
        position_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn') and contains(text(), 'Position')]")
        position_button.click()
        time.sleep(2)
        
        # 查找tbody
        tbody = driver.find_element(By.CSS_SELECTOR, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        if not tr_list:
            log_print(f"[{serial_number}] ⚠ 没有Position数据")
            return ""
        
        # 如果有子标题，需要找到匹配的行
        if trending_part1:
            log_print(f"[{serial_number}] 有子标题，查找匹配行: {trending_part1}")
            for tr_idx, tr in enumerate(tr_list, 1):
                try:
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if not tds:
                        continue
                    
                    # 检查第一个td是否包含子标题
                    first_td = tds[0]
                    p_tags = first_td.find_elements(By.TAG_NAME, "p")
                    
                    if len(p_tags) == 2:
                        # 有两个p标签，说明这是子标题行
                        subtitle_text = p_tags[1].text.strip()
                        if subtitle_text == trending_part1:
                            # 找到匹配的行，获取第2个td的已成交数量
                            if len(tds) > 1:
                                td2_ps = tds[1].find_elements(By.TAG_NAME, "p")
                                filled_amount = td2_ps[0].text.strip() if td2_ps else ""
                                log_print(f"[{serial_number}] ✓ 找到匹配行，已成交数量: {filled_amount}")
                                return filled_amount
                except Exception as e:
                    log_print(f"[{serial_number}] ⚠ 解析Position行{tr_idx}失败: {str(e)}")
                    continue
            
            log_print(f"[{serial_number}] ⚠ 未找到匹配的子标题行")
            return ""
        else:
            # 无子标题，获取第一行数据
            try:
                first_tr = tr_list[0]
                tds = first_tr.find_elements(By.TAG_NAME, "td")
                if len(tds) > 1:
                    td2_ps = tds[1].find_elements(By.TAG_NAME, "p")
                    filled_amount = td2_ps[0].text.strip() if td2_ps else ""
                    log_print(f"[{serial_number}] ✓ 获取第一行已成交数量: {filled_amount}")
                    return filled_amount
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 获取第一行数据失败: {str(e)}")
                return ""
        
        return ""
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 获取Position已成交数量失败: {str(e)}")
        return ""


def wait_for_type5_order_and_collect_data(driver, initial_position_count, serial_number, trending_part1, task_data, trade_type):
    """
    Type 5 任务专用：等待订单成功并收集数据
    
    Args:
        driver: Selenium WebDriver对象
        initial_position_count: 初始 Position 行数
        serial_number: 浏览器序列号
        trending_part1: 子标题（用于筛选）
        task_data: 任务数据
        trade_type: Buy 或 Sell
        
    Returns:
        tuple: (success, msg)
    """
    mission = task_data.get('mission', {})
    mission_id = mission.get('id')
    tp1 = mission.get('tp1')  # 如果是任务二，这里有任务一的ID
    
    # 判断当前是任务一还是任务二
    is_task1 = not tp1
    task_label = "任务一" if is_task1 else "任务二"
    target_mission_id = mission_id if is_task1 else tp1  # 需要操作的任务ID（始终是任务一）
    
    log_print(f"[{serial_number}] [{task_label}] Type 5 专用等待流程开始...")
    log_print(f"[{serial_number}] [{task_label}] 交易类型: {trade_type}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Position 数量: {initial_position_count}")
    
    # 切换回主页面
    try:
        all_windows = driver.window_handles
        for window in all_windows:
            driver.switch_to.window(window)
            current_url = driver.current_url
            if "app.opinion.trade" in current_url:
                log_print(f"[{serial_number}] [{task_label}] ✓ 已切换回主页面")
                break
    except Exception as e:
        log_print(f"[{serial_number}] [{task_label}] ⚠ 切换回主页面失败: {str(e)}")
        return False, "切换页面失败"
    
    # 如果是Sell类型，获取初始已成交数量
    initial_filled_amount = ""
    if trade_type == "Sell":
        log_print(f"[{serial_number}] [{task_label}] Sell类型，获取初始已成交数量...")
        initial_filled_amount = get_position_filled_amount(driver, serial_number, trending_part1)
        log_print(f"[{serial_number}] [{task_label}] 初始已成交数量: {initial_filled_amount}")
    
    # 第一阶段：检测Position变化（10分钟超时）
    if trade_type == "Buy":
        log_print(f"[{serial_number}] [{task_label}] ========== 第一阶段：检测Position数量增加 ==========")
    else:
        log_print(f"[{serial_number}] [{task_label}] ========== 第一阶段：检测Position已成交数量变化 ==========")
    
    phase1_timeout = 600  # 10分钟
    check_interval = 20 if trade_type == "Sell" else 60  # Sell每20秒检查，Buy每60秒检查
    refresh_interval = 180  # 每3分钟刷新一次
    
    phase1_start_time = time.time()
    last_refresh_time = phase1_start_time
    position_changed = False
    
    time.sleep(10)
    while time.time() - phase1_start_time < phase1_timeout:
        try:
            elapsed = int(time.time() - phase1_start_time)
            log_print(f"[{serial_number}] [{task_label}] 检查Position（已用时 {elapsed}秒）...")
            
            # 对于Buy类型，每3分钟刷新；Sell类型不刷新
            if trade_type == "Buy" and time.time() - last_refresh_time >= refresh_interval:
                log_print(f"[{serial_number}] [{task_label}] 3分钟无变化，刷新页面...")
                driver.refresh()
                time.sleep(5)
                last_refresh_time = time.time()
            
            if trade_type == "Buy":
                # Buy类型：检查Position数量是否增加
                current_position_count = check_position_count(driver, serial_number, trending_part1)
                
                if current_position_count < 0:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取 Position 数量")
                else:
                    log_print(f"[{serial_number}] [{task_label}] 当前 Position 数量: {current_position_count} (初始: {initial_position_count})")
                    
                    if current_position_count > initial_position_count:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Position增加！")
                        position_changed = True
                        
                        # 更新任务一的状态
                        current_status = get_mission_status(target_mission_id)
                        log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}")
                        
                        if is_task1:
                            # 任务一检测到变化
                            if current_status == 9:
                                # 任务一状态已经是9，改为10
                                log_print(f"[{serial_number}] [{task_label}] 任务一状态为9，更改为10...")
                                save_mission_result(target_mission_id, 10)
                            else:
                                # 任务一检测到变化，改为8
                                log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为8...")
                                save_mission_result(target_mission_id, 8)
                        else:
                            # 任务二检测到变化
                            if current_status == 8:
                                # 任务一状态已经是8，改为10
                                log_print(f"[{serial_number}] [{task_label}] 任务一状态为8，更改为10...")
                                save_mission_result(target_mission_id, 10)
                            else:
                                # 任务二检测到变化，改为9
                                log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，更改任务一状态为9...")
                                save_mission_result(target_mission_id, 9)
                        
                        break
            else:
                # Sell类型：检查已成交数量是否变化
                current_filled_amount = get_position_filled_amount(driver, serial_number, trending_part1)
                
                if not current_filled_amount:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取已成交数量")
                else:
                    log_print(f"[{serial_number}] [{task_label}] 当前已成交数量: {current_filled_amount} (初始: {initial_filled_amount})")
                    
                    if current_filled_amount != initial_filled_amount:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到已成交数量变化！")
                        position_changed = True
                        
                        # 更新任务一的状态
                        current_status = get_mission_status(target_mission_id)
                        log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}")
                        
                        if is_task1:
                            # 任务一检测到变化
                            if current_status == 9:
                                # 任务一状态已经是9，改为10
                                log_print(f"[{serial_number}] [{task_label}] 任务一状态为9，更改为10...")
                                save_mission_result(target_mission_id, 10)
                            else:
                                # 任务一检测到变化，改为8
                                log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为8...")
                                save_mission_result(target_mission_id, 8)
                        else:
                            # 任务二检测到变化
                            if current_status == 8:
                                # 任务一状态已经是8，改为10
                                log_print(f"[{serial_number}] [{task_label}] 任务一状态为8，更改为10...")
                                save_mission_result(target_mission_id, 10)
                            else:
                                # 任务二检测到变化，改为9
                                log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，更改任务一状态为9...")
                                save_mission_result(target_mission_id, 9)
                        
                        break
            
            time.sleep(check_interval)
            
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 检查Position时出错: {str(e)}")
            time.sleep(check_interval)
    
    if not position_changed:
        log_print(f"[{serial_number}] [{task_label}] ✗ Position未检测到变化，超时")
        return False, "Position未检测到变化超时"
    
    # 第二阶段：轮询任务一状态，等待状态变为10（10分钟超时，每10秒检查一次）
    log_print(f"[{serial_number}] [{task_label}] ========== 第二阶段：轮询任务状态 ==========")
    phase2_timeout = 600  # 10分钟
    phase2_check_interval = 10  # 每10秒检查一次
    phase2_start_time = time.time()
    status_is_10 = False
    
    while time.time() - phase2_start_time < phase2_timeout:
        try:
            elapsed = int(time.time() - phase2_start_time)
            current_status = get_mission_status(target_mission_id)
            log_print(f"[{serial_number}] [{task_label}] 轮询任务一状态: {current_status}（已用时 {elapsed}秒）")
            
            if current_status == 10:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到任务一状态为10！")
                status_is_10 = True
                break
            
            time.sleep(phase2_check_interval)
            
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 轮询任务状态时出错: {str(e)}")
            time.sleep(phase2_check_interval)
    
    if not status_is_10:
        log_print(f"[{serial_number}] [{task_label}] ✗ 检测吃单超时")
        return False, "检测吃单超时"
    
    # 第三阶段：获取Position和Open Orders的详细数据
    log_print(f"[{serial_number}] [{task_label}] ========== 第三阶段：收集数据 ==========")
    
    try:
        # 点击Position
        log_print(f"[{serial_number}] [{task_label}] 点击Position按钮...")
        position_buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in position_buttons:
            if btn.text.strip() == "Position":
                btn.click()
                time.sleep(7)
                break
        
        # 获取Position数据
        log_print(f"[{serial_number}] [{task_label}] 获取Position数据...")
        
        # 查找 Position div
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        position_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'content-position' in div_id.lower():
                position_div = div
                break
        
        if not position_div:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Position div")
            return False, "未找到Position数据"
        
        # 获取 tbody 和 tr
        tbody = position_div.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        if not tr_list or len(tr_list) == 0:
            log_print(f"[{serial_number}] [{task_label}] ⚠ Position中没有tr")
            return False, "Position中没有数据"
        
        # 等待tr中的内容完全加载
        log_print(f"[{serial_number}] [{task_label}] 等待tr内容加载...")
        time.sleep(3)
        
        filled_amount = ""
        filled_price = ""
        
        if trending_part1:
            # 有子标题：找到包含子标题的tr
            log_print(f"[{serial_number}] [{task_label}] 有子标题，查找包含 '{trending_part1}' 的行...")
            for tr in tr_list:
                try:
                    # 获取第一个td的div下的p标签
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) > 0:
                        first_td_ps = tds[0].find_elements(By.TAG_NAME, "p")
                        first_td_text = " ".join([p.text.strip() for p in first_td_ps])
                        if trending_part1 in first_td_text:
                            log_print(f"[{serial_number}] [{task_label}] ✓ 找到包含子标题的行")
                            # 【DEBUG】打印所有td的详细内容
                            log_print(f"[{serial_number}] [{task_label}] === 开始打印该tr下所有td的详细内容 ===")
                            for td_idx, td in enumerate(tds):
                                # 方法1：直接获取td.text
                                td_text = td.text.strip()
                                # 方法2：查找p标签
                                td_ps = td.find_elements(By.TAG_NAME, "p")
                                td_p_texts = [p.text.strip() for p in td_ps]
                                # 方法3：查找div标签
                                td_divs = td.find_elements(By.TAG_NAME, "div")
                                # 方法4：获取innerHTML
                       
                                log_print(f"[{serial_number}] [{task_label}] TD[{td_idx}]:")
                                log_print(f"[{serial_number}] [{task_label}]   - td.text: '{td_text}'")
                                log_print(f"[{serial_number}] [{task_label}]   - p标签: {td_p_texts}")
                                log_print(f"[{serial_number}] [{task_label}]   - div数量: {len(td_divs)}")
              
                            log_print(f"[{serial_number}] [{task_label}] === 打印完毕 ===")
                            # 第2个td（index=1）：已成交数量
                            if len(tds) > 1:
                                td2_ps = tds[1].find_elements(By.TAG_NAME, "p")
                                filled_amount = td2_ps[0].text.strip() if td2_ps else ""
                            # 第4个td（index=3）：价格
                            if len(tds) > 3:
                                td4_ps = tds[3].find_elements(By.TAG_NAME, "p")
                                filled_price = td4_ps[0].text.strip() if td4_ps else ""
                            break
                except Exception as e:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 解析Position行失败: {str(e)}")
                    continue
        else:
            # 无子标题：第一个tr
            log_print(f"[{serial_number}] [{task_label}] 无子标题，获取第一行数据...")
            try:
                first_tr = tr_list[0]
                tds = first_tr.find_elements(By.TAG_NAME, "td")
                # 【DEBUG】打印所有td的详细内容
                log_print(f"[{serial_number}] [{task_label}] === 开始打印该tr下所有td的详细内容 ===")
                for td_idx, td in enumerate(tds):
                    # 方法1：直接获取td.text
                    td_text = td.text.strip()
                    # 方法2：查找p标签
                    td_ps = td.find_elements(By.TAG_NAME, "p")
                    td_p_texts = [p.text.strip() for p in td_ps]
                    # 方法3：查找div标签
                    td_divs = td.find_elements(By.TAG_NAME, "div")
       
                    
                    log_print(f"[{serial_number}] [{task_label}] TD[{td_idx}]:")
                    log_print(f"[{serial_number}] [{task_label}]   - td.text: '{td_text}'")
                    log_print(f"[{serial_number}] [{task_label}]   - p标签: {td_p_texts}")
                    log_print(f"[{serial_number}] [{task_label}]   - div数量: {len(td_divs)}")
 
                log_print(f"[{serial_number}] [{task_label}] === 打印完毕 ===")
                # 第2个td（index=1）：已成交数量
                if len(tds) > 1:
                    td2_ps = tds[1].find_elements(By.TAG_NAME, "p")
                    filled_amount = td2_ps[0].text.strip() if td2_ps else ""
                # 第4个td（index=3）：价格
                if len(tds) > 3:
                    td4_ps = tds[3].find_elements(By.TAG_NAME, "p")
                    filled_price = td4_ps[0].text.strip() if td4_ps else ""
            except Exception as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 获取Position数据失败: {str(e)}")
        
        log_print(f"[{serial_number}] [{task_label}] Position数据 - 已成交数量: {filled_amount}, 价格: {filled_price}")
        
        # 点击Open Orders
        log_print(f"[{serial_number}] [{task_label}] 点击Open Orders按钮...")
        open_orders_buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in open_orders_buttons:
            if btn.text.strip() == "Open Orders":
                btn.click()
                time.sleep(7)
                break
        
        # 获取Open Orders数据
        log_print(f"[{serial_number}] [{task_label}] 获取Open Orders数据...")
        
        # 查找 Open Orders div
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        open_orders_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'open orders' in div_id.lower():
                open_orders_div = div
                break
        
        if not open_orders_div:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Open Orders div")
            # 没找到div，检查 Transactions
            transaction_fee, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = initial_filled_amount
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 无挂单且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 无挂单但交易费检查失败，任务失败")
                return False, msg
        
        # 获取 tbody 和 tr
        try:
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        except:
            # 没有tbody或tr，说明没有挂单
            transaction_fee, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = initial_filled_amount
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 无挂单且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 无挂单但交易费检查失败，任务失败")
                return False, msg
        
        if not tr_list or len(tr_list) == 0:
            # 没有tr，说明没有挂单
            transaction_fee, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = initial_filled_amount
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 无挂单且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 无挂单但交易费检查失败，任务失败")
                return False, msg
        
        # 有Open Orders，任务失败，需要获取挂单价格和进度
        pending_price = ""
        progress = ""
        
        if trending_part1:
            # 有子标题：找到包含子标题的tr
            log_print(f"[{serial_number}] [{task_label}] 有子标题，查找包含 '{trending_part1}' 的挂单...")
            for tr in tr_list:
                try:
                    # 获取第二个td的div下的p标签
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) > 1:
                        second_td_ps = tds[1].find_elements(By.TAG_NAME, "p")
                        second_td_text = " ".join([p.text.strip() for p in second_td_ps])
                        if trending_part1 in second_td_text:
                            log_print(f"[{serial_number}] [{task_label}] ✓ 找到包含子标题的挂单")
                            # 第4个td（index=3）：挂单价格
                            if len(tds) > 3:
                                td4_ps = tds[3].find_elements(By.TAG_NAME, "p")
                                pending_price = td4_ps[0].text.strip() if td4_ps else ""
                            # 第6个td（index=5）：进度
                            if len(tds) > 5:
                                td6_ps = tds[5].find_elements(By.TAG_NAME, "p")
                                progress = " ".join([p.text.strip() for p in td6_ps])
                            break
                except Exception as e:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 解析Open Orders行失败: {str(e)}")
                    continue
        else:
            # 无子标题：第一个tr
            log_print(f"[{serial_number}] [{task_label}] 无子标题，获取第一行挂单数据...")
            try:
                first_tr = tr_list[0]
                tds = first_tr.find_elements(By.TAG_NAME, "td")
                # 第4个td（index=3）：挂单价格
                if len(tds) > 3:
                    td4_ps = tds[3].find_elements(By.TAG_NAME, "p")
                    pending_price = td4_ps[0].text.strip() if td4_ps else ""
                # 第6个td（index=5）：进度
                if len(tds) > 5:
                    td6_ps = tds[5].find_elements(By.TAG_NAME, "p")
                    progress = " ".join([p.text.strip() for p in td6_ps])
            except Exception as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 获取Open Orders数据失败: {str(e)}")
        
        log_print(f"[{serial_number}] [{task_label}] Open Orders数据 - 挂单价格: {pending_price}, 进度: {progress}")
        
        # 有挂单，获取交易费
        transaction_fee, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1)
        
        # 有挂单，任务失败
        import json
        msg_data = {
            "type": "TYPE5_PARTIAL",
            "filled_amount": filled_amount,
            "filled_price": filled_price,
            "pending_price": pending_price,
            "progress": progress,
            "transaction_fee": transaction_fee
        }
        
        # Sell类型添加原数量
        if trade_type == "Sell":
            msg_data["initial_filled_amount"] = initial_filled_amount
        
        msg = json.dumps(msg_data, ensure_ascii=False)
        log_print(f"[{serial_number}] [{task_label}] ✗ 有挂单，任务失败")
        log_print(f"[{serial_number}] [{task_label}] 结果详情:")
        if trade_type == "Sell":
            log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_filled_amount}")
        log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
        log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
        log_print(f"[{serial_number}] [{task_label}]   挂单价格: {pending_price}")
        log_print(f"[{serial_number}] [{task_label}]   挂单进度: {progress}")
        log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
        return False, msg
        
    except Exception as e:
        log_print(f"[{serial_number}] [{task_label}] ✗ 收集数据失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [{task_label}] 错误详情:\n{traceback.format_exc()}")
        return False, f"收集数据失败: {str(e)}"


def wait_for_opinion_order_success(driver, initial_open_orders_count, initial_position_count, trade_type, serial_number, trending_part1='', timeout=600):
    """
    等待 Opinion Trade 订单成功（交替检查 Open Orders 和 Position）
    
    Args:
        driver: Selenium WebDriver对象
        initial_open_orders_count: 初始 Open Orders 行数
        initial_position_count: 初始 Position 行数
        trade_type: 交易类型（Buy/Sell）
        serial_number: 浏览器序列号
        trending_part1: 子标题（用于筛选）
        timeout: 超时时间（默认10分钟）
        
    Returns:
        bool: 成功返回True
    """
    log_print(f"[{serial_number}] [OP] 开始监测订单状态...")
    log_print(f"[{serial_number}] [OP] 交易类型: {trade_type}")
    log_print(f"[{serial_number}] [OP] 初始 Open Orders 数量: {initial_open_orders_count}")
    log_print(f"[{serial_number}] [OP] 初始 Position 数量: {initial_position_count}")
    
    start_time = time.time()
    check_interval = 60  # 每隔1分钟检查一次
    
    # 切换回主页面
    try:
        all_windows = driver.window_handles
        for window in all_windows:
            driver.switch_to.window(window)
            current_url = driver.current_url
            if "app.opinion.trade" in current_url:
                log_print(f"[{serial_number}] [OP] ✓ 已切换回主页面")
                break
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ⚠ 切换回主页面失败: {str(e)}")
    
    # 交替检查标志：True=检查Open Orders，False=检查Position
    # 第一次先检查 Open Orders
    check_open_orders = True
    
    while time.time() - start_time < timeout:
        try:
            elapsed = int(time.time() - start_time)
            log_print(f"[{serial_number}] [OP] ========== 第 {elapsed // 60 + 1} 次检查（已用时 {elapsed}秒）==========")
            
            if check_open_orders:
                # 检查 Open Orders
                log_print(f"[{serial_number}] [OP] 检查 Open Orders...")
                current_open_orders_count = get_opinion_table_row_count(
                    driver, 
                    serial_number, 
                    need_click_open_orders=True, 
                    trending_part1=trending_part1
                )
                
                if current_open_orders_count < 0:
                    log_print(f"[{serial_number}] [OP] ⚠ 无法获取 Open Orders 数量")
                else:
                    log_print(f"[{serial_number}] [OP] 当前 Open Orders 数量: {current_open_orders_count} (初始: {initial_open_orders_count})")
                    
                    if trade_type == "Buy":
                        # Buy 类型：挂单数量增加即成功
                        if current_open_orders_count > initial_open_orders_count:
                            log_print(f"[{serial_number}] [OP] ✓✓✓ Buy 订单成功！Open Orders 从 {initial_open_orders_count} 增加到 {current_open_orders_count}")
                            return True
                    else:  # Sell
                        # Sell 类型：挂单数量增加即成功
                        if current_open_orders_count > initial_open_orders_count:
                            log_print(f"[{serial_number}] [OP] ✓✓✓ Sell 订单成功！Open Orders 从 {initial_open_orders_count} 增加到 {current_open_orders_count}")
                            return True
                
                # 下次检查 Position
                check_open_orders = False
                
            else:
                # 检查 Position
                log_print(f"[{serial_number}] [OP] 检查 Position...")
                current_position_count = check_position_count(driver, serial_number, trending_part1)
                
                if current_position_count < 0:
                    log_print(f"[{serial_number}] [OP] ⚠ 无法获取 Position 数量")
                else:
                    log_print(f"[{serial_number}] [OP] 当前 Position 数量: {current_position_count} (初始: {initial_position_count})")
                    
                    if trade_type == "Buy":
                        # Buy 类型：仓位数量增加即成功
                        if current_position_count > initial_position_count:
                            log_print(f"[{serial_number}] [OP] ✓✓✓ Buy 订单成功！Position 从 {initial_position_count} 增加到 {current_position_count}")
                            return True
                    else:  # Sell
                        # Sell 类型：仓位数量减少即成功
                        if current_position_count < initial_position_count:
                            log_print(f"[{serial_number}] [OP] ✓✓✓ Sell 订单成功！Position 从 {initial_position_count} 减少到 {current_position_count}")
                            return True
                
                # 下次检查 Open Orders
                check_open_orders = True
            
            log_print(f"[{serial_number}] [OP] 等待 {check_interval} 秒后继续检查...")
            time.sleep(check_interval)
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 检查订单状态时出错: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] [OP] 错误详情:\n{traceback.format_exc()}")
            time.sleep(check_interval)
    
    log_print(f"[{serial_number}] [OP] ✗ 等待订单超时（{timeout}秒）")
    return False


# ============================================================================
# Polymarket 特定函数
# ============================================================================

def wait_for_polymarket_trade_box(driver, serial_number, max_retries=3):
    """
    等待 Polymarket 页面加载完成
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
        
    Returns:
        WebElement: 交易区域元素，失败返回None
    """
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] [POLY] 等待页面加载完成... (尝试 {attempt + 1}/{max_retries})")
            
            time.sleep(2)
            
            # 查找交易区域
            trade_box = driver.find_element(By.CSS_SELECTOR, 'div.c-dhzjXW.c-fSirSU')
            
            if trade_box:
                log_print(f"[{serial_number}] [POLY] ✓ 页面加载成功，找到交易区域")
                return trade_box
            
        except Exception as e:
            log_print(f"[{serial_number}] [POLY] ⚠ 未找到交易区域: {str(e)}")
            
            if attempt < max_retries - 1:
                log_print(f"[{serial_number}] [POLY] 刷新页面并重试...")
                driver.refresh()
            else:
                log_print(f"[{serial_number}] [POLY] ✗ 页面加载失败，已达到最大重试次数")
                return None
    
    return None


def click_polymarket_trade_type_button(trade_box, trade_type, serial_number):
    """
    点击 Polymarket 的买卖类型按钮
    
    Args:
        trade_box: 交易区域元素
        trade_type: Buy 或 Sell
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [POLY] 在10秒内查找并点击 {trade_type} 按钮...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                buttons = trade_box.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if trade_type in button.text:
                        button.click()
                        log_print(f"[{serial_number}] [POLY] ✓ 已点击 {trade_type} 按钮")
                        time.sleep(0.5)
                        return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [POLY] ✗ 10秒内未找到 {trade_type} 按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 点击 {trade_type} 按钮失败: {str(e)}")
        return False


def select_polymarket_price_type(trade_box, price_type, serial_number):
    """
    选择 Polymarket 的价格类型
    
    Args:
        trade_box: 交易区域元素
        price_type: Market 或 Limit
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [POLY] 查找价格类型 {price_type}...")
        
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        
        target_p = None
        other_price_type = "Market" if price_type == "Limit" else "Limit"
        other_p = None
        
        for p in p_tags:
            text = p.text.strip()
            if text == price_type:
                target_p = p
                break
            elif text == other_price_type:
                other_p = p
        
        if target_p:
            log_print(f"[{serial_number}] [POLY] ✓ 找到目标价格类型 {price_type}")
            return True
        elif other_p:
            log_print(f"[{serial_number}] [POLY] 未找到 {price_type}，点击 {other_price_type} 的父节点切换...")
            parent = other_p.find_element(By.XPATH, "..")
            parent.click()
            time.sleep(0.5)
            log_print(f"[{serial_number}] [POLY] ✓ 已点击切换到 {price_type}")
            return True
        else:
            log_print(f"[{serial_number}] [POLY] ✗ 未找到任何价格类型标签")
            return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 选择价格类型失败: {str(e)}")
        return False


def select_polymarket_option_type(trade_box, option_type, serial_number):
    """
    选择 Polymarket 的种类
    
    Args:
        trade_box: 交易区域元素
        option_type: Yes 或 No
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [POLY] 在10秒内查找并选择种类 {option_type}...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                p_tags = trade_box.find_elements(By.TAG_NAME, "p")
                
                for p in p_tags:
                    if p.text.strip() == option_type:
                        # 点击4级父节点
                        parent1 = p.find_element(By.XPATH, "..")
                        parent2 = parent1.find_element(By.XPATH, "..")
                        parent4 = parent2.find_element(By.XPATH, "..")
                        
                        parent4.click()
                        log_print(f"[{serial_number}] [POLY] ✓ 已点击 {option_type} 选项（4级父节点）")
                        time.sleep(1)
                        
                        # 检查 aria-checked
                        aria_checked = parent4.get_attribute("aria-checked")
                        if aria_checked == "true":
                            log_print(f"[{serial_number}] [POLY] ✓ {option_type} 选项已激活")
                            return True
                        else:
                            log_print(f"[{serial_number}] [POLY] ⚠ {option_type} 选项未激活")
                            return False
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [POLY] ✗ 10秒内未找到 {option_type} 选项")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 选择种类失败: {str(e)}")
        return False


def fill_polymarket_price_and_amount(trade_box, price, amount, serial_number):
    """
    填入 Polymarket 的价格和数量
    
    Args:
        trade_box: 交易区域元素
        price: 价格（Market模式时为None）
        amount: 数量
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        inputs = trade_box.find_elements(By.TAG_NAME, "input")
        
        log_print(f"[{serial_number}] [POLY] 在 trade-box 下找到 {len(inputs)} 个 input 元素")
        
        if len(inputs) == 0:
            log_print(f"[{serial_number}] [POLY] ✗ 未找到任何 input 元素")
            return False
        
        # Market模式：price为None，只填第一个input（数量）
        if price is None:
            log_print(f"[{serial_number}] [POLY] Market模式，填入数量到第一个input...")
            amount_input = inputs[0]
            amount_input.clear()
            amount_input.send_keys(str(amount))
            log_print(f"[{serial_number}] [POLY] ✓ 已填入数量: {amount}")
            time.sleep(0.3)
        else:
            # Limit模式：填入价格和数量到前两个input
            if len(inputs) < 2:
                log_print(f"[{serial_number}] [POLY] ✗ Limit模式需要至少2个input，但只找到 {len(inputs)} 个")
                return False
            
            log_print(f"[{serial_number}] [POLY] Limit模式，填入价格和数量...")
            
            # 第一个input填价格
            price_input = inputs[0]
            price_input.clear()
            price_input.send_keys(str(price))
            log_print(f"[{serial_number}] [POLY] ✓ 已填入价格: {price}")
            time.sleep(0.3)
            
            # 第二个input填数量
            amount_input = inputs[1]
            amount_input.clear()
            amount_input.send_keys(str(amount))
            log_print(f"[{serial_number}] [POLY] ✓ 已填入数量: {amount}")
            time.sleep(0.3)
        
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 填入价格和数量失败: {str(e)}")
        return False


def get_polymarket_open_orders_count(driver, serial_number):
    """
    获取 Polymarket Open Orders 中的订单数量
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        int: 订单数量，失败返回-1
    """
    try:
        log_print(f"[{serial_number}] [POLY] 查找 Open Orders 区域...")
        
        h3_tags = driver.find_elements(By.TAG_NAME, "h3")
        
        open_orders_h3 = None
        for h3 in h3_tags:
            if h3.text.strip() == "Open Orders":
                open_orders_h3 = h3
                break
        
        if not open_orders_h3:
            log_print(f"[{serial_number}] [POLY] 未找到 'Open Orders' h3 标签，订单数量为 0")
            return 0
        
        # 找到父节点的父节点
        parent1 = open_orders_h3.find_element(By.XPATH, "..")
        openordersbox = parent1.find_element(By.XPATH, "..")
        
        log_print(f"[{serial_number}] [POLY] ✓ 找到 Open Orders 区域")
        
        # 获取子节点
        children = openordersbox.find_elements(By.XPATH, "./*")
        
        if len(children) < 2:
            log_print(f"[{serial_number}] [POLY] Open Orders 区域子节点不足，订单数量为 0")
            return 0
        
        # 获取第二个子节点
        second_child = children[1]
        
        # 获取第二个子节点下的所有子节点数量
        order_items = second_child.find_elements(By.XPATH, "./*")
        count = len(order_items)
        
        log_print(f"[{serial_number}] [POLY] Open Orders 中有 {count} 个订单")
        return count
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ⚠ 获取 Open Orders 订单数量失败: {str(e)}")
        return -1


def submit_polymarket_order(driver, trade_box, serial_number, browser_id):
    """
    提交 Polymarket 订单
    
    Args:
        driver: Selenium WebDriver对象
        trade_box: 交易区域元素
        serial_number: 浏览器序列号
        browser_id: 浏览器ID
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [POLY] 查找提交订单按钮...")
        
        try:
            submit_button = driver.find_element(By.CSS_SELECTOR, 'button.c-bDcLpV.c-bDcLpV-fLyPyt-color-blue.c-bDcLpV-ileGDsu-css')
            log_print(f"[{serial_number}] [POLY] ✓ 找到提交按钮")
            
            submit_button.click()
            log_print(f"[{serial_number}] [POLY] ✓ 已点击提交订单按钮")
            
            time.sleep(3)
            
            # 切换到OKX页面
            log_print(f"[{serial_number}] [POLY] 切换到 OKX 钱包页面...")
            all_windows = driver.window_handles
            
            for window in all_windows:
                driver.switch_to.window(window)
                current_url = driver.current_url
                if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                    log_print(f"[{serial_number}] [POLY] ✓ 已切换到 OKX 页面")
                    
                    # 解锁
                    unlock_okx_wallet(driver, serial_number, browser_id)
                    
                    # 点击确认按钮
                    log_print(f"[{serial_number}] [POLY] 查找确认按钮...")
                    time.sleep(1)
                    buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                    
                    if len(buttons) >= 2:
                        buttons[1].click()
                        log_print(f"[{serial_number}] [POLY] ✓ 已点击 OKX 确认按钮")
                        
                        # 切换回主页面
                        time.sleep(1)
                        for window in driver.window_handles:
                            driver.switch_to.window(window)
                            if "polymarket.com" in driver.current_url:
                                log_print(f"[{serial_number}] [POLY] ✓ 已切换回主页面")
                                break
                        
                        return True
                    else:
                        log_print(f"[{serial_number}] [POLY] ⚠ OKX 按钮数量不足: {len(buttons)}")
                        return False
            
            log_print(f"[{serial_number}] [POLY] ⚠ 未找到 OKX 页面")
            return False
            
        except Exception as e:
            log_print(f"[{serial_number}] [POLY] ✗ 未找到提交按钮: {str(e)}")
            return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 提交订单失败: {str(e)}")
        return False


def wait_for_polymarket_order_success(driver, initial_count, serial_number, timeout=60):
    """
    等待 Polymarket 订单成功
    
    Args:
        driver: Selenium WebDriver对象
        initial_count: 初始订单数量
        serial_number: 浏览器序列号
        timeout: 超时时间
        
    Returns:
        bool: 成功返回True
    """
    log_print(f"[{serial_number}] [POLY] 开始监测订单状态，初始订单数量: {initial_count}")
    
    start_time = time.time()
    check_interval = 5
    
    while time.time() - start_time < timeout:
        try:
            current_count = get_polymarket_open_orders_count(driver, serial_number)
            
            if current_count > initial_count:
                log_print(f"[{serial_number}] [POLY] ✓✓✓ 订单挂单成功！订单数量从 {initial_count} 增加到 {current_count}")
                return True
            
            log_print(f"[{serial_number}] [POLY] 当前订单数量: {current_count}，等待增加...")
            time.sleep(check_interval)
            
        except Exception as e:
            log_print(f"[{serial_number}] [POLY] ⚠ 检查订单状态时出错: {str(e)}")
            time.sleep(check_interval)
    
    log_print(f"[{serial_number}] [POLY] ✗ 等待订单超时（{timeout}秒）")
    return False


# ============================================================================
# 统一任务处理函数
# ============================================================================

def process_trading_mission(task_data, keep_browser_open=False, retry_count=0):
    """
    处理交易任务（支持 Opinion Trade 和 Polymarket）
    
    Args:
        task_data: 任务数据，包含 mission 和 exchangeConfig
        keep_browser_open: 是否保持浏览器打开（用于后续数据收集）
        retry_count: 当前重试次数（用于type=5任务的IP更换重试）
        
    Returns:
        tuple: (success, failure_reason, driver, browser_id) 如果 keep_browser_open=True
               (success, failure_reason) 如果 keep_browser_open=False
    """
    mission = task_data.get("mission", {})
    exchange_config = task_data.get("exchangeConfig", {})
    
    # 提取任务参数
    browser_id = mission.get("numberList", "")
    mission_id = mission.get("id", "")
    exchange_name = mission.get("exchangeName", "")
    side = mission.get("side", 1)  # 1=买, 2=卖
    ps_side = mission.get("psSide", 1)  # 1=Yes, 2=No
    price = mission.get("price")
    amount = mission.get("amt", 0)
    
    # 转换交易方向
    trade_type = "Buy" if side == 1 else "Sell"
    
    # 转换价格类型
    price_type = "Limit" if price else "Market"
    
    # 从 trending 中提取主标题和子标题
    trending = exchange_config.get("trending", "")
    trending_part1 = ""
    
    if "###" in trending:
        # 如果包含 ###，说明有子标题
        parts = trending.split("###")
        trending_part1 = parts[1].strip() if len(parts) > 1 else ""
        log_print(f"[{browser_id}] 检测到子标题: {trending_part1}")
    
    # 根据交易所选择URL和选项类型格式
    if exchange_name == "OP":
        # Opinion Trade
        target_url = exchange_config.get("opUrl", "")
        option_type = "YES" if ps_side == 1 else "NO"
        exchange_type = "OP"
    else:
        # Polymarket
        target_url = exchange_config.get("polyUrl", "")
        option_type = "Yes" if ps_side == 1 else "No"
        exchange_type = "POLY"
    
    log_print(f"\n[{browser_id}] ========== 开始处理交易任务 ({exchange_type}) ==========")
    log_print(f"[{browser_id}] 任务ID: {mission_id}")
    log_print(f"[{browser_id}] 交易所: {exchange_name}")
    log_print(f"[{browser_id}] 买卖类型: {trade_type}")
    log_print(f"[{browser_id}] 价格类型: {price_type}")
    log_print(f"[{browser_id}] 种类: {option_type}")
    log_print(f"[{browser_id}] 页面URL: {target_url}")
    log_print(f"[{browser_id}] 价格: {price if price else '市价'}")
    log_print(f"[{browser_id}] 数量: {amount}")
    
    driver = None
    is_new_browser = False  # 标记是否是新启动的浏览器
    
    try:
        # 1. 检查浏览器是否已经运行
        log_print(f"[{browser_id}] 步骤1: 检查浏览器状态...")
        is_active, browser_data = check_browser_active(browser_id)
        
        if is_active and browser_data:
            log_print(f"[{browser_id}] ✓ 浏览器已在运行，直接使用")
            is_new_browser = False
        else:
            # 2. 检查IP并更新代理（仅在需要启动浏览器时）
            log_print(f"[{browser_id}] 步骤2: 检查IP并更新代理...")
            try_update_ip_before_start(browser_id)
            
            # 3. 启动浏览器
            log_print(f"[{browser_id}] 步骤3: 启动浏览器...")
            browser_data = start_adspower_browser(browser_id)
            
            if not browser_data:
                return False, "浏览器启动失败"
            
            is_new_browser = True
            log_print(f"[{browser_id}] ✓ 浏览器已新启动")
        
        # 4. 创建Selenium驱动
        log_print(f"[{browser_id}] 步骤4: 创建Selenium驱动...")
        driver = create_selenium_driver(browser_data)
        
        # 4.5 等待4秒后再进入目标页面
        log_print(f"[{browser_id}] 等待4秒...")
        time.sleep(4)
        
        # 5. 打开目标页面
        log_print(f"[{browser_id}] 步骤5: 打开目标页面")
        driver.get(target_url)
        
        # 根据交易所类型选择不同的处理流程
        if exchange_type == "OP":
            success, failure_reason = process_opinion_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, trending_part1, task_data, retry_count)
        else:
            success, failure_reason = process_polymarket_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser)
        
        # 检查是否需要换IP重试（仅type=5任务且未重试过）
        if not success and failure_reason == "NEED_IP_RETRY" and retry_count == 0:
            mission_type = mission.get("type")
            if mission_type == 5:
                log_print(f"[{browser_id}] Type=5 任务需要换IP重试，开始执行重试流程...")
                
                # 1. 关闭浏览器
                log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                try:
                    if driver:
                        driver.quit()
                except:
                    pass
                close_adspower_browser(browser_id)
                time.sleep(2)
                
                # 2. 强制更换IP
                log_print(f"[{browser_id}] 步骤2: 强制更换IP...")
                proxy_config = force_change_ip_for_browser(browser_id, timeout=15)
                
                if not proxy_config:
                    log_print(f"[{browser_id}] ✗ 获取新IP失败")
                    if keep_browser_open:
                        return False, "换IP失败", None, None, None
                    else:
                        return False, "换IP失败"
                
                log_print(f"[{browser_id}] ✓ 获取新IP: {proxy_config['ip']}")
                
                # 3. 更新代理配置
                log_print(f"[{browser_id}] 步骤3: 更新代理配置...")
                if not update_adspower_proxy(browser_id, proxy_config):
                    log_print(f"[{browser_id}] ✗ 更新代理失败")
                    if keep_browser_open:
                        return False, "更新代理失败", None, None, None
                    else:
                        return False, "更新代理失败"
                
                log_print(f"[{browser_id}] ✓ 代理配置已更新")
                time.sleep(2)
                
                # 4. 递归重试任务（retry_count+1）
                log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: 1）...")
                return process_trading_mission(task_data, keep_browser_open, retry_count=1)
        
        # 根据 keep_browser_open 返回不同的格式
        if keep_browser_open:
            if success:
                log_print(f"[{browser_id}] 任务成功，保持浏览器打开以收集数据...")
            return success, failure_reason, driver, browser_id, exchange_name
        else:
            return success, failure_reason
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗✗✗ 任务执行异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        if keep_browser_open:
            return False, f"执行异常: {str(e)}", None, None, None
        else:
            return False, f"执行异常: {str(e)}"
        
    finally:
        # 只有在不保持浏览器打开时才关闭
        if not keep_browser_open:
            log_print(f"[{browser_id}] 任务完成，正在关闭浏览器...")
            close_adspower_browser(browser_id)


def check_okx_wallet_p_exists(driver, browser_id, timeout=5):
    """
    检查是否存在 OKX Wallet 的 P 标签
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        timeout: 检查超时时间（秒）
        
    Returns:
        bool: 存在返回True，不存在返回False
    """
    try:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                for p in p_tags:
                    if p.text.strip() == "OKX Wallet":
                        log_print(f"[{browser_id}] ✓ 检测到 OKX Wallet P标签存在")
                        return True
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{browser_id}] ✓ 未检测到 OKX Wallet P标签")
        return False
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查 OKX Wallet P标签时出错: {str(e)}")
        return False


def connect_wallet_if_needed(driver, browser_id):
    """
    检查并连接钱包（如果需要）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{browser_id}] 在10秒内检查是否需要连接钱包...")
        
        # 在10秒内查找是否有 "Connect Wallet" 按钮或 "OKX Wallet" 的 p 标签
        connect_wallet_button = None
        okx_wallet_p = None
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                # 查找 Connect Wallet 按钮
                connect_buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in connect_buttons:
                    if button.text.strip() == "Connect Wallet":
                        connect_wallet_button = button
                        log_print(f"[{browser_id}] ✓ 找到 Connect Wallet 按钮")
                        break
                
                # 查找 OKX Wallet 的 p 标签
                if not connect_wallet_button:
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    for p in p_tags:
                        if p.text.strip() == "OKX Wallet":
                            okx_wallet_p = p
                            log_print(f"[{browser_id}] ✓ 找到 OKX Wallet 选项")
                            break
                
                # 如果找到了其中一个，停止查找
                if connect_wallet_button or okx_wallet_p:
                    break
                
                # 如果3秒后两个都没找到，认为已连接
                if time.time() - start_time > 3:
                    log_print(f"[{browser_id}] ✓ 未找到 Connect Wallet 按钮和 OKX Wallet 选项，钱包已连接")
                    return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        # 10秒后，检查结果
        if not connect_wallet_button and not okx_wallet_p:
            log_print(f"[{browser_id}] ✓ 未找到 Connect Wallet 按钮和 OKX Wallet 选项，钱包已连接")
            return True
        
        # 如果有 Connect Wallet 按钮，点击它
        if connect_wallet_button:
            log_print(f"[{browser_id}] → 点击 Connect Wallet 按钮...")
            connect_wallet_button.click()
            time.sleep(1)
            
            # 点击后需要查找 OKX Wallet 选项
            okx_wallet_p = None
        
        # 如果还没有找到 OKX Wallet 选项，在10秒内查找
        if not okx_wallet_p:
            log_print(f"[{browser_id}] → 在10秒内查找 OKX Wallet 选项...")
            start_time = time.time()
            
            while time.time() - start_time < 10:
                try:
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    
                    for p in p_tags:
                        if p.text.strip() == "OKX Wallet":
                            okx_wallet_p = p
                            log_print(f"[{browser_id}] ✓ 找到 OKX Wallet 选项")
                            break
                    
                    if okx_wallet_p:
                        break
                    
                    time.sleep(0.5)
                except:
                    time.sleep(0.5)
        
        # 如果找到了 OKX Wallet 选项，点击它
        if okx_wallet_p:
            try:
                log_print(f"[{browser_id}] → 点击 OKX Wallet 选项...")
                # 点击父节点的父节点
                parent_parent = okx_wallet_p.find_element(By.XPATH, "../..")
                parent_parent.click()
                log_print(f"[{browser_id}] ✓ 已点击 OKX Wallet")
                time.sleep(2)
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 点击 OKX Wallet 失败: {str(e)}")
                return True  # 继续执行
        else:
            log_print(f"[{browser_id}] ⚠ 10秒内未找到 OKX Wallet 选项")
            return True  # 继续执行
        
        # 切换到 OKX 窗口
        log_print(f"[{browser_id}] → 切换到 OKX 窗口...")
        main_window = driver.current_window_handle
        all_windows = driver.window_handles
        
        okx_window = None
        for window in all_windows:
            if window != main_window:
                driver.switch_to.window(window)
                if "okx" in driver.current_url.lower() or "mcohilncbfahbmgdjkbpemcciiolgcge" in driver.current_url:
                    okx_window = window
                    log_print(f"[{browser_id}] ✓ 找到 OKX 窗口")
                    break
        
        if okx_window:
            # 解锁 OKX 钱包
            log_print(f"[{browser_id}] → 解锁 OKX 钱包...")
            unlock_okx_wallet(driver, browser_id, browser_id)
            
            # 点击确认按钮
            log_print(f"[{browser_id}] → 查找确认按钮...")
            confirm_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
            if len(confirm_buttons) >= 2:
                confirm_buttons[1].click()
                log_print(f"[{browser_id}] ✓ 已点击确认按钮")
            
            # 切换回主窗口
            driver.switch_to.window(main_window)
            log_print(f"[{browser_id}] ✓ 已切换回主窗口")
        
        return True
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 连接钱包失败: {str(e)}")
        return True  # 即使失败也继续执行


def wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
    """
    等待Position按钮出现，如果没有则重新加载页面并重试
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        max_retries: 最大重试次数
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    log_print(f"[{browser_id}] 从OKX切换回来，等待3秒...")
    time.sleep(3)
    
    for retry in range(max_retries + 1):
        if retry > 0:
            log_print(f"[{browser_id}] 第 {retry} 次重试...")
        
        # 在10秒内查找Position按钮
        log_print(f"[{browser_id}] 在10秒内查找Position按钮...")
        start_time = time.time()
        position_button_found = False
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.text.strip() == "Position":
                        position_button_found = True
                        log_print(f"[{browser_id}] ✓ 找到Position按钮")
                        return True
                
                time.sleep(0.5)  # 每0.5秒检查一次
                
            except Exception as e:
                log_print(f"[{browser_id}] 查找按钮时出错: {str(e)}")
                time.sleep(0.5)
        
        # 10秒后还没找到Position按钮
        if not position_button_found:
            if retry < max_retries:
                log_print(f"[{browser_id}] ⚠ 10秒后仍未找到Position按钮，重新加载页面...")
                driver.refresh()
                time.sleep(2)
                
                # 重新检查并连接钱包
                log_print(f"[{browser_id}] 重新检查并连接钱包...")
                connect_wallet_if_needed(driver, browser_id)
                
                # 等待3秒后继续下一次重试
                log_print(f"[{browser_id}] 等待3秒后重试...")
                time.sleep(3)
            else:
                log_print(f"[{browser_id}] ✗ 已达到最大重试次数，仍未找到Position按钮")
                return False
    
    return False


def check_position_count(driver, browser_id, trending_part1=''):
    """
    检查 Position 标签页中是否有仓位
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        trending_part1: 子标题名称，如果有，需要检查tr内p标签内容
        
    Returns:
        int: tr数量，失败返回-1
    """
    try:
        log_print(f"[{browser_id}] 检查 Position 仓位...")
        
        # 在10秒内查找并点击 "Position" 按钮
        log_print(f"[{browser_id}] 在10秒内查找 Position 按钮...")
        position_button = None
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Position":
                        position_button = button
                        break
                
                if position_button:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not position_button:
            log_print(f"[{browser_id}] ⚠ 10秒内未找到 Position 按钮")
            return -1
        
        position_button.click()
        log_print(f"[{browser_id}] ✓ 已点击 Position 按钮")
        time.sleep(2)
        
        # 查找 data-scope="tabs" 且 id 包含 "content-position" 的 div
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        
        target_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'content-position' in div_id.lower():
                target_div = div
                log_print(f"[{browser_id}] ✓ 找到 Position div，id: {div_id}")
                break
        
        if not target_div:
            log_print(f"[{browser_id}] ⚠ 未找到 Position div")
            return -1
        
        # 在目标 div 中查找 tbody
        tbody = target_div.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        count = len(tr_list)
        log_print(f"[{browser_id}] Position 中有 {count} 个仓位")
        
        # 如果有子标题，需要进一步检查tr内p标签内容
        if trending_part1 and count > 0:
            log_print(f"[{browser_id}] 检测到子标题 '{trending_part1}'，检查tr内p标签内容...")
            matched_count = 0
            for tr in tr_list:
                try:
                    # 获取tr内所有p标签
                    p_tags = tr.find_elements(By.TAG_NAME, "p")
                    # 检查是否有p标签内容包含子标题
                    for p in p_tags:
                        p_text = p.text.strip()
                        if trending_part1 in p_text:
                            matched_count += 1
                            log_print(f"[{browser_id}] ✓ 找到匹配的仓位，p标签内容: {p_text}")
                            break
                except:
                    continue
            
            log_print(f"[{browser_id}] 有子标题情况下，匹配的仓位数量: {matched_count}")
            return matched_count
        
        return count
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查 Position 失败: {str(e)}")
        return -1


def click_trending_part1_if_needed(driver, browser_id, trending_part1):
    """
    如果有 trendingPart1，点击对应的子主题
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        trending_part1: 子主题名称
        
    Returns:
        bool: 成功返回True
    """
    try:
        if not trending_part1:
            log_print(f"[{browser_id}] trendingPart1 为空，跳过子主题选择")
            return True
        
        log_print(f"[{browser_id}] 查找并点击子主题: {trending_part1}")
        
        # 找到 data-sentry-element="Accordion" 的 div
        accordion_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-sentry-element="Accordion"]')
        
        if not accordion_divs:
            log_print(f"[{browser_id}] ⚠ 未找到 Accordion div")
            return False
        
        log_print(f"[{browser_id}] ✓ 找到 {len(accordion_divs)} 个 Accordion div")
        
        # 在 Accordion div 中查找内容等于 trending_part1 的 p 标签
        for accordion_div in accordion_divs:
            p_tags = accordion_div.find_elements(By.TAG_NAME, "p")
            
            for p in p_tags:
                log_print(f"[{browser_id}] ✓ 找到 p 标签: {p.text.strip()}")
                if p.text.strip() == trending_part1:
                    log_print(f"[{browser_id}] ✓ 找到匹配的 p 标签: {trending_part1}")
                    
                    # 点击 p 标签的父节点的父节点的父节点
                    parent1 = p.find_element(By.XPATH, "..")
                    parent2 = parent1.find_element(By.XPATH, "..")
                    parent3 = parent2.find_element(By.XPATH, "..")
                    
                    parent3.click()
                    log_print(f"[{browser_id}] ✓ 已点击子主题")
                    
                    # 等待3秒
                    time.sleep(3)
                    return True
        
        log_print(f"[{browser_id}] ⚠ 未找到匹配的子主题: {trending_part1}")
        return False
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 点击子主题失败: {str(e)}")
        return False


def process_opinion_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, trending_part1='', task_data=None, retry_count=0):
    """
    处理 Opinion Trade 交易流程
    
    Args:
        is_new_browser: 是否是新启动的浏览器
        trending_part1: 子主题名称（如果有）
        task_data: 任务数据（用于type=5的同步机制）
        retry_count: 当前重试次数
    
    Returns:
        tuple: (success, failure_reason)
    """
    try:
        # 5. 等待页面加载
        log_print(f"[{browser_id}] 步骤5: 等待页面加载...")
        trade_box = wait_for_opinion_trade_box(driver, browser_id, max_retries=3)
        
        if not trade_box:
            return False, "页面加载失败"
        
        # 6. 预打开OKX钱包并连接（仅在新启动的浏览器时执行）
        if is_new_browser:
            log_print(f"[{browser_id}] 步骤6: 预打开OKX钱包（浏览器新启动）...")
            preopen_okx_wallet(driver, browser_id)
        else:
            log_print(f"[{browser_id}] 步骤6: 跳过预打开OKX钱包（浏览器已在运行）")
        
        # 6.1 检查并连接钱包
        log_print(f"[{browser_id}] 步骤6.1: 检查并连接钱包...")
        connect_wallet_if_needed(driver, browser_id)
        
        # 6.1.5 等待Position按钮出现（带重试机制）
        log_print(f"[{browser_id}] 步骤6.1.5: 等待Position按钮出现...")
        if not wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
            # 检查是否是 type=5 任务且未重试过
            mission = task_data.get('mission', {}) if task_data else {}
            mission_type = mission.get('type')
            
            if mission_type == 5 and retry_count == 0:
                log_print(f"[{browser_id}] Type=5 任务Position按钮未出现，需要换IP重试...")
                return False, "NEED_IP_RETRY"
            else:
                return False, "Position按钮未出现，页面加载可能失败"
        
        # 6.1.6 如果有 trendingPart1，点击子主题
        if trending_part1:
            log_print(f"[{browser_id}] 步骤6.1.6: 检查并点击子主题 {trending_part1}...")
            if not click_trending_part1_if_needed(driver, browser_id, trending_part1):
                log_print(f"[{browser_id}] ⚠ 点击子主题失败，继续执行...")
        
        # 6.2 检查仓位和挂单，记录初始数量
        log_print(f"[{browser_id}] 步骤6.2: 检查并记录初始仓位和挂单数量...")
        
        # 检查 Position 数量
        initial_position_count = check_position_count(driver, browser_id, trending_part1)
        if initial_position_count < 0:
            log_print(f"[{browser_id}] ⚠ 无法获取 Position 数量，设为 0")
            initial_position_count = 0
        
        log_print(f"[{browser_id}] 初始 Position 数量: {initial_position_count}")
        
        # Buy 类型：如果已有仓位则不能下单
        if trade_type == "Buy" and initial_position_count > 0:
            return False, f"{browser_id}已有仓位"
        
        # Sell 类型：如果没有仓位则不能下单
        if trade_type == "Sell" and initial_position_count == 0:
            return False, f"{browser_id}无仓位可平"
        
        # 检查 Open Orders 数量
        log_print(f"[{browser_id}] 步骤6.3: 检查 Open Orders...")
        initial_open_orders_count = get_opinion_table_row_count(driver, browser_id, need_click_open_orders=True, trending_part1=trending_part1)
        
        if initial_open_orders_count < 0:
            log_print(f"[{browser_id}] ⚠ 无法获取 Open Orders 数量，设为 0")
            initial_open_orders_count = 0
        
        log_print(f"[{browser_id}] 初始 Open Orders 数量: {initial_open_orders_count}")
        
        # Buy 和 Sell 类型：如果已有挂单则不能下单
        if initial_open_orders_count > 0:
            return False, f"{browser_id}已有挂单"
        
        if trade_type == "Buy":
            log_print(f"[{browser_id}] ✓ Buy 类型检查通过：无仓位，无挂单")
        else:
            log_print(f"[{browser_id}] ✓ Sell 类型检查通过：有仓位，无挂单")
        
        # 重试机制：第7-12步最多重试2次（总共3次尝试）
        max_retry_attempts = 2
        retry_count = 0
        
        while retry_count <= max_retry_attempts:
            try:
                if retry_count > 0:
                    log_print(f"[{browser_id}] ⚠ 第{retry_count}次重试，刷新页面...")
                    driver.refresh()
                    
                    # 重新等待页面加载
                    log_print(f"[{browser_id}] 等待页面重新加载...")
                    trade_box = wait_for_opinion_trade_box(driver, browser_id, max_retries=3)
                    if not trade_box:
                        log_print(f"[{browser_id}] ✗ 页面重新加载失败")
                        retry_count += 1
                        continue
                    
                    # 重新检查并连接钱包
                    log_print(f"[{browser_id}] 重新检查并连接钱包...")
                    connect_wallet_if_needed(driver, browser_id)
                    
                    # 重新等待Position按钮出现
                    log_print(f"[{browser_id}] 重新等待Position按钮...")
                    if not wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
                        log_print(f"[{browser_id}] ✗ Position按钮未出现")
                        retry_count += 1
                        continue
                    
                    # 如果有 trendingPart1，重新点击子主题
                    if trending_part1:
                        log_print(f"[{browser_id}] 重新点击子主题 {trending_part1}...")
                        if not click_trending_part1_if_needed(driver, browser_id, trending_part1):
                            log_print(f"[{browser_id}] ⚠ 点击子主题失败，继续执行...")
                
                # 7. 点击买卖类型按钮
                log_print(f"[{browser_id}] 步骤7: 选择买卖类型 {trade_type}...")
                if not click_opinion_trade_type_button(trade_box, trade_type, browser_id):
                    log_print(f"[{browser_id}] ✗ 未找到{trade_type}按钮")
                    retry_count += 1
                    continue
                
                # 8. 选择价格类型
                log_print(f"[{browser_id}] 步骤8: 选择价格类型 {price_type}...")
                if not select_opinion_price_type(trade_box, price_type, browser_id):
                    log_print(f"[{browser_id}] ✗ 选择价格类型{price_type}失败")
                    retry_count += 1
                    continue
                
                # 9. 选择种类
                log_print(f"[{browser_id}] 步骤9: 选择种类 {option_type}...")
                if not select_opinion_option_type(trade_box, option_type, browser_id):
                    log_print(f"[{browser_id}] ✗ 选择种类{option_type}失败")
                    retry_count += 1
                    continue
                
                # 10. 点击 Amount 标签
                log_print(f"[{browser_id}] 步骤10: 点击 Amount 标签...")
                click_opinion_amount_tab(trade_box, browser_id)
                
                # 11. 填入价格和数量
                log_print(f"[{browser_id}] 步骤11: 填入价格和数量（模式：{price_type}）...")
                # Market模式传None，Limit模式传price
                fill_price = None if price_type == "Market" else price
                if not fill_opinion_price_and_amount(trade_box, fill_price, amount, browser_id):
                    log_print(f"[{browser_id}] ✗ 填入价格/数量失败")
                    retry_count += 1
                    continue
                
                # 12. 提交订单
                log_print(f"[{browser_id}] 步骤12: 提交订单...")
                submit_success, should_retry = submit_opinion_order(driver, trade_box, trade_type, option_type, browser_id, browser_id, task_data)
                if not submit_success:
                    log_print(f"[{browser_id}] ✗ 提交订单失败")
                    if not should_retry:
                        # type=5点击取消按钮，不应重试
                        log_print(f"[{browser_id}] ✗ Type 5 任务已取消，不进行重试")
                        return False, "Type 5 任务已取消"
                    elif isinstance(should_retry, str):
                        # should_retry是字符串，表示具体的失败原因
                        log_print(f"[{browser_id}] ✗ Type 5 任务失败: {should_retry}")
                        return False, should_retry
                    retry_count += 1
                    continue
                
                # 如果所有步骤都成功，跳出循环
                log_print(f"[{browser_id}] ✓ 步骤7-12执行成功")
                break
                
            except Exception as e:
                log_print(f"[{browser_id}] ✗ 步骤7-12执行异常: {str(e)}")
                retry_count += 1
                if retry_count > max_retry_attempts:
                    return False, f"执行异常: {str(e)}"
                continue
        
        # 检查是否所有重试都失败了
        if retry_count > max_retry_attempts:
            return False, f"执行步骤7-12失败，已重试{max_retry_attempts}次"
        
        # 13. 等待订单成功
        # Type 5 任务使用特殊的等待和数据收集逻辑
        mission = task_data.get('mission', {}) if task_data else {}
        mission_type = mission.get('type')
        
        if mission_type == 5:
            log_print(f"[{browser_id}] 步骤13: Type 5 任务 - 等待订单确认并收集数据...")
            success, msg = wait_for_type5_order_and_collect_data(
                driver, 
                initial_position_count, 
                browser_id, 
                trending_part1,
                task_data,
                trade_type
            )
            
            if not success:
                log_print(f"[{browser_id}] ========== Type 5 任务失败: {msg} ==========\n")
                return False, msg
            else:
                log_print(f"[{browser_id}] ========== Type 5 任务成功: {msg} ==========\n")
                return True, msg
        else:
            # Type 1 任务使用原有的等待逻辑
            log_print(f"[{browser_id}] 步骤13: 等待订单确认（交替检查 Open Orders 和 Position）...")
            if not wait_for_opinion_order_success(
                driver, 
                initial_open_orders_count, 
                initial_position_count, 
                trade_type,
                browser_id, 
                trending_part1,
                timeout=600
            ):
                return False, "订单确认超时"
            
            log_print(f"[{browser_id}] ========== Opinion Trade 任务完成 ==========\n")
            return True, ""
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗✗✗ Opinion Trade 任务执行异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, f"执行异常: {str(e)}"


def process_polymarket_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser):
    """
    处理 Polymarket 交易流程
    
    Args:
        is_new_browser: 是否是新启动的浏览器
    
    Returns:
        tuple: (success, failure_reason)
    """
    try:
        # 5. 等待页面加载
        log_print(f"[{browser_id}] 步骤5: 等待页面加载...")
        trade_box = wait_for_polymarket_trade_box(driver, browser_id, max_retries=3)
        
        if not trade_box:
            return False, "页面加载失败"
        
        # 6. 预打开OKX钱包（仅在新启动的浏览器时执行）
        if is_new_browser:
            log_print(f"[{browser_id}] 步骤6: 预打开OKX钱包（浏览器新启动）...")
            preopen_okx_wallet(driver, browser_id)
        else:
            log_print(f"[{browser_id}] 步骤6: 跳过预打开OKX钱包（浏览器已在运行）")
        
        # 7. 点击买卖类型按钮
        log_print(f"[{browser_id}] 步骤7: 选择买卖类型 {trade_type}...")
        if not click_polymarket_trade_type_button(trade_box, trade_type, browser_id):
            return False, f"未找到{trade_type}按钮"
        
        # 8. 选择价格类型
        log_print(f"[{browser_id}] 步骤8: 选择价格类型 {price_type}...")
        if not select_polymarket_price_type(trade_box, price_type, browser_id):
            return False, f"选择价格类型{price_type}失败"
        
        # 9. 选择种类
        log_print(f"[{browser_id}] 步骤9: 选择种类 {option_type}...")
        if not select_polymarket_option_type(trade_box, option_type, browser_id):
            return False, f"选择种类{option_type}失败"
        
        # 10. 填入价格和数量
        log_print(f"[{browser_id}] 步骤10: 填入价格和数量（模式：{price_type}）...")
        # Market模式传None，Limit模式传price
        fill_price = None if price_type == "Market" else price
        if not fill_polymarket_price_and_amount(trade_box, fill_price, amount, browser_id):
            return False, "填入价格/数量失败"
        
        # 11. 获取初始订单数量
        log_print(f"[{browser_id}] 步骤11: 获取初始订单数量...")
        initial_count = get_polymarket_open_orders_count(driver, browser_id)
        
        if initial_count < 0:
            log_print(f"[{browser_id}] ⚠ 无法获取初始订单数量，将继续执行...")
            initial_count = 0
        
        # 12. 提交订单
        log_print(f"[{browser_id}] 步骤12: 提交订单...")
        if not submit_polymarket_order(driver, trade_box, browser_id, browser_id):
            return False, "提交订单失败"
        
        # 13. 等待订单成功
        log_print(f"[{browser_id}] 步骤13: 等待订单确认...")
        if not wait_for_polymarket_order_success(driver, initial_count, browser_id, timeout=60):
            return False, "订单确认超时"
        
        log_print(f"[{browser_id}] ========== Polymarket 任务完成 ==========\n")
        return True, ""
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗✗✗ Polymarket 任务执行异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, f"执行异常: {str(e)}"


# ============================================================================
# Type 2 任务 - 数据获取函数（Opinion Trade）
# ============================================================================

def get_opinion_portfolio_value(driver, serial_number):
    """
    获取 Opinion Trade Portfolio 的值（在180秒内多次尝试）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (Portfolio值, 是否需要刷新重试)
            - 如果正常获取数据: (value, False)
            - 如果超时未获取到: (None, True)
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找 Portfolio 值...")
        
        # 在180秒内多次尝试查找
        max_retry_time = 180
        retry_start_time = time.time()
        
        while time.time() - retry_start_time < max_retry_time:
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                
                for p in p_tags:
                    if p.text.strip() == "Portfolio":
                        parent = p.find_element(By.XPATH, "..")
                        child_p_tags = parent.find_elements(By.TAG_NAME, "p")
                        
                        if len(child_p_tags) >= 2:
                            portfolio_value = child_p_tags[1].text.strip()
                            if portfolio_value:  # 确保值不为空
                                log_print(f"[{serial_number}] [OP] ✓ Portfolio 值: {portfolio_value}")
                                return portfolio_value, False
                
                # 如果没找到或值为空，等待5秒后重试
                elapsed = int(time.time() - retry_start_time)
                log_print(f"[{serial_number}] [OP] ⚠ Portfolio 值未找到或为空，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                time.sleep(5)
                
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 查找 Portfolio 值异常: {str(e)}，等待5秒后重试...")
                time.sleep(5)
        
        log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Portfolio 值，需要刷新重试")
        return None, True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 获取 Portfolio 值失败: {str(e)}")
        return None, False


def get_opinion_balance_value(driver, serial_number):
    """
    获取 Opinion Trade Balance 的值（在180秒内多次尝试）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (Balance值, 是否需要刷新重试)
            - 如果正常获取数据: (value, False)
            - 如果超时未获取到: (None, True)
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找 Balance 值...")
        
        # 在180秒内多次尝试查找
        max_retry_time = 180
        retry_start_time = time.time()
        
        while time.time() - retry_start_time < max_retry_time:
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                
                for p in p_tags:
                    if p.text.strip() == "Balance":
                        parent = p.find_element(By.XPATH, "..")
                        children = parent.find_elements(By.XPATH, "./*")
                        
                        if len(children) >= 2:
                            second_child = children[1]
                            p_in_second_child = second_child.find_elements(By.TAG_NAME, "p")
                            
                            if p_in_second_child:
                                balance_value = p_in_second_child[0].text.strip()
                                if balance_value:  # 确保值不为空
                                    log_print(f"[{serial_number}] [OP] ✓ Balance 值: {balance_value}")
                                    return balance_value, False
                
                # 如果没找到或值为空，等待5秒后重试
                elapsed = int(time.time() - retry_start_time)
                log_print(f"[{serial_number}] [OP] ⚠ Balance 值未找到或为空，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                time.sleep(5)
                
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 查找 Balance 值异常: {str(e)}，等待5秒后重试...")
                time.sleep(5)
        
        log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Balance 值，需要刷新重试")
        return None, True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 获取 Balance 值失败: {str(e)}")
        return None, False


def click_opinion_position_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Position 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (p标签内容列表, 是否需要刷新重试)
            - 如果正常获取数据或找到"No data yet": (data, False)
            - 如果超时且没有"No data yet": ([], True)
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 Position 按钮...")
        
        position_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Position":
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 Position 按钮")
                        position_clicked = True
                        break
                
                if position_clicked:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not position_clicked:
            log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 Position 按钮")
            return [], False
        
        time.sleep(3)
        
        try:
            # 先找到 ID 以 content-position 结尾的 div
            log_print(f"[{serial_number}] [OP] 查找 Position 内容区域...")
            position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
            log_print(f"[{serial_number}] [OP] ✓ 找到 Position 内容区域 (ID: {position_div.get_attribute('id')})")
            
            # 在180秒内多次查找p标签，如果数量为0则等待5秒后重试
            max_retry_time = 180
            retry_start_time = time.time()
            p_contents = []
            
            while time.time() - retry_start_time < max_retry_time:
                try:
                    # 先检查是否有"No data yet"
                    all_p_tags_in_div = position_div.find_elements(By.TAG_NAME, "p")
                    for p in all_p_tags_in_div:
                        if "No data yet" in p.text:
                            log_print(f"[{serial_number}] [OP] ✓ Position 发现 'No data yet'，无数据")
                            return [], False
                    
                    # 再找这个 div 下的 tbody
                    tbody = position_div.find_element(By.TAG_NAME, "tbody")
                    p_tags = tbody.find_elements(By.TAG_NAME, "p")
                    p_contents = [p.text.strip() for p in p_tags if p.text.strip()]
                    
                    if len(p_contents) > 0:
                        log_print(f"[{serial_number}] [OP] ✓ Position tbody 中找到 {len(p_contents)} 个 p 标签")
                        return p_contents, False
                    else:
                        elapsed = int(time.time() - retry_start_time)
                        log_print(f"[{serial_number}] [OP] ⚠ Position p标签数量为0，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                        time.sleep(5)
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Position p标签异常: {str(e)}，等待5秒后重试...")
                    time.sleep(5)
            
            log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Position 数据且无'No data yet'，需要刷新重试")
            return [], True
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Position tbody 失败: {str(e)}")
            return [], False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Position 按钮失败: {str(e)}")
        return [], False


def click_opinion_open_orders_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Open Orders 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (p标签内容列表, 是否需要刷新重试)
            - 如果正常获取数据或找到"No data yet": (data, False)
            - 如果超时且没有"No data yet": ([], True)
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 Open Orders 按钮...")
        
        open_orders_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Open Orders":
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 Open Orders 按钮")
                        open_orders_clicked = True
                        break
                
                if open_orders_clicked:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not open_orders_clicked:
            log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 Open Orders 按钮")
            return [], False
        
        time.sleep(5)
        
        try:
            # 先找到 ID 以 content-open-orders 结尾的 div
            log_print(f"[{serial_number}] [OP] 查找 Open Orders 内容区域...")
            open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
            log_print(f"[{serial_number}] [OP] ✓ 找到 Open Orders 内容区域 (ID: {open_orders_div.get_attribute('id')})")
            
            # 在180秒内多次查找p标签，如果数量为0则等待5秒后重试
            max_retry_time = 180
            retry_start_time = time.time()
            p_contents = []
            
            while time.time() - retry_start_time < max_retry_time:
                try:
                    # 先检查是否有"No data yet"
                    all_p_tags_in_div = open_orders_div.find_elements(By.TAG_NAME, "p")
                    for p in all_p_tags_in_div:
                        if "No data yet" in p.text:
                            log_print(f"[{serial_number}] [OP] ✓ Open Orders 发现 'No data yet'，无数据")
                            return [], False
                    
                    # 再找这个 div 下的 tbody
                    tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                    p_tags = tbody.find_elements(By.TAG_NAME, "p")
                    p_contents = [p.text.strip() for p in p_tags if p.text.strip()]
                    
                    if len(p_contents) > 0:
                        log_print(f"[{serial_number}] [OP] ✓ Open Orders tbody 中找到 {len(p_contents)} 个 p 标签")
                        return p_contents, False
                    else:
                        elapsed = int(time.time() - retry_start_time)
                        log_print(f"[{serial_number}] [OP] ⚠ Open Orders p标签数量为0，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                        time.sleep(5)
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Open Orders p标签异常: {str(e)}，等待5秒后重试...")
                    time.sleep(5)
            
            log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Open Orders 数据且无'No data yet'，需要刷新重试")
            return [], True
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Open Orders tbody 失败: {str(e)}")
            return [], False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Open Orders 按钮失败: {str(e)}")
        return [], False


def click_opinion_transactions_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Transactions 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (交易记录列表, 是否需要刷新重试)
            - 如果正常获取数据或找到"No data yet": (data, False)
            - 如果超时且没有"No data yet": ([], True)
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 Transactions 按钮...")
        
        transactions_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Transactions":
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 Transactions 按钮")
                        transactions_clicked = True
                        break
                
                if transactions_clicked:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not transactions_clicked:
            log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 Transactions 按钮")
            return [], False
        
        time.sleep(3)
        
        try:
            # 先找到 ID 以 content-transactions 结尾的 div
            log_print(f"[{serial_number}] [OP] 查找 Transactions 内容区域...")
            transactions_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-transactions']")
            log_print(f"[{serial_number}] [OP] ✓ 找到 Transactions 内容区域 (ID: {transactions_div.get_attribute('id')})")
            
            # 在180秒内多次查找tr标签，如果数量为0则等待5秒后重试
            max_retry_time = 180
            retry_start_time = time.time()
            tr_list = []
            
            while time.time() - retry_start_time < max_retry_time:
                try:
                    # 先检查是否有"No data yet"
                    all_p_tags_in_div = transactions_div.find_elements(By.TAG_NAME, "p")
                    for p in all_p_tags_in_div:
                        if "No data yet" in p.text:
                            log_print(f"[{serial_number}] [OP] ✓ Transactions 发现 'No data yet'，无数据")
                            return [], False
                    
                    # 再找这个 div 下的 tbody
                    tbody = transactions_div.find_element(By.TAG_NAME, "tbody")
                    tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    if len(tr_list) > 0:
                        log_print(f"[{serial_number}] [OP] ✓ Transactions tbody 中找到 {len(tr_list)} 个 tr 标签")
                        break
                    else:
                        elapsed = int(time.time() - retry_start_time)
                        log_print(f"[{serial_number}] [OP] ⚠ Transactions tr标签数量为0，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                        time.sleep(5)
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Transactions tr标签异常: {str(e)}，等待5秒后重试...")
                    time.sleep(5)
            
            if len(tr_list) == 0:
                log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Transactions 数据且无'No data yet'，需要刷新重试")
                return [], True
            
            transactions = []
            current_title = None
            
            for tr_idx, tr in enumerate(tr_list, 1):
                try:
                    p_tags = tr.find_elements(By.TAG_NAME, "p")
                    p_count = len(p_tags)
                    
                    # 打印所有 p 标签内容
                    log_print(f"[{serial_number}] [OP] TR {tr_idx}: 共 {p_count} 个 p 标签")
                    for p_idx, p_tag in enumerate(p_tags, 1):
                        p_content = p_tag.text.strip()
                        # log_print(f"[{serial_number}] [OP]   P{p_idx}: {p_content}")
                    
                    # 如果只有一个 p 标签，说明这是主题标题
                    if p_count == 1:
                        current_title = p_tags[0].text.strip()
                        log_print(f"[{serial_number}] [OP] TR {tr_idx}: 主题标题 = {current_title}")
                    # 如果有多个 p 标签，说明这是交易记录（实际有10个p标签）
                    elif p_count >= 9:
                        if not current_title:
                            log_print(f"[{serial_number}] [OP] ⚠ TR {tr_idx}: 没有主题标题，跳过")
                            continue
                        
                        # P1: 买卖方向 (索引0)
                        direction = p_tags[0].text.strip()
                        
                        # P2: 选项 (索引1)，可能包含子标题
                        option_text = p_tags[1].text.strip()
                        
                        # P3: 数量/shares (索引2)
                        amount = p_tags[2].text.strip()
                        
                        # P4: 金额/amount (索引3)
                        value = p_tags[3].text.strip()
                        
                        # P5: 价格/price (索引4)
                        price = p_tags[4].text.strip()
                        
                        # P9: 时间/time (索引8)
                        trade_time = p_tags[8].text.strip()
                        
                        # log_print(f"[{serial_number}] [OP] TR {tr_idx}: 提取数据 - 方向={direction}, 选项={option_text}, 数量={amount}, 金额={value}, 价格={price}, 时间={trade_time}")
                        
                        # 检查是否有子标题（包含 " - "）
                        final_title = current_title
                        final_option = option_text
                        
                        if " - " in option_text:
                            parts = option_text.split(" - ")
                            if len(parts) >= 2:
                                sub_title = parts[0].strip()
                                final_option = parts[1].strip()
                                # 将子标题连接到主标题
                                final_title = f"{current_title}###{sub_title}"
                                log_print(f"[{serial_number}] [OP] TR {tr_idx}: 检测到子标题 - 主题={final_title}, 选项={final_option}")
                        
                        transaction = {
                            "title": final_title,
                            "direction": direction,
                            "option": final_option,
                            "amount": amount,
                            "value": value,
                            "price": price,
                            "time": trade_time
                        }
                        
                        transactions.append(transaction)
                     
                    
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 处理 TR {tr_idx} 时出错: {str(e)}")
                    continue
            
            log_print(f"[{serial_number}] [OP] ✓ 共收集到 {len(transactions)} 条交易记录")
            return transactions, False
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Transactions tbody 失败: {str(e)}")
            return [], False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Transactions 按钮失败: {str(e)}")
        return [], False


# ============================================================================
# Type 2 任务 - 数据处理和格式化函数
# ============================================================================

def process_op_position_data(position_data):
    """
    处理 OP Position 数据，格式化为标准格式
    
    Args:
        position_data: list，原始的p标签内容列表
        
    Returns:
        list: 格式化后的数据，每项为 {"title": 标题, "option": 选项, "amount": ±数量, "avg_price": 平均价格}
    """
    processed = {}  # 使用字典来存储每个标题+选项的数据 {(title, option): {"amount": x, "avg_price": "y"}}
    current_title = None  # 记录当前标题
    i = 0
    
    while i < len(position_data):
        # 判断当前项是否是 YES/NO（单独的选项，使用上一个标题）
        if position_data[i] in ["YES", "NO"]:
            # 这是一行数据的开始（没有标题，使用上一个标题）
            if i + 5 < len(position_data):
                option = position_data[i]
                amount_str = position_data[i + 1]
                avg_price = position_data[i + 3] if i + 3 < len(position_data) else ""  # 平均价格
                
                # 忽略 <0.01 的数量
                if amount_str != "<0.01" and current_title:
                    try:
                        amount = float(amount_str.replace(',', ''))
                        # YES为正数，NO为负数（忽略大小写）
                        if option.upper() == "NO":
                            amount = -amount
                        
                        # 使用 title+option 作为key来存储数据
                        key = (current_title, option)
                        if key in processed:
                            processed[key]["amount"] += amount
                            processed[key]["avg_price"] = avg_price  # 更新为最新的平均价格
                        else:
                            processed[key] = {"amount": amount, "avg_price": avg_price}
                    except:
                        pass
                
                i += 6  # 跳过这一行的其他数据（6项）
            else:
                i += 1
        # 判断是否是带子标题的选项（如 "50+ bps decrease - YES"），没有新的主标题
        elif " - " in position_data[i] and (position_data[i].endswith(" - YES") or position_data[i].endswith(" - NO")) and i + 5 < len(position_data):
            # 这是同一标题下的另一个选项（带子标题）
            option_str = position_data[i]
            amount_str = position_data[i + 1]
            avg_price = position_data[i + 3] if i + 3 < len(position_data) else ""  # 平均价格
            
            # 解析子标题和选项
            parts = option_str.split(" - ")
            if len(parts) >= 2 and current_title:
                sub_title = parts[0].strip()
                final_option = parts[1].strip()
                final_title = f"{current_title}###" + sub_title
                
                # 忽略 <0.01 的数量
                if amount_str != "<0.01":
                    try:
                        amount = float(amount_str.replace(',', ''))
                        # YES为正数，NO为负数（忽略大小写）
                        if final_option.upper() == "NO":
                            amount = -amount
                        
                        # 使用 title+option 作为key来存储数据
                        key = (final_title, final_option)
                        if key in processed:
                            processed[key]["amount"] += amount
                            processed[key]["avg_price"] = avg_price  # 更新为最新的平均价格
                        else:
                            processed[key] = {"amount": amount, "avg_price": avg_price}
                    except:
                        pass
                
                i += 6  # 跳过这一行的其他数据（6项）
            else:
                i += 1
        else:
            # 这是新的标题行
            if i + 6 < len(position_data):
                current_title = position_data[i]
                option = position_data[i + 1]
                amount_str = position_data[i + 2]
                avg_price = position_data[i + 4] if i + 4 < len(position_data) else ""  # 平均价格
                
                # 检查 option 中是否包含 " - "，如果有则说明有子标题
                final_title = current_title
                final_option = option
                
                if " - " in option:
                    # 例如 "Microsoft - YES" -> 子标题="Microsoft", option="YES"
                    parts = option.split(" - ")
                    if len(parts) >= 2:
                        sub_title = parts[0].strip()
                        final_option = parts[1].strip()
                        # 将子标题连接到主标题
                        final_title = f"{current_title}###" + sub_title
                
                # 忽略 <0.01 的数量
                if amount_str != "<0.01":
                    try:
                        amount = float(amount_str.replace(',', ''))
                        # YES为正数，NO为负数（忽略大小写）
                        if final_option.upper() == "NO":
                            amount = -amount
                        
                        # 使用 title+option 作为key来存储数据
                        key = (final_title, final_option)
                        if key in processed:
                            processed[key]["amount"] += amount
                            processed[key]["avg_price"] = avg_price  # 更新为最新的平均价格
                        else:
                            processed[key] = {"amount": amount, "avg_price": avg_price}
                    except:
                        pass
                
                i += 7  # 跳过这一行的所有数据（7项）
            else:
                i += 1
    
    # 转换为列表格式
    result = [{"title": title, "option": option, "amount": data["amount"], "avg_price": data["avg_price"]} 
              for (title, option), data in processed.items()]
    return result


def process_op_open_orders_data(open_orders_data):
    """
    处理 OP Open Orders 数据，格式化为标准格式
    
    Args:
        open_orders_data: list，原始的p标签内容列表
        
    Returns:
        list: 格式化后的数据，每项为 {"title": 标题, "price": 价格, "progress": "$x/$y"}
    """
    result = []
    
    # OP的Open Orders数据是每11项为一组
    for i in range(0, len(open_orders_data), 11):
        if i + 10 >= len(open_orders_data):
            break
            
        title = open_orders_data[i]
        option_field = open_orders_data[i + 2]  # 可能包含子标题，如 "Kendrick Lamar - YES"
        price = open_orders_data[i + 4]  # 价格
        progress1 = open_orders_data[i + 6]  # $0
        progress2 = open_orders_data[i + 8]  # $4.99
        
        # 检查 option_field 中是否包含 " - "，如果有则说明有子标题
        final_title = title
        if " - " in option_field:
            # 例如 "Kendrick Lamar - YES" -> 子标题="Kendrick Lamar"
            parts = option_field.split(" - ")
            if len(parts) >= 2:
                sub_title = parts[0].strip()
                # 将子标题连接到主标题
                final_title = f"{title}###{sub_title}"
        
        result.append({
            "title": final_title,
            "price": price,
            "progress": f"{progress1}/{progress2}"
        })
    
    return result


def process_poly_position_data(positions_data):
    """
    处理 Polymarket Position 数据，格式化为标准格式
    
    Args:
        positions_data: list，tr数据列表，每个tr包含多个td
        
    Returns:
        list: 格式化后的数据，每项为 {"title": 标题, "amount": ±数量}
    """
    result = []
    
    for tr_data in positions_data:
        if len(tr_data) == 0:
            continue
        
        # TD1 包含标题和方向/数量信息
        td1 = tr_data[0] if len(tr_data) > 0 else []
        
        title = None
        side = None
        shares = None
        
        # 从 TD1 提取信息
        for item in td1:
            if isinstance(item, dict):
                if item.get('tag') == 'h2':
                    title = item.get('content', '')
                elif item.get('tag') == 'span' and 'shares' in item.get('content', ''):
                    # "3.5 shares" -> 3.5
                    shares_str = item.get('content', '').replace(' shares', '').strip()
                    try:
                        shares = float(shares_str)
                    except:
                        pass
                elif item.get('tag') == 'div':
                    # "No 85¢" 或 "Yes 4¢"
                    content = item.get('content', '')
                    if content.startswith('Yes') or content.startswith('No'):
                        side = 'Yes' if content.startswith('Yes') else 'No'
        
        # 忽略 Total 行
        if title == "Total" or not title:
            continue
        
        if title and shares is not None and side:
            # Yes为正数，No为负数
            amount = shares if side == 'Yes' else -shares
            result.append({"title": title, "option": side, "amount": amount})
    
    return result


def process_poly_open_orders_data(open_orders_data):
    """
    处理 Polymarket Open Orders 数据，格式化为标准格式
    
    Args:
        open_orders_data: list，每个订单的数据列表
        
    Returns:
        list: 格式化后的数据，每项为 {"title": 标题, "price": 价格, "progress": "$x/$y"}
    """
    result = []
    
    for order_data in open_orders_data:
        title = None
        price_str = None
        progress_str = None  # "0 / 20"
        
        for item in order_data:
            if isinstance(item, dict):
                content = item.get('content', '')
                tag = item.get('tag', '')
                
                if tag == 'h2':
                    title = content
                elif '¢' in content:
                    # 价格，如 "7¢"，必须包含 ¢ 符号
                    if not price_str:  # 只取第一个匹配的
                        price_str = content
                elif '/' in content:
                    # 进度，如 "0 / 20"，必须包含 /
                    # 并且不能是 "$1.40" 这样的（虽然也有 /，但不是进度格式）
                    parts = content.split('/')
                    if len(parts) == 2 and not content.startswith('$'):
                        if not progress_str:  # 只取第一个匹配的
                            progress_str = content
        
        if title and price_str and progress_str:
            # 解析价格（去掉¢符号，转换为美元）
            try:
                price_value = float(price_str.replace('¢', '').replace('c', '').strip()) / 100
            except:
                continue
            
            # 解析进度 "0 / 20"
            try:
                parts = progress_str.split('/')
                num1 = float(parts[0].strip())
                num2 = float(parts[1].strip())
                
                # 乘以价格转换为金额
                amount1 = num1 * price_value
                amount2 = num2 * price_value
                
                # 格式化为 $x/$y，去除不必要的小数
                if amount1 == int(amount1):
                    amount1_str = f"${int(amount1)}"
                else:
                    amount1_str = f"${amount1:.2f}".rstrip('0').rstrip('.')
                
                if amount2 == int(amount2):
                    amount2_str = f"${int(amount2)}"
                else:
                    amount2_str = f"${amount2:.2f}".rstrip('0').rstrip('.')
                
                progress = f"{amount1_str}/{amount2_str}"
                
                result.append({
                    "title": title,
                    "price": price_str,
                    "progress": progress
                })
            except:
                continue
    
    return result


# ============================================================================
# Type 2 任务 - 数据获取函数（Polymarket）
# ============================================================================

def get_polymarket_portfolio_value(driver, serial_number):
    """
    获取 Polymarket Portfolio 的值
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: Portfolio的值，失败返回None
    """
    try:
        log_print(f"[{serial_number}] [POLY] 查找 Portfolio 值...")
        
        p_tags = driver.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            if p.text.strip() == "Portfolio":
                log_print(f"[{serial_number}] [POLY] ✓ 找到 Portfolio 标签")
                
                parent = p.find_element(By.XPATH, "..")
                children = parent.find_elements(By.XPATH, "./*")
                
                if len(children) >= 2:
                    portfolio_value = children[1].text.strip()
                    log_print(f"[{serial_number}] [POLY] ✓ Portfolio 值: {portfolio_value}")
                    return portfolio_value
                else:
                    log_print(f"[{serial_number}] [POLY] ⚠ Portfolio 父节点的子节点数量不足")
                    return None
        
        log_print(f"[{serial_number}] [POLY] ✗ 未找到 Portfolio 标签")
        return None
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 获取 Portfolio 值失败: {str(e)}")
        return None


def get_polymarket_cash_value(driver, serial_number):
    """
    获取 Polymarket Cash 的值
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: Cash的值，失败返回None
    """
    try:
        log_print(f"[{serial_number}] [POLY] 查找 Cash 值...")
        
        p_tags = driver.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            if p.text.strip() == "Cash":
                log_print(f"[{serial_number}] [POLY] ✓ 找到 Cash 标签")
                
                parent = p.find_element(By.XPATH, "..")
                grandparent = parent.find_element(By.XPATH, "..")
                children = grandparent.find_elements(By.XPATH, "./*")
                
                if len(children) >= 2:
                    cash_value = children[1].text.strip()
                    log_print(f"[{serial_number}] [POLY] ✓ Cash 值: {cash_value}")
                    return cash_value
                else:
                    log_print(f"[{serial_number}] [POLY] ⚠ Cash 祖父节点的子节点数量不足")
                    return None
        
        log_print(f"[{serial_number}] [POLY] ✗ 未找到 Cash 标签")
        return None
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 获取 Cash 值失败: {str(e)}")
        return None


def get_polymarket_positions_data(driver, serial_number):
    """
    点击 Polymarket Positions 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        list: 每个tr的数据列表，每个tr包含所有td的内容
    """
    try:
        log_print(f"[{serial_number}] [POLY] 在10秒内查找并点击 Positions 按钮...")
        
        positions_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Positions":
                        button.click()
                        log_print(f"[{serial_number}] [POLY] ✓ 已点击 Positions 按钮")
                        positions_clicked = True
                        break
                
                if positions_clicked:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not positions_clicked:
            log_print(f"[{serial_number}] [POLY] ✗ 10秒内未找到 Positions 按钮")
            return []
        
        time.sleep(2)
        
        try:
            tbody = driver.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            
            log_print(f"[{serial_number}] [POLY] ✓ 找到 {len(tr_list)} 个 tr 标签")
            
            all_tr_data = []
            
            for i, tr in enumerate(tr_list, 1):
                        log_print(f"[{serial_number}] [POLY] 处理第 {i} 个 tr...")
                
                        # 获取当前 tr 下的所有 td
                        td_list = tr.find_elements(By.TAG_NAME, "td")
                        log_print(f"[{serial_number}] [POLY] 第 {i} 个 tr 中找到 {len(td_list)} 个 td")
                        
                        # 如果TD数量不对，尝试其他方法
                        if len(td_list) == 0:
                            log_print(f"[{serial_number}] [POLY] ⚠ 未找到TD，尝试使用XPATH")
                            td_list = tr.find_elements(By.XPATH, "./td")
                            log_print(f"[{serial_number}] [POLY] XPATH找到 {len(td_list)} 个 td")
                        
                        tr_data = []
                        
                        # 遍历每个 td
                        for j, td in enumerate(td_list, 1):
                            td_data = []
                            
                            try:
                                # 获取 td 中的 h2 标签
                                h2_tags = td.find_elements(By.TAG_NAME, "h2")
                                for h2 in h2_tags:
                                    content = h2.text.strip()
                                    if content:
                                        td_data.append({"tag": "h2", "content": content})
                                
                                # 获取 td 中的 p 标签
                                p_tags = td.find_elements(By.TAG_NAME, "p")
                                for p in p_tags:
                                    content = p.text.strip()
                                    if content:
                                        td_data.append({"tag": "p", "content": content})
                                
                                # 获取 td 中的 span 标签
                                span_tags = td.find_elements(By.TAG_NAME, "span")
                                for span in span_tags:
                                    # 只获取没有子元素的 span
                                    children = span.find_elements(By.XPATH, "./*")
                                    if len(children) == 0:
                                        content = span.text.strip()
                                        if content and content not in [item.get("content", "") for item in td_data]:
                                            td_data.append({"tag": "span", "content": content})
                                
                                # 获取 td 中最底层的 div 标签
                                div_tags = td.find_elements(By.TAG_NAME, "div")
                                for div in div_tags:
                                    children = div.find_elements(By.XPATH, "./*")
                                    if len(children) == 0:
                                        content = div.text.strip()
                                        if content and content not in [item.get("content", "") for item in td_data]:
                                            td_data.append({"tag": "div", "content": content})
                                
                                # 如果 td_data 为空，尝试直接获取 td 的文本内容
                                if not td_data:
                                    td_content = td.text.strip()
                                    if td_content:
                                        td_data.append({"tag": "text", "content": td_content})
                                
                                log_print(f"[{serial_number}] [POLY]   TD {j}: 收集到 {len(td_data)} 项数据")
                                
                            except Exception as td_error:
                                log_print(f"[{serial_number}] [POLY]   TD {j}: 获取数据时出错 - {str(td_error)}")
                            
                            # 始终添加 td_data，即使为空也添加空列表
                            tr_data.append(td_data)
                        
                        log_print(f"[{serial_number}] [POLY] 第 {i} 个 tr 共收集 {len(tr_data)} 个 td 的数据")
                        all_tr_data.append(tr_data)
                    
            log_print(f"[{serial_number}] [POLY] ✓ Positions 数据收集完成")
            return all_tr_data
            
        except Exception as e:
            log_print(f"[{serial_number}] [POLY] ⚠ 获取 tbody 失败: {str(e)}")
            return []
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 获取 Positions 数据失败: {str(e)}")
        return []


def get_polymarket_open_orders_data(driver, serial_number):
    """
    点击 Polymarket Open orders 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        list: 每个订单的数据列表
    """
    try:
        log_print(f"[{serial_number}] [POLY] 在10秒内查找并点击 Open orders 按钮...")
        
        open_orders_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == "Open orders":
                        button.click()
                        log_print(f"[{serial_number}] [POLY] ✓ 已点击 Open orders 按钮")
                        open_orders_clicked = True
                        break
                
                if open_orders_clicked:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not open_orders_clicked:
            log_print(f"[{serial_number}] [POLY] ✗ 10秒内未找到 Open orders 按钮")
            return []
        
        time.sleep(3)
        
        try:
                    # 找到 role="tabpanel" 且 data-state="active" 的 div
                    log_print(f"[{serial_number}] [POLY] 查找 active tabpanel...")
                    tabpanel = driver.find_element(By.CSS_SELECTOR, 'div[role="tabpanel"][data-state="active"]')
                    tabpanel_class = tabpanel.get_attribute("class")
                    log_print(f"[{serial_number}] [POLY] ✓ 找到 active tabpanel")
                    log_print(f"[{serial_number}] [POLY] tabpanel class: {tabpanel_class}")
                    
                    # 获取 tabpanel 的子节点
                    tabpanel_children = tabpanel.find_elements(By.XPATH, "./*")
                    log_print(f"[{serial_number}] [POLY] tabpanel 有 {len(tabpanel_children)} 个子节点")
                    
                    if len(tabpanel_children) == 0:
                        log_print(f"[{serial_number}] [POLY] ⚠ tabpanel 没有子节点")
                        return []
                    
                    # 获取第一个子节点
                    first_child = tabpanel_children[0]
                    first_child_class = first_child.get_attribute("class")
                    first_child_tag = first_child.tag_name
                    log_print(f"[{serial_number}] [POLY] tabpanel的第一个子节点 - 标签: {first_child_tag}, class: {first_child_class}")
                    
                    # 获取第一个子节点的子节点（这些才是A）
                    a_nodes = first_child.find_elements(By.XPATH, "./*")
                    log_print(f"[{serial_number}] [POLY] tabpanel的第一个子节点有 {len(a_nodes)} 个子节点（这些是A节点）")
                    
                    if len(a_nodes) == 0:
                        log_print(f"[{serial_number}] [POLY] ⚠ 没有找到 A 节点")
                        return []
                    
                    # 打印所有 A 节点的信息
                    for idx, a_node in enumerate(a_nodes, 1):
                        a_node_tag = a_node.tag_name
                        a_node_class = a_node.get_attribute("class")
                        log_print(f"[{serial_number}] [POLY] A 节点 {idx}: 标签={a_node_tag}, class={a_node_class}")
                    
                    # 从所有 A 节点中收集 data-orientation="vertical" 的子 div
                    vertical_divs = []
                    for a_idx, a_node in enumerate(a_nodes, 1):
                        log_print(f"[{serial_number}] [POLY] 在 A 节点 {a_idx} 中查找 vertical div...")
                        a_children = a_node.find_elements(By.XPATH, "./*")
                        log_print(f"[{serial_number}] [POLY] A 节点 {a_idx} 有 {len(a_children)} 个子节点")
                        
                        for child_idx, child in enumerate(a_children, 1):
                            child_tag = child.tag_name
                            child_orientation = child.get_attribute("data-orientation")
                            log_print(f"[{serial_number}] [POLY]   子节点 {child_idx}: 标签={child_tag}, data-orientation={child_orientation}")
                            
                            if child.tag_name == "div" and child_orientation == "vertical":
                                vertical_divs.append(child)
                                log_print(f"[{serial_number}] [POLY]   ✓ 找到 vertical div!")
                    
                    log_print(f"[{serial_number}] [POLY] 找到 {len(vertical_divs)} 个 vertical div")
                    
                    all_orders_data = []
                    
                    # 遍历每个 vertical div
                    for idx, vertical_div in enumerate(vertical_divs, 1):
                        log_print(f"[{serial_number}] [POLY] 处理第 {idx} 个 vertical div...")
                        
                        order_data = []
                        
                        # 获取所有最下级的 h2 标签
                        h2_tags = vertical_div.find_elements(By.TAG_NAME, "h2")
                        for h2 in h2_tags:
                            children = h2.find_elements(By.XPATH, "./*")
                            if len(children) == 0:
                                content = h2.text.strip()
                                if content and content not in [item.get("content", "") for item in order_data]:
                                    order_data.append({"tag": "h2", "content": content})
                        
                        # 获取所有最下级的 span 标签
                        span_tags = vertical_div.find_elements(By.TAG_NAME, "span")
                        for span in span_tags:
                            children = span.find_elements(By.XPATH, "./*")
                            if len(children) == 0:
                                content = span.text.strip()
                                if content and content not in [item.get("content", "") for item in order_data]:
                                    order_data.append({"tag": "span", "content": content})
                        
                        # 获取所有最下级的 div 标签
                        div_tags = vertical_div.find_elements(By.TAG_NAME, "div")
                        for div in div_tags:
                            children = div.find_elements(By.XPATH, "./*")
                            if len(children) == 0:
                                content = div.text.strip()
                                if content and content not in [item.get("content", "") for item in order_data]:
                                    order_data.append({"tag": "div", "content": content})
                        
                        log_print(f"[{serial_number}] [POLY] 第 {idx} 个 vertical div 收集到 {len(order_data)} 项数据")
                        all_orders_data.append(order_data)
                    
                    log_print(f"[{serial_number}] [POLY] ✓ Open orders 数据收集完成，共 {len(all_orders_data)} 个订单")
                    return all_orders_data
            
        except Exception as e:
            log_print(f"[{serial_number}] [POLY] ⚠ 获取 Open orders 数据失败: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] [POLY] 错误详情:\n{traceback.format_exc()}")
            return []
        
    except Exception as e:
        log_print(f"[{serial_number}] [POLY] ✗ 获取 Open orders 数据失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [POLY] 错误详情:\n{traceback.format_exc()}")
        return []


# ============================================================================
# Type 2 任务 - 数据上传函数
# ============================================================================

def update_browser_timestamp(browser_id):
    """
    更新浏览器配置的 f 字段为当前时间戳
    
    Args:
        browser_id: 浏览器编号
        
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    try:
        log_print(f"[{browser_id}] 更新浏览器时间戳...")
        
        # 1. 获取现有配置
        get_url = f"{SERVER_BASE_URL}/boost/findAccountConfigByNo"
        params = {"no": browser_id}
        
        response = requests.get(get_url, params=params, timeout=10)
        
        if response.status_code != 200:
            log_print(f"[{browser_id}] ✗ 获取账户配置失败: HTTP {response.status_code}")
            return False
        
        result = response.json()
        if not result or not result.get('data'):
            log_print(f"[{browser_id}] ⚠ 账户配置不存在，跳过更新")
            return False
        
        account_config = result['data']
        
        # 2. 更新 f 字段为当前时间戳（毫秒）
        timestamp = int(time.time() * 1000)
        account_config['f'] = str(timestamp)
        
        log_print(f"[{browser_id}] 更新 f 字段: {timestamp}")
        
        # 3. 上传更新
        upload_url = f"{SERVER_BASE_URL}/boost/addAccountConfig"
        
        response = requests.post(upload_url, json=account_config, timeout=10)
        
        if response.status_code != 200:
            log_print(f"[{browser_id}] ✗ 上传时间戳失败: HTTP {response.status_code}")
            return False
        
        log_print(f"[{browser_id}] ✓ 时间戳更新成功")
        return True
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 更新时间戳异常: {str(e)}")
        return False


def upload_type2_data(browser_id, collected_data, exchange_name=''):
    """
    上传 Type 2 任务收集到的数据
    
    Args:
        browser_id: 浏览器编号
        collected_data: 收集到的数据，包含 positions, open_orders, balance, portfolio 等
        exchange_name: 交易所名称（OP 或 Ploy）
        
    Returns:
        bool: 上传成功返回True，失败返回False
    """
    try:
        log_print(f"[{browser_id}] 开始上传数据...")
        
        # 1. 先获取现有配置
        log_print(f"[{browser_id}] 步骤1: 获取现有账户配置...")
        get_url = f"{SERVER_BASE_URL}/boost/findAccountConfigByNo"
        params = {"no": browser_id}
        
        response = requests.get(get_url, params=params, timeout=10)
        
        if response.status_code != 200:
            log_print(f"[{browser_id}] ✗ 获取账户配置失败: HTTP {response.status_code}")
            return False
        
        result = response.json()
        if not result or not result.get('data'):
            log_print(f"[{browser_id}] ✗ 账户配置不存在")
            return False
        
        account_config = result['data']
        log_print(f"[{browser_id}] ✓ 已获取现有账户配置")
        
        # 2. 格式化 position 数据（使用 ||| 作为字段分隔符，避免标题中的逗号）
        positions = collected_data.get('positions', [])
        position_str_list = []
        for pos in positions:
            title = pos['title']
            option = pos.get('option', '')
            amount = pos['amount']
            avg_price = pos.get('avg_price', '')
            position_str_list.append(f"{title}|||{option}|||{amount:+.2f}|||{avg_price}")
        position_str = ";".join(position_str_list)
        
        # 3. 格式化 open orders 数据（使用 ||| 作为字段分隔符，避免标题中的逗号）
        open_orders = collected_data.get('open_orders', [])
        open_orders_str_list = []
        for order in open_orders:
            title = order['title']
            price = order['price']
            progress = order['progress']
            open_orders_str_list.append(f"{title}|||{price}|||{progress}")
        open_orders_str = ";".join(open_orders_str_list)
        
        # 4. 获取 balance 和 portfolio
        # Polymarket 使用 cash，OP 使用 balance
        if exchange_name.upper() == 'PLOY':
            balance_str = collected_data.get('cash', '')
            log_print(f"[{browser_id}] 使用 Polymarket 的 cash 作为余额")
        else:
            balance_str = collected_data.get('balance', '')
            log_print(f"[{browser_id}] 使用 OP 的 balance 作为余额")
        
        portfolio_str = collected_data.get('portfolio', '')
        
        # 5. 判断数据是否收集成功（必须至少成功获取到portfolio或balance其中一个）
        data_collected_success = False
        
        # 检查是否成功获取到 balance 或 portfolio（不是None，不是空字符串）
        balance_found = balance_str is not None and balance_str != ''
        portfolio_found = portfolio_str is not None and portfolio_str != ''
        
        if balance_found or portfolio_found:
            data_collected_success = True
            log_print(f"[{browser_id}] ✓ 数据收集成功（balance: {'已获取' if balance_found else '未获取'}, portfolio: {'已获取' if portfolio_found else '未获取'}），将更新时间戳")
        else:
            log_print(f"[{browser_id}] ✗ 数据收集失败：portfolio 和 balance 组件都未找到，不更新时间戳")
        
        # 转换为数字（去掉$符号）
        try:
            if isinstance(balance_str, str):
                balance = float(balance_str.replace('$', '').replace(',', ''))
            else:
                balance = float(balance_str) if balance_str else 0
        except:
            balance = 0
        
        try:
            if isinstance(portfolio_str, str):
                portfolio = float(portfolio_str.replace('$', '').replace(',', ''))
            else:
                portfolio = float(portfolio_str) if portfolio_str else 0
        except:
            portfolio = 0
        
        # 6. 更新字段
        account_config['a'] = position_str
        account_config['b'] = open_orders_str
        account_config['balance'] = balance
        account_config['c'] = str(portfolio)
        
        # 只有在数据收集成功时才更新时间戳 d
        if data_collected_success:
            import time
            timestamp = int(time.time() * 1000)
            account_config['d'] = str(timestamp)
            log_print(f"[{browser_id}] ✓ 更新时间戳: {timestamp}")
        else:
            log_print(f"[{browser_id}] ℹ 保持原有时间戳不变")
        
        account_config['e'] = exchange_name  # 平台名称
        
        # 6. 格式化 transactions 数据并上传到新接口
        transactions = collected_data.get('transactions', [])
        log_print(f"[{browser_id}] 开始格式化 {len(transactions)} 条交易记录...")
        
        if transactions:
            # 将时间字符串转换为时间戳的函数
            def parse_time_to_timestamp(time_str):
                """
                将时间字符串转换为时间戳（毫秒）
                格式: Nov 26, 2025 19:38:42
                """
                try:
                    from datetime import datetime
                    # 解析时间字符串
                    dt = datetime.strptime(time_str, "%b %d, %Y %H:%M:%S")
                    # 转换为时间戳（毫秒）
                    timestamp = int(dt.timestamp() * 1000)
                    return timestamp
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 时间解析失败 '{time_str}': {str(e)}")
                    return 0
            
            # 清理金额和价格字段，只保留数字和小数点
            def clean_number_string(value_str):
                """
                去除字符串中的货币符号，只保留数字和小数点
                例如: "$1.49" -> "1.49", "1.5 ¢" -> "1.5"
                """
                if not value_str:
                    return "0"
                
                # 去除所有非数字、非小数点、非负号的字符
                import re
                cleaned = re.sub(r'[^\d\.\-]', '', value_str)
                
                # 如果清理后为空，返回 "0"
                if not cleaned or cleaned == '.':
                    return "0"
                
                return cleaned
            
            # 格式化为新接口所需的格式
            transactions_list = []
            for idx, trans in enumerate(transactions, 1):
                # 清理 shares, amount 和 price，去除符号
                cleaned_shares = clean_number_string(trans['amount'])
                cleaned_amount = clean_number_string(trans['value'])
                cleaned_price = clean_number_string(trans['price'])
                
                transaction_data = {
                    "trending": trans['title'],
                    "side": trans['direction'],
                    "outCome": trans['option'],
                    "shares": cleaned_shares,    # 原 amount 字段映射到 shares (去除逗号)
                    "amount": cleaned_amount,    # 原 value 字段映射到 amount (去除符号)
                    "price": cleaned_price,      # price (去除符号)
                    "time": parse_time_to_timestamp(trans['time'])
                }
                transactions_list.append(transaction_data)
                log_print(f"[{browser_id}]   交易 {idx}: {trans['title']} | {trans['direction']} | {trans['option']} | shares={cleaned_shares} (原:{trans['amount']}) | amount={cleaned_amount} (原:{trans['value']}) | price={cleaned_price} (原:{trans['price']}) | time={transaction_data['time']}")
            
            log_print(f"[{browser_id}] ✓ 交易记录格式化完成，共 {len(transactions_list)} 条")
            
            # 上传交易记录到新接口
            try:
                insert_order_url = f"{SERVER_BASE_URL}/boost/insertOrderHist"
                order_data = {
                    "number": str(browser_id),
                    "list": transactions_list
                }
                
                # 打印 order_data 的字符串格式
                import json
                order_data_str = json.dumps(order_data, ensure_ascii=False, indent=2)
                log_print(f"[{browser_id}] ==================== order_data 详细内容 ====================")
                log_print(f"[{browser_id}] {order_data_str}")
                log_print(f"[{browser_id}] =================================================================")
                
                log_print(f"[{browser_id}] 开始上传交易记录到 /boost/insertOrderHist...")
                order_response = requests.post(insert_order_url, json=order_data, timeout=15)
                
                if order_response.status_code == 200:
                    log_print(f"[{browser_id}] ✓ 交易记录上传成功")
                    log_print(f"[{browser_id}] 服务器响应: {order_response.json()}")
                else:
                    log_print(f"[{browser_id}] ⚠ 交易记录上传失败: HTTP {order_response.status_code}")
            except Exception as e:
                log_print(f"[{browser_id}] ✗ 交易记录上传异常: {str(e)}")
        else:
            log_print(f"[{browser_id}] 无交易记录需要上传")
        
        log_print(f"[{browser_id}] 步骤2: 更新数据字段...")
        log_print(f"[{browser_id}]   a (positions): {position_str[:100]}...")
        log_print(f"[{browser_id}]   b (open_orders): {open_orders_str[:100]}...")
        log_print(f"[{browser_id}]   balance: {balance}")
        log_print(f"[{browser_id}]   c (portfolio): {portfolio}")
        log_print(f"[{browser_id}]   d (timestamp): {'已更新' if data_collected_success else '保持不变'}")
        log_print(f"[{browser_id}]   e (platform): {exchange_name}")
        log_print(f"[{browser_id}]   transactions: {len(transactions)} 条交易记录已上传到 insertOrderHist 接口")
        
        # 7. 上传更新
        log_print(f"[{browser_id}] 步骤3: 上传更新到服务器...")
        upload_url = f"{SERVER_BASE_URL}/boost/addAccountConfig"
        
        # 将数据放在数组中
        upload_data = account_config
        
        response = requests.post(upload_url, json=upload_data, timeout=15)
        
        if response.status_code != 200:
            log_print(f"[{browser_id}] ✗ 上传失败: HTTP {response.status_code}")
            return False
        
        result = response.json()
        log_print(f"[{browser_id}] ✓ 数据上传成功")
        log_print(f"[{browser_id}] 服务器响应: {result}")
        
        return True
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 上传数据失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False


# ============================================================================
# Type 3 任务处理函数 - 收集订单簿数据
# ============================================================================

def click_subtopic_button_for_type3(driver, browser_id, trending_part1):
    """
    为 type=3 任务点击子主题按钮（不获取数据）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        trending_part1: 子主题名称
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        log_print(f"[{browser_id}] 查找并点击子主题按钮: {trending_part1}")
        
        # 找到 data-sentry-element="Accordion" 的 div
        accordion_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-sentry-element="Accordion"]')
        
        if not accordion_divs:
            log_print(f"[{browser_id}] ⚠ 未找到 Accordion div")
            return False
        
        log_print(f"[{browser_id}] ✓ 找到 {len(accordion_divs)} 个 Accordion div")
        
        # 在 Accordion div 中查找内容等于 trending_part1 的 p 标签
        for accordion_div in accordion_divs:
            p_tags = accordion_div.find_elements(By.TAG_NAME, "p")
            
            for p in p_tags:
                if p.text.strip() == trending_part1:
                    log_print(f"[{browser_id}] ✓ 找到匹配的 p 标签: {trending_part1}")
                    
                    # 点击 p 标签的父节点的父节点的父节点（即子主题按钮）
                    parent1 = p.find_element(By.XPATH, "..")
                    parent2 = parent1.find_element(By.XPATH, "..")
                    sub_topic_button = parent2.find_element(By.XPATH, "..")
                    
                    # 检查 aria-expanded 属性
                    aria_expanded = sub_topic_button.get_attribute("aria-expanded")
                    log_print(f"[{browser_id}] 子主题按钮 aria-expanded: {aria_expanded}")
                    
                    if aria_expanded == "false":
                        sub_topic_button.click()
                        log_print(f"[{browser_id}] ✓ 已点击子主题按钮（展开）")
                    elif aria_expanded == "true":
                        log_print(f"[{browser_id}] ✓ 子主题按钮已展开，无需点击")
                    else:
                        # aria-expanded 为 None 或其他值，尝试点击
                        log_print(f"[{browser_id}] ⚠ aria-expanded 值异常: {aria_expanded}，尝试点击")
                        sub_topic_button.click()
                        log_print(f"[{browser_id}] ✓ 已点击子主题按钮")
                    
                    return True
        
        log_print(f"[{browser_id}] ⚠ 未找到匹配的子主题: {trending_part1}")
        return False
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 点击子主题按钮失败: {str(e)}")
        return False


def click_higher_price_button(driver, browser_id):
    """
    点击价格较高的按钮
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        tuple: (success, button_prefix) 
               success: 成功返回True，失败返回False
               button_prefix: 第一个按钮返回"YES"，第二个按钮返回"NO"，失败返回None
    """
    try:
        log_print(f"[{browser_id}] 查找 trade-box div...")
        
        # 找到 data-flag="trade-box" 的 div
        trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
        
        if not trade_box_divs:
            log_print(f"[{browser_id}] ⚠ 未找到 trade-box div")
            return False, None
        
        trade_box = trade_box_divs[0]
        log_print(f"[{browser_id}] ✓ 找到 trade-box div")
        
        # 在 trade-box 中查找前两个 BuySell 按钮
        buttons = trade_box.find_elements(By.CSS_SELECTOR, 
            'button[data-sentry-element="Button"][data-sentry-source-file="BuySell.tsx"]')
        
        if len(buttons) < 2:
            log_print(f"[{browser_id}] ⚠ 按钮数量不足，期望2个，实际{len(buttons)}个")
            return False, None
        
        log_print(f"[{browser_id}] ✓ 找到 {len(buttons)} 个按钮，使用前2个")
        
        # 获取前两个按钮的价格信息
        button_prices = []
        for idx, button in enumerate(buttons[:2], 1):
            p_tags = button.find_elements(By.TAG_NAME, "p")
            
            if len(p_tags) < 2:
                log_print(f"[{browser_id}] ⚠ 按钮{idx} p标签数量不足: {len(p_tags)}")
                continue
            
            side = p_tags[0].text.strip()  # 例如: "YES" 或 "NO"
            price_text = p_tags[1].text.strip()  # 例如: "0.8¢"
            
            # 提取价格数字
            try:
                # 去除特殊字符，只保留数字和小数点
                price_str = price_text.replace('¢', '').replace('$', '').replace(',', '').strip()
                price = float(price_str)
                
                button_prices.append({
                    'index': idx - 1,
                    'button': button,
                    'side': side,
                    'price': price,
                    'price_text': price_text
                })
                
                log_print(f"[{browser_id}] 按钮{idx}: {side} - {price_text} (数值: {price})")
            except ValueError as e:
                log_print(f"[{browser_id}] ⚠ 按钮{idx} 价格解析失败: {price_text}, 错误: {str(e)}")
        
        if len(button_prices) < 2:
            log_print(f"[{browser_id}] ⚠ 有效按钮数量不足: {len(button_prices)}")
            return False, None
        
        # 找出价格较高的按钮
        higher_price_button = max(button_prices, key=lambda x: x['price'])
        
        log_print(f"[{browser_id}] 价格较高的按钮: {higher_price_button['side']} - {higher_price_button['price_text']} (数值: {higher_price_button['price']})")
        
        # 点击价格较高的按钮
        higher_price_button['button'].click()
        log_print(f"[{browser_id}] ✓ 已点击价格较高的按钮")
        
        # 根据按钮位置返回前缀：第一个按钮返回 "YES"，第二个按钮返回 "NO"
        button_prefix = "YES" if higher_price_button['index'] == 0 else "NO"
        log_print(f"[{browser_id}] 按钮前缀: {button_prefix} (按钮索引: {higher_price_button['index']})")
        
        return True, button_prefix
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 点击价格按钮失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, None


def get_orderbook_data_with_subtopic_simple(driver, browser_id):
    """
    有子主题时获取订单簿数据（简化版，不点击子主题按钮）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        str: 订单簿数据字符串，格式为 "xx,xx,xx;xx2,xx2,xx2"
    """
    try:
        log_print(f"[{browser_id}] 查找订单簿 div...")
        
        # 直接查找两个订单簿 div
        orderbook_divs = driver.find_elements(By.CSS_SELECTOR, 
            'div[class="flex-col flex w-full flex-1 overflow-y-auto"][data-sentry-element="Stack"][data-sentry-source-file="Orderbook.tsx"]')
        
        log_print(f"[{browser_id}] 找到 {len(orderbook_divs)} 个订单簿 div")
        
        if len(orderbook_divs) < 2:
            log_print(f"[{browser_id}] ⚠ 订单簿 div 数量不足，期望2个，实际{len(orderbook_divs)}个")
            return ""
        
        # 获取两个 div 的数据
        results = []
        for idx, orderbook_div in enumerate(orderbook_divs[:2], 1):
            log_print(f"[{browser_id}] 处理第 {idx} 个订单簿 div...")
            
            # 获取第一个子 div
            child_divs = orderbook_div.find_elements(By.XPATH, "./div")
            if not child_divs:
                log_print(f"[{browser_id}] ⚠ 第 {idx} 个订单簿 div 没有子 div")
                continue
            
            first_child_div = child_divs[0]
            
            # 获取所有 p 标签内容，去除逗号
            p_tags = first_child_div.find_elements(By.TAG_NAME, "p")
            p_contents = [p.text.strip().replace(',', '') for p in p_tags if p.text.strip()]
            
            log_print(f"[{browser_id}] 第 {idx} 个订单簿收集到 {len(p_contents)} 个 p 标签")
            results.append(",".join(p_contents))
        
        # 用分号连接两个订单簿的数据
        result_str = ";".join(results)
        log_print(f"[{browser_id}] ✓ 订单簿数据收集完成: {result_str[:100]}...")
        return result_str
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取订单簿数据失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return ""


def get_orderbook_data_with_subtopic(driver, browser_id, trending_part1, needClick = True):
    """
    有子主题时获取订单簿数据
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        trending_part1: 子主题名称
        
    Returns:
        str: 订单簿数据字符串，格式为 "xx,xx,xx;xx2,xx2,xx2"
    """
    try:
        log_print(f"[{browser_id}] 查找并点击子主题按钮: {trending_part1}")
        
        # 找到 data-sentry-element="Accordion" 的 div
        accordion_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-sentry-element="Accordion"]')
        
        if not accordion_divs:
            log_print(f"[{browser_id}] ⚠ 未找到 Accordion div")
            return ""
        
        log_print(f"[{browser_id}] ✓ 找到 {len(accordion_divs)} 个 Accordion div")
        
        # 在 Accordion div 中查找内容等于 trending_part1 的 p 标签
        for accordion_div in accordion_divs:
            p_tags = accordion_div.find_elements(By.TAG_NAME, "p")
            
            for p in p_tags:
                if p.text.strip() == trending_part1:
                    log_print(f"[{browser_id}] ✓ 找到匹配的 p 标签: {trending_part1}")
                    
                    # 点击 p 标签的父节点的父节点的父节点（即子主题按钮）
                    parent1 = p.find_element(By.XPATH, "..")
                    parent2 = parent1.find_element(By.XPATH, "..")
                    sub_topic_button = parent2.find_element(By.XPATH, "..")
                    
                    if needClick:
                        sub_topic_button.click()
                    else:
                        log_print(f"[{browser_id}] ✓ 无需点击子主题按钮")
                        
                    log_print(f"[{browser_id}] ✓ 已点击子主题按钮")
                    time.sleep(2)
                    
                    # 获取子主题按钮的父节点
                    button_parent = sub_topic_button.find_element(By.XPATH, "..")
                    log_print(f"[{browser_id}] ✓ 获取到按钮的父节点")
                    
                    # 找到父节点下与 button 同级的 div 子节点
                    sibling_divs = button_parent.find_elements(By.XPATH, "./div")
                    log_print(f"[{browser_id}] 找到 {len(sibling_divs)} 个同级 div")
                    
                    # 在这些 div 中找到包含订单簿的 div
                    orderbook_divs = []
                    for sibling_div in sibling_divs:
                        # 查找两个订单簿 div
                        target_divs = sibling_div.find_elements(By.CSS_SELECTOR, 
                            'div[class="flex-col flex w-full flex-1 overflow-y-auto"][data-sentry-element="Stack"][data-sentry-source-file="Orderbook.tsx"]')
                        if target_divs:
                            orderbook_divs.extend(target_divs)
                    
                    log_print(f"[{browser_id}] 找到 {len(orderbook_divs)} 个订单簿 div")
                    
                    if len(orderbook_divs) < 2:
                        log_print(f"[{browser_id}] ⚠ 订单簿 div 数量不足，期望2个，实际{len(orderbook_divs)}个")
                        return ""
                    
                    # 获取两个 div 的数据
                    results = []
                    total_p_count = 0  # 统计收集到的总 p 标签数量
                    
                    for idx, orderbook_div in enumerate(orderbook_divs[:2], 1):
                        log_print(f"[{browser_id}] 处理第 {idx} 个订单簿 div...")
                        
                        # 获取第一个子 div
                        child_divs = orderbook_div.find_elements(By.XPATH, "./div")
                        if not child_divs:
                            log_print(f"[{browser_id}] ⚠ 第 {idx} 个订单簿 div 没有子 div")
                            continue
                        
                        first_child_div = child_divs[0]
                        
                        # 获取所有 p 标签内容（包括所有嵌套层级），去除逗号
                        p_tags = first_child_div.find_elements(By.TAG_NAME, "p")
                        p_contents = [p.text.strip().replace(',', '') for p in p_tags if p.text.strip()]
                        
                        log_print(f"[{browser_id}] 第 {idx} 个订单簿收集到 {len(p_contents)} 个 p 标签")
                        total_p_count += len(p_contents)
                        results.append(",".join(p_contents))
                    
                    # 检查是否收集到数据
                    if total_p_count == 0:
                        log_print(f"[{browser_id}] ⚠ 未收集到任何订单簿数据（0个p标签）")
                        # 检查是否已经重试过
                        if not hasattr(get_orderbook_data_with_subtopic, f'_retried_{browser_id}'):
                            log_print(f"[{browser_id}] 刷新页面并重试一次...")
                            setattr(get_orderbook_data_with_subtopic, f'_retried_{browser_id}', True)
                            
                            # 刷新页面
                            driver.refresh()
                            time.sleep(3)
                            
                            # 清除重试标志（在递归调用完成后）
                            try:
                                result = get_orderbook_data_with_subtopic(driver, browser_id, trending_part1, needClick)
                                return result
                            finally:
                                # 清除重试标志
                                delattr(get_orderbook_data_with_subtopic, f'_retried_{browser_id}')
                        else:
                            log_print(f"[{browser_id}] ⚠ 已重试过一次，仍未收集到数据")
                            return ""
                    
                    # 用分号连接两个订单簿的数据
                    result_str = ";".join(results)
                    log_print(f"[{browser_id}] ✓ 订单簿数据收集完成: {result_str[:100]}...")
                    return result_str
        
        log_print(f"[{browser_id}] ⚠ 未找到匹配的子主题: {trending_part1}")
        return ""
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取订单簿数据失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return ""


def get_orderbook_data_without_subtopic(driver, browser_id):
    """
    没有子主题时获取订单簿数据
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        str: 订单簿数据字符串，格式为 "xx,xx,xx;xx2,xx2,xx2"
    """
    try:
        log_print(f"[{browser_id}] 查找订单簿容器 div (无子主题)...")
        
        # 查找 div(A)
        container_divs = driver.find_elements(By.CSS_SELECTOR, 
            'div[class="flex-col flex min-h-0 flex-1"][data-sentry-element="Stack"][data-sentry-source-file="Orderbook.tsx"]')
        
        if not container_divs:
            log_print(f"[{browser_id}] ⚠ 未找到订单簿容器 div")
            return ""
        
        container_div = container_divs[0]
        log_print(f"[{browser_id}] ✓ 找到订单簿容器 div")
        
        # 获取 div(A) 的所有子 div
        child_divs = container_div.find_elements(By.XPATH, "./div")
        
        if len(child_divs) < 2:
            log_print(f"[{browser_id}] ⚠ 容器 div 子节点数量不足: {len(child_divs)}")
            return ""
        
        log_print(f"[{browser_id}] 容器 div 有 {len(child_divs)} 个子 div")
        
        results = []
        
        # 第一部分：div(A) 下的第一个 div 子节点下的最后一个 div 子节点的所有 p 标签
        log_print(f"[{browser_id}] 处理第一部分数据...")
        first_child_div = child_divs[0]
        first_child_sub_divs = first_child_div.find_elements(By.XPATH, "./div")
        
        if first_child_sub_divs:
            last_sub_div = first_child_sub_divs[-1]
            p_tags = last_sub_div.find_elements(By.TAG_NAME, "p")
            # 获取 p 标签内容，去除逗号
            p_contents = [p.text.strip().replace(',', '') for p in p_tags if p.text.strip()]
            log_print(f"[{browser_id}] 第一部分收集到 {len(p_contents)} 个 p 标签")
            results.append(",".join(p_contents))
        else:
            log_print(f"[{browser_id}] ⚠ 第一个子 div 没有子节点")
            results.append("")
        
        # 第二部分：div(A) 下的最后一个 div 子节点的第一个 div 子节点下的所有 p 标签
        log_print(f"[{browser_id}] 处理第二部分数据...")
        last_child_div = child_divs[-1]
        last_child_sub_divs = last_child_div.find_elements(By.XPATH, "./div")
        
        if last_child_sub_divs:
            first_sub_div = last_child_sub_divs[0]
            p_tags = first_sub_div.find_elements(By.TAG_NAME, "p")
            # 获取 p 标签内容，去除逗号
            p_contents = [p.text.strip().replace(',', '') for p in p_tags if p.text.strip()]
            log_print(f"[{browser_id}] 第二部分收集到 {len(p_contents)} 个 p 标签")
            results.append(",".join(p_contents))
        else:
            log_print(f"[{browser_id}] ⚠ 最后一个子 div 没有子节点")
            results.append("")
        
        # 用分号连接两部分数据
        result_str = ";".join(results)
        log_print(f"[{browser_id}] ✓ 订单簿数据收集完成: {result_str[:100]}...")
        return result_str
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取订单簿数据失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return ""


def execute_type3_data_collection(driver, browser_id, target_url, trending_part1, side='Buy'):
    """
    执行Type 3数据收集流程（从步骤5开始，可重试）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        target_url: 目标URL
        trending_part1: 子主题（如果有）
        side: Buy 或 Sell，默认为Buy
        
    Returns:
        tuple: (success, button_prefix, orderbook_data, error_msg)
    """
    try:
        # 5. 等待 Position 按钮出现
        log_print(f"[{browser_id}] 步骤5: 等待 Position 按钮出现...")
        if not wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
            return False, None, "", "Position按钮未出现，页面加载可能失败"
        
        # 6. 如果有子主题，点击子主题按钮
        if trending_part1:
            log_print(f"[{browser_id}] 步骤6a: 点击子主题按钮...")
            if not click_subtopic_button_for_type3(driver, browser_id, trending_part1):
                return False, None, "", "点击子主题按钮失败"
            time.sleep(8)
        
        # 6.5. 点击 Buy 或 Sell 按钮
        log_print(f"[{browser_id}] 步骤6.5: 点击 {side} 按钮...")
        trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
        if not trade_box_divs:
            return False, None, "", "未找到trade-box"
        
        trade_box = trade_box_divs[0]
        if not click_opinion_trade_type_button(trade_box, side, browser_id):
            return False, None, "", f"点击{side}按钮失败"
        
        time.sleep(1)
        
        # 7. 点击价格较高的按钮
        log_print(f"[{browser_id}] 步骤7: 点击价格较高的按钮...")
        button_success, button_prefix = click_higher_price_button(driver, browser_id)
        if not button_success:
            return False, None, "", "价格解析失败"
        
        time.sleep(3)
        
        # 8. 根据是否有子主题，收集不同的数据
        if trending_part1:
            log_print(f"[{browser_id}] 步骤8: 收集订单簿数据（有子主题）...")
            orderbook_data = get_orderbook_data_with_subtopic(driver, browser_id, trending_part1, False)
        else:
            log_print(f"[{browser_id}] 步骤8: 收集订单簿数据（无子主题）...")
            orderbook_data = get_orderbook_data_without_subtopic(driver, browser_id)
        
        if not orderbook_data:
            return False, None, "", "订单簿数据收集失败"
        
        return True, button_prefix, orderbook_data, ""
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 数据收集流程异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, None, "", f"执行异常: {str(e)}"


def process_type3_mission(task_data):
    """
    处理 Type 3 任务 - 获取订单簿数据
    
    Args:
        task_data: 任务数据，包含 mission 和 exchangeConfig
        
    Returns:
        tuple: (success, failure_reason, orderbook_data)
    """
    mission = task_data.get("mission", {})
    exchange_config = task_data.get("exchangeConfig", {})
    
    browser_id = mission.get("numberList", "")
    mission_id = mission.get("id", "")
    exchange_name = mission.get("exchangeName", "")
    side1 = mission.get("side", 1)  # 获取方向参数，默认为Buy
    side = "Buy" if side1 == 1 else "Sell"
    log_print(f"\n[{browser_id}] ========== 开始处理 Type 3 任务 ==========")
    log_print(f"[{browser_id}] 任务ID: {mission_id}")
    log_print(f"[{browser_id}] 交易所: {exchange_name}")
    log_print(f"[{browser_id}] 方向: {side}")
    
    driver = None
    orderbook_data = ""
    
    try:
        # 获取网页地址
        if exchange_name.upper() == "OP":
            target_url = exchange_config.get("opUrl", "")
        else:
            target_url = exchange_config.get("polyUrl", "")
        
        if not target_url:
            return False, "未找到目标URL", orderbook_data
        
        log_print(f"[{browser_id}] 目标URL: {target_url}")
        
        # 从 trending 中提取子主题
        trending = exchange_config.get("trending", "")
        trending_part1 = ""
        
        if "###" in trending:
            parts = trending.split("###")
            trending_part1 = parts[1].strip() if len(parts) > 1 else ""
            log_print(f"[{browser_id}] 检测到子主题: {trending_part1}")
        else:
            log_print(f"[{browser_id}] 无子主题")
        
        # 1. 检查IP并更新代理
        # log_print(f"[{browser_id}] 步骤1: 检查IP并更新代理...")
        # try_update_ip_before_start(browser_id)
        
        # 2. 打开浏览器
        log_print(f"[{browser_id}] 步骤2: 打开浏览器...")
        browser_data = start_adspower_browser(browser_id)
        
        if not browser_data:
            return False, "浏览器启动失败", orderbook_data
        
        # 3. 创建Selenium驱动
        log_print(f"[{browser_id}] 步骤3: 创建Selenium驱动...")
        driver = create_selenium_driver(browser_data)
        
        # 3.5 等待4秒后再操作页面
        log_print(f"[{browser_id}] 等待4秒...")
        time.sleep(4)
        
        # 4. 检查当前页面并刷新
        log_print(f"[{browser_id}] 步骤4: 检查当前页面URL...")
        current_url = driver.current_url
        log_print(f"[{browser_id}] 当前URL: {current_url}")
        
        # 比较URL（忽略协议和尾部斜杠）
        def normalize_url(url):
            url = url.replace('https://', '').replace('http://', '')
            url = url.rstrip('/')
            return url
        
        if normalize_url(current_url) != normalize_url(target_url):
            log_print(f"[{browser_id}] URL不一致，打开目标页面...")
            driver.get(target_url)
            time.sleep(2)
        else:
            log_print(f"[{browser_id}] ✓ 当前页面已是目标页面，刷新页面...")
            driver.refresh()
            time.sleep(2)
        
        # 执行数据收集流程（带重试机制）
        max_retries = 2
        button_prefix = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                log_print(f"[{browser_id}] ⚠ 第 {attempt} 次重试，重新加载页面...")
                driver.refresh()
                time.sleep(3)
            
            log_print(f"[{browser_id}] 开始数据收集流程（尝试 {attempt + 1}/{max_retries + 1}）...")
            success, button_prefix, orderbook_data, error_msg = execute_type3_data_collection(
                driver, browser_id, target_url, trending_part1, side
            )
            
            if success:
                log_print(f"[{browser_id}] ✓ 数据收集成功")
                break
            else:
                log_print(f"[{browser_id}] ✗ 数据收集失败: {error_msg}")
                if attempt < max_retries:
                    log_print(f"[{browser_id}] 准备重试...")
                else:
                    log_print(f"[{browser_id}] ✗✗✗ 已达到最大重试次数，任务失败")
                    return False, f"数据收集失败（重试{max_retries}次后）: {error_msg}", orderbook_data
        
        # 在订单簿数据前面加上按钮前缀
        if button_prefix:
            orderbook_data = f"{button_prefix};{orderbook_data}"
            log_print(f"[{browser_id}] 添加按钮前缀: {button_prefix}")
        
        log_print(f"[{browser_id}] ========== Type 3 任务完成 ==========\n")
        log_print(f"[{browser_id}] 保持浏览器打开状态（Type 3 任务）")
        return True, "", orderbook_data
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗✗✗ Type 3 任务执行异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, f"执行异常: {str(e)}", orderbook_data
        
    finally:
        # Type 3 任务不关闭浏览器
        log_print(f"[{browser_id}] Type 3 任务结束，浏览器保持打开")


# ============================================================================
# Type 2 任务处理函数
# ============================================================================

def collect_position_data(driver, browser_id, exchange_name):
    """
    收集持仓和订单数据（可在 type=1 任务后调用）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器编号
        exchange_name: 交易所名称
        
    Returns:
        tuple: (success, collected_data)
    """
    collected_data = {}
    
    try:
        log_print(f"\n[{browser_id}] ========== 额外收集持仓数据 ==========")
        
        # 判断交易所
        if exchange_name.upper() == "OP":
            log_print(f"[{browser_id}] 交易所为 OP，进入 profile 页面...")
            
            profile_url = "https://app.opinion.trade/profile"
            driver.get(profile_url)
            log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
            
            time.sleep(2)
            
            # 检查并连接钱包
            log_print(f"[{browser_id}] 检查并连接钱包...")
            connect_wallet_if_needed(driver, browser_id)
            
            # 获取数据（带重试机制）
            max_data_collection_retries = 3
            retry_attempt = 0
            position_data = []
            open_orders_data = []
            transactions_data = []
            
            while retry_attempt < max_data_collection_retries:
                try:
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}获取 Portfolio 值...")
                    portfolio_value, need_retry_portfolio = get_opinion_portfolio_value(driver, browser_id)
                    collected_data['portfolio'] = portfolio_value
                    
                    if need_retry_portfolio:
                        log_print(f"[{browser_id}] ⚠ Portfolio 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Portfolio 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}获取 Balance 值...")
                    balance_value, need_retry_balance = get_opinion_balance_value(driver, browser_id)
                    collected_data['balance'] = balance_value
                    
                    if need_retry_balance:
                        log_print(f"[{browser_id}] ⚠ Balance 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Balance 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}点击 Position 并获取数据...")
                    position_data, need_retry_position = click_opinion_position_and_get_data(driver, browser_id)
                    collected_data['position'] = position_data
                    
                    if need_retry_position:
                        log_print(f"[{browser_id}] ⚠ Position 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Position 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}点击 Open Orders 并获取数据...")
                    open_orders_data, need_retry_orders = click_opinion_open_orders_and_get_data(driver, browser_id)
                    
                    if need_retry_orders:
                        log_print(f"[{browser_id}] ⚠ Open Orders 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Open Orders 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}点击 Transactions 并获取数据...")
                    transactions_data, need_retry_transactions = click_opinion_transactions_and_get_data(driver, browser_id)
                    
                    if need_retry_transactions:
                        log_print(f"[{browser_id}] ⚠ Transactions 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Transactions 数据获取失败")
                            break
                    
                    # 全部成功，跳出重试循环
                    log_print(f"[{browser_id}] ✓ 所有数据获取成功")
                    break
                    
                except Exception as e:
                    log_print(f"[{browser_id}] ✗ 数据获取异常: {str(e)}")
                    retry_attempt += 1
                    if retry_attempt < max_data_collection_retries:
                        log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                        driver.refresh()
                        time.sleep(5)
                        connect_wallet_if_needed(driver, browser_id)
                        time.sleep(2)
                    else:
                        log_print(f"[{browser_id}] ✗ 已达到最大重试次数")
                        break
            
            # 处理数据为标准格式
            log_print(f"[{browser_id}] 处理数据为标准格式...")
            processed_positions = process_op_position_data(position_data)
            processed_open_orders = process_op_open_orders_data(open_orders_data)
            
            collected_data['positions'] = processed_positions
            collected_data['open_orders'] = processed_open_orders
            collected_data['transactions'] = transactions_data
            
            # 打印收集到的数据
            log_print(f"\n[{browser_id}] ========== 收集到的数据 (OP) ==========")
            log_print(f"[{browser_id}] Portfolio: {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Balance: {collected_data.get('balance', 'N/A')}")
            log_print(f"[{browser_id}] Position 数据 ({len(processed_positions)} 项):")
            for i, item in enumerate(processed_positions, 1):
                log_print(f"[{browser_id}]   {i}. {item}")
            log_print(f"[{browser_id}] Open Orders 数据 ({len(processed_open_orders)} 项):")
            for i, item in enumerate(processed_open_orders, 1):
                log_print(f"[{browser_id}]   {i}. {item['title']}, {item['price']}, {item['progress']}")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 上传数据
            log_print(f"[{browser_id}] 上传数据到服务器...")
            upload_success = upload_type2_data(browser_id, collected_data, 'OP')
            
            if upload_success:
                log_print(f"[{browser_id}] ✓ 数据上传成功")
            else:
                log_print(f"[{browser_id}] ⚠ 数据上传失败")
            
            return True, collected_data
        
        elif exchange_name.upper() == "PLOY":
            log_print(f"[{browser_id}] 交易所为 Ploy，进入 Polymarket portfolio 页面...")
            
            portfolio_url = "https://polymarket.com/portfolio?tab=positions"
            driver.get(portfolio_url)
            log_print(f"[{browser_id}] ✓ 已打开页面: {portfolio_url}")
            
            time.sleep(3)
            
            # 获取数据
            log_print(f"[{browser_id}] 获取 Portfolio 值...")
            portfolio_value = get_polymarket_portfolio_value(driver, browser_id)
            collected_data['portfolio'] = portfolio_value
            
            log_print(f"[{browser_id}] 获取 Cash 值...")
            cash_value = get_polymarket_cash_value(driver, browser_id)
            collected_data['cash'] = cash_value
            
            log_print(f"[{browser_id}] 点击 Positions 并获取数据...")
            positions_data = get_polymarket_positions_data(driver, browser_id)
            collected_data['positions'] = positions_data
            
            log_print(f"[{browser_id}] 点击 Open orders 并获取数据...")
            open_orders_data = get_polymarket_open_orders_data(driver, browser_id)
            
            # 处理数据为标准格式
            log_print(f"[{browser_id}] 处理数据为标准格式...")
            processed_positions = process_poly_position_data(positions_data)
            processed_open_orders = process_poly_open_orders_data(open_orders_data)
            
            collected_data['positions'] = processed_positions
            collected_data['open_orders'] = processed_open_orders
            
            # 打印收集到的数据
            log_print(f"\n[{browser_id}] ========== 收集到的数据 (Polymarket) ==========")
            log_print(f"[{browser_id}] Portfolio: {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Cash: {collected_data.get('cash', 'N/A')}")
            log_print(f"[{browser_id}] Position 数据 ({len(processed_positions)} 项):")
            for i, item in enumerate(processed_positions, 1):
                log_print(f"[{browser_id}]   {i}. {item}")
            log_print(f"[{browser_id}] Open Orders 数据 ({len(processed_open_orders)} 项):")
            for i, item in enumerate(processed_open_orders, 1):
                log_print(f"[{browser_id}]   {i}. {item['title']}, {item['price']}, {item['progress']}")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 上传数据
            log_print(f"[{browser_id}] 上传数据到服务器...")
            upload_success = upload_type2_data(browser_id, collected_data, 'Ploy')
            
            if upload_success:
                log_print(f"[{browser_id}] ✓ 数据上传成功")
            else:
                log_print(f"[{browser_id}] ⚠ 数据上传失败")
            
            return True, collected_data
            
        else:
            log_print(f"[{browser_id}] ⚠ 不支持的交易所: {exchange_name}")
            return False, collected_data
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 收集数据异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, collected_data


def process_type2_mission(task_data, retry_count=0):
    """
    处理 Type 2 任务 - 获取交易所数据
    
    Args:
        task_data: 任务数据，包含 mission 和 exchangeConfig
        retry_count: 重试次数（默认为0）
        
    Returns:
        tuple: (success, failure_reason, collected_data)
    """
    mission = task_data.get("mission", {})
    
    browser_id = mission.get("numberList", "")
    mission_id = mission.get("id", "")
    exchange_name = mission.get("exchangeName", "")
    
    log_print(f"\n[{browser_id}] ========== 开始处理 Type 2 任务 {'(重试第' + str(retry_count) + '次)' if retry_count > 0 else ''} ==========")
    log_print(f"[{browser_id}] 任务ID: {mission_id}")
    log_print(f"[{browser_id}] 交易所: {exchange_name}")
    
    driver = None
    collected_data = {}
    
    try:
        # 1. 检查IP并更新代理
        log_print(f"[{browser_id}] 步骤1: 检查IP并更新代理...")
        try_update_ip_before_start(browser_id)
        
        # 2. 打开浏览器
        log_print(f"[{browser_id}] 步骤2: 打开浏览器...")
        browser_data = start_adspower_browser(browser_id)
        
        if not browser_data:
            return False, "浏览器启动失败", collected_data
        
        # 3. 创建Selenium驱动
        log_print(f"[{browser_id}] 步骤3: 创建Selenium驱动...")
        driver = create_selenium_driver(browser_data)
        
        # 3.5 等待4秒后再进入目标页面
        log_print(f"[{browser_id}] 等待4秒...")
        time.sleep(4)
        
        # 4. 判断交易所
        if exchange_name.upper() == "OP":
            log_print(f"[{browser_id}] 步骤4: 交易所为 OP，进入 profile 页面...")
            
            profile_url = "https://app.opinion.trade/profile"
            driver.get(profile_url)
            log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
            
            time.sleep(2)
            
            # 4.0.5 预打开OKX钱包
            log_print(f"[{browser_id}] 步骤4.0.5: 预打开OKX钱包...")
            main_window = preopen_okx_wallet(driver, browser_id)
            
            # 4.1 检查并连接钱包
            log_print(f"[{browser_id}] 步骤4.1: 检查并连接钱包...")
            connect_wallet_if_needed(driver, browser_id)
            
            # 4.2 Type2任务特殊处理：检查OKX Wallet P标签
            log_print(f"[{browser_id}] 步骤4.2: 等待15秒后检查 OKX Wallet 状态...")
            time.sleep(15)
            
            # 第一次检查是否存在 OKX Wallet P标签
            if check_okx_wallet_p_exists(driver, browser_id, timeout=5):
                log_print(f"[{browser_id}] ⚠ 检测到 OKX Wallet P标签仍然存在，执行第一次重连...")
                connect_wallet_if_needed(driver, browser_id)
                
                # 等待15秒后第二次检查
                log_print(f"[{browser_id}] 等待15秒后进行第二次检查...")
                time.sleep(15)
                
                # 第二次检查是否存在 OKX Wallet P标签
                if check_okx_wallet_p_exists(driver, browser_id, timeout=5):
                    log_print(f"[{browser_id}] ✗✗✗ OKX Wallet P标签依然存在，需要换IP重试...")
                    
                    # 检查是否已经重试过
                    if retry_count == 0:
                        log_print(f"[{browser_id}] Type=2 任务需要换IP重试，开始执行重试流程...")
                        
                        # 1. 关闭浏览器
                        log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        close_adspower_browser(browser_id)
                        time.sleep(2)
                        
                        # 2. 强制更换IP
                        log_print(f"[{browser_id}] 步骤2: 强制更换IP...")
                        proxy_config = force_change_ip_for_browser(browser_id, timeout=15)
                        
                        if not proxy_config:
                            log_print(f"[{browser_id}] ✗ 获取新IP失败")
                            return False, "换IP失败", collected_data
                        
                        log_print(f"[{browser_id}] ✓ 获取新IP: {proxy_config['ip']}")
                        
                        # 3. 更新代理配置
                        log_print(f"[{browser_id}] 步骤3: 更新代理配置...")
                        if not update_adspower_proxy(browser_id, proxy_config):
                            log_print(f"[{browser_id}] ✗ 更新代理失败")
                            return False, "更新代理失败", collected_data
                        
                        log_print(f"[{browser_id}] ✓ 代理配置已更新")
                        time.sleep(2)
                        
                        # 4. 递归重试任务（retry_count+1）
                        log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: 1）...")
                        return process_type2_mission(task_data, retry_count=1)
                    else:
                        log_print(f"[{browser_id}] ✗ 已经重试过一次，不再重试")
                        return False, "OKX Wallet连接失败且已重试", collected_data
                else:
                    log_print(f"[{browser_id}] ✓ 第二次检查通过，OKX Wallet 已正常连接")
            else:
                log_print(f"[{browser_id}] ✓ 第一次检查通过，OKX Wallet 已正常连接")
            
            # 获取数据（步骤5-9带重试机制）
            max_data_collection_retries = 3
            retry_attempt = 0
            position_data = []
            open_orders_data = []
            transactions_data = []
            
            while retry_attempt < max_data_collection_retries:
                try:
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤5: 获取 Portfolio 值...")
                    portfolio_value, need_retry_portfolio = get_opinion_portfolio_value(driver, browser_id)
                    collected_data['portfolio'] = portfolio_value
                    
                    if need_retry_portfolio:
                        log_print(f"[{browser_id}] ⚠ Portfolio 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            # 重新连接钱包
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Portfolio 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤6: 获取 Balance 值...")
                    balance_value, need_retry_balance = get_opinion_balance_value(driver, browser_id)
                    collected_data['balance'] = balance_value
                    
                    if need_retry_balance:
                        log_print(f"[{browser_id}] ⚠ Balance 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            # 重新连接钱包
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Balance 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤7: 点击 Position 并获取数据...")
                    position_data, need_retry_position = click_opinion_position_and_get_data(driver, browser_id)
                    collected_data['position'] = position_data
                    
                    if need_retry_position:
                        log_print(f"[{browser_id}] ⚠ Position 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            # 重新连接钱包
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Position 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤8: 点击 Open Orders 并获取数据...")
                    open_orders_data, need_retry_orders = click_opinion_open_orders_and_get_data(driver, browser_id)
                    
                    if need_retry_orders:
                        log_print(f"[{browser_id}] ⚠ Open Orders 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            # 重新连接钱包
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Open Orders 数据获取失败")
                            break
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤9: 点击 Transactions 并获取数据...")
                    transactions_data, need_retry_transactions = click_opinion_transactions_and_get_data(driver, browser_id)
                    
                    if need_retry_transactions:
                        log_print(f"[{browser_id}] ⚠ Transactions 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.refresh()
                            time.sleep(5)
                            # 重新连接钱包
                            connect_wallet_if_needed(driver, browser_id)
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Transactions 数据获取失败")
                            break
                    
                    # 全部成功，跳出重试循环
                    log_print(f"[{browser_id}] ✓ 所有数据获取成功")
                    break
                    
                except Exception as e:
                    log_print(f"[{browser_id}] ✗ 数据获取异常: {str(e)}")
                    retry_attempt += 1
                    if retry_attempt < max_data_collection_retries:
                        log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                        driver.refresh()
                        time.sleep(5)
                        connect_wallet_if_needed(driver, browser_id)
                        time.sleep(2)
                    else:
                        log_print(f"[{browser_id}] ✗ 已达到最大重试次数")
                        break
            
            # 打印原始数据
            log_print(f"\n[{browser_id}] ========== 原始数据 ==========")
            log_print(f"[{browser_id}] Portfolio (原始): {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Balance (原始): {collected_data.get('balance', 'N/A')}")
            log_print(f"[{browser_id}] Position 原始数据 ({len(position_data)} 项):")
            log_print(f"[{browser_id}]   {position_data}")
            log_print(f"[{browser_id}] Open Orders 原始数据 ({len(open_orders_data)} 项):")
            log_print(f"[{browser_id}]   {open_orders_data}")
            log_print(f"[{browser_id}] Transactions 原始数据 ({len(transactions_data)} 项):")
            log_print(f"[{browser_id}]   {transactions_data}")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 整理原始数据，准备传到服务器
            raw_data_for_server = {
                'portfolio': collected_data.get('portfolio', ''),
                'balance': collected_data.get('balance', ''),
                'position': position_data,
                'open_orders': open_orders_data,
                'transactions': transactions_data
            }
            log_print(f"[{browser_id}] 收集到的原始数据: {raw_data_for_server}")
            
            # 处理数据为标准格式
            log_print(f"[{browser_id}] 步骤10: 处理数据为标准格式...")
            processed_positions = process_op_position_data(position_data)
            processed_open_orders = process_op_open_orders_data(open_orders_data)
            
            collected_data['positions'] = processed_positions
            collected_data['open_orders'] = processed_open_orders
            collected_data['transactions'] = transactions_data
            
            # 打印收集到的数据
            log_print(f"\n[{browser_id}] ========== 收集到的数据 (OP) ==========")
            log_print(f"[{browser_id}] Portfolio: {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Balance: {collected_data.get('balance', 'N/A')}")
            log_print(f"[{browser_id}] Position 数据 ({len(processed_positions)} 项):")
            for i, item in enumerate(processed_positions, 1):
                log_print(f"[{browser_id}]   {i}. {item}")
            log_print(f"[{browser_id}] Open Orders 数据 ({len(processed_open_orders)} 项):")
            for i, item in enumerate(processed_open_orders, 1):
                log_print(f"[{browser_id}]   {i}. {item['title']}, {item['price']}, {item['progress']}")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 上传数据
            log_print(f"[{browser_id}] 步骤10: 上传数据到服务器...")
            upload_success = upload_type2_data(browser_id, collected_data, 'OP')
            
            if upload_success:
                log_print(f"[{browser_id}] ✓ 数据上传成功")
            else:
                log_print(f"[{browser_id}] ⚠ 数据上传失败，但任务继续")
            
            log_print(f"[{browser_id}] ========== Type 2 任务完成 (OP) ==========\n")
            return True, "", collected_data
        
        elif exchange_name.upper() == "PLOY":
            log_print(f"[{browser_id}] 步骤4: 交易所为 Ploy，进入 Polymarket portfolio 页面...")
            
            portfolio_url = "https://polymarket.com/portfolio?tab=positions"
            driver.get(portfolio_url)
            log_print(f"[{browser_id}] ✓ 已打开页面: {portfolio_url}")
            
            time.sleep(2)
            
            # 4.0.5 预打开OKX钱包
            log_print(f"[{browser_id}] 步骤4.0.5: 预打开OKX钱包...")
            main_window = preopen_okx_wallet(driver, browser_id)
            
            time.sleep(1)
            
            # 获取数据
            log_print(f"[{browser_id}] 步骤5: 获取 Portfolio 值...")
            portfolio_value = get_polymarket_portfolio_value(driver, browser_id)
            collected_data['portfolio'] = portfolio_value
            
            log_print(f"[{browser_id}] 步骤6: 获取 Cash 值...")
            cash_value = get_polymarket_cash_value(driver, browser_id)
            collected_data['cash'] = cash_value
            
            log_print(f"[{browser_id}] 步骤7: 点击 Positions 并获取数据...")
            positions_data = get_polymarket_positions_data(driver, browser_id)
            collected_data['positions'] = positions_data
            
            log_print(f"[{browser_id}] 步骤8: 点击 Open orders 并获取数据...")
            open_orders_data = get_polymarket_open_orders_data(driver, browser_id)
            
            # 处理数据为标准格式
            log_print(f"[{browser_id}] 步骤9: 处理数据为标准格式...")
            processed_positions = process_poly_position_data(positions_data)
            processed_open_orders = process_poly_open_orders_data(open_orders_data)
            
            collected_data['positions'] = processed_positions
            collected_data['open_orders'] = processed_open_orders
            
            # 打印收集到的数据
            log_print(f"\n[{browser_id}] ========== 收集到的数据 (Polymarket) ==========")
            log_print(f"[{browser_id}] Portfolio: {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Cash: {collected_data.get('cash', 'N/A')}")
            log_print(f"[{browser_id}] Position 数据 ({len(processed_positions)} 项):")
            for i, item in enumerate(processed_positions, 1):
                log_print(f"[{browser_id}]   {i}. {item}")
            log_print(f"[{browser_id}] Open Orders 数据 ({len(processed_open_orders)} 项):")
            for i, item in enumerate(processed_open_orders, 1):
                log_print(f"[{browser_id}]   {i}. {item['title']}, {item['price']}, {item['progress']}")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 上传数据
            log_print(f"[{browser_id}] 步骤10: 上传数据到服务器...")
            upload_success = upload_type2_data(browser_id, collected_data, 'Ploy')
            
            if upload_success:
                log_print(f"[{browser_id}] ✓ 数据上传成功")
            else:
                log_print(f"[{browser_id}] ⚠ 数据上传失败，但任务继续")
            
            log_print(f"[{browser_id}] ========== Type 2 任务完成 (Ploy) ==========\n")
            return True, "", collected_data
            
        else:
            log_print(f"[{browser_id}] ⚠ 不支持的交易所: {exchange_name}")
            return False, f"不支持的交易所: {exchange_name}", collected_data
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗✗✗ Type 2 任务执行异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False, f"执行异常: {str(e)}", collected_data
        
    finally:
        # 关闭浏览器
        log_print(f"[{browser_id}] 任务完成，正在关闭浏览器...")
        close_adspower_browser(browser_id)


# ============================================================================
# 多线程任务管理函数
# ============================================================================

def get_thread_pool_status():
    """
    获取线程池状态
    
    Returns:
        tuple: (active_count, pending_count)
    """
    with active_tasks_lock:
        active_count = len(active_tasks)
        pending_count = sum(task_info['total'] - task_info['completed'] 
                          for task_info in active_tasks.values())
    return active_count, pending_count


def check_and_submit_completed_missions():
    """
    检查并提交已完成的任务
    """
    completed_missions = []
    
    with active_tasks_lock:
        for mission_id, task_info in list(active_tasks.items()):
            if task_info['completed'] >= task_info['total']:
                completed_missions.append(mission_id)
    
    # 处理每个已完成的任务
    for mission_id in completed_missions:
        with active_tasks_lock:
            task_info = active_tasks.get(mission_id)
            if not task_info:
                continue
            
            results = task_info['results']
            task_type = task_info.get('type')
            
            # Type 3任务特殊处理
            if task_type == 3:
                # Type 3任务的结果在单浏览器处理时已提交
                log_print(f"[系统] ✓ Type 3 任务 {mission_id} 已完成")
            elif task_type == 5:
                # Type 5任务特殊处理：直接使用详细的msg
                success_count = sum(1 for r in results.values() if r['success'])
                failed_count = sum(1 for r in results.values() if not r['success'])
                
                # 获取详细msg（优先使用第一个结果的msg）
                detailed_msg = None
                for browser_id, result in results.items():
                    if 'msg' in result and result['msg']:
                        detailed_msg = result['msg']
                        break
                
                # 如果有详细msg，直接使用；否则使用默认格式
                if detailed_msg:
                    # 直接提交详细msg
                    status = 2 if success_count > 0 else 3
                    url = f"{SERVER_BASE_URL}/mission/saveResult"
                    payload = {
                        "id": mission_id,
                        "status": status,
                        "msg": detailed_msg
                    }
                    
                    log_print(f"\n[系统] Type 5 任务提交详细结果: {url}")
                    log_print(f"[系统] 提交数据: {payload}")
                    
                    try:
                        response = requests.post(url, json=payload, timeout=10)
                        if response.status_code == 200:
                            log_print(f"[系统] ✓ Type 5 结果提交成功")
                        else:
                            log_print(f"[系统] ✗ Type 5 结果提交失败，状态码: {response.status_code}")
                    except Exception as e:
                        log_print(f"[系统] ✗ Type 5 结果提交异常: {str(e)}")
                else:
                    # 没有详细msg，使用默认格式
                    failed_info = {bid: r['reason'] for bid, r in results.items() if not r['success']}
                    status = 2 if success_count > 0 else 3
                    submit_mission_result(mission_id, success_count, failed_count, failed_info, status)
            else:
                # 其他类型任务
                # 统计成功和失败数
                success_count = sum(1 for r in results.values() if r['success'])
                failed_count = sum(1 for r in results.values() if not r['success'])
                failed_info = {bid: r['reason'] for bid, r in results.items() if not r['success']}
                
                # 提交任务结果
                status = 2 if success_count > 0 else 3
                submit_mission_result(mission_id, success_count, failed_count, failed_info, status)
            
            # 从活动任务列表中移除
            del active_tasks[mission_id]
            log_print(f"[系统] 任务 {mission_id} 已从活动任务列表中移除")


def submit_mission_to_pool(task_data):
    """
    将任务提交到全局线程池
    
    Args:
        task_data: 包含mission和exchangeConfig的任务数据
    """
    mission = task_data.get("mission", {})
    mission_id = mission.get("id")
    mission_type = mission.get("type")
    browser_id = str(mission.get("numberList", ""))
    
    log_print(f"[系统] 提交任务 {mission_id} (type={mission_type}, browser={browser_id}) 到线程池")
    
    # 初始化任务状态
    with active_tasks_lock:
        active_tasks[mission_id] = {
            'futures': [],
            'results': {},
            'total': 1,  # auto_trader.py中每个任务只有一个浏览器
            'completed': 0,
            'type': mission_type
        }
    
    # 提交到线程池
    future = global_thread_pool.submit(execute_mission_in_thread, task_data, mission_id, browser_id)
    
    with active_tasks_lock:
        active_tasks[mission_id]['futures'].append(future)
    
    log_print(f"[系统] ✓ 任务 {mission_id} 已提交到线程池")


def execute_mission_in_thread(task_data, mission_id, browser_id):
    """
    在线程中执行任务
    
    Args:
        task_data: 任务数据
        mission_id: 任务ID
        browser_id: 浏览器ID
    """
    mission = task_data.get("mission", {})
    mission_type = mission.get("type")
    
    try:
        # 先更新浏览器时间戳
        if browser_id:
            update_browser_timestamp(browser_id)
        
        # 根据任务类型执行
        if mission_type == 1 or mission_type == 5:
            # Type 1: 普通交易任务
            # Type 5: 自动对冲交易任务（带同步机制）
            result = process_trading_mission(task_data, keep_browser_open=True)
            
            if len(result) == 5:
                success, failure_reason, driver, task_browser_id, task_exchange_name = result
            else:
                success, failure_reason = result
                driver = None
                task_browser_id = None
                task_exchange_name = None
            
            # 立即记录任务结果（不等待数据收集）
            log_print(f"[{browser_id}] Type {mission_type} 任务{'成功' if success else '失败'}，立即记录结果...")
            with active_tasks_lock:
                if mission_id in active_tasks:
                    active_tasks[mission_id]['results'][browser_id] = {
                        'success': success,
                        'reason': failure_reason if not success else '',
                        'msg': failure_reason  # 保存完整的 msg（成功或失败都保存）
                    }
                    active_tasks[mission_id]['completed'] += 1
            log_print(f"[{browser_id}] ✓ Type {mission_type} 任务结果已记录")
            
            # Type 5任务特殊处理：任务二失败时通知任务一
            if mission_type == 5 and not success:
                tp1 = mission.get('tp1')
                if tp1:
                    # 这是任务二，失败了
                    log_print(f"[{browser_id}] Type 5 任务二失败，检查任务一状态...")
                    task1_status = get_mission_status(tp1)
                    if task1_status is not None and task1_status != 3:
                        # 任务一状态不是3，将其改为3
                        log_print(f"[{browser_id}] 任务一当前状态: {task1_status}，将其改为状态3（任务二失败）")
                        save_mission_result(tp1, 3, "任务二失败")
                    else:
                        log_print(f"[{browser_id}] 任务一状态已是3或无法获取，无需修改")
            
            # Type 1/5任务完成后收集持仓数据（不影响任务结果）
            if success and driver and task_browser_id and task_exchange_name:
                try:
                    log_print(f"[{browser_id}] 开始额外收集持仓数据（不影响任务结果）...")
                    collect_position_data(driver, task_browser_id, task_exchange_name)
                    log_print(f"[{browser_id}] ✓ 额外持仓数据收集完成")
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 额外数据收集异常: {str(e)}，但不影响任务")
                finally:
                    log_print(f"[{browser_id}] 关闭浏览器...")
                    close_adspower_browser(task_browser_id)
            elif not success:
                # 任务失败，直接关闭浏览器
                if driver and task_browser_id:
                    log_print(f"[{browser_id}] 任务失败，关闭浏览器...")
                    close_adspower_browser(task_browser_id)
            
            # Type 1/5 任务结果已经在上面记录了，跳过后面的统一记录
            return
            
        elif mission_type == 2:
            # Type 2: 数据获取任务
            success, failure_reason, collected_data = process_type2_mission(task_data)
            
        elif mission_type == 3:
            # Type 3: 订单簿数据获取任务
            # 初始化变量（放在最前面，确保即使前面发生异常也能访问）
            success = False
            failure_reason = "未执行"
            type3_completed_updated = False  # 标记是否已更新计数
            
            try:
                # 将浏览器ID和任务ID加入正在执行的映射
                with active_type3_browsers_lock:
                    active_type3_browsers[browser_id] = mission_id
                    log_print(f"[{browser_id}] Type 3 任务 {mission_id} 开始，浏览器已标记为繁忙")
                
                try:
                    success, failure_reason, orderbook_data = process_type3_mission(task_data)
                    
                    # Type 3任务直接提交结果
                    if success:
                        payload = {
                            "id": mission_id,
                            "status": 2,
                            "msg": orderbook_data
                        }
                        url = f"{SERVER_BASE_URL}/mission/saveResult"
                        try:
                            response = requests.post(url, json=payload, timeout=10)
                            if response.status_code == 200:
                                log_print(f"[{browser_id}] ✓ Type 3 结果提交成功")
                        except Exception as e:
                            log_print(f"[{browser_id}] ✗ Type 3 结果提交异常: {str(e)}")
                    else:
                        submit_mission_result(mission_id, 0, 1, {browser_id: failure_reason}, status=3)
                finally:
                    # 无论成功还是失败，都从映射中移除浏览器ID
                    with active_type3_browsers_lock:
                        active_type3_browsers.pop(browser_id, None)
                        log_print(f"[{browser_id}] Type 3 任务 {mission_id} 完成，浏览器标记已清除")
                    
                    # 更新任务完成计数，以便任务可以从 active_tasks 中清理
                    with active_tasks_lock:
                        if mission_id in active_tasks:
                            active_tasks[mission_id]['results'][browser_id] = {
                                'success': success,
                                'reason': failure_reason if not success else ''
                            }
                            active_tasks[mission_id]['completed'] += 1
                            type3_completed_updated = True
                            log_print(f"[{browser_id}] ✓ Type 3 任务计数已更新 (completed: {active_tasks[mission_id]['completed']}/{active_tasks[mission_id]['total']})")
            finally:
                # 确保浏览器标记被清除（双重保险）
                with active_type3_browsers_lock:
                    if browser_id in active_type3_browsers:
                        active_type3_browsers.pop(browser_id, None)
                        log_print(f"[{browser_id}] Type 3 任务 {mission_id} 外层finally：确保浏览器标记已清除")
                
                # 如果内层 finally 没有更新计数（比如在加入浏览器集合时就异常了），这里补充更新
                if not type3_completed_updated:
                    with active_tasks_lock:
                        if mission_id in active_tasks:
                            active_tasks[mission_id]['results'][browser_id] = {
                                'success': False,
                                'reason': failure_reason
                            }
                            active_tasks[mission_id]['completed'] += 1
                            log_print(f"[{browser_id}] ✓ Type 3 任务计数已补充更新（外层finally）")
            
            # Type 3 任务结果已经提交了，跳过后面的统一记录
            return
            
        else:
            log_print(f"[{browser_id}] ⚠ 不支持的任务类型: {mission_type}")
            success = False
            failure_reason = f"不支持的任务类型{mission_type}"
        
        # 记录结果
        with active_tasks_lock:
            if mission_id in active_tasks:
                active_tasks[mission_id]['results'][browser_id] = {
                    'success': success,
                    'reason': failure_reason if not success else ''
                }
                active_tasks[mission_id]['completed'] += 1
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 线程执行异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        
        # 如果是 type=3 任务发生异常，确保清除浏览器标记
        if mission_type == 3:
            with active_type3_browsers_lock:
                if browser_id in active_type3_browsers:
                    active_type3_browsers.pop(browser_id, None)
                    log_print(f"[{browser_id}] Type 3 任务 {mission_id} 异常，清除浏览器标记")
        
        # 记录失败（Type 1 和 Type 3 已经在各自的逻辑中更新了计数，这里只处理 Type 2 和其他类型）
        if mission_type not in [1, 3]:
            with active_tasks_lock:
                if mission_id in active_tasks:
                    active_tasks[mission_id]['results'][browser_id] = {
                        'success': False,
                        'reason': f"执行异常: {str(e)}"
                    }
                    active_tasks[mission_id]['completed'] += 1
        else:
            log_print(f"[{browser_id}] Type {mission_type} 任务异常，计数已在其他地方更新")


# ============================================================================
# 主循环
# ============================================================================

def main():
    """
    主函数 - 多线程任务循环
    """
    log_print("\n" + "="*80)
    log_print("统一交易自动化脚本启动 - 多线程模式")
    log_print("="*80)
    log_print(f"电脑组编号: {COMPUTER_GROUP}")
    log_print(f"服务器地址: {SERVER_BASE_URL}")
    log_print(f"最大并发线程数: {MAX_WORKERS}")
    log_print(f"轮询间隔: 3秒")
    log_print("="*80 + "\n")
    
    log_print("[系统] 开始监听任务...\n")
    
    # 永久循环
    while True:
        try:
            # 1. 检查并提交已完成的任务
            check_and_submit_completed_missions()
            
            # 2. 获取线程池状态
            active_count, pending_count = get_thread_pool_status()
            
            # 3. 检查线程池状态
            log_print(f"[系统] 线程池状态: 活跃任务 {active_count} 个, 待处理 {pending_count}/{MAX_WORKERS}")
            
            # 线程池是否已满
            pool_is_full = pending_count >= MAX_WORKERS
            
            if pool_is_full:
                log_print(f"[系统] 线程池已满 ({pending_count}/{MAX_WORKERS})，等待空闲...")
                time.sleep(3)
                continue  # 跳过获取任务，直接进入下一次循环
            
            # 4. 线程池有空闲，从服务器获取任务
            log_print(f"[系统] 线程池有空闲，尝试从服务器获取新任务...")
            task_data = get_mission_from_server()
            
            if task_data:
                mission = task_data.get("mission", {})
                mission_id = mission.get("id")
                mission_type = mission.get("type")
                exchange_name = mission.get("exchangeName", "")
                browser_id = str(mission.get("numberList", ""))
                
                log_print(f"[系统] 获取到任务 {mission_id}，类型: {mission_type}，交易所: {exchange_name}，浏览器: {browser_id}")
                
                # 如果是 type=3 任务，检查该浏览器是否已经在执行 type=3 任务
                if mission_type == 3:
                    browser_is_busy = False
                    with active_type3_browsers_lock:
                        if browser_id in active_type3_browsers:
                            old_mission_id = active_type3_browsers[browser_id]
                            # 检查旧任务是否真的还在运行
                            with active_tasks_lock:
                                if old_mission_id in active_tasks:
                                    # 旧任务还在运行，浏览器确实繁忙
                                    browser_is_busy = True
                                    log_print(f"[系统] 浏览器 {browser_id} 正在执行 Type=3 任务 {old_mission_id}")
                                else:
                                    # 旧任务已完成但标记未清除（幽灵标记），自动清理
                                    log_print(f"[系统] ⚠ 检测到幽灵标记：浏览器 {browser_id} 的旧任务 {old_mission_id} 已完成但标记未清除，自动清理")
                                    active_type3_browsers.pop(browser_id, None)
                                    browser_is_busy = False
                    
                    if browser_is_busy:
                        log_print(f"[系统] ⚠ 浏览器 {browser_id} 已有 Type=3 任务正在执行，跳过任务 {mission_id}")
                        # 提交失败结果
                        submit_mission_result(mission_id, 0, 1, {browser_id: "该浏览器已有Type=3任务正在执行"}, status=3)
                        log_print(f"[系统] ✓ Type=3 任务 {mission_id} 已标记为失败")
                        continue  # 跳过后续处理，继续下一次循环
                
                # 如果是 type=3 任务且线程池已有5个或更多任务，直接跳过
                if mission_type == 3 and pending_count >= 5:
                    log_print(f"[系统] ⚠ 线程池已有 {pending_count} 个任务，跳过 Type=3 任务 {mission_id}")
                    # 提交失败结果
                    submit_mission_result(mission_id, 0, 1, {browser_id: "线程池繁忙，Type=3任务被跳过"}, status=3)
                    log_print(f"[系统] ✓ Type=3 任务 {mission_id} 已标记为失败")
                # 线程池有空闲，提交任务
                else:
                    # 提交到线程池
                    submit_mission_to_pool(task_data)
            else:
                if not pool_is_full:
                    log_print(f"[系统] 暂无新任务")
            
            # 短暂等待后继续
            time.sleep(3)
            
        except KeyboardInterrupt:
            log_print("\n\n[系统] 收到退出信号，等待当前任务完成...")
            
            # 等待所有任务完成
            with active_tasks_lock:
                pending_tasks = list(active_tasks.keys())
            
            if pending_tasks:
                log_print(f"[系统] 等待 {len(pending_tasks)} 个任务完成: {pending_tasks}")
                while True:
                    check_and_submit_completed_missions()
                    active_count, pending_count = get_thread_pool_status()
                    
                    if active_count == 0:
                        log_print(f"[系统] ✓ 所有任务已完成")
                        break
                    
                    log_print(f"[系统] 等待中... 剩余 {active_count} 个任务")
                    time.sleep(2)
            
            # 关闭线程池
            log_print(f"[系统] 关闭线程池...")
            global_thread_pool.shutdown(wait=True)
            
            break
            
        except Exception as e:
            log_print(f"\n[系统] ✗ 主循环发生错误: {str(e)}")
            import traceback
            log_print(f"[系统] 错误详情:\n{traceback.format_exc()}")
            log_print(f"[系统] 3秒后继续...")
            time.sleep(3)
    
    log_print("\n" + "="*80)
    log_print("程序已退出")
    log_print("="*80 + "\n")


def initialize_fingerprint_mapping():
    """
    初始化浏览器编号到用户ID的映射数据
    """
    global FINGERPRINT_TO_USERID
    
    # 映射数据
    mapping_data = """2000	k15jmeql
1999	k15jmeqk
1998	k15jmeqj
1997	k15jmeqi
1996	k15jmeqh
1995	k15jmeqg
1994	k15jmeqe
1993	k15jmeqd
1992	k15jmeqc
1991	k15jmeqb
1990	k15jmeqa
1989	k15jmeq9
1988	k15jmeq8
1987	k15jmeq7
1986	k15jmeq6
1985	k15jmeq4
1984	k15jmeq3
1983	k15jmeq2
1982	k15jmeq1
1981	k15jmeq0
1980	k15jmepy
1979	k15jmepx
1978	k15jmepw
1977	k15jmepu
1976	k15jmept
1975	k15jmeps
1974	k15jmepr
1973	k15jmepq
1972	k15jmepo
1971	k15jmepn
1970	k15jmepm
1969	k15jmepl
1968	k15jmepk
1967	k15jmepj
1966	k15jmepi
1965	k15jmeph
1964	k15jmepg
1963	k15jmepf
1962	k15jmepe
1961	k15jmepd
1960	k15jmepc
1959	k15jmepb
1958	k15jmep9
1957	k15jmep8
1956	k15jmep7
1955	k15jmep6
1954	k15jmep5
1953	k15jmep3
1952	k15jmep2
1951	k15jmep1
1950	k15jmep0
1949	k15jmeoy
1948	k15jmeox
1947	k15jmeow
1946	k15jmeov
1945	k15jmeou
1944	k15jmeot
1943	k15jmeos
1942	k15jmeoq
1941	k15jmeop
1940	k15jmeoo
1939	k15jmeom
1938	k15jmeol
1937	k15jmeok
1936	k15jmeoj
1935	k15jmeoi
1934	k15jmeoh
1933	k15jmeog
1932	k15jmeof
1931	k15jmeoe
1930	k15jmeod
1929	k15jmeob
1928	k15jmeo8
1927	k15jmeo7
1926	k15jmeo6
1925	k15jmeo5
1924	k15jmeo4
1923	k15jmeo3
1922	k15jmeo2
1921	k15jmeo1
1920	k15jmeo0
1919	k15jmeny
1918	k15jmenx
1917	k15jmenv
1916	k15jment
1915	k15jmens
1914	k15jmenr
1913	k15jmenq
1912	k15jmenp
1911	k15jmeno
1910	k15jmenn
1909	k15jmenm
1908	k15jmenk
1907	k15jmenj
1906	k15jmeni
1905	k15jmenh
1904	k15jmeng
1903	k15jmenf
1902	k15jmene
1901	k15jmend
1900	k15jmenc
1899	k15jmenb
1898	k15jmena
1897	k15jmen9
1896	k15jmen8
1895	k15jmen7
1894	k15jmen5
1893	k15jmen4
1892	k15jmen3
1891	k15jmen1
1890	k15jmen0
1889	k15jmemy
1888	k15jmemx
1887	k15jmemw
1886	k15jmemv
1885	k15jmemu
1884	k15jmemt
1883	k15jmems
1882	k15jmemr
1881	k15jmemp
1880	k15jmemo
1879	k15jmemn
1878	k15jmemm
1877	k15jmeml
1876	k15jmemk
1875	k15jmemj
1874	k15jmemh
1873	k15jmemg
1872	k15jmemf
1871	k15jmeme
1870	k15jmemd
1869	k15jmemc
1868	k15jmemb
1867	k15jmema
1866	k15jmem9
1865	k15jmem8
1864	k15jmem7
1863	k15jmem5
1862	k15jmem4
1861	k15jmem3
1860	k15jmem2
1859	k15jmem1
1858	k15jmem0
1857	k15jmely
1856	k15jmelx
1855	k15jmelw
1854	k15jmelu
1853	k15jmelt
1852	k15jmels
1851	k15jmelr
1850	k15jmelq
1849	k15jmelp
1848	k15jmelo
1847	k15jmeln
1846	k15jmelm
1845	k15jmell
1844	k15jmelk
1843	k15jmelj
1842	k15jmeli
1841	k15jmelh
1840	k15jmelg
1839	k15jmelf
1838	k15jmele
1837	k15jmeld
1836	k15jmelc
1835	k15jmelb
1834	k15jmel9
1833	k15jmel8
1832	k15jmel7
1831	k15jmel6
1830	k15jmel5
1829	k15jmel4
1828	k15jmel3
1827	k15jmel2
1826	k15jmel1
1825	k15jmel0
1824	k15jmeky
1823	k15jmekx
1822	k15jmekw
1821	k15jmeku
1820	k15jmekt
1819	k15jmeks
1818	k15jmekr
1817	k15jmekq
1816	k15jmekp
1815	k15jmeko
1814	k15jmekn
1813	k15jmekm
1812	k15jmekl
1811	k15jmekj
1810	k15jmeki
1809	k15jmekh
1808	k15jmekg
1807	k15jmekf
1806	k15jmeke
1805	k15jmekd
1804	k15jmekc
1803	k15jmekb
1802	k15jmeka
1801	k15jmek8
1800	k15jmek7
1799	k15jmek6
1798	k15jmek5
1797	k15jmek4
1796	k15jmek2
1795	k15jmek1
1794	k15jmek0
1793	k15jmejx
1792	k15jmejw
1791	k15jmejv
1790	k15jmeju
1789	k15jmejt
1788	k15jmejs
1787	k15jmejq
1786	k15jmejp
1785	k15jmejo
1784	k15jmejn
1783	k15jmejm
1782	k15jmejl
1781	k15jmejk
1780	k15jmejj
1779	k15jmeji
1778	k15jmejh
1777	k15jmejg
1776	k15jmejf
1775	k15jmeje
1774	k15jmejd
1773	k15jmeja
1772	k15jmej9
1771	k15jmej8
1770	k15jmej7
1769	k15jmej6
1768	k15jmej5
1767	k15jmej4
1766	k15jmej3
1765	k15jmej2
1764	k15jmej1
1763	k15jmej0
1762	k15jmeix
1761	k15jmeiv
1760	k15jmeiu
1759	k15jmeit
1758	k15jmeis
1757	k15jmeir
1756	k15jmeiq
1755	k15jmeip
1754	k15jmeio
1753	k15jmein
1752	k15jmeim
1751	k15jmeil
1750	k15jmeik
1749	k15jmeij
1748	k15jmeii
1747	k15jmeig
1746	k15jmeie
1745	k15jmeid
1744	k15jmeic
1743	k15jmeib
1742	k15jmeia
1741	k15jmei9
1740	k15jmei8
1739	k15jmei7
1738	k15jmei6
1737	k15jmei5
1736	k15jmei4
1735	k15jmei3
1734	k15jmei2
1733	k15jmei1
1732	k15jmei0
1731	k15jmehy
1730	k15jmehx
1729	k15jmehw
1728	k15jmehv
1727	k15jmehu
1726	k15jmeht
1725	k15jmehs
1724	k15jmehr
1723	k15jmehq
1722	k15jmehp
1721	k15jmeho
1720	k15jmehn
1719	k15jmehm
1718	k15jmehl
1717	k15jmehk
1716	k15jmehj
1715	k15jmehh
1714	k15jmehg
1713	k15jmehe
1712	k15jmehd
1711	k15jmehc
1710	k15jmehb
1709	k15jmeha
1708	k15jmeh8
1707	k15jmeh7
1706	k15jmeh6
1705	k15jmeh5
1704	k15jmeh4
1703	k15jmeh3
1702	k15jmeh2
1701	k15jmeh1
1700	k15jmegy
1699	k15jmegx
1698	k15jmegw
1697	k15jmegv
1696	k15jmegu
1695	k15jmegt
1694	k15jmegs
1693	k15jmegr
1692	k15jmegq
1691	k15jmegp
1690	k15jmego
1689	k15jmegn
1688	k15jmegm
1687	k15jmegl
1686	k15jmegk
1685	k15jmegj
1684	k15jmegi
1683	k15jmegh
1682	k15jmegg
1681	k15jmegf
1680	k15jmege
1679	k15jmegc
1678	k15jmegb
1677	k15jmega
1676	k15jmeg9
1675	k15jmeg8
1674	k15jmeg7
1673	k15jmeg6
1672	k15jmeg5
1671	k15jmeg4
1670	k15jmeg3
1669	k15jmeg2
1668	k15jmeg1
1667	k15jmeg0
1666	k15jmefy
1665	k15jmefx
1664	k15jmefw
1663	k15jmefv
1662	k15jmefu
1661	k15jmeft
1660	k15jmefs
1659	k15jmefr
1658	k15jmefq
1657	k15jmefp
1656	k15jmefo
1655	k15jmefn
1654	k15jmefm
1653	k15jmefl
1652	k15jmefk
1651	k15jmefj
1650	k15jmefi
1649	k15jmefh
1648	k15jmefg
1647	k15jmeff
1646	k15jmefe
1645	k15jmefd
1644	k15jmefc
1643	k15jmefb
1642	k15jmef9
1641	k15jmef8
1640	k15jmef7
1639	k15jmef6
1638	k15jmef5
1637	k15jmef4
1636	k15jmef3
1635	k15jmef2
1634	k15jmef1
1633	k15jmef0
1632	k15jmeey
1631	k15jmeex
1630	k15jmeew
1629	k15jmeev
1628	k15jmeeu
1627	k15jmeet
1626	k15jmees
1625	k15jmeer
1624	k15jmeep
1623	k15jmeeo
1622	k15jmeen
1621	k15jmeem
1620	k15jmeel
1619	k15jmeek
1618	k15jmeej
1617	k15jmeeh
1616	k15jmeeg
1615	k15jmeef
1614	k15jmeee
1613	k15jmeed
1612	k15jmeeb
1611	k15jmeea
1610	k15jmee9
1609	k15jmee8
1608	k15jmee7
1607	k15jmee5
1606	k15jmee2
1605	k15jmee1
1604	k15jmee0
1603	k15jmedy
1602	k15jmedx
1601	k15jmedv
1600	k15jmedu
1599	k15jmedr
1598	k15jmedp
1597	k15jmedn
1596	k15jmedl
1595	k15jmedj
1594	k15jmedh
1593	k15jmedf
1592	k15jmedd
1591	k15jmedb
1590	k15jmed9
1589	k15jmed7
1588	k15jmed6
1587	k15jmed5
1586	k15jmed4
1585	k15jmed3
1584	k15jmed2
1583	k15jmed1
1582	k15jmed0
1581	k15jmecy
1580	k15jmecx
1579	k15jmecw
1578	k15jmecu
1577	k15jmect
1576	k15jmecs
1575	k15jmecr
1574	k15jmecq
1573	k15jmecp
1572	k15jmeco
1571	k15jmecn
1570	k15jmecm
1569	k15jmeck
1568	k15jmecj
1567	k15jmeci
1566	k15jmech
1565	k15jmecg
1564	k15jmecf
1563	k15jmece
1562	k15jmecd
1561	k15jmecb
1560	k15jmeca
1559	k15jmec9
1558	k15jmec8
1557	k15jmec7
1556	k15jmec6
1555	k15jmec5
1554	k15jmec4
1553	k15jmec3
1552	k15jmec2
1551	k15jmec1
1550	k15jmec0
1549	k15jmebx
1548	k15jmebw
1547	k15jmebu
1546	k15jmebt
1545	k15jmebs
1544	k15jmebr
1543	k15jmebq
1542	k15jmebo
1541	k15jmebk
1540	k15jmebi
1539	k15jmebf
1538	k15jmebd
1537	k15jmeba
1536	k15jmeb8
1535	k15jmeb6
1534	k15jmeb4
1533	k15jmeb3
1532	k15jmeb1
1531	k15jmeb0
1530	k15jmeax
1529	k15jmeav
1528	k15jmeau
1527	k15jmeat
1526	k15jmeas
1525	k15jmear
1524	k15jmeaq
1523	k15jmeap
1522	k15jmeao
1521	k15jmean
1520	k15jmeam
1519	k15jmeak
1518	k15jmeaj
1517	k15jmeai
1516	k15jmeah
1515	k15jmeag
1514	k15jmeaf
1513	k15jmeae
1512	k15jmead
1511	k15jmeac
1510	k15jmeab
1509	k15jmeaa
1508	k15jmea9
1507	k15jmea8
1506	k15jmea6
1505	k15jmea4
1504	k15jmea2
1503	k15jmea1
1502	k15jme9x
1501	k15jme9w
1500	k15jme9t
1499	k15jme9s
1498	k15jme9p
1497	k15jme9n
1496	k15jme9m
1495	k15jme9k
1494	k15jme9j
1493	k15jme9i
1492	k15jme9h
1491	k15jme9g
1490	k15jme9f
1489	k15jme9e
1488	k15jme9c
1487	k15jme9b
1486	k15jme9a
1485	k15jme99
1484	k15jme98
1483	k15jme97
1482	k15jme96
1481	k15jme95
1480	k15jme94
1479	k15jme93
1478	k15jme92
1477	k15jme91
1476	k15jme90
1475	k15jme8y
1474	k15jme8x
1473	k15jme8v
1472	k15jme8u
1471	k15jme8t
1470	k15jme8s
1469	k15jme8q
1468	k15jme8p
1467	k15jme8o
1466	k15jme8n
1465	k15jme8m
1464	k15jme8l
1463	k15jme8k
1462	k15jme8j
1461	k15jme8i
1460	k15jme8h
1459	k15jme8g
1458	k15jme8f
1457	k15jme8e
1456	k15jme8d
1455	k15jme8c
1454	k15jme8b
1453	k15jme88
1452	k15jme87
1451	k15jme86
1450	k15jme85
1449	k15jme84
1448	k15jme83
1447	k15jme82
1446	k15jme81
1445	k15jme7y
1444	k15jme7w
1443	k15jme7v
1442	k15jme7u
1441	k15jme7t
1440	k15jme7s
1439	k15jme7r
1438	k15jme7q
1437	k15jme7p
1436	k15jme7n
1435	k15jme7m
1434	k15jme7k
1433	k15jme7j
1432	k15jme7i
1431	k15jme7g
1430	k15jme7f
1429	k15jme7e
1428	k15jme7d
1427	k15jme7b
1426	k15jme7a
1425	k15jme79
1424	k15jme78
1423	k15jme77
1422	k15jme76
1421	k15jme75
1420	k15jme74
1419	k15jme72
1418	k15jme71
1417	k15jme70
1416	k15jme6y
1415	k15jme6x
1414	k15jme6w
1413	k15jme6v
1412	k15jme6u
1411	k15jme6t
1410	k15jme6s
1409	k15jme6q
1408	k15jme6o
1407	k15jme6m
1406	k15jme6k
1405	k15jme6i
1404	k15jme6g
1403	k15jme6e
1402	k15jme6c
1401	k15jme6a
1400	k15jme68
1399	k15jme67
1398	k15jme65
1397	k15jme64
1396	k15jme63
1395	k15jme62
1394	k15jme60
1393	k15jme5y
1392	k15jme5x
1391	k15jme5w
1390	k15jme5v
1389	k15jme5u
1388	k15jme5t
1387	k15jme5s
1386	k15jme5r
1385	k15jme5p
1384	k15jme5o
1383	k15jme5n
1382	k15jme5m
1381	k15jme5l
1380	k15jme5k
1379	k15jme5j
1378	k15jme5i
1377	k15jme5h
1376	k15jme5g
1375	k15jme5f
1374	k15jme5e
1373	k15jme5d
1372	k15jme5c
1371	k15jme5b
1370	k15jme5a
1369	k15jme59
1368	k15jme58
1367	k15jme57
1366	k15jme56
1365	k15jme55
1364	k15jme53
1363	k15jme52
1362	k15jme51
1361	k15jme50
1360	k15jme4y
1359	k15jme4x
1358	k15jme4w
1357	k15jme4u
1356	k15jme4s
1355	k15jme4q
1354	k15jme4o
1353	k15jme4m
1352	k15jme4j
1351	k15jme4h
1350	k15jme4e
1349	k15jme4b
1348	k15jme49
1347	k15jme47
1346	k15jme46
1345	k15jme45
1344	k15jme44
1343	k15jme43
1342	k15jme42
1341	k15jme41
1340	k15jme40
1339	k15jme3y
1338	k15jme3x
1337	k15jme3w
1336	k15jme3v
1335	k15jme3u
1334	k15jme3s
1333	k15jme3r
1332	k15jme3q
1331	k15jme3p
1330	k15jme3o
1329	k15jme3m
1328	k15jme3k
1327	k15jme3j
1326	k15jme3h
1325	k15jme3f
1324	k15jme3e
1323	k15jme3d
1322	k15jme3c
1321	k15jme3b
1320	k15jme3a
1319	k15jme38
1318	k15jme37
1317	k15jme36
1316	k15jme35
1315	k15jme34
1314	k15jme33
1313	k15jme32
1312	k15jme31
1311	k15jme30
1310	k15jme2y
1309	k15jme2w
1308	k15jme2v
1307	k15jme2u
1306	k15jme2t
1305	k15jme2s
1304	k15jme2r
1303	k15jme2p
1302	k15jme2o
1301	k15jme2n
1300	k15jme2m
1299	k15jme2l
1298	k15jme2k
1297	k15jme2j
1296	k15jme2i
1295	k15jme2h
1294	k15jme2g
1293	k15jme2f
1292	k15jme2e
1291	k15jme2d
1290	k15jme2c
1289	k15jme2b
1288	k15jme2a
1287	k15jme28
1286	k15jme27
1285	k15jme25
1284	k15jme24
1283	k15jme23
1282	k15jme22
1281	k15jme20
1280	k15jme1y
1279	k15jme1x
1278	k15jme1v
1277	k15jme1u
1276	k15jme1s
1275	k15jme1r
1274	k15jme1p
1273	k15jme1n
1272	k15jme1m
1271	k15jme1l
1270	k15jme1k
1269	k15jme1j
1268	k15jme1h
1267	k15jme1g
1266	k15jme1f
1265	k15jme1d
1264	k15jme1c
1263	k15jme1a
1262	k15jme19
1261	k15jme18
1260	k15jme17
1259	k15jme16
1258	k15jme14
1257	k15jme13
1256	k15jme12
1255	k15jme11
1254	k15jme10
1253	k15jme0y
1252	k15jme0x
1251	k15jme0w
1250	k15jme0v
1249	k15jme0u
1248	k15jme0t
1247	k15jme0s
1246	k15jme0r
1245	k15jme0p
1244	k15jme0o
1243	k15jme0n
1242	k15jme0m
1241	k15jme0l
1240	k15jme0k
1239	k15jme0i
1238	k15jme0h
1237	k15jme0g
1236	k15jme0f
1235	k15jme0e
1234	k15jme0d
1233	k15jme0c
1232	k15jme0b
1231	k15jme0a
1230	k15jme09
1229	k15jme08
1228	k15jme07
1227	k15jme06
1226	k15jme05
1225	k15jme03
1224	k15jme02
1223	k15jme01
1222	k15jme00
1221	k15jmdyy
1220	k15jmdyw
1219	k15jmdyv
1218	k15jmdyu
1217	k15jmdyt
1216	k15jmdys
1215	k15jmdyq
1214	k15jmdyp
1213	k15jmdyo
1212	k15jmdyn
1211	k15jmdym
1210	k15jmdyl
1209	k15jmdyk
1208	k15jmdyj
1207	k15jmdyh
1206	k15jmdyg
1205	k15jmdyf
1204	k15jmdye
1203	k15jmdyd
1202	k15jmdyc
1201	k15jmdya
1200	k15iai33
1199	k15iai32
1198	k15iai31
1197	k15iai30
1196	k15iai2y
1195	k15iai2x
1194	k15iai2v
1193	k15iai2u
1192	k15iai2t
1191	k15iai2s
1190	k15iai2r
1189	k15iai2q
1188	k15iai2p
1187	k15iai2o
1186	k15iai2n
1185	k15iai2m
1184	k15iai2l
1183	k15iai2k
1182	k15iai2j
1181	k15iai2i
1180	k15iai2h
1179	k15iai2g
1178	k15iai2f
1177	k15iai2d
1176	k15iai2b
1175	k15iai2a
1174	k15iai29
1173	k15iai28
1172	k15iai27
1171	k15iai26
1170	k15iai25
1169	k15iai24
1168	k15iai23
1167	k15iai22
1166	k15iai21
1165	k15iai20
1164	k15iai1y
1163	k15iai1x
1162	k15iai1w
1161	k15iai1u
1160	k15iai1t
1159	k15iai1s
1158	k15iai1r
1157	k15iai1q
1156	k15iai1p
1155	k15iai1o
1154	k15iai1n
1153	k15iai1m
1152	k15iai1l
1151	k15iai1k
1150	k15iai1j
1149	k15iai1i
1148	k15iai1h
1147	k15iai1e
1146	k15iai1d
1145	k15iai1c
1144	k15iai1b
1143	k15iai1a
1142	k15iai19
1141	k15iai18
1140	k15iai17
1139	k15iai16
1138	k15iai15
1137	k15iai14
1136	k15iai13
1135	k15iai12
1134	k15iai11
1133	k15iai10
1132	k15iai0y
1131	k15iai0x
1130	k15iai0w
1129	k15iai0v
1128	k15iai0t
1127	k15iai0s
1126	k15iai0q
1125	k15iai0p
1124	k15iai0n
1123	k15iai0m
1122	k15iai0l
1121	k15iai0k
1120	k15iai0j
1119	k15iai0i
1118	k15iai0h
1117	k15iai0g
1116	k15iai0f
1115	k15iai0e
1114	k15iai0d
1113	k15iai0c
1112	k15iai0b
1111	k15iai09
1110	k15iai07
1109	k15iai05
1108	k15iai03
1107	k15iai02
1106	k15iai01
1105	k15iai00
1104	k15iahyy
1103	k15iahyw
1102	k15iahyv
1101	k15iahyu
1100	k15iahyt
1099	k15iahys
1098	k15iahyr
1097	k15iahyq
1096	k15iahyp
1095	k15iahyo
1094	k15iahyn
1093	k15iahym
1092	k15iahyl
1091	k15iahyk
1090	k15iahyj
1089	k15iahyi
1088	k15iahyf
1087	k15iahye
1086	k15iahyd
1085	k15iahyb
1084	k15iahya
1083	k15iahy9
1082	k15iahy8
1081	k15iahy7
1080	k15iahy6
1079	k15iahy5
1078	k15iahy4
1077	k15iahy3
1076	k15iahy2
1075	k15iahxy
1074	k15iahxx
1073	k15iahxw
1072	k15iahxv
1071	k15iahxu
1070	k15iahxt
1069	k15iahxs
1068	k15iahxr
1067	k15iahxp
1066	k15iahxo
1065	k15iahxn
1064	k15iahxl
1063	k15iahxk
1062	k15iahxj
1061	k15iahxi
1060	k15iahxg
1059	k15iahxf
1058	k15iahxe
1057	k15iahxd
1056	k15iahxc
1055	k15iahxb
1054	k15iahx9
1053	k15iahx8
1052	k15iahx6
1051	k15iahx5
1050	k15iahx4
1049	k15iahx3
1048	k15iahx2
1047	k15iahx1
1046	k15iahx0
1045	k15iahwy
1044	k15iahww
1043	k15iahwv
1042	k15iahwu
1041	k15iahwt
1040	k15iahws
1039	k15iahwr
1038	k15iahwp
1037	k15iahwo
1036	k15iahwm
1035	k15iahwl
1034	k15iahwk
1033	k15iahwj
1032	k15iahwi
1031	k15iahwh
1030	k15iahwf
1029	k15iahwe
1028	k15iahwc
1027	k15iahwb
1026	k15iahwa
1025	k15iahw9
1024	k15iahw7
1023	k15iahw5
1022	k15iahw4
1021	k15iahw3
1020	k15iahw2
1019	k15iahw1
1018	k15iahw0
1017	k15iahvy
1016	k15iahvx
1015	k15iahvv
1014	k15iahvu
1013	k15iahvt
1012	k15iahvs
1011	k15iahvq
1010	k15iahvp
1009	k15iahvo
1008	k15iahvn
1007	k15iahvm
1006	k15iahvk
1005	k15iahvj
1004	k15iahvi
1003	k15iahvh
1002	k15iahvg
1001	k15iahvf
1000	k15iahve
999	k15iahvd
998	k15iahvc
997	k15iahvb
996	k15iahva
995	k15iahv8
994	k15iahv7
993	k15iahv5
992	k15iahv4
991	k15iahv3
990	k15iahv2
989	k15iahv1
988	k15iahv0
987	k15iahuy
986	k15iahux
985	k15iahuw
984	k15iahuu
983	k15iahut
982	k15iahur
981	k15iahup
980	k15iahuo
979	k15iahun
978	k15iahum
977	k15iahul
976	k15iahuk
975	k15iahuj
974	k15iahui
973	k15iahug
972	k15iahuf
971	k15iahue
970	k15iahud
969	k15iahuc
968	k15iahub
967	k15iahua
966	k15iahu8
965	k15iahu7
964	k15iahu6
963	k15iahu5
962	k15iahu4
961	k15iahu3
960	k15iahu2
959	k15iahu1
958	k15iahu0
957	k15iahty
956	k15iahtx
955	k15iahtw
954	k15iahtv
953	k15iahtu
952	k15iahts
951	k15iahtr
950	k15iahtq
949	k15iahtp
948	k15iahto
947	k15iahtn
946	k15iahtm
945	k15iahtl
944	k15iahtk
943	k15iahtj
942	k15iahti
941	k15iahth
940	k15iahtg
939	k15iahtf
938	k15iahte
937	k15iahtd
936	k15iahtc
935	k15iahta
934	k15iaht9
933	k15iaht8
932	k15iaht7
931	k15iaht5
930	k15iaht3
929	k15iaht2
928	k15iaht1
927	k15iaht0
926	k15iahsx
925	k15iahsw
924	k15iahsv
923	k15iahsu
922	k15iahst
921	k15iahss
920	k15iahsr
919	k15iahsq
918	k15iahsp
917	k15iahso
916	k15iahsm
915	k15iahsl
914	k15iahsk
913	k15iahsj
912	k15iahsg
911	k15iahsf
910	k15iahse
909	k15iahsd
908	k15iahsc
907	k15iahsb
906	k15iahsa
905	k15iahs9
904	k15iahs8
903	k15iahs7
902	k15iahs6
901	k15iahs5
900	k15iahs4
899	k15iahs3
898	k15iahs1
897	k15iahs0
896	k15iahry
895	k15iahrx
894	k15iahrv
893	k15iahru
892	k15iahrt
891	k15iahrs
890	k15iahrr
889	k15iahrq
888	k15iahrp
887	k15iahrn
886	k15iahrm
885	k15iahrl
884	k15iahri
883	k15iahrh
882	k15iahrg
881	k15iahrf
880	k15iahrd
879	k15iahrb
878	k15iahra
877	k15iahr9
876	k15iahr8
875	k15iahr7
874	k15iahr6
873	k15iahr4
872	k15iahr3
871	k15iahr2
870	k15iahr1
869	k15iahr0
868	k15iahqy
867	k15iahqx
866	k15iahqw
865	k15iahqv
864	k15iahqt
863	k15iahqs
862	k15iahqr
861	k15iahqq
860	k15iahqp
859	k15iahqo
858	k15iahqn
857	k15iahql
856	k15iahqk
855	k15iahqj
854	k15iahqi
853	k15iahqh
852	k15iahqg
851	k15iahqf
850	k15iahqe
849	k15iahqd
848	k15iahqc
847	k15iahqb
846	k15iahqa
845	k15iahq8
844	k15iahq7
843	k15iahq6
842	k15iahq5
841	k15iahq4
840	k15iahq3
839	k15iahq1
838	k15iahpy
837	k15iahpx
836	k15iahpv
835	k15iahpu
834	k15iahpt
833	k15iahps
832	k15iahpr
831	k15iahpq
830	k15iahpp
829	k15iahpo
828	k15iahpn
827	k15iahpm
826	k15iahpl
825	k15iahpk
824	k15iahpj
823	k15iahpi
822	k15iahph
821	k15iahpf
820	k15iahpe
819	k15iahpd
818	k15iahpc
817	k15iahpb
816	k15iahpa
815	k15iahp8
814	k15iahp7
813	k15iahp6
812	k15iahp5
811	k15iahp4
810	k15iahp3
809	k15iahp2
808	k15iahp1
807	k15iahoy
806	k15iahox
805	k15iahow
804	k15iahov
803	k15iahou
802	k15iahot
801	k15iahor
800	k15iahoq
799	k15iahop
798	k15iahoo
797	k15iahon
796	k15iahom
795	k15iahol
794	k15iahok
793	k15iahoj
792	k15iahoi
791	k15iahoh
790	k15iahog
789	k15iahof
788	k15iahoe
787	k15iahoc
786	k15iahob
785	k15iahoa
784	k15iaho9
783	k15iaho7
782	k15iaho6
781	k15iaho5
780	k15iaho4
779	k15iaho3
778	k15iaho2
777	k15iaho1
776	k15iahny
775	k15iahnx
774	k15iahnw
773	k15iahnv
772	k15iahns
771	k15iahnr
770	k15iahnq
769	k15iahnp
768	k15iahno
767	k15iahnn
766	k15iahnm
765	k15iahnl
764	k15iahnk
763	k15iahnj
762	k15iahni
761	k15iahnh
760	k15iahng
759	k15iahne
758	k15iahnd
757	k15iahnc
756	k15iahnb
755	k15iahn9
754	k15iahn8
753	k15iahn7
752	k15iahn6
751	k15iahn5
750	k15iahn3
749	k15iahn1
748	k15iahn0
747	k15iahmy
746	k15iahmx
745	k15iahmw
744	k15iahmv
743	k15iahmt
742	k15iahms
741	k15iahmr
740	k15iahmq
739	k15iahmp
738	k15iahmo
737	k15iahmn
736	k15iahmll
735	k15iahmj
734	k15iahmg
733	k15iahme
732	k15iahmc
731	k15iahma
730	k15iahm8
729	k15iahm6
728	k15iahm4
727	k15iahm3
726	k15iahm1
725	k15iahly
724	k15iahlx
723	k15iahlw
722	k15iahlv
721	k15iahlu
720	k15iahlt
719	k15iahls
718	k15iahlr
717	k15iahlp
716	k15iahlo
715	k15iahln
714	k15iahlm
713	k15iahll
712	k15iahlk
711	k15iahlj
710	k15iahlh
709	k15iahlg
708	k15iahlf
707	k15iahle
706	k15iahld
705	k15iahlc
704	k15iahla
703	k15iahl9
702	k15iahl8
701	k15iahl7
700	k15iahl6
699	k15iahl4
698	k15iahl3
697	k15iahl2
696	k15iahl0
695	k15iahky
694	k15iahkx
693	k15iahkw
692	k15iahkv
691	k15iahku
690	k15iahkt
689	k15iahks
688	k15iahkr
687	k15iahkq
686	k15iahko
685	k15iahkn
684	k15iahkm
683	k15iahkk
682	k15iahki
681	k15iahkf
680	k15iahke
679	k15iahkd
678	k15iahkc
677	k15iahkb
676	k15iahka
675	k15iahk9
674	k15iahk8
673	k15iahk7
672	k15iahk6
671	k15iahk5
670	k15iahk4
669	k15iahk3
668	k15iahk1
667	k15iahk0
666	k15iahjy
665	k15iahjx
664	k15iahjw
663	k15iahjv
662	k15iahju
661	k15iahjt
660	k15iahjs
659	k15iahjq
658	k15iahjo
657	k15iahjn
656	k15iahjm
655	k15iahjl
654	k15iahjk
653	k15iahjj
652	k15iahji
651	k15iahjh
650	k15iahje
649	k15iahjc
648	k15iahjb
647	k15iahj9
646	k15iahj8
645	k15iahj7
644	k15iahj6
643	k15iahj5
642	k15iahj4
641	k15iahj3
640	k15iahj1
639	k15iahj0
638	k15iahiy
637	k15iahix
636	k15iahiw
635	k15iahiv
634	k15iahiu
633	k15iahit
632	k15iahis
631	k15iahiq
630	k15iahio
629	k15iahin
628	k15iahim
627	k15iahil
626	k15iahik
625	k15iahij
624	k15iahii
623	k15iahih
622	k15iahif
621	k15iahie
620	k15iahid
619	k15iahic
618	k15iahib
617	k15iahia
616	k15iahi9
615	k15iahi8
614	k15iahi7
613	k15iahi6
612	k15iahi4
611	k15iahi3
610	k15iahi2
609	k15iahi1
608	k15iahi0
607	k15iahhy
606	k15iahhx
605	k15iahhv
604	k15iahht
603	k15iahhs
602	k15iahhr
601	k15iahhq
600	k15i41cm
599	k15i3x2w
598	k15i3x2v
597	k15i3x2u
596	k15i3x2t
595	k15i3x2s
594	k15i3x2q
593	k15i3x2p
592	k15i3x2o
591	k15i3x2n
590	k15i3x2m
589	k15i3x2l
588	k15i3x2k
587	k15i3x2j
586	k15i3x2i
585	k15i3x2h
584	k15i3x2g
583	k15i3x2f
582	k15i3x2e
581	k15i3x2d
580	k15i3x2c
579	k15i3x2b
578	k15i3x2a
577	k15i3x29
576	k15i3x28
575	k15i3x27
574	k15i3x25
573	k15i3x24
572	k15i3x23
571	k15i3x22
570	k15i3x20
569	k15i3x1y
568	k15i3x1x
567	k15i3x1w
566	k15i3x1v
565	k15i3x1u
564	k15i3x1s
563	k15i3x1r
562	k15i3x1q
561	k15i3x1o
560	k15i3x1m
559	k15i3x1l
558	k15i3x1k
557	k15i3x1i
556	k15i3x1h
555	k15i3x1g
554	k15i3x1f
553	k15i3x1e
552	k15i3x1d
551	k15i3x1c
550	k15i3x1b
549	k15i3x1a
548	k15i3x19
547	k15i3x18
546	k15i3x16
545	k15i3x15
544	k15i3x14
543	k15i3x13
542	k15i3x12
541	k15i3x11
540	k15i3x10
539	k15i3x0y
538	k15i3x0x
537	k15i3x0w
536	k15i3x0v
535	k15i3x0u
534	k15i3x0t
533	k15i3x0s
532	k15i3x0r
531	k15i3x0p
530	k15i3x0o
529	k15i3x0m
528	k15i3x0k
527	k15i3x0j
526	k15i3x0i
525	k15i3x0h
524	k15i3x0g
523	k15i3x0f
522	k15i3x0e
521	k15i3x0b
520	k15i3x0a
519	k15i3x09
518	k15i3x08
517	k15i3x07
516	k15i3x06
515	k15i3x05
514	k15i3x04
513	k15i3x03
512	k15i3x02
511	k15i3x01
510	k15i3x00
509	k15i3wyy
508	k15i3wyx
507	k15i3wyw
506	k15i3wyv
505	k15i3wyu
504	k15i3wys
503	k15i3wyr
502	k15i3wyq
501	k15i3wyp
500	k15i3wyo
499	k15i3wyn
498	k15i3wym
497	k15i3wyl
496	k15i3wyk
495	k15i3wyj
494	k15i3wyi
493	k15i3wyh
492	k15i3wyg
491	k15i3wyf
490	k15i3wye
489	k15i3wyd
488	k15i3wyc
487	k15i3wyb
486	k15i3wya
485	k15i3wy8
484	k15i3wy7
483	k15i3wy6
482	k15i3wy4
481	k15i3wy3
480	k15i3wy2
479	k15i3wy1
478	k15i3wy0
477	k15i3wxy
476	k15i3wxx
475	k15i3wxw
474	k15i3wxu
473	k15i3wxt
472	k15i3wxr
471	k15i3wxq
470	k15i3wxp
469	k15i3wxo
468	k15i3wxn
467	k15i3wxm
466	k15i3wxl
465	k15i3wxk
464	k15i3wxj
463	k15i3wxi
462	k15i3wxg
461	k15i3wxf
460	k15i3wxe
459	k15i3wxd
458	k15i3wxc
457	k15i3wxb
456	k15i3wxa
455	k15i3wx9
454	k15i3wx8
453	k15i3wx7
452	k15i3wx6
451	k15i3wx5
450	k15i3wx4
449	k15i3wx2
448	k15i3wx1
447	k15i3wx0
446	k15i3wwy
445	k15i3wwx
444	k15i3www
443	k15i3wwv
442	k15i3wwu
441	k15i3wwt
440	k15i3wws
439	k15i3wwq
438	k15i3wwp
437	k15i3wwo
436	k15i3wwn
435	k15i3wwm
434	k15i3wwl
433	k15i3wwk
432	k15i3wwj
431	k15i3wwi
430	k15i3wwh
429	k15i3wwg
428	k15i3wwe
427	k15i3wwc
426	k15i3wwb
425	k15i3wwa
424	k15i3ww8
423	k15i3ww7
422	k15i3ww6
421	k15i3ww5
420	k15i3ww4
419	k15i3ww3
418	k15i3ww2
417	k15i3ww1
416	k15i3ww0
415	k15i3wvy
414	k15i3wvx
413	k15i3wvw
412	k15i3wvv
411	k15i3wvu
410	k15i3wvt
409	k15i3wvs
408	k15i3wvr
407	k15i3wvq
406	k15i3wvp
405	k15i3wvo
404	k15i3wvn
403	k15i3wvm
402	k15i3wvl
401	k15i3wvk
400	k15i3wvj
399	k15harx4
398	k15harx3
397	k15harx2
396	k15harx1
395	k15harx0
394	k15harwy
393	k15harwx
392	k15harww
391	k15harwv
390	k15harwu
389	k15harws
388	k15harwr
387	k15harwq
386	k15harwo
385	k15harwn
384	k15harwl
383	k15harwk
382	k15harwi
381	k15harwh
380	k15harwg
379	k15harwf
378	k15harwe
377	k15harwd
376	k15harwc
375	k15harwb
374	k15harwa
373	k15harw8
372	k15harw6
371	k15harw5
370	k15harw3
369	k15harw2
368	k15harw1
367	k15harw0
366	k15harvy
365	k15harvx
364	k15harvw
363	k15harvv
362	k15harvu
361	k15harvt
360	k15harvr
359	k15harvq
358	k15harvp
357	k15harvo
356	k15harvn
355	k15harvm
354	k15harvj
353	k15harvi
352	k15harvf
351	k15harve
350	k15harvc
349	k15harvb
348	k15harva
347	k15harv9
346	k15harv7
345	k15harv6
344	k15harv5
343	k15harv4
342	k15harv3
341	k15harv2
340	k15harv0
339	k15haruy
338	k15harux
337	k15haruw
336	k15haruv
335	k15haruu
334	k15harus
333	k15harur
332	k15haruq
331	k15harup
330	k15haruo
329	k15harun
328	k15harul
327	k15haruk
326	k15haruj
325	k15haruh
324	k15harug
323	k15haruf
322	k15harue
321	k15harud
320	k15harub
319	k15harua
318	k15haru9
317	k15haru8
316	k15haru6
315	k15haru5
314	k15haru4
313	k15haru3
312	k15haru2
311	k15haru1
310	k15haru0
309	k15harty
308	k15hartx
307	k15hartv
306	k15hartt
305	k15hartr
304	k15hartp
303	k15hartn
302	k15hartl
301	k15hartj
300	k15hartg
299	k15hartf
298	k15hartd
297	k15hartb
296	k15harta
295	k15hart8
294	k15hart5
293	k15hart4
292	k15hart3
291	k15hart2
290	k15dua2i
289	k15dua2g
288	k15dua2e
287	k15dua2b
286	k15dua28
285	k15dua26
284	k15dua24
283	k15dua23
282	k15dua22
281	k15dua21
280	k15dua20
279	k15dua1x
278	k15dua1w
277	k15dua1v
276	k15dua1u
275	k15dua1t
274	k15dua1s
273	k15dua1r
272	k15dua1q
271	k15dua1p
270	k15dua1o
269	k15dua1m
268	k15dua1l
267	k15dua1k
266	k15dua1j
265	k15dua1i
264	k15dua1h
263	k15dua1g
262	k15dua1f
261	k15dua1e
260	k15dua1d
259	k15dua1c
258	k15dua1b
257	k15dua1a
256	k15dua19
255	k15dua18
254	k15dua17
253	k15dua16
252	k15dua14
251	k15dua13
250	k15dua12
249	k15dua11
248	k15dua10
247	k15dua0y
246	k15dua0x
245	k15dua0w
244	k15dua0v
243	k15dua0u
242	k15dua0s
241	k15dua0r
240	k15dua0o
239	k15dua0n
238	k15dua0m
237	k15dua0l
236	k15dua0k
235	k15dua0j
234	k15dua0i
233	k15dua0h
232	k15dua0g
231	k15dua0f
230	k15dua0e
229	k15dua0d
228	k15dua0c
227	k15dua0b
226	k15dua0a
225	k15dua08
224	k15dua07
223	k15dua06
222	k15dua05
221	k15dua02
220	k15dua00
219	k15du9yx
218	k15du9yv
217	k15du9ys
216	k15du9yp
215	k15du9yn
214	k15du9yl
213	k15du9yj
212	k15du9yg
211	k15du9ye
210	k15du9yc
209	k15du9yb
208	k15du9y9
207	k15du9y8
206	k15du9y7
205	k15du9y5
204	k15du9y3
203	k15du9y2
202	k15du9y0
201	k15du9xy
200	k15du9xx
199	k15du9xw
198	k15du9xv
197	k15du9xu
196	k15du9xt
195	k15du9xs
194	k15du9xr
193	k15du9xq
192	k15du9xp
191	k15du9xo
190	k15du9xn
189	k15du9xk
188	k15du9xj
187	k15du9xi
186	k15du9xh
185	k15du9xf
184	k15du9xe
183	k15du9xd
182	k15du9xc
181	k15du9xb
180	k15du9xa
179	k15du9x9
178	k15du9x8
177	k15du9x7
176	k15du9x6
175	k15du9x4
174	k15du9x3
173	k15du9x1
172	k15du9x0
171	k15du9wy
170	k15du9wx
169	k15du9wv
168	k15du9wt
167	k15du9ws
166	k15du9wr
165	k15du9wp
164	k15du9wn
163	k15du9wm
162	k15du9wl
161	k15du9wk
160	k15du9wj
159	k15du9wi
158	k15du9wh
157	k15du9wg
156	k15du9wf
155	k15du9we
154	k15du9wd
153	k15du9wc
152	k15du9wa
151	k15du9w9
150	k15du9w7
149	k15du9w4
148	k15du9w3
147	k15du9w2
146	k15du9w0
145	k15du9vy
144	k15du9vx
143	k15du9vv
142	k15du9vt
141	k15du9vs
140	k15du9vq
139	k15du9vp
138	k15du9vn
137	k15du9vm
136	k15du9vl
135	k15du9vk
134	k15du9vi
133	k15du9vh
132	k15du9vg
131	k15du9vf
130	k15du9ve
129	k15du9vd
128	k15du9vc
127	k15du9vb
126	k15du9va
125	k15du9v9
124	k15du9v8
123	k15du9v7
122	k15du9v6
121	k15du9v5
120	k15du9v3
119	k15du9v2
118	k15du9uy
117	k15du9ux
116	k15du9uv
115	k15du9uu
114	k15du9ut
113	k15du9us
112	k15du9ur
111	k15du9uq
110	k15du9up
109	k15du9uo
108	k15du9un
107	k15du9ul
106	k15du9uj
105	k15du9ui
104	k15du9uh
103	k15du9uf
102	k15du9ue
101	k15du9ud
100	k15du9uc
99	k15du9ub
98	k15du9ua
97	k15du9u9
96	k15du9u8
95	k15du9u7
94	k15du9u6
93	k15du9u5
92	k15du9u4
91	k15du9u3
90	k15du9u2
89	k15du9u1
88	k15du9u0
87	k15du9ty
86	k15du9tx
85	k15du9tv
84	k15du9tu
83	k15du9tt
82	k15du9ts
81	k15du9tr
80	k15du9tq
79	k15du9to
78	k15du9tn
77	k15du9tm
76	k15du9tl
75	k15du9tk
74	k15du9tj
73	k15du9ti
72	k15du9tg
71	k15du9tf
70	k15du9te
69	k15du9tc
68	k15du9tb
67	k15du9ta
66	k15du9t9
65	k15du9t8
64	k15du9t6
63	k15du9t5
62	k15du9t4
61	k15du9t3
60	k15du9t2
59	k15du9t1
58	k15du9t0
57	k15du9sy
56	k15du9sx
55	k15du9sw
54	k15du9sv
53	k15du9su
52	k15du9st
51	k15du9ss
50	k15du9sr
49	k15du9sq
48	k15du9sp
47	k15du9so
46	k15du9sn
45	k15du9sm
44	k15du9sl
43	k15du9sk
42	k15du9sj
41	k15du9si
40	k15du9sh
39	k15du9sg
38	k15du9sf
37	k15du9se
36	k15du9sd
35	k15du9sc
34	k15du9sb
33	k15du9s9
32	k15du9s8
31	k15du9s7
30	k15du9s6
29	k15du9s5
28	k15du9s4
27	k15du9s3
26	k15du9s2
25	k15du9s1
24	k15du9s0
23	k15du9ry
22	k15du9rx
21	k15du9rv
20	k15du9ru
19	k15du9rs
18	k15du9rr
17	k15du9rq
16	k15du9rp
15	k15du9ro
14	k15du9rn
13	k15du9rm
12	k15du9rl
11	k15du9rk
10	k15du9rj
9	k15du9ri
8	k15du9rf
7	k15du9re
6	k15du9rd
5	k15du9rc
4	k15du9rb
3	k15du9ra
2	k15du9r9
1	k15du9r7"""
    
    # 解析映射数据
    lines = mapping_data.strip().split('\n')
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 2:
            browser_num = parts[0].strip()
            user_id = parts[1].strip()
            FINGERPRINT_TO_USERID[browser_num] = user_id
    
    # 添加测试浏览器映射（4001用于测试）
    FINGERPRINT_TO_USERID["4001"] = "k17cah7w"
    
    log_print(f"[系统] ✓ 已加载 {len(FINGERPRINT_TO_USERID)} 个浏览器映射")


if __name__ == "__main__":
    # 初始化并启动主循环
    initialize_fingerprint_mapping()
    main()

