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
COMPUTER_GROUP = "0"

# 密码配置
PASSWORD_MAP = {
    # 示例配置
    # "your_password": "1,2,3,4,5",
    # "another_password": "else",
}

# 默认密码
PWD = "Ok123456"

# 服务器API配置
SERVER_BASE_URL = "https://sg.bicoin.com.cn/99l"

# 全局线程池配置
MAX_WORKERS = 6
global_thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks_lock = threading.Lock()
active_tasks = {}  # {mission_id: {'futures': [], 'results': {}, 'total': 0, 'completed': 0}}

# 正在执行 type=3 任务的浏览器ID集合
active_type3_browsers = set()
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
    等待 Opinion Trade 页面加载完成
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
        
    Returns:
        WebElement: trade-box元素，失败返回None
    """
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] [OP] 等待页面加载完成... (尝试 {attempt + 1}/{max_retries})")
            
            time.sleep(2)
            
            # 查找 trade-box
            trade_box = driver.find_element(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
            
            if trade_box:
                log_print(f"[{serial_number}] [OP] ✓ 页面加载成功，找到 trade-box")
                return trade_box
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 未找到 trade-box: {str(e)}")
            
            if attempt < max_retries - 1:
                log_print(f"[{serial_number}] [OP] 刷新页面并重试...")
                driver.refresh()
            else:
                log_print(f"[{serial_number}] [OP] ✗ 页面加载失败，已达到最大重试次数")
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


def submit_opinion_order(driver, trade_box, trade_type, option_type, serial_number, browser_id):
    """
    提交 Opinion Trade 订单
    
    Args:
        driver: Selenium WebDriver对象
        trade_box: trade-box元素
        trade_type: 买卖类型
        option_type: 种类
        serial_number: 浏览器序列号
        browser_id: 浏览器ID
        
    Returns:
        bool: 成功返回True
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
                            buttons[1].click()
                            log_print(f"[{serial_number}] [OP] ✓ 已点击 OKX 确认按钮")
                            return True
                        else:
                            log_print(f"[{serial_number}] [OP] ⚠ OKX 按钮数量不足: {len(buttons)}")
                            return False
                
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 OKX 页面")
                return False
        
        log_print(f"[{serial_number}] [OP] ✗ 未找到提交订单按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 提交订单失败: {str(e)}")
        return False


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

def process_trading_mission(task_data, keep_browser_open=False):
    """
    处理交易任务（支持 Opinion Trade 和 Polymarket）
    
    Args:
        task_data: 任务数据，包含 mission 和 exchangeConfig
        keep_browser_open: 是否保持浏览器打开（用于后续数据收集）
        
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
            success, failure_reason = process_opinion_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, trending_part1)
        else:
            success, failure_reason = process_polymarket_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser)
        
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


def process_opinion_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, trending_part1=''):
    """
    处理 Opinion Trade 交易流程
    
    Args:
        is_new_browser: 是否是新启动的浏览器
        trending_part1: 子主题名称（如果有）
    
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
        
        # 检查 Open Orders 数量
        log_print(f"[{browser_id}] 步骤6.3: 检查 Open Orders...")
        initial_open_orders_count = get_opinion_table_row_count(driver, browser_id, need_click_open_orders=True, trending_part1=trending_part1)
        
        if initial_open_orders_count < 0:
            log_print(f"[{browser_id}] ⚠ 无法获取 Open Orders 数量，设为 0")
            initial_open_orders_count = 0
        
        log_print(f"[{browser_id}] 初始 Open Orders 数量: {initial_open_orders_count}")
        
        # Buy 类型：如果已有挂单则不能下单
        if trade_type == "Buy" and initial_open_orders_count > 0:
            return False, f"{browser_id}已有挂单"
        
        if trade_type == "Buy":
            log_print(f"[{browser_id}] ✓ Buy 类型检查通过：无仓位，无挂单")
        else:
            log_print(f"[{browser_id}] ✓ Sell 类型：已记录初始数量")
        
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
                if not submit_opinion_order(driver, trade_box, trade_type, option_type, browser_id, browser_id):
                    log_print(f"[{browser_id}] ✗ 提交订单失败")
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
        
        # 13. 等待订单成功（交替检查 Open Orders 和 Position）
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
    获取 Opinion Trade Portfolio 的值
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: Portfolio的值，失败返回None
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找 Portfolio 值...")
        
        p_tags = driver.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            if p.text.strip() == "Portfolio":
                log_print(f"[{serial_number}] [OP] ✓ 找到 Portfolio 标签")
                
                parent = p.find_element(By.XPATH, "..")
                child_p_tags = parent.find_elements(By.TAG_NAME, "p")
                
                if len(child_p_tags) >= 2:
                    portfolio_value = child_p_tags[1].text.strip()
                    log_print(f"[{serial_number}] [OP] ✓ Portfolio 值: {portfolio_value}")
                    return portfolio_value
                else:
                    log_print(f"[{serial_number}] [OP] ⚠ Portfolio 父节点的子节点数量不足")
                    return None
        
        log_print(f"[{serial_number}] [OP] ✗ 未找到 Portfolio 标签")
        return None
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 获取 Portfolio 值失败: {str(e)}")
        return None


def get_opinion_balance_value(driver, serial_number):
    """
    获取 Opinion Trade Balance 的值
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: Balance的值，失败返回None
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找 Balance 值...")
        
        p_tags = driver.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            if p.text.strip() == "Balance":
                log_print(f"[{serial_number}] [OP] ✓ 找到 Balance 标签")
                
                parent = p.find_element(By.XPATH, "..")
                children = parent.find_elements(By.XPATH, "./*")
                
                if len(children) >= 2:
                    second_child = children[1]
                    p_in_second_child = second_child.find_elements(By.TAG_NAME, "p")
                    
                    if p_in_second_child:
                        balance_value = p_in_second_child[0].text.strip()
                        log_print(f"[{serial_number}] [OP] ✓ Balance 值: {balance_value}")
                        return balance_value
                    else:
                        log_print(f"[{serial_number}] [OP] ⚠ 第二个子节点中没有找到 p 标签")
                        return None
                else:
                    log_print(f"[{serial_number}] [OP] ⚠ Balance 父节点的子节点数量不足")
                    return None
        
        log_print(f"[{serial_number}] [OP] ✗ 未找到 Balance 标签")
        return None
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 获取 Balance 值失败: {str(e)}")
        return None


def click_opinion_position_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Position 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        list: p标签内容列表
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
            return []
        
        time.sleep(3)
        
        try:
            # 先找到 ID 以 content-position 结尾的 div
            log_print(f"[{serial_number}] [OP] 查找 Position 内容区域...")
            position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
            log_print(f"[{serial_number}] [OP] ✓ 找到 Position 内容区域 (ID: {position_div.get_attribute('id')})")
            
            # 再找这个 div 下的 tbody
            tbody = position_div.find_element(By.TAG_NAME, "tbody")
            p_tags = tbody.find_elements(By.TAG_NAME, "p")
            p_contents = [p.text.strip() for p in p_tags if p.text.strip()]
            
            log_print(f"[{serial_number}] [OP] ✓ Position tbody 中找到 {len(p_contents)} 个 p 标签")
            return p_contents
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Position tbody 失败: {str(e)}")
            return []
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Position 按钮失败: {str(e)}")
        return []


def click_opinion_open_orders_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Open Orders 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        list: p标签内容列表
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
            return []
        
        time.sleep(5)
        
        try:
            # 先找到 ID 以 content-open-orders 结尾的 div
            log_print(f"[{serial_number}] [OP] 查找 Open Orders 内容区域...")
            open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
            log_print(f"[{serial_number}] [OP] ✓ 找到 Open Orders 内容区域 (ID: {open_orders_div.get_attribute('id')})")
            
            # 再找这个 div 下的 tbody
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            p_tags = tbody.find_elements(By.TAG_NAME, "p")
            p_contents = [p.text.strip() for p in p_tags if p.text.strip()]
            
            log_print(f"[{serial_number}] [OP] ✓ Open Orders tbody 中找到 {len(p_contents)} 个 p 标签")
            return p_contents
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Open Orders tbody 失败: {str(e)}")
            return []
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Open Orders 按钮失败: {str(e)}")
        return []


def click_opinion_transactions_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Transactions 按钮并获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        list: 交易记录列表，每条记录为字典 {"title": 主题, "direction": 买卖方向, "option": 选项, "amount": 数量, "value": 金额, "price": 价格, "time": 时间}
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
            return []
        
        time.sleep(3)
        
        try:
            # 先找到 ID 以 content-transactions 结尾的 div
            log_print(f"[{serial_number}] [OP] 查找 Transactions 内容区域...")
            transactions_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-transactions']")
            log_print(f"[{serial_number}] [OP] ✓ 找到 Transactions 内容区域 (ID: {transactions_div.get_attribute('id')})")
            
            # 再找这个 div 下的 tbody
            tbody = transactions_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            
            log_print(f"[{serial_number}] [OP] ✓ Transactions tbody 中找到 {len(tr_list)} 个 tr 标签")
            
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
            return transactions
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Transactions tbody 失败: {str(e)}")
            return []
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Transactions 按钮失败: {str(e)}")
        return []


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
        # 判断当前项是否是 YES/NO
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
                        # YES为正数，NO为负数
                        if option == "NO":
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
        else:
            # 这是新的标题
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
                        # YES为正数，NO为负数
                        if final_option == "NO":
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


def execute_type3_data_collection(driver, browser_id, target_url, trending_part1):
    """
    执行Type 3数据收集流程（从步骤5开始，可重试）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        target_url: 目标URL
        trending_part1: 子主题（如果有）
        
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
            time.sleep(2)
        
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
    
    log_print(f"\n[{browser_id}] ========== 开始处理 Type 3 任务 ==========")
    log_print(f"[{browser_id}] 任务ID: {mission_id}")
    log_print(f"[{browser_id}] 交易所: {exchange_name}")
    
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
        log_print(f"[{browser_id}] 步骤1: 检查IP并更新代理...")
        try_update_ip_before_start(browser_id)
        
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
                driver, browser_id, target_url, trending_part1
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
            
            # 获取数据
            log_print(f"[{browser_id}] 获取 Portfolio 值...")
            portfolio_value = get_opinion_portfolio_value(driver, browser_id)
            collected_data['portfolio'] = portfolio_value
            
            log_print(f"[{browser_id}] 获取 Balance 值...")
            balance_value = get_opinion_balance_value(driver, browser_id)
            collected_data['balance'] = balance_value
            
            log_print(f"[{browser_id}] 点击 Position 并获取数据...")
            position_data = click_opinion_position_and_get_data(driver, browser_id)
            collected_data['position'] = position_data
            
            log_print(f"[{browser_id}] 点击 Open Orders 并获取数据...")
            open_orders_data = click_opinion_open_orders_and_get_data(driver, browser_id)
            
            log_print(f"[{browser_id}] 点击 Transactions 并获取数据...")
            transactions_data = click_opinion_transactions_and_get_data(driver, browser_id)
            
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


def process_type2_mission(task_data):
    """
    处理 Type 2 任务 - 获取交易所数据
    
    Args:
        task_data: 任务数据，包含 mission 和 exchangeConfig
        
    Returns:
        tuple: (success, failure_reason, collected_data)
    """
    mission = task_data.get("mission", {})
    
    browser_id = mission.get("numberList", "")
    mission_id = mission.get("id", "")
    exchange_name = mission.get("exchangeName", "")
    
    log_print(f"\n[{browser_id}] ========== 开始处理 Type 2 任务 ==========")
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
            
            # 获取数据
            log_print(f"[{browser_id}] 步骤5: 获取 Portfolio 值...")
            portfolio_value = get_opinion_portfolio_value(driver, browser_id)
            collected_data['portfolio'] = portfolio_value
            
            log_print(f"[{browser_id}] 步骤6: 获取 Balance 值...")
            balance_value = get_opinion_balance_value(driver, browser_id)
            collected_data['balance'] = balance_value
            
            log_print(f"[{browser_id}] 步骤7: 点击 Position 并获取数据...")
            position_data = click_opinion_position_and_get_data(driver, browser_id)
            collected_data['position'] = position_data
            
            log_print(f"[{browser_id}] 步骤8: 点击 Open Orders 并获取数据...")
            open_orders_data = click_opinion_open_orders_and_get_data(driver, browser_id)
            
            log_print(f"[{browser_id}] 步骤9: 点击 Transactions 并获取数据...")
            transactions_data = click_opinion_transactions_and_get_data(driver, browser_id)
            
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
            else:
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
        if mission_type == 1:
            # Type 1: 交易任务
            result = process_trading_mission(task_data, keep_browser_open=True)
            
            if len(result) == 5:
                success, failure_reason, driver, task_browser_id, task_exchange_name = result
            else:
                success, failure_reason = result
                driver = None
                task_browser_id = None
                task_exchange_name = None
            
            # 立即记录任务结果（不等待数据收集）
            log_print(f"[{browser_id}] Type 1 任务{'成功' if success else '失败'}，立即记录结果...")
            with active_tasks_lock:
                if mission_id in active_tasks:
                    active_tasks[mission_id]['results'][browser_id] = {
                        'success': success,
                        'reason': failure_reason if not success else ''
                    }
                    active_tasks[mission_id]['completed'] += 1
            log_print(f"[{browser_id}] ✓ Type 1 任务结果已记录")
            
            # Type 1任务完成后收集持仓数据（不影响任务结果）
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
            
            # Type 1 任务结果已经在上面记录了，跳过后面的统一记录
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
                # 将浏览器ID加入正在执行的集合
                with active_type3_browsers_lock:
                    active_type3_browsers.add(browser_id)
                    log_print(f"[{browser_id}] Type 3 任务开始，浏览器已标记为繁忙")
                
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
                    # 无论成功还是失败，都从集合中移除浏览器ID
                    with active_type3_browsers_lock:
                        active_type3_browsers.discard(browser_id)
                        log_print(f"[{browser_id}] Type 3 任务完成，浏览器标记已清除")
                    
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
                    active_type3_browsers.discard(browser_id)
                    log_print(f"[{browser_id}] Type 3 任务异常，清除浏览器标记")
        
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
            
            # 3. 尝试获取新任务
            log_print(f"[系统] 线程池状态: 活跃任务 {active_count} 个, 待处理 {pending_count}/{MAX_WORKERS}")
            
            # 线程池是否已满
            pool_is_full = pending_count >= MAX_WORKERS
            
            if pool_is_full:
                log_print(f"[系统] 线程池已满 ({pending_count}/{MAX_WORKERS})")
            else:
                log_print(f"[系统] 线程池有空闲，尝试获取新任务...")
            
            # 从服务器获取任务
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
                    with active_type3_browsers_lock:
                        browser_is_busy = browser_id in active_type3_browsers
                    
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
                # 如果线程池已满（不管什么类型），等待下一次循环
                elif pool_is_full:
                    log_print(f"[系统] 线程池已满，Type={mission_type} 任务将在下次循环处理")
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
4001    k15m8scy"""
    
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

