import time
import random
import re
import requests
import threading
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


# 自定义打印函数，在每条日志前加上时间戳
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
        
    说明：
        - PASSWORD_MAP 格式：{"密码": "浏览器ID1,浏览器ID2,..."}
        - 特殊值 "else" 表示其他所有浏览器
        - 如果没有匹配，返回默认密码 PWD
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
COMPUTER_GROUP = "2"

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
PWD = "ywj000805*"

# 服务器API配置
SERVER_BASE_URL = "https://sg.bicoin.com.cn/99j"

# 全局线程池配置
MAX_WORKERS = 6  # 最大同时运行的线程数
global_thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks_lock = threading.Lock()
active_tasks = {}  # {mission_id: {'futures': [], 'results': {}, 'total': 0, 'completed': 0}}

# Type 6 任务特殊处理
type6_task_lock = threading.Lock()
type6_task_running = False  # 标记是否有 type=6 任务正在运行
type6_task_thread = None  # type=6 任务的线程对象

# AdsPower配置
ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"

# 全局字典：存储每个浏览器最后使用的代理配置
# 用于在重试时判断是否需要切换代理类型（isMain!=1时从socks5切换到http）
LAST_PROXY_CONFIG = {}

# 浏览器编号到用户ID的映射（从 App.vue 中导入）
# 格式: {浏览器编号: 用户ID}
FINGERPRINT_TO_USERID = {}


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
        
        url = "https://sg.bicoin.com.cn/99j/bro/getIp"
        payload = {"number": browser_id}
        
        response = requests.post(url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] 获取IP接口返回: {result}")
            
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                ip = data.get("ip")
                is_main = data.get("isMain", 0)  # 默认为0
                
                if not ip:
                    log_print(f"[{browser_id}] ⚠ 返回数据中没有IP字段")
                    return None
                
                # 根据 isMain 字段决定如何构建代理配置
                if is_main == 1:
                    # isMain=1: 使用服务器的 ip, port, username, password，type 写死为 "http"
                    port = data.get("port")
                    username = data.get("username")
                    password = data.get("password")
                    
                    if ip and port and username and password:
                        proxy_config = {
                            "ip": ip,
                            "port": str(port),
                            "username": username,
                            "password": password,
                            "type": "http",  # 写死为 http
                            "isMain": is_main
                        }
                        log_print(f"[{browser_id}] ✓ 成功获取新代理配置 (isMain=1): IP={ip}, Port={port}, Type=http(写死)")
                        return proxy_config
                    else:
                        log_print(f"[{browser_id}] ⚠ isMain=1 但返回数据中缺少必要字段 (ip={ip}, port={port}, username={username}, password={password})")
                        return None
                else:
                    # isMain!=1: 只使用服务器的 ip，其他字段全部写死
                    proxy_config = {
                        "ip": ip,
                        "port": "50101",  # 写死
                        "username": "nolanwang",  # 写死
                        "password": "HFVsyegfeyigrfkjb",  # 写死
                        "type": "socks5",  # 写死
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


def try_update_ip_before_start(browser_id):
    """
    在打开浏览器前尝试获取并更新代理配置（8秒超时）
    如果8秒内获取到代理配置就更新，否则直接返回继续执行
    
    Args:
        browser_id: 浏览器编号
        
    Returns:
        bool: 是否成功更新了代理配置（True=更新成功，False=未更新或更新失败）
    """
    try:
        log_print(f"[{browser_id}] 尝试在打开浏览器前获取新代理配置...")
        
        # 尝试获取新代理配置，8秒超时
        proxy_config = get_new_ip_for_browser(browser_id, timeout=8)
        
        if proxy_config:
            # 获取到代理配置，尝试更新
            log_print(f"[{browser_id}] 在8秒内获取到新代理配置: IP={proxy_config['ip']}, Port={proxy_config['port']}, Type={proxy_config['type']}，开始更新...")
            update_success = update_adspower_proxy(browser_id, proxy_config)
            
            if update_success:
                log_print(f"[{browser_id}] ✓ 代理配置更新成功，将使用新配置打开浏览器")
                return True
            else:
                log_print(f"[{browser_id}] ⚠ 代理配置更新失败，将使用原配置打开浏览器")
                return False
        else:
            # 8秒内未获取到代理配置
            log_print(f"[{browser_id}] 8秒内未获取到新代理配置，将使用原配置打开浏览器")
            return False
            
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 尝试更新代理配置时发生异常: {str(e)}，将使用原配置打开浏览器")
        return False


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
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
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
            return False
            
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 更新AdsPower代理配置异常: {str(e)}")
        return False


def retry_with_new_ip_and_reopen(serial_number, driver, try_proxy_switch=True):
    """
    当页面打开失败时，更换IP并重新打开浏览器
    对于 isMain!=1 的情况，会先尝试切换代理类型（socks5->http），失败后再获取新IP
    
    Args:
        serial_number: 浏览器编号
        driver: Selenium驱动对象（失败时需要先关闭）
        try_proxy_switch: 是否尝试切换代理类型（默认True）
        
    Returns:
        WebDriver: 成功返回新驱动，失败返回None
    """
    try:
        # 1. 关闭当前驱动和浏览器
        if driver:
            try:
                driver.quit()
                log_print(f"[{serial_number}] ✓ Selenium驱动已关闭")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 关闭驱动失败: {str(e)}")
        
        time.sleep(2)
        close_adspower_browser(serial_number)
        time.sleep(3)
        
        # 2. 检查是否可以先尝试切换代理类型（仅限 isMain!=1 的情况）
        last_config = LAST_PROXY_CONFIG.get(str(serial_number))
        should_try_switch = False
        
        if try_proxy_switch and last_config:
            is_main = last_config.get('isMain', 0)
            current_type = last_config.get('type', '')
            current_port = last_config.get('port', '')
            
            # 如果 isMain!=1 且当前使用的是 socks5 + 50101，尝试切换到 http + 50100
            if is_main != 1 and current_type == 'socks5' and current_port == '50101':
                should_try_switch = True
                log_print(f"[{serial_number}] ⚠ 检测到使用 socks5:50101，尝试切换到 http:50100...")
                
                # 构建新的代理配置（只改变 type 和 port）
                switched_config = last_config.copy()
                switched_config['type'] = 'http'
                switched_config['port'] = '50100'
                
                # 尝试更新代理配置
                log_print(f"[{serial_number}] 正在更新代理配置为 http:50100...")
                update_success = update_adspower_proxy(serial_number, switched_config)
                
                if update_success:
                    log_print(f"[{serial_number}] ✓ 代理配置切换成功，重新打开浏览器...")
                    
                    # 重新打开浏览器
                    time.sleep(2)
                    browser_data = start_adspower_browser(serial_number)
                    
                    if not browser_data:
                        log_print(f"[{serial_number}] ✗ 浏览器启动失败")
                        # 切换代理后浏览器启动失败，继续获取新IP
                        log_print(f"[{serial_number}] 代理切换后浏览器启动失败，将获取新IP...")
                    else:
                        # 创建新的Selenium驱动
                        log_print(f"[{serial_number}] 正在创建Selenium驱动...")
                        new_driver = create_selenium_driver(browser_data)
                        log_print(f"[{serial_number}] ✓ Selenium驱动创建成功")
                        log_print(f"[{serial_number}] ✓✓✓ 代理切换并重新打开浏览器成功 (socks5:50101 -> http:50100)")
                        return new_driver
                else:
                    log_print(f"[{serial_number}] ✗ 代理配置切换失败，将获取新IP...")
        
        # 3. 获取新IP（切换代理失败或不需要切换时）
        log_print(f"[{serial_number}] 正在获取新IP...")
        new_ip = get_new_ip_for_browser(serial_number)
        
        if not new_ip:
            log_print(f"[{serial_number}] ✗ 无法获取新IP，停止重试")
            return None
        
        log_print(f"[{serial_number}] ✓ 获取到新IP: {new_ip}")
        
        # 4. 更新AdsPower代理配置（如果失败则继续获取新IP）
        # ⚠️ 添加最大重试次数限制，防止无限循环导致系统资源耗尽
        MAX_IP_UPDATE_RETRIES = 5
        ip_update_retry_count = 0
        
        while ip_update_retry_count < MAX_IP_UPDATE_RETRIES:
            ip_update_retry_count += 1
            log_print(f"[{serial_number}] 正在更新浏览器代理配置 (尝试 {ip_update_retry_count}/{MAX_IP_UPDATE_RETRIES})...")
            update_success = update_adspower_proxy(serial_number, new_ip)
            
            if update_success:
                log_print(f"[{serial_number}] ✓ 代理配置更新成功")
                break
            
            # 更新失败，检查是否还能重试
            if ip_update_retry_count >= MAX_IP_UPDATE_RETRIES:
                log_print(f"[{serial_number}] ✗ 代理配置更新失败，已达到最大重试次数 ({MAX_IP_UPDATE_RETRIES})，停止重试")
                return None
            
            # 尝试获取新IP
            log_print(f"[{serial_number}] ✗ 代理配置更新失败，尝试获取新IP...")
            new_ip = get_new_ip_for_browser(serial_number)
            
            if not new_ip:
                log_print(f"[{serial_number}] ✗ 无法获取新IP，停止重试")
                return None
            
            log_print(f"[{serial_number}] ✓ 获取到新IP: {new_ip}")
        
        time.sleep(2)
        
        # 5. 重新打开浏览器
        log_print(f"[{serial_number}] 正在重新打开浏览器...")
        browser_data = start_adspower_browser(serial_number)
        
        if not browser_data:
            log_print(f"[{serial_number}] ✗ 浏览器启动失败")
            return None
        
        # 6. 创建新的Selenium驱动
        log_print(f"[{serial_number}] 正在创建Selenium驱动...")
        new_driver = create_selenium_driver(browser_data)
        log_print(f"[{serial_number}] ✓ Selenium驱动创建成功")
        
        # 成功返回新驱动
        log_print(f"[{serial_number}] ✓✓✓ IP更换并重新打开浏览器成功")
        return new_driver
        
    except Exception as e:
        log_print(f"[{serial_number}] ✗ IP更换重试过程中发生异常: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return None

# 浏览器ID数组 - 现在从服务器获取任务
# 格式: [{"id": "浏览器ID", "type": 1-5, "refCode": "邀请码", "pwd": "密码"}, ...]
# type: 1 = 收集数据（资产和仓位），完成后自动关闭浏览器
# type: 2 = 打开浏览器，处理扩展页面和asterdex页面，不关闭浏览器
# type: 3 = 关闭对应的指纹浏览器
# type: 4 = 执行兑换和绑定邀请码操作
# type: 5 = 连接已打开的浏览器，切换到asterdex页面并收集数据，完成后不关闭浏览器
BROWSER_IDS = [
    {"id": "901", "type": 1, "refCode": "","pwd":""},
    {"id": "902", "type": 1, "refCode": "","pwd":""},
    {"id": "903", "type": 1, "refCode": "","pwd":""},
]

# 目标URL
TARGET_URL = "https://www.asterdex.com/en/futures/v1/BTCUSDT"

# 最大重试次数
MAX_RETRIES = 3


RANDOM_PATH = [
    [
        "https://www.asterdex.com/en/futures/v1/BTCUSDT",
        "https://www.asterdex.com/en/portfolio/overview",
        "https://www.asterdex.com/en/spot/CDLUSD1",
        "https://www.asterdex.com/en/trade-and-earn",
        "https://www.asterdex.com/en/strategy/futures/grid/TAKEUSDT",
        "https://www.asterdex.com/en/referral",
        "https://www.asterdex.com/en/stage3/statistics",
    ],
    [
        "https://www.asterdex.com/en/futures/v1/BTCUSDT",
        "https://www.asterdex.com/en/referral",
        "https://www.asterdex.com/en/futures/BNBUSD",
        "https://www.asterdex.com/en/rewards_hub",
        "https://www.asterdex.com/en/trading-leaderboard",
        "https://www.asterdex.com/en/spot/ETHUSDT",
        "https://www.asterdex.com/en/portfolio/overview",
        "https://www.asterdex.com/en/stage3/statistics",
    ],
    [
        "https://www.asterdex.com/en/futures/v1/BNBUSDT",
        "https://www.asterdex.com/en/futures/v1/XRPUSDT",
        "https://www.asterdex.com/en/portfolio/overview",
        "https://www.asterdex.com/en/apx-upgrade",
        "https://www.asterdex.com/en/airdrop",
        "https://www.asterdex.com/en/referral",
        "https://www.asterdex.com/en/trade-and-earn",
        "https://www.asterdex.com/en/rewards_hub",
        "https://www.asterdex.com/en/stage3/statistics",
    ]
    ,
    [
        "https://www.asterdex.com/en/spot/ETHUSDT",
        "https://www.asterdex.com/en/futures/ETHUSD",
        "https://www.asterdex.com/en/futures/SOLUSD",
        "https://www.asterdex.com/en/futures/v1/ETHUSDT",
        "https://www.asterdex.com/en/rewards_hub",
        "https://www.asterdex.com/en/referral",
        "https://www.asterdex.com/en/trading-leaderboard",
        "https://www.asterdex.com/en/stage3/statistics",
    ],
    [
        "https://www.asterdex.com/en/airdrop",
        "https://www.asterdex.com/en/airdrop/statistics",
        "https://www.asterdex.com/en/trade-and-earn",
        "https://www.asterdex.com/en/spot/BTCUSDT",
        "https://www.asterdex.com/en/earn",
        "https://www.asterdex.com/en/futures/v1/ETHUSDT",
        "https://www.asterdex.com/en/futures/BTCUSD",
        "https://www.asterdex.com/en/stage3/statistics",
    ],
    [
        "https://www.asterdex.com/zh-CN",
        "https://www.asterdex.com/zh-CN/futures/v1/BTCUSDT",
        "https://www.asterdex.com/en/usdf",
        "https://www.asterdex.com/en/trading-leaderboard",
        "https://www.asterdex.com/en/stage3/statistics",
    ],
    [
        "https://www.asterdex.com/zh-CN/futures/v1/BTCUSDT",
        "https://www.asterdex.com/en/portfolio/overview",
        "https://www.asterdex.com/en/portfolio/pro",
        "https://www.asterdex.com/en/portfolio/earn",
        "https://www.asterdex.com/en/futures/NVDAUSD",
        "https://www.asterdex.com/en/trade-and-earn",
        "https://www.asterdex.com/en/stage3/statistics",
    ]
]


def get_mission_from_server():
    """
    从服务器获取任务
    
    Returns:
        dict: 任务数据，如果没有任务或失败则返回None
    """
    try:
        url = f"{SERVER_BASE_URL}/mission/getOneMission"
        payload = {"number": COMPUTER_GROUP}
        
        log_print(f"\n[系统] 请求任务: {url}")
        log_print(f"[系统] 请求参数: {payload}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[系统] 服务器响应: {result}")
            
            # 检查返回码和数据
            if result and isinstance(result, dict):
                code = result.get("code")
                msg = result.get("msg")
                data = result.get("data")
                
                if code == 0 and data:
                    # 验证 number 是否匹配
                    if data.get("number") == COMPUTER_GROUP:
                        log_print(f"[系统] ✓ 获取到任务 ID: {data.get('id')}, 类型: {data.get('type')}")
                        return data
                    else:
                        log_print(f"[系统] ℹ 任务电脑组不匹配: {data.get('number')} != {COMPUTER_GROUP}")
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


def submit_mission_result(mission_id, success_count, failed_count, failed_info):
    """
    提交任务结果到服务器（带重试机制）
    
    Args:
        mission_id: 任务ID
        success_count: 成功数量
        failed_count: 失败数量
        failed_info: 失败的浏览器信息字典 {browser_id: failure_reason}
        
    Returns:
        bool: 提交成功返回True，失败返回False
    """
    url = f"{SERVER_BASE_URL}/mission/saveResult"
    
    # 构建消息
    msg = f"成功: {success_count}个, 失败: {failed_count}个"
    if failed_info:
        msg += f", 失败的浏览器: {', '.join(failed_info.keys())}"
        # 添加失败原因详情
        reasons = []
        for bid, reason in failed_info.items():
            if reason:
                reasons.append(f"{bid}{reason}")
        if reasons:
            msg += f"，其中{'，'.join(reasons)}"
    
    payload = {
        "id": mission_id,
        "status": 2,  # 2 代表已完成
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
                time.sleep(2)  # 重试前等待2秒
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                log_print(f"[系统] 服务器响应: {result}")
                
                # 检查是否返回空字典 {} 表示成功
                if result == {}:
                    log_print(f"[系统] ✓ 结果提交成功（服务器返回空字典）")
                    return True
                
                # 检查返回码
                if result and isinstance(result, dict):
                    code = result.get("code")
                    server_msg = result.get("msg")
                    
                    if code == 0:
                        log_print(f"[系统] ✓ 结果提交成功")
                        return True
                    else:
                        log_print(f"[系统] ✗ 结果提交失败 (code: {code}, msg: {server_msg})")
                        if attempt < max_retries - 1:
                            log_print(f"[系统] 将在2秒后重试...")
                            continue
                        return False
                else:
                    log_print(f"[系统] ✗ 服务器返回数据格式错误")
                    if attempt < max_retries - 1:
                        log_print(f"[系统] 将在2秒后重试...")
                        continue
                    return False
            else:
                log_print(f"[系统] ✗ 结果提交失败，状态码: {response.status_code}")
                if attempt < max_retries - 1:
                    log_print(f"[系统] 将在2秒后重试...")
                    continue
                return False
                
        except requests.exceptions.Timeout:
            log_print(f"[系统] ✗ 提交结果超时")
            if attempt < max_retries - 1:
                log_print(f"[系统] 将在2秒后重试...")
                continue
            return False
        except Exception as e:
            log_print(f"[系统] ✗ 提交结果失败: {str(e)}")
            import traceback
            log_print(f"[系统] 错误详情:\n{traceback.format_exc()}")
            if attempt < max_retries - 1:
                log_print(f"[系统] 将在2秒后重试...")
                continue
            return False
    
    # 所有重试都失败
    log_print(f"[系统] ✗✗✗ 提交结果失败，已重试 {max_retries} 次")
    return False


def start_adspower_browser(serial_number):
    import json
    """
    启动AdsPower浏览器
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        dict: 包含浏览器连接信息的字典，失败返回None
    """
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/start"
    params = {
        "serial_number": serial_number,
        "user_id": "",
        "open_tabs": 1
    }
    launch_args = []
    launch_args.append(f"--window-size={1500},{1000}")
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
        
        # 如果不是最后一次尝试，等待随机时间后重试
        if attempt < MAX_RETRIES - 1:
            wait_time = random.randint(5, 10)
            log_print(f"[{serial_number}] 等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    log_print(f"[{serial_number}] ✗✗✗ 浏览器启动失败，已达到最大重试次数")
    return None


def check_browser_status(serial_number):
    """
    检查浏览器是否正在运行
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        bool: 浏览器正在运行返回True，否则返回False
    """
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/active"
    params = {
        "serial_number": serial_number
    }
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data.get("code") == 0 and data.get("data", {}).get("status") == "Active":
            return True
        return False
    except:
        return False


def get_running_browser_data(serial_number):
    """
    获取已经运行的浏览器连接信息
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        dict: 包含浏览器连接信息的字典，失败返回None
    """
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/active"
    params = {
        "serial_number": serial_number
    }
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    try:
        log_print(f"[{serial_number}] 检查浏览器是否已运行...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("code") == 0:
            browser_data = data.get("data", {})
            if browser_data.get("status") == "Active":
                log_print(f"[{serial_number}] ✓ 浏览器已在运行中")
                return browser_data
            else:
                log_print(f"[{serial_number}] ✗ 浏览器未运行，状态: {browser_data.get('status')}")
                return None
        else:
            log_print(f"[{serial_number}] ✗ 获取浏览器状态失败: {data.get('msg')}")
            return None
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 获取浏览器状态时发生错误: {str(e)}")
        return None


def close_extra_tabs(driver, serial_number):
    """
    关闭所有多余的标签页，只保留一个（优先保留非插件页面）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
    """
    try:
        all_windows = driver.window_handles
        if len(all_windows) <= 1:
            log_print(f"[{serial_number}] ℹ 只有一个标签页，无需关闭")
            return
        
        log_print(f"[{serial_number}] 当前有 {len(all_windows)} 个标签页，准备关闭多余标签页...")
        
        # 找到一个非插件页面作为保留页面（优先）
        keep_window = None
        window_info = []
        
        for window_handle in all_windows:
            try:
                driver.switch_to.window(window_handle)
                current_url = driver.current_url
                is_extension = current_url.startswith('chrome-extension://')
                window_info.append({
                    'handle': window_handle,
                    'url': current_url,
                    'is_extension': is_extension
                })
                
                # 优先选择非插件页面保留
                if keep_window is None and not is_extension:
                    keep_window = window_handle
                    log_print(f"[{serial_number}] 将保留页面: {current_url[:80]}")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 无法获取标签页URL: {str(e)}")
                window_info.append({
                    'handle': window_handle,
                    'url': 'unknown',
                    'is_extension': False
                })
        
        # 如果没有找到非插件页面，保留第一个
        if keep_window is None:
            keep_window = all_windows[0]
            log_print(f"[{serial_number}] 未找到普通页面，保留第一个标签页")
        
        # 关闭其他所有标签页
        closed_count = 0
        for info in window_info:
            if info['handle'] != keep_window:
                try:
                    driver.switch_to.window(info['handle'])
                    
                    # 对于插件页面，尝试使用JavaScript强制关闭
                    if info['is_extension']:
                        try:
                            driver.execute_script("window.close();")
                            log_print(f"[{serial_number}] ✓ 已关闭插件页面")
                            closed_count += 1
                        except:
                            # JavaScript失败，尝试普通关闭
                            driver.close()
                            log_print(f"[{serial_number}] ✓ 已关闭插件页面（普通方式）")
                            closed_count += 1
                    else:
                        driver.close()
                        log_print(f"[{serial_number}] ✓ 已关闭页面: {info['url'][:60]}")
                        closed_count += 1
                except Exception as e:
                    log_print(f"[{serial_number}] ⚠ 关闭标签页失败: {str(e)}")
        
        # 切换回保留的标签页
        try:
            driver.switch_to.window(keep_window)
            log_print(f"[{serial_number}] ✓ 已关闭 {closed_count}/{len(all_windows)-1} 个标签页")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 切换到保留标签页失败: {str(e)}")
        
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 关闭多余标签页时发生错误: {str(e)}")


def close_adspower_browser(serial_number, max_retries=3):
    """
    关闭AdsPower浏览器，带重试机制和状态验证
    
    Args:
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
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
                # 等待一下确保浏览器完全关闭
                time.sleep(2)
                
                # 验证浏览器是否真的关闭了
                if not check_browser_status(serial_number):
                    log_print(f"[{serial_number}] ✓ 浏览器已确认关闭")
                    return True
                else:
                    log_print(f"[{serial_number}] ⚠ 浏览器仍在运行，继续重试...")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
            else:
                log_print(f"[{serial_number}] ✗ 关闭浏览器失败: {data.get('msg')}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    log_print(f"[{serial_number}] 等待 2 秒后重试...")
                    time.sleep(2)
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 关闭浏览器时发生错误: {str(e)}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                time.sleep(2)
    
    # 最后再检查一次状态
    if not check_browser_status(serial_number):
        log_print(f"[{serial_number}] ✓ 浏览器最终确认已关闭")
        return True
    
    log_print(f"[{serial_number}] ⚠ 浏览器关闭失败，可能仍在运行，建议手动检查")
    return False


def create_selenium_driver(browser_data):
    """
    创建Selenium WebDriver
    
    Args:
        browser_data: 浏览器启动返回的数据
        
    Returns:
        WebDriver: Selenium驱动对象
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", browser_data["ws"]["selenium"])
    
    # 使用返回的webdriver路径
    service = Service(executable_path=browser_data["webdriver"])
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 设置页面加载超时时间为60秒，防止页面加载卡死
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    
    return driver


def wait_for_page_ready(driver, serial_number, timeout=20):
    """
    等待页面就绪（检查是否有包含 "Avbl" 或 "可用" 的 P 标签）
    使用 Selenium 的 WebDriverWait 和自定义条件
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        timeout: 超时时间（秒），默认20秒
        
    Returns:
        tuple: (is_ready, message) - (是否就绪, 提示信息)
    """
    try:
        log_print(f"[{serial_number}] 等待页面就绪（最多{timeout}秒）...")
        
        def check_page_ready(driver):
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "div")
                for p in p_tags:
                    p_text = p.text.strip()
                    if "Avbl" in p_text or "可用" in p_text:
                        return True
                return False
            except:
                return False
        
        # 使用 WebDriverWait 等待条件满足
        start_time = time.time()
        wait = WebDriverWait(driver, timeout)
        wait.until(check_page_ready)
        
        elapsed = time.time() - start_time
        log_print(f"[{serial_number}] ✓ 页面就绪（用时 {elapsed:.1f}秒）")
        return True, ""
        
    except TimeoutException:
        log_print(f"[{serial_number}] ✗ 页面未就绪：{timeout}秒内未找到包含 'Avbl' 或 '可用' 的元素")
        return False, "页面加载超时"
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 等待页面就绪时发生错误: {str(e)}")
        return False, "页面检查异常"





def check_wallet_signature(driver, serial_number):
    """
    检查钱包是否已签名
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (is_signed, message) - (是否已签名, 提示信息)
    """
    try:
        
        log_print(f"[{serial_number}] 开始检查钱包签名状态...")
        
        # 检查是否有 "连接钱包" 或 "Connect wallet" 按钮
        try:
            connect_wallet_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='连接钱包'], button[aria-label='Connect wallet']")
            if connect_wallet_btn:
                log_print(f"[{serial_number}] ✗ 发现未签名标志：连接钱包按钮")
                return False, "未连接钱包"
        except:
            pass
        
        # 检查是否有 "Get your Aster key" 或 "获取您的Aster密钥" 的 h4
        try:
            aster_key_h4 = driver.find_elements(By.XPATH, "//h4[contains(text(), 'Get your Aster key') or contains(text(), '获取您的Aster密钥')]")
            if aster_key_h4:
                log_print(f"[{serial_number}] ✗ 发现未签名标志：获取Aster密钥")
                return False, "未签名"
        except:
            pass
        
        # 检查是否有 "启用交易" 或 "Enable Trading" 按钮
        try:
            enable_trading_btn = driver.find_elements(By.XPATH, "//button[contains(text(), '启用交易') or contains(text(), 'Enable Trading')]")
            if enable_trading_btn:
                log_print(f"[{serial_number}] ✗ 发现未签名标志：启用交易按钮")
                return False, "未签名"
        except:
            pass
        
        log_print(f"[{serial_number}] ✓ 钱包已签名")
        return True, ""
        
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 检查签名状态时出错: {str(e)}")
        # 出错时假设已签名，继续执行
        return True, ""


def open_target_page(driver, serial_number):
    """
    打开目标页面
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    for attempt in range(MAX_RETRIES):
        try:
            log_print(f"[{serial_number}] 尝试打开页面 (第 {attempt + 1}/{MAX_RETRIES} 次)")
            driver.get(TARGET_URL)
            
            # 等待页面加载完成 - 等待特定元素出现
            wait = WebDriverWait(driver, 30)
            # 等待可用余额元素出现
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
            
            log_print(f"[{serial_number}] ✓ 页面加载成功")
            log_print(f"[{serial_number}] 等待 2 秒确保页面数据加载完成...")
            time.sleep(2)  # 等待2秒确保页面数据完全加载
            return True
            
        except TimeoutException:
            log_print(f"[{serial_number}] ✗ 页面加载超时")
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 打开页面时发生错误: {str(e)}")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < MAX_RETRIES - 1:
            log_print(f"[{serial_number}] 等待 3 秒后重试...")
            time.sleep(3)
    
    log_print(f"[{serial_number}] ✗✗✗ 页面打开失败，已达到最大重试次数")
    return False


def collect_and_submit_data(driver, serial_number):
    """
    执行数据收集和上传操作
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (success, failure_reason) - (是否成功, 失败原因)
    """
    # API基础URL
    API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
    
    # 使用 serial_number 作为用户编号
    user_no = str(serial_number)
    
    # 首先验证服务器是否有对应数据
    log_print(f"[{serial_number}] 验证服务器数据...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        server_data = response.json()
        
        if not server_data.get('data') or not server_data['data']:
            log_print(f"[{serial_number}] ✗ 服务器没有编号 {user_no} 的对应数据，跳过采集")
            return False, "服务器无对应数据"
        
        log_print(f"[{serial_number}] ✓ 服务器数据验证通过")
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 验证服务器数据失败: {str(e)}")
        return False, "服务器数据验证失败"
    
    # 数据收集脚本
    def execute_data_collection_script():
        """执行数据收集JavaScript脚本"""
        script = """
        return new Promise((resolve) => {
            const results = {
                availableBalance: '',
                availableBalanceNumber: '',
                accountEquity: '',
                accountEquityNumber: '',
                maintenanceMargin: '',
                maintenanceMarginNumber: '',
                positionsData: [],
                positionsButtonFound: false,
                success: false,
                availableSuccess: false,
                equitySuccess: false,
                positionsSuccess: false
            };

            try {
                // 1. 获取可用余额
                const pTags = Array.from(document.querySelectorAll('p.text-t-third.flex.gap-1'));
                for (const p of pTags) {
                    const pText = (p.textContent || '').trim();
                    if (pText.includes('可用') || pText.includes('Avbl')) {
                        const span = p.querySelector('span.text-t-primary') || p.querySelector('span');
                        if (span) {
                            const balanceText = (span.textContent || '').trim();
                            results.availableBalance = balanceText;
                            const balanceMatch = balanceText.match(/[\\d,.]+/);
                            results.availableBalanceNumber = balanceMatch ? balanceMatch[0] : '';
                            if (results.availableBalanceNumber) {
                                results.availableSuccess = true;
                            }
                            break;
                        }
                    }
                }

                // 2. 获取账户权益
                const allSpans = Array.from(document.querySelectorAll('span'));
                for (const span of allSpans) {
                    const spanText = (span.textContent || '').trim();
                    if (spanText.includes('账户权益') || spanText.includes('Account Equity')) {
                        const greatGreatGreatGrandParent = span?.parentElement?.parentElement?.parentElement?.parentElement;
                        if (greatGreatGreatGrandParent) {
                            const childDivs = greatGreatGreatGrandParent.querySelectorAll(':scope > div');
                            if (childDivs && childDivs.length > 0) {
                                const lastDiv = childDivs[childDivs.length - 1];
                                const equityText = (lastDiv.textContent || '').trim();
                                results.accountEquity = equityText;
                                const equityMatch = equityText.match(/[\\d,.]+/);
                                results.accountEquityNumber = equityMatch ? equityMatch[0] : '';
                                if (results.accountEquityNumber) {
                                    results.equitySuccess = true;
                                }
                            }
                        }
                        break;
                    }
                }

                // 2.5. 获取账户维持保证金
                const allDivs = Array.from(document.querySelectorAll('div'));
                for (const div of allDivs) {
                    const divText = (div.textContent || '').trim();
                    if (divText === '账户维持保证金' || divText === 'Account Maintenance Margin') {
                        const parentDiv = div.parentElement;
                        if (parentDiv) {
                            const childDivs = parentDiv.querySelectorAll(':scope > div');
                            if (childDivs && childDivs.length > 0) {
                                const lastDiv = childDivs[childDivs.length - 1];
                                const marginText = (lastDiv.textContent || '').trim();
                                results.maintenanceMargin = marginText;
                                const marginMatch = marginText.match(/[\\d,.]+/);
                                results.maintenanceMarginNumber = marginMatch ? marginMatch[0] : '';
                            }
                        }
                        break;
                    }
                }

                // 3. 点击仓位按钮
                let positionsButtonFound = false;
                const allButtons = Array.from(document.querySelectorAll('button'));
                for (const btn of allButtons) {
                    const btnText = (btn.textContent || '').trim();
                    if (btnText.includes('Positions') || btnText.includes('仓位')) {
                        btn.click();
                        positionsButtonFound = true;
                        break;
                    }
                }
                results.positionsButtonFound = positionsButtonFound;

                // 4. 等待后获取持仓数据
                setTimeout(() => {
                    if (positionsButtonFound) {
                        results.positionsSuccess = true;
                        
                        // 循环获取 data-id 从 0 到 5 的持仓数据
                        for (let i = 0; i <= 5; i++) {
                            const dataDiv = document.querySelector(`div[data-id="${i}"]`);
                            if (!dataDiv) {
                                // 如果没有找到当前 data-id，停止循环
                                break;
                            }
                            
                            const allDivs = dataDiv.querySelectorAll('div');
                            const texts = [];
                            allDivs.forEach(div => {
                                const text = (div.textContent || '').trim();
                                if (text) texts.push(text);
                            });

                            if (texts.length > 0) {
                                results.positionsData.push({
                                    dataId: String(i),
                                    index0: texts[0] || '',
                                    index8: texts[8] || '',
                                    index10: texts[10] || '',
                                    index13: texts[13] || '',
                                    index20: texts[20] || ''
                                });
                            }
                        }
                    }

                    // 三个数据都必须成功，任务才算成功
                    if (results.availableSuccess && results.equitySuccess && results.positionsSuccess) {
                        results.success = true;
                    }

                    resolve(results);
                }, 1000);
            } catch (e) {
                resolve(results);
            }
        });
        """
        return driver.execute_script(script)
    
    def get_assets_data(driver):
        """
        单独获取资产数据的方法
        
        Returns:
            dict: 包含 assetsValue, assetsValueNumber, assetsSuccess 的字典
        """
        script = """
        return new Promise((resolve) => {
            const results = {
                assetsButtonFound: false,
                assetsValue: '',
                assetsValueNumber: '',
                assetsValueSecond: '',
                assetsValueSecondNumber: '',
                assetsSuccess: false,
                assetsSecondSuccess: false,
                allAssetsChildren: []
            };
            
            try {
                // 1. 点击资产按钮
                const assetsButtons = Array.from(document.querySelectorAll('button'));
                let assetsButtonFound = false;
                
                for (const btn of assetsButtons) {
                    const btnText = (btn.textContent || '').trim();
                    if (btnText === '资产' || btnText === 'Assets') {
                        // 使用多种方式尝试点击
                        try {
                            btn.scrollIntoView({ behavior: 'instant', block: 'center' });
                            
                            const mouseDownEvent = new MouseEvent('mousedown', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                detail: 1
                            });
                            const mouseUpEvent = new MouseEvent('mouseup', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                detail: 1
                            });
                            const clickEvent = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                detail: 1
                            });
                            
                            btn.dispatchEvent(mouseDownEvent);
                            btn.dispatchEvent(mouseUpEvent);
                            btn.dispatchEvent(clickEvent);
                            
                            const pointerDownEvent = new PointerEvent('pointerdown', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            const pointerUpEvent = new PointerEvent('pointerup', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            btn.dispatchEvent(pointerDownEvent);
                            btn.dispatchEvent(pointerUpEvent);
                            
                            btn.click();
                            
                            assetsButtonFound = true;
                            results.assetsButtonFound = true;
                        } catch (e) {
                            // 忽略错误
                        }
                        break;
                    }
                }
                
                if (assetsButtonFound) {
                    // 轮询获取资产数据：30秒内每3秒抓取一次，直到获取到非0值
                    const startTime = Date.now();
                    const maxWaitTime = 80000; // 30秒
                    const pollInterval = 2000; // 3秒
                    
                    const pollAssets = () => {
                        const dataDiv2Element = document.querySelector('div[data-id="0"]');
                        let dataDiv2 = null;
                        
                         if (dataDiv2Element) {
                            // 获取父节点
                            const parentNode = dataDiv2Element.parentNode;
                            if (parentNode) {
                                // 获取父节点下所有子节点的所有子div内容
                                const allChildrenData = [];
                                const children = parentNode.children;
                                
                                for (let i = 0; i < children.length; i++) {
                                    const child = children[i];
                                    // 获取该子节点的直接子div（只取一层）
                                    const childDivs = child.querySelectorAll(':scope > div');
                                    const childTexts = [];
                                    
                                    childDivs.forEach(div => {
                                        const text = (div.textContent || '').trim();
                                        if (text) {
                                            childTexts.push(text);
                                        }
                                    });
                                    
                                    if (childTexts.length > 0) {
                                        allChildrenData.push({
                                            childIndex: i,
                                            texts: childTexts
                                        });
                                    }
                                }
                                
                                // 将所有数据存储到 results
                                results.allAssetsChildren = allChildrenData;
                                
                                // 调试输出：打印所有子节点数据
                                console.info('📊 所有资产子节点数据 (allAssetsChildren):');
                                console.info('  总共子节点数量:', allChildrenData.length);
                                allChildrenData.forEach((childData, idx) => {
                                    console.info(`  子节点[${childData.childIndex}] 包含 ${childData.texts.length} 个文本:`);
                                    childData.texts.forEach((text, textIdx) => {
                                        console.info(`    [${textIdx}]: ${text}`);
                                    });
                                });
                                
                            }
                        }
                        
                        
                        // 检查是否超时
                        const elapsedTime = Date.now() - startTime;
                        if (elapsedTime >= maxWaitTime) {
                            // 超时处理：如果 allAssetsChildren 数量为 0，继续抓取；大于 0 就返回结果
                            if (results.allAssetsChildren && results.allAssetsChildren.length === 0) {
                                console.info('⚠️ 超时但 allAssetsChildren 为空，继续抓取');
                                setTimeout(pollAssets, pollInterval);
                            } else {
                                console.info('✓ 获取到资产数据，返回结果');
                                results.assetsSuccess = true;
                                resolve(results);
                            }
                        } else {
                            // 如果已经获取到数据（allAssetsChildren 长度 > 0），立即返回
                            if (results.allAssetsChildren && results.allAssetsChildren.length > 0) {
                                console.info('✓ 已获取到资产数据，立即返回');
                                results.assetsSuccess = true;
                                resolve(results);
                            } else {
                                // 继续等待后再次抓取
                                setTimeout(pollAssets, pollInterval);
                            }
                        }
                    };
                    
                    // 初次等待3秒后开始轮询
                    setTimeout(pollAssets, pollInterval);
                } else {
                    resolve(results);
                }
            } catch (e) {
                resolve(results);
            }
        });
        """
        return driver.execute_script(script)
    
    def is_valid_number(value_str):
        """检查字符串是否是有效数字或能转换成数字"""
        if not value_str:
            return False
        try:
            # 移除逗号后尝试转换
            float(value_str.replace(',', ''))
            return True
        except (ValueError, AttributeError):
            return False
    
    # 阶段1: 等待账户维持保证金变成有效数字
    log_print(f"[{serial_number}] 开始抓取账户维持保证金数据...")
    max_attempts_per_round = 10  # 每轮最多10次
    max_rounds = 2  # 最多2轮（第一轮+刷新后的第二轮）
    
    margin_number = None
    margin_is_valid = False
    assets_data = None
    
    for round_num in range(max_rounds):
        if round_num > 0:
            log_print(f"[{serial_number}] 刷新页面后重新尝试...")
            driver.refresh()
            time.sleep(2)  # 页面加载后等待2秒
        
        for attempt in range(max_attempts_per_round):
            log_print(f"[{serial_number}] 抓取数据 (第 {round_num + 1} 轮, 第 {attempt + 1}/{max_attempts_per_round} 次)")
            
            data = execute_data_collection_script()
            margin_number = data.get('maintenanceMarginNumber', '')
            
            log_print(f"[{serial_number}]   账户维持保证金: {margin_number if margin_number else '(空)'}")
            # 检查是否是有效数字
            if is_valid_number(margin_number):
                margin_is_valid = True
                margin_value = float(margin_number.replace(',', ''))
                log_print(f"[{serial_number}] ✓ 账户维持保证金是有效数字: {margin_value}")
                time.sleep(4)
                data = execute_data_collection_script()
                # 继续后面的流程
                break
            else:
                log_print(f"[{serial_number}] ✗ 账户维持保证金不是有效数字，等待2秒后重试...")
                time.sleep(2)
        
        if margin_is_valid:
            break
    
    # 如果最终还是无效数字，返回失败
    if not margin_is_valid:
        log_print(f"[{serial_number}] ✗✗✗ 账户维持保证金始终不是有效数字，任务失败")
        return False, "账户维持保证金无效"
    
    # 阶段2: 继续抓取其他数据（可用余额、权益、仓位）
    log_print(f"[{serial_number}] 继续抓取可用余额、权益和仓位数据...")
    
    # 重新执行完整的数据收集（包括可用余额、权益和仓位）
    data = execute_data_collection_script()
    
    # 更新账户维持保证金（使用之前验证过的值）
    data['maintenanceMarginNumber'] = margin_number
    
    # 检查三个关键数据
    available_success = data.get('availableSuccess', False)
    equity_success = data.get('equitySuccess', False)
    positions_success = data.get('positionsSuccess', False)
    available_balance = data.get('availableBalanceNumber', '0')
    equity_number = data.get('accountEquityNumber', '0')
    positions_data = data.get('positionsData', [])
    
    log_print(f"[{serial_number}] 数据采集状态:")
    log_print(f"[{serial_number}]   可用余额: {'✓' if available_success else '✗'} {available_balance}")
    log_print(f"[{serial_number}]   账户权益: {'✓' if equity_success else '✗'} {equity_number}")
    log_print(f"[{serial_number}]   维持保证金: ✓ {margin_number}")
    log_print(f"[{serial_number}]   仓位按钮: {'✓' if positions_success else '✗'}")
    log_print(f"[{serial_number}]   持仓数量: {len(positions_data)}")
    
    # 特殊处理1：如果维持保证金>0但无持仓数据
    try:
        margin_value = float(margin_number.replace(',', '')) if margin_number else 0
        
        if margin_value > 0 and len(positions_data) == 0 and positions_success:
            log_print(f"[{serial_number}] ⚠ 维持保证金>0但无持仓数据，等待5秒后重新抓取仓位...")
            time.sleep(5)
            
            # 重新抓取仓位
            data = execute_data_collection_script()
            data['maintenanceMarginNumber'] = margin_number
            positions_data = data.get('positionsData', [])
            log_print(f"[{serial_number}]   重新获取的持仓数量: {len(positions_data)}")
            
            # 如果还是失败，刷新页面
            if len(positions_data) == 0:
                log_print(f"[{serial_number}] ⚠ 仍无持仓数据，刷新页面后再次尝试...")
                driver.refresh()
                time.sleep(2)
                
                # 刷新后重新抓取
                data = execute_data_collection_script()
                data['maintenanceMarginNumber'] = margin_number
                positions_data = data.get('positionsData', [])
                log_print(f"[{serial_number}]   刷新后获取的持仓数量: {len(positions_data)}")
    except ValueError:
        pass
    
    # 特殊处理3：维持保证金≠0 但 持仓数量=0，返回失败
    try:
        margin_value = float(margin_number.replace(',', '')) if margin_number else 0
        positions_count = len(data.get('positionsData', []))
        
        if margin_value != 0 and positions_count == 0:
            log_print(f"[{serial_number}] ✗✗✗ 维持保证金≠0({margin_value})但持仓数量=0，数据异常")
            return False, "维持保证金存在但无持仓数据"
        
    # 特殊处理3：维持保证金≠0 但 持仓数量=0，返回失败  都使用资产的数据   
        else:
            log_print(f"尝试获取资产数据...")
            
            try:
                # 设置脚本超时时间为45秒（资产轮询最长30秒）
                driver.set_script_timeout(45)
                
                ndata = get_assets_data(driver)
                # 调用资产获取方法
                assets_data  = ndata.get('allAssetsChildren', [])
                
                if len(assets_data) > 0:
                    data['equitySuccess'] = True
                    log_print(f"[{serial_number}] ✓ 已使用资产数据")
                    
                    # 获取到 assets_data 后，判断权益是否为0
                    equity_str = data.get('accountEquityNumber', '0').replace(',', '')
                    try:
                        equity_value = float(equity_str) if equity_str else 0
                    except ValueError:
                        equity_value = 0
                    
                    if equity_value == 0:
                        log_print(f"[{serial_number}] ⚠ 权益为0，尝试从资产数据中获取USDT余额...")
                        # 从 assets_data 中查找 USDT
                        for child_data in assets_data:
                            texts = child_data.get('texts', [])
                            if texts and len(texts) >= 2:
                                raw_currency = texts[0]
                                # 提取币种名称
                                if raw_currency.upper() == 'USDT':
                                    balance = texts[1] if len(texts) > 1 else '0'
                                    balance = balance.replace(',', '')
                                    if balance != '--' and balance != '–' and balance != '—':
                                        data['accountEquityNumber'] = balance
                                        log_print(f"[{serial_number}] ✓ 已使用USDT余额更新权益: {balance}")
                                        break
                else:
                    log_print(f"[{serial_number}] ✗ 资产数据获取失败")
                    return False, "资产数据获取失败"
            finally:
                # 无论成功或失败，都恢复默认脚本超时时间
                driver.set_script_timeout(30)
            
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 特殊处理异常: {str(e)}")
        return False, "资产数据获取异常"
    
    # 更新最终状态
    available_success = data.get('availableSuccess', False)
    equity_success = data.get('equitySuccess', False)
    positions_success = data.get('positionsSuccess', False)
    
    # 检查是否所有数据都成功
    if  not equity_success or not positions_success:
        failed_items = []
        if not equity_success:
            failed_items.append("账户权益")
        if not positions_success:
            failed_items.append("仓位")
        
        failure_reason = f"{'、'.join(failed_items)}获取失败"
        log_print(f"[{serial_number}] ✗ 数据收集失败：{failure_reason}")
        return False, failure_reason
    
    log_print(f"[{serial_number}] ✓ 数据收集完全成功")
    
    # 阶段3: 上传数据
    upload_success, upload_failure_reason = upload_collected_data(data, user_no, serial_number,assets_data)
    
    if upload_success:
        return True, ""
    else:
        log_print(f"[{serial_number}] ✗ 数据上传失败")
        return False, upload_failure_reason


def handle_zero_equity_with_positions(data, user_no, serial_number, API_BASE_URL, max_upload_retries, assets_data):
    """
    处理权益=0但有持仓数据的特殊情况
    只提交持仓列表和部分配置更新（c、d字段）
    
    Args:
        data: 采集的数据
        user_no: 用户编号
        serial_number: 浏览器序列号
        API_BASE_URL: API基础URL
        max_upload_retries: 最大重试次数
        assets_data: 资产数据（用于构建balance列表）
        
    Returns:
        tuple: (False, reason) - 返回失败
    """
    try:
        positions_data = data.get('positionsData', [])
        
        # 先构建 balance 列表（从 assets_data）
        balance_list = []
        if assets_data and len(assets_data) > 0:
            for child_data in assets_data:
                texts = child_data.get('texts', [])
                if texts and len(texts) >= 3:
                    # 提取币种名称（去除APY等后缀）
                    raw_currency = texts[0]
                    currency = extract_currency_name(raw_currency)
                    
                    # 第二个值是 balance，第三个值是 unPnl
                    balance = texts[1] if len(texts) > 1 else '0'
                    un_pnl = texts[2] if len(texts) > 2 else '0'
                    
                    # 处理 balance：替换逗号，如果是 "--" 则替换为 "0"
                    balance = balance.replace(',', '')
                    if balance == '--' or balance == '–' or balance == '—':
                        balance = '0'
                    
                    # 处理 unPnl：替换逗号，如果是 "--" 则替换为 "0"
                    un_pnl = un_pnl.replace(',', '')
                    if un_pnl == '--' or un_pnl == '–' or un_pnl == '—':
                        un_pnl = '0'
                    
                    balance_list.append({
                        "currency": currency,
                        "balance": balance,
                        "unPnl": un_pnl
                    })
        
        # 0. 提交资产列表数据 (bro/balance)
        assets_list_success = False
        if balance_list and len(balance_list) > 0:
            for attempt in range(max_upload_retries):
                try:
                    log_print(f"[{serial_number}] 正在提交资产列表数据 (共 {len(balance_list)} 个币种)... (尝试 {attempt + 1}/{max_upload_retries})")
                    
                    # 构建请求数据
                    assets_request_data = {
                        "number": user_no,
                        "list": balance_list
                    }
                    
                    log_print(f"[{serial_number}] 资产列表数据: {assets_request_data}")
                    
                    response = requests.post(
                        f"https://sg.bicoin.com.cn/99j/bro/balance",
                        json=assets_request_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        code = result.get('code')
                        
                        if code == 0:
                            log_print(f"[{serial_number}] ✓ 资产列表提交成功 (code=0)")
                            assets_list_success = True
                            break
                        else:
                            log_print(f"[{serial_number}] ✗ 资产列表提交失败: code={code}, msg={result.get('msg')}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                time.sleep(2)
                    else:
                        log_print(f"[{serial_number}] ✗ 资产列表提交失败: HTTP状态码 {response.status_code}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                except Exception as e:
                    log_print(f"[{serial_number}] ✗ 资产列表提交异常: {str(e)}")
                    if attempt < max_upload_retries - 1:
                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                        time.sleep(2)
            
            if not assets_list_success:
                log_print(f"[{serial_number}] ⚠ 资产列表提交失败，已达到最大重试次数，继续执行后续接口")
        else:
            log_print(f"[{serial_number}] ℹ 无资产数据，跳过资产列表提交")
        
        # 1. 提交持仓列表数据（使用新的 V2 接口）
        positions_success = False
        for attempt in range(max_upload_retries):
            try:
                log_print(f"[{serial_number}] 正在提交持仓列表 V2 (共 {len(positions_data)} 条)... (尝试 {attempt + 1}/{max_upload_retries})")
                
                position_list = []
                for pos in positions_data:
                    # 处理 liquidPrice：如果是 '–' 符号，传 -1
                    liquid_price_raw = pos.get('index20', '').strip()
                    if liquid_price_raw == '–' or liquid_price_raw == '—':
                        liquid_price = '-1'
                    else:
                        liquid_price = liquid_price_raw.replace(',', '')
                    
                    position_list.append({
                        "no": user_no,
                        "currency": pos.get('index0', ''),
                        "qty": pos.get('index8', '').replace(',', ''),
                        "openPrice": pos.get('index10', '').replace(',', ''),
                        "liquidPrice": liquid_price,
                        "time": int(time.time() * 1000),
                        "c": pos.get('index13', '').replace(',', ''),
                        "d": data.get('availableBalanceNumber', ''),
                        "e": data.get('accountEquityNumber', '').replace(',', '')
                    })
                
                # 构建新的请求数据格式
                request_data = {
                    "balance": balance_list,
                    "position": position_list
                }
                
                log_print(f"[{serial_number}] 提交数据: balance数={len(balance_list)}, position数={len(position_list)}")
                
                response = requests.post(
                    f"{API_BASE_URL}/insertPositionListV2",
                    json=request_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    code = result.get('code')
                    
                    if code == 0:
                        log_print(f"[{serial_number}] ✓ 持仓列表 V2 提交成功 (code=0)")
                        positions_success = True
                        break
                    else:
                        log_print(f"[{serial_number}] ✗ 持仓列表 V2 提交失败: code={code}, msg={result.get('msg')}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                else:
                    log_print(f"[{serial_number}] ✗ 持仓列表 V2 提交失败: HTTP状态码 {response.status_code}")
                    if attempt < max_upload_retries - 1:
                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                        time.sleep(2)
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 持仓列表 V2 提交异常: {str(e)}")
                if attempt < max_upload_retries - 1:
                    log_print(f"[{serial_number}] 等待 2 秒后重试...")
                    time.sleep(2)
        
        if not positions_success:
            log_print(f"[{serial_number}] ✗ 持仓列表提交失败")
        
        # 2. 更新账户配置（只更新c和d字段）
        config_success = False
        for attempt in range(max_upload_retries):
            try:
                log_print(f"[{serial_number}] 正在更新账户配置（c、d、balance字段）... (尝试 {attempt + 1}/{max_upload_retries})")
                
                # 计算BTC和ETH持仓量
                btc_qty = '0'
                eth_qty = '0'
                
                if positions_data:
                    for pos in positions_data:
                        currency = pos.get('index0', '').upper()
                        qty = pos.get('index8', '').replace(',', '')
                        if 'BTC' in currency:
                            btc_qty = qty
                        if 'ETH' in currency:
                            eth_qty = qty
                
                # 先获取现有配置
                response = requests.get(
                    f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    existing_data = response.json()
                    # 更新配置（只更新c和d）
                    updated_config = existing_data.get('data', {})
                    updated_config.update({
                        "fingerprintNo": user_no,
                        "c": btc_qty,
                        "d": eth_qty,
                        "balance": data.get('accountEquityNumber', '').replace(',', ''),
                    })
                    
                    # 提交更新
                    response = requests.post(
                        f"{API_BASE_URL}/addAccountConfig",
                        json=updated_config,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        code = result.get('code')
                        
                        if code == 0:
                            log_print(f"[{serial_number}] ✓ 账户配置更新成功（c、d、balance字段） (code=0)")
                            config_success = True
                            break
                        else:
                            log_print(f"[{serial_number}] ✗ 账户配置更新失败: code={code}, msg={result.get('msg')}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                time.sleep(2)
                    else:
                        log_print(f"[{serial_number}] ✗ 账户配置更新失败: HTTP状态码 {response.status_code}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                else:
                    log_print(f"[{serial_number}] ✗ 获取现有配置失败: HTTP状态码 {response.status_code}")
                    if attempt < max_upload_retries - 1:
                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                        time.sleep(2)
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 账户配置更新异常: {str(e)}")
                if attempt < max_upload_retries - 1:
                    log_print(f"[{serial_number}] 等待 2 秒后重试...")
                    time.sleep(2)
        
        # 无论成功与否，都返回失败（按用户要求）
        log_print(f"[{serial_number}] ⚠ 特殊情况处理完成，返回失败状态")
        return False, "权益为0但有持仓数据"
        
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 特殊情况处理异常: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False, "特殊情况处理异常"

def extract_currency_name(raw_text):
    """
    从资产子节点的第一个值中提取币种名称
    
    例如:
        "USDFAPY up to 7.60%" -> "USDF"
        "ASBNBAPY 11.94%" -> "ASBNB"
        "USDF年收益率高达7.50%" -> "USDF"
        "USDT" -> "USDT"
    
    Args:
        raw_text: 原始文本
        
    Returns:
        str: 提取的币种名称
    """
    if not raw_text:
        return ''
    
    # 优先处理中文格式：移除 "年收益" 及其后面的所有内容
    if '年收益' in raw_text:
        currency = raw_text.split('年收益')[0].strip()
    # 处理英文格式：移除 "APY" 及其后面的所有内容
    elif 'APY' in raw_text:
        currency = raw_text.split('APY')[0].strip()
    else:
        currency = raw_text.strip()
    
    return currency

def upload_collected_data(data, user_no, serial_number,assets_data):
    """
    上传采集的数据到服务器，每个接口失败后会重试1次
    
    Args:
        data: 采集的数据
        user_no: 用户编号
        serial_number: 浏览器序列号（用于日志）
        
    Returns:
        tuple: (success, failure_reason) - (是否成功, 失败原因)
    """
    API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
    
    # 每个接口最多尝试2次
    max_upload_retries = 2
    
    # 判断权益和仓位数量
    equity_value_str = data.get('accountEquityNumber', '0').replace(',', '')
    try:
        equity_value = float(equity_value_str) if equity_value_str else 0
    except ValueError:
        equity_value = 0
    
    positions_data = data.get('positionsData', [])
    positions_count = len(positions_data)
    
    log_print(f"[{serial_number}] 数据上传条件判断: 权益={equity_value}, 仓位数量={positions_count}")
    
    # 特殊情况判断
    # 情况1: 权益=0 且 仓位数量>0
    if equity_value == 0 and positions_count > 0:
        log_print(f"[{serial_number}] ⚠ 特殊情况: 权益=0但有持仓数据，提交资产列表、持仓列表和部分配置更新")
        return handle_zero_equity_with_positions(data, user_no, serial_number, API_BASE_URL, max_upload_retries, assets_data)
    
    
    # 情况3: 权益=0 且 仓位=0，以及其他情况，执行正常逻辑
    log_print(f"[{serial_number}] ℹ 执行正常上传流程")
    
    # 在外层定义 assets_list，以便在后续的持仓提交中使用
    assets_list = []
    
    try:
       # 0. 提交所有资产子节点数据 (allAssetsChildren)
        all_assets_children = assets_data
        if all_assets_children and len(all_assets_children) > 0:
            assets_list_success = False
            for attempt in range(max_upload_retries):
                try:
                    log_print(f"[{serial_number}] 正在提交资产列表数据 (共 {len(all_assets_children)} 个币种)... (尝试 {attempt + 1}/{max_upload_retries})")
                    
                    # 构建资产列表（在外层变量中）
                    assets_list = []
                    for child_data in all_assets_children:
                        texts = child_data.get('texts', [])
                        if texts and len(texts) >= 3:
                            # 提取币种名称（去除APY等后缀）
                            raw_currency = texts[0]
                            currency = extract_currency_name(raw_currency)
                            
                            # 第二个值是 balance，第三个值是 unPnl
                            balance = texts[1] if len(texts) > 1 else '0'
                            un_pnl = texts[2] if len(texts) > 2 else '0'
                            
                            # 处理 balance：替换逗号，如果是 "--" 则替换为 "0"
                            balance = balance.replace(',', '')
                            if balance == '--' or balance == '–' or balance == '—':
                                balance = '0'
                            
                            # 处理 unPnl：替换逗号，如果是 "--" 则替换为 "0"
                            un_pnl = un_pnl.replace(',', '')
                            if un_pnl == '--' or un_pnl == '–' or un_pnl == '—':
                                un_pnl = '0'
                            
                            assets_list.append({
                                "currency": currency,
                                "balance": balance,
                                "unPnl": un_pnl
                            })
                    
                    # 特殊处理：如果 equity_value == 0，使用 USDT 的 balance 更新 accountEquityNumber
                    if equity_value == 0:
                        usdt_balance = None
                        for asset in assets_list:
                            if asset.get('currency', '').upper() == 'USDT':
                                usdt_balance = asset.get('balance', '0')
                                break
                        
                        if usdt_balance is not None:
                            log_print(f"[{serial_number}] ⚠ equity_value=0，使用 USDT balance 更新 accountEquityNumber: {usdt_balance}")
                            data['accountEquityNumber'] = usdt_balance
                        else:
                            log_print(f"[{serial_number}] ⚠ equity_value=0 但未找到 USDT 资产")
                    
                    # 构建最终请求数据
                    assets_request_data = {
                        "number": user_no,
                        "list": assets_list
                    }
                    
                    log_print(f"[{serial_number}] 资产列表数据: {assets_request_data}")
                    
                    response = requests.post(
                        f"https://sg.bicoin.com.cn/99j/bro/balance",  # 临时占位URL
                        json=assets_request_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        code = result.get('code')
                        
                        if code == 0:
                            log_print(f"[{serial_number}] ✓ 资产列表提交成功 (code=0)")
                            assets_list_success = True
                            break
                        else:
                            log_print(f"[{serial_number}] ✗ 资产列表提交失败: code={code}, msg={result.get('msg')}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                time.sleep(2)
                    else:
                        log_print(f"[{serial_number}] ✗ 资产列表提交失败: HTTP状态码 {response.status_code}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                except Exception as e:
                    log_print(f"[{serial_number}] ✗ 资产列表提交异常: {str(e)}")
                    if attempt < max_upload_retries - 1:
                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                        time.sleep(2)
            
            if not assets_list_success:
                log_print(f"[{serial_number}] ⚠ 资产列表提交失败，已达到最大重试次数，继续执行后续接口")
        else:
            log_print(f"[{serial_number}] ℹ 无 allAssetsChildren 数据，跳过资产列表提交")
        
        # 2. 提交持仓列表数据
        positions_success = True  # 如果没有持仓数据，默认成功
        positions_data = data.get('positionsData', [])
        
        # 判断是否需要上传"无仓位"假数据
        # 条件：保证金为0 且 持仓数量为0
        margin_value = data.get('marginNumber', '0').replace(',', '')
        try:
            margin_float = float(margin_value) if margin_value else 0.0
        except ValueError:
            margin_float = 0.0
        
        should_upload_empty = (margin_float == 0.0 and (not positions_data or len(positions_data) == 0))
        
        if should_upload_empty:
            log_print(f"[{serial_number}] 检测到保证金为0且无持仓，将上传'无仓位'假数据")
        
        if (positions_data and len(positions_data) > 0) or should_upload_empty:
            positions_success = False
            for attempt in range(max_upload_retries):
                try:
                    if should_upload_empty:
                        log_print(f"[{serial_number}] 正在提交'无仓位'假数据 V2... (尝试 {attempt + 1}/{max_upload_retries})")
                    else:
                        log_print(f"[{serial_number}] 正在提交持仓列表 V2 (共 {len(positions_data)} 条)... (尝试 {attempt + 1}/{max_upload_retries})")
                    
                    position_list = []
                    
                    if should_upload_empty:
                        # 上传"无仓位"假数据
                        position_list.append({
                            "no": user_no,
                            "currency": "无仓位",
                            "qty": "0",
                            "openPrice": "0",
                            "liquidPrice": "0",
                            "time": int(time.time() * 1000),
                            "c": "0",
                            "d": data.get('availableBalanceNumber', ''),
                            "e":  data.get('accountEquityNumber', '').replace(',', '')
                            
                        })
                    else:
                        # 正常上传持仓数据
                        for pos in positions_data:
                            # 处理 liquidPrice：如果是 '–' 符号，传 -1
                            liquid_price_raw = pos.get('index20', '').strip()
                            if liquid_price_raw == '–' or liquid_price_raw == '—':
                                liquid_price = '-1'
                            else:
                                liquid_price = liquid_price_raw.replace(',', '')
                            
                            position_list.append({
                                "no": user_no,
                                "currency": pos.get('index0', ''),
                                "qty": pos.get('index8', '').replace(',', ''),
                                "openPrice": pos.get('index10', '').replace(',', ''),
                                "liquidPrice": liquid_price,
                                "time": int(time.time() * 1000),
                                "c": pos.get('index13', '').replace(',', ''),
                                "d": data.get('availableBalanceNumber', ''),
                                "e":  data.get('accountEquityNumber', '').replace(',', '')
                            })
                    
                    # 构建新的请求数据格式（V2）
                    request_data = {
                        "balance": assets_list,
                        "position": position_list
                    }
                    
                    log_print(f"[{serial_number}] 提交数据 V2: balance数={len(assets_list)}, position数={len(position_list)}")
                    
                    response = requests.post(
                        f"{API_BASE_URL}/insertPositionListV2",
                        json=request_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        code = result.get('code')
                        
                        if code == 0:
                            log_print(f"[{serial_number}] ✓ 持仓列表 V2 提交成功 (code=0)")
                            positions_success = True
                            break
                        else:
                            log_print(f"[{serial_number}] ✗ 持仓列表 V2 提交失败: code={code}, msg={result.get('msg')}")
                            log_print(f"[{serial_number}] 提交的数据: {request_data}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                time.sleep(2)
                    else:
                        log_print(f"[{serial_number}] ✗ 持仓列表 V2 提交失败: HTTP状态码 {response.status_code}")
                        log_print(f"[{serial_number}] 提交的数据: {request_data}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                except Exception as e:
                    log_print(f"[{serial_number}] ✗ 持仓列表 V2 提交异常: {str(e)}")
                    log_print(f"[{serial_number}] 提交的数据: {request_data}")
                    if attempt < max_upload_retries - 1:
                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                        time.sleep(2)
            
            if not positions_success:
                log_print(f"[{serial_number}] ⚠ 持仓列表提交失败，已达到最大重试次数，继续执行后续接口")
        else:
            log_print(f"[{serial_number}] ℹ 无持仓数据，跳过持仓列表提交")
        
        # 3. 更新账户配置数据（最终判断任务成功与否的关键接口）
        config_success = False
        for attempt in range(max_upload_retries):
            try:
                log_print(f"[{serial_number}] 正在更新账户配置... (尝试 {attempt + 1}/{max_upload_retries})")
                
                # 计算BTC、ETH和SOL持仓量
                btc_qty = '0' if data.get('positionsButtonFound') else None
                eth_qty = '0' if data.get('positionsButtonFound') else None
                sol_qty = '0' if data.get('positionsButtonFound') else None
                
                if data.get('positionsButtonFound') and positions_data:
                    for pos in positions_data:
                        currency = pos.get('index0', '').upper()
                        qty = pos.get('index8', '').replace(',', '')
                        if 'BTC' in currency:
                            btc_qty = qty
                        if 'ETH' in currency:
                            eth_qty = qty
                        if 'SOL' in currency:
                            sol_qty = qty
                
                # 先获取现有配置
                response = requests.get(
                    f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                log_print(f"[{serial_number}] 正在更新账户配置... (btc {btc_qty}   eth {eth_qty}   sol {sol_qty})")
                if response.status_code == 200:
                    existing_data = response.json()
                      # 获取权益值
                    equity_value = data.get('accountEquityNumber', '').replace(',', '')
                    # 更新配置
                    updated_config = existing_data.get('data', {})
                    updated_config.update({
                        "fingerprintNo": user_no,
                        "c": btc_qty,
                        "d": eth_qty,
                        "sol": sol_qty,
                        "balance": data.get('accountEquityNumber', '').replace(',', ''),
                        "available": data.get('availableBalanceNumber', '').replace(',', ''),
                        "totalVolume": equity_value,
                        "f": int(time.time()),  # 当前时间戳
                    })
                    
                    # 提交更新
                    response = requests.post(
                        f"{API_BASE_URL}/addAccountConfig",
                        json=updated_config,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        code = result.get('code')
                        
                        if code == 0:
                            log_print(f"[{serial_number}] ✓ 账户配置更新成功 (code=0)")
                            config_success = True
                            break
                        else:
                            log_print(f"[{serial_number}] ✗ 账户配置更新失败: code={code}, msg={result.get('msg')}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                time.sleep(2)
                    else:
                        log_print(f"[{serial_number}] ✗ 账户配置更新失败: HTTP状态码 {response.status_code}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                else:
                    log_print(f"[{serial_number}] ✗ 获取现有配置失败: HTTP状态码 {response.status_code}")
                    if attempt < max_upload_retries - 1:
                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                        time.sleep(2)
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 账户配置更新异常: {str(e)}")
                if attempt < max_upload_retries - 1:
                    log_print(f"[{serial_number}] 等待 2 秒后重试...")
                    time.sleep(2)
        
        if not config_success:
            log_print(f"[{serial_number}] ✗✗✗ 账户配置更新失败，已达到最大重试次数，任务失败")
            return False, "账户配置更新失败"
        
        # addAccountConfig 接口成功，任务成功
        log_print(f"[{serial_number}] ✓✓✓ 账户配置更新成功，任务完成！")
        return True, ""
            
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 上传数据时发生错误: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False, "数据上传异常"


def open_new_tab_with_url(driver, url, serial_number):
    """
    使用 Selenium 4 的 switch_to.new_window 打开新标签页
    
    Args:
        driver: Selenium WebDriver
        url: 要打开的URL
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    original_window = driver.current_window_handle
    original_count = len(driver.window_handles)
    
    try:
        log_print(f"[{serial_number}] 打开新标签页: {url}")
        driver.switch_to.new_window('tab')
        driver.get(url)
        time.sleep(1)
        if len(driver.window_handles) > original_count:
            log_print(f"[{serial_number}] ✓ 新标签页打开成功")
            return True
        else:
            log_print(f"[{serial_number}] ✗ 新标签页打开失败")
            return False
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 打开新标签页失败: {str(e)}")
        try:
            driver.switch_to.window(original_window)
        except:
            pass
        return False


def check_and_unlock_wallet(driver, serial_number, password):
    """
    检查OKX钱包是否需要解锁，如果需要则输入密码解锁
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        password: 钱包密码
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        log_print(f"[{serial_number}] 检查钱包是否需要解锁...")
        
       
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
                    log_print(f"[{serial_number}] ✓ 已输入密码（React 方式）: {password}")
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
            
            # 在5秒内找到并等待解锁按钮变为可点击 (去掉 disabled 属性)
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


def handle_wallet_connection_and_signature(driver, serial_number, password,timecount):
    """
    处理钱包连接和签名的完整流程
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        password: OKX钱包密码
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        log_print(f"[{serial_number}] ========================================")
        log_print(f"[{serial_number}] 开始钱包连接和签名流程")
        log_print(f"[{serial_number}] ========================================")
        
        # 保存主窗口句柄
        main_window = driver.current_window_handle
        log_print(f"[{serial_number}] 已保存主窗口句柄: {main_window}")
        
        # ==================== 预处理: 打开 OKX 钱包页面 ====================
        log_print(f"[{serial_number}] ")
        log_print(f"[{serial_number}] [预处理] 预先打开 OKX 钱包页面...")
        
        okx_extension_id = "mcohilncbfahbmgdjkbpemcciiolgcge"
        okx_popup_url = f"chrome-extension://{okx_extension_id}/popup.html"
        if timecount == 1:
            try:
                # 使用 open_new_tab_with_url 方法打开 OKX 钱包
                log_print(f"[{serial_number}] → 使用 open_new_tab_with_url 打开 OKX 钱包...")
                success = open_new_tab_with_url(driver, okx_popup_url, serial_number)
                
                if success:
                    log_print(f"[{serial_number}] ✓ OKX 钱包页面已打开")
                else:
                    log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包失败，继续执行...")
                    time.sleep(3)
                    
                   # 切换回主窗口
                log_print(f"[{serial_number}] → 切换回主窗口: {main_window}")
                driver.switch_to.window(main_window)
                log_print(f"[{serial_number}] ✓ 已切换回主窗口")
                
                # 等待1秒
                log_print(f"[{serial_number}] → 等待 1 秒...")
                time.sleep(1)
                    
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包异常: {str(e)}，继续执行...")
            
        # ==================== 步骤1: 检查 Aster key ====================
        log_print(f"[{serial_number}] ")
        log_print(f"[{serial_number}] [步骤1] 检查是否需要获取 Aster key...")
        log_print(f"[{serial_number}] 查找元素(5秒内): //h4[contains(text(), 'Get your Aster key') or contains(text(), '获取您的Aster密钥')]")
        
        try:
            aster_key_h4 = WebDriverWait(driver, 8).until(
                EC.presence_of_all_elements_located((By.XPATH, "//h4[contains(text(), 'Get your Aster key') or contains(text(), '获取您的Aster密钥')]"))
            )
            log_print(f"[{serial_number}] 查找结果: 找到 {len(aster_key_h4)} 个 Aster key 元素")
        except TimeoutException:
            aster_key_h4 = []
            log_print(f"[{serial_number}] 查找结果: 5秒内未找到 Aster key 元素")
        
        if aster_key_h4:
            log_print(f"[{serial_number}] ✓ 发现 Aster key 提示")
            log_print(f"[{serial_number}] → 准备发送请求并授权...")
            # 点击 Send request 按钮
            if not click_send_request_and_authorize(driver, serial_number, password, main_window):
                log_print(f"[{serial_number}] ✗ Send request 流程失败")
                return False
            log_print(f"[{serial_number}] ✓ Send request 流程完成")
        else:
            log_print(f"[{serial_number}] ✗ 未找到 Aster key 元素")
            
            # ==================== 步骤2: 检查启用交易 ====================
            log_print(f"[{serial_number}] ")
            log_print(f"[{serial_number}] [步骤2] 检查是否需要启用交易...")
            log_print(f"[{serial_number}] 查找元素(5秒内): //button[contains(text(), '启用交易') or contains(text(), 'Enable Trading')]")
            
            try:
                enable_trading_btn = WebDriverWait(driver, 8).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), '启用交易') or contains(text(), 'Enable Trading')]"))
                )
                log_print(f"[{serial_number}] 查找结果: 找到 {len(enable_trading_btn)} 个启用交易按钮")
            except TimeoutException:
                enable_trading_btn = []
                log_print(f"[{serial_number}] 查找结果: 5秒内未找到启用交易按钮")
            
            if enable_trading_btn:
                log_print(f"[{serial_number}] ✓ 发现启用交易按钮")
                log_print(f"[{serial_number}] → 点击启用交易按钮...")
                enable_trading_btn[0].click()
                log_print(f"[{serial_number}] ✓ 已点击启用交易按钮")
                
                log_print(f"[{serial_number}] → 等待 2 秒...")
                time.sleep(2)
                log_print(f"[{serial_number}] ✓ 等待完成")
                
                # 查找包含"连接"或"Connect"的按钮
                log_print(f"[{serial_number}] → 查找包含 '连接' 或 'Connect' 的按钮(5秒内)...")
                try:
                    connect_buttons = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), '连接') or contains(text(), 'Connect')]"))
                    )
                    log_print(f"[{serial_number}] 查找结果: 找到 {len(connect_buttons)} 个连接按钮")
                except TimeoutException:
                    connect_buttons = []
                    log_print(f"[{serial_number}] 查找结果: 5秒内未找到连接按钮")
                
                if connect_buttons:
                    log_print(f"[{serial_number}] ✓ 发现连接按钮")
                    log_print(f"[{serial_number}] → 点击连接按钮...")
                    connect_buttons[0].click()
                    log_print(f"[{serial_number}] ✓ 已点击连接按钮")
                    
                    log_print(f"[{serial_number}] → 等待 2 秒...")
                    time.sleep(2)
                    log_print(f"[{serial_number}] ✓ 等待完成")
                    
                    # 切换到 OKX 钱包并授权
                    log_print(f"[{serial_number}] → 切换到 OKX 钱包进行授权...")
                    authorize_okx_wallet(driver, serial_number, password)
                    
                    # 切换回主窗口
                    log_print(f"[{serial_number}] → 等待 3 秒后切换回主窗口...")
                    time.sleep(3)
                    driver.switch_to.window(main_window)
                    log_print(f"[{serial_number}] ✓ 已切换回主窗口")
                else:
                    log_print(f"[{serial_number}] ⚠ 点击启用交易后未找到连接按钮")
            else:
                log_print(f"[{serial_number}] ✗ 未找到启用交易按钮")
                
                # ==================== 步骤3: 检查连接钱包 ====================
                log_print(f"[{serial_number}] ")
                log_print(f"[{serial_number}] [步骤3] 检查是否需要连接钱包...")
                log_print(f"[{serial_number}] 查找元素(5秒内): button[aria-label='连接钱包'] 或 button[aria-label='Connect wallet']")
                
                try:
                    connect_wallet_btn = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[aria-label='连接钱包'], button[aria-label='Connect wallet']"))
                    )
                    log_print(f"[{serial_number}] 查找结果: 找到 {len(connect_wallet_btn)} 个连接钱包按钮")
                except TimeoutException:
                    connect_wallet_btn = []
                    log_print(f"[{serial_number}] 查找结果: 5秒内未找到连接钱包按钮")
                
                if connect_wallet_btn:
                    log_print(f"[{serial_number}] ✓ 发现连接钱包按钮")
                    log_print(f"[{serial_number}] → 开始连接钱包流程...")
                    
                    # 切换语言到英文
                    log_print(f"[{serial_number}] → 执行语言切换...")
                    switch_language_to_english(driver, serial_number)
                    log_print(f"[{serial_number}] ✓ 语言切换完成")
                    
                    # 点击 Connect wallet
                    try:
                        log_print(f"[{serial_number}] → 等待 Connect wallet 按钮可点击(5秒内)...")
                        connect_button = WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Connect wallet']"))
                        )
                        log_print(f"[{serial_number}] → 点击 Connect wallet 按钮...")
                        connect_button.click()
                        log_print(f"[{serial_number}] ✓ 已点击 Connect wallet 按钮")
                        
                        log_print(f"[{serial_number}] → 等待 2 秒...")
                        time.sleep(2)
                        log_print(f"[{serial_number}] ✓ 等待完成")
                        
                        # 选择 OKX Wallet
                        log_print(f"[{serial_number}] → 查找 OKX Wallet 选项...")
                        okx_elements = WebDriverWait(driver, 15).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), 'OKX Wallet')]"))
                        )
                        log_print(f"[{serial_number}] 查找结果: 找到 {len(okx_elements)} 个 OKX Wallet 元素")
                        
                        if okx_elements:
                            log_print(f"[{serial_number}] → 点击 OKX Wallet...")
                            parent = okx_elements[0].find_element(By.XPATH, "./..")
                            parent.click()
                            log_print(f"[{serial_number}] ✓ 已选择 OKX Wallet")
                            
                            # 切换到 OKX 标签页并授权
                            log_print(f"[{serial_number}] → 执行 OKX 授权流程...")
                            authorize_okx_wallet(driver, serial_number, password)
                            log_print(f"[{serial_number}] ✓ OKX 授权流程完成")
                            
                            # 切换回主窗口
                            log_print(f"[{serial_number}] → 切换回主窗口...")
                            driver.switch_to.window(main_window)
                            log_print(f"[{serial_number}] ✓ 已切换回主窗口")
                            
                            log_print(f"[{serial_number}] → 等待 2 秒...")
                            time.sleep(2)
                            log_print(f"[{serial_number}] ✓ 等待完成")
                            
                            # 检查是否有 Aster key 提示
                            log_print(f"[{serial_number}] → 检查是否出现 Aster key 提示(5秒内)...")
                            try:
                                aster_key_h4 = WebDriverWait(driver, 5).until(
                                    EC.presence_of_all_elements_located((By.XPATH, "//h4[contains(text(), 'Get your Aster key') or contains(text(), '获取您的Aster密钥')]"))
                                )
                                log_print(f"[{serial_number}] 查找结果: 找到 {len(aster_key_h4)} 个 Aster key 元素")
                            except TimeoutException:
                                aster_key_h4 = []
                                log_print(f"[{serial_number}] 查找结果: 5秒内未找到 Aster key 元素")
                            
                            if aster_key_h4:
                                log_print(f"[{serial_number}] ✓ 发现 Aster key 提示")
                                log_print(f"[{serial_number}] → 准备发送请求并授权...")
                                if not click_send_request_and_authorize(driver, serial_number, password, main_window):
                                    log_print(f"[{serial_number}] ✗ Send request 流程失败")
                                    return False
                                log_print(f"[{serial_number}] ✓ Send request 流程完成")
                            else:
                                log_print(f"[{serial_number}] ℹ 连接钱包后未出现 Aster key 提示")
                        else:
                            log_print(f"[{serial_number}] ✗ 未找到 OKX Wallet 元素")
                            
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 连接钱包流程出错: {str(e)}")
                        return False
                else:
                    log_print(f"[{serial_number}] ✗ 未找到连接钱包按钮")
                    log_print(f"[{serial_number}] ℹ 未发现需要处理的钱包连接或签名元素")
        
        
        # ==================== 额外检查: 启用交易按钮 ====================
        log_print(f"[{serial_number}] ")
        log_print(f"[{serial_number}] [额外检查] 再次检查启用交易按钮...")
        log_print(f"[{serial_number}] 查找元素(5秒内): //button[contains(text(), '启用交易') or contains(text(), 'Enable Trading')]")
        time.sleep(10)
        try:
            enable_trading_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), '启用交易') or contains(text(), 'Enable Trading')]"))
            )
            log_print(f"[{serial_number}] 查找结果: 找到 {len(enable_trading_btn)} 个启用交易按钮")
        except TimeoutException:
            enable_trading_btn = []
            log_print(f"[{serial_number}] 查找结果: 5秒内未找到启用交易按钮")
            
        if enable_trading_btn:
                log_print(f"[{serial_number}] ✓ 发现启用交易按钮")
                log_print(f"[{serial_number}] → 点击启用交易按钮...")
                enable_trading_btn[0].click()
                log_print(f"[{serial_number}] ✓ 已点击启用交易按钮")
                
                log_print(f"[{serial_number}] → 等待 2 秒...")
                time.sleep(2)
                log_print(f"[{serial_number}] ✓ 等待完成")
                
                # 查找包含"连接"或"Connect"的按钮
                log_print(f"[{serial_number}] → 查找包含 '连接' 或 'Connect' 的按钮(5秒内)...")
                try:
                    connect_buttons = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), '连接') or contains(text(), 'Connect')]"))
                    )
                    log_print(f"[{serial_number}] 查找结果: 找到 {len(connect_buttons)} 个连接按钮")
                except TimeoutException:
                    connect_buttons = []
                    log_print(f"[{serial_number}] 查找结果: 5秒内未找到连接按钮")
                
                if connect_buttons:
                    log_print(f"[{serial_number}] ✓ 发现连接按钮")
                    log_print(f"[{serial_number}] → 点击连接按钮...")
                    connect_buttons[0].click()
                    log_print(f"[{serial_number}] ✓ 已点击连接按钮")
                    
                    log_print(f"[{serial_number}] → 等待 2 秒...")
                    time.sleep(2)
                    log_print(f"[{serial_number}] ✓ 等待完成")
                    
                    # 切换到 OKX 钱包并授权
                    log_print(f"[{serial_number}] → 切换到 OKX 钱包进行授权...")
                    authorize_okx_wallet(driver, serial_number, password)
                    
                    # 切换回主窗口
                    log_print(f"[{serial_number}] → 等待 3 秒后切换回主窗口...")
                    time.sleep(3)
                    driver.switch_to.window(main_window)
                    log_print(f"[{serial_number}] ✓ 已切换回主窗口")
                else:
                    log_print(f"[{serial_number}] ⚠ 点击启用交易后未找到连接按钮")
                    
                    
        log_print(f"[{serial_number}] ")
        log_print(f"[{serial_number}] ========================================")
        log_print(f"[{serial_number}] ✓ 钱包连接和签名流程完成")
        log_print(f"[{serial_number}] ========================================")
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] ")
        log_print(f"[{serial_number}] ========================================")
        log_print(f"[{serial_number}] ✗ 钱包连接和签名流程失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        log_print(f"[{serial_number}] ========================================")
        return False


def click_send_request_and_authorize(driver, serial_number, password, main_window):
    """
    点击 Send request 按钮并完成 OKX 授权
    """
    try:
        log_print(f"[{serial_number}]   → [子流程] 开始 Send request 授权...")
        
        # 点击 Send request 按钮
        log_print(f"[{serial_number}]   → 查找 Send request 按钮...")
        send_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Send request') or contains(text(), '发送请求')]")
        log_print(f"[{serial_number}]   → 查找结果: 找到 {len(send_buttons)} 个按钮")
        
        if send_buttons:
            log_print(f"[{serial_number}]   → 点击 Send request 按钮...")
            send_buttons[0].click()
            log_print(f"[{serial_number}]   ✓ 已点击 Send request 按钮")
            
            log_print(f"[{serial_number}]   → 等待 3 秒...")
            time.sleep(3)
            log_print(f"[{serial_number}]   ✓ 等待完成")
            
            # 切换到 OKX 标签页并授权
            log_print(f"[{serial_number}]   → 调用 OKX 授权...")
            authorize_okx_wallet(driver, serial_number, password)
            log_print(f"[{serial_number}]   ✓ OKX 授权完成")
            
            # 切换回主窗口
            log_print(f"[{serial_number}]   → 切换回主窗口 {main_window}...")
            driver.switch_to.window(main_window)
            log_print(f"[{serial_number}]   ✓ 已切换回主窗口")
            
            log_print(f"[{serial_number}]   → 等待 2 秒...")
            time.sleep(2)
            log_print(f"[{serial_number}]   ✓ 等待完成")
            
            log_print(f"[{serial_number}]   ✓ [子流程] Send request 授权成功")
            return True
        else:
            log_print(f"[{serial_number}]   ✗ 未找到 Send request 按钮")
            return False
    except Exception as e:
        log_print(f"[{serial_number}]   ✗ Send request 流程失败: {str(e)}")
        return False


def authorize_okx_wallet(driver, serial_number, password):
    """
    切换到 OKX 标签页，解锁并授权
    """
    try:
        log_print(f"[{serial_number}]     → [子流程] 开始 OKX 钱包授权...")
        
        # OKX 钱包扩展ID
        okx_extension_id = "mcohilncbfahbmgdjkbpemcciiolgcge"
        
        # 方式1: 先尝试查找已有的钱包标签页（最多尝试3次，每次等待1秒）
        log_print(f"[{serial_number}]     → 方式1: 查找现有 OKX 钱包标签页...")
        wallet_window = None
        
        for i in range(3):
            log_print(f"[{serial_number}]     → 第 {i+1}/3 次尝试查找...")
            time.sleep(1)
            
            all_handles = driver.window_handles
            log_print(f"[{serial_number}]     → 当前共有 {len(all_handles)} 个窗口")
            
            for idx, handle in enumerate(all_handles):
                driver.switch_to.window(handle)
                current_url = driver.current_url
                log_print(f"[{serial_number}]     → 检查窗口 {idx+1}: {current_url[:80]}...")
                
                if okx_extension_id in current_url:
                    wallet_window = handle
                    log_print(f"[{serial_number}]     ✓ 找到 OKX 钱包标签页！")
                    break
            
            if wallet_window:
                break
        
        # 方式2: 如果没找到，直接在新标签页打开钱包扩展
        if not wallet_window:
            log_print(f"[{serial_number}]     ℹ 未找到现有标签页，使用方式2: 直接打开钱包扩展...")
            
            # 保存当前窗口数量
            original_handles_count = len(driver.window_handles)
            log_print(f"[{serial_number}]     → 当前窗口数: {original_handles_count}")
            
            # 尝试多个可能的 OKX 钱包页面 URL
            wallet_urls = [
                f"chrome-extension://{okx_extension_id}/notification.html",
                f"chrome-extension://{okx_extension_id}/popup.html",
                f"chrome-extension://{okx_extension_id}/home.html"
            ]
            
            for url in wallet_urls:
                try:
                    log_print(f"[{serial_number}]     → 尝试打开: {url}")
                    
                    # 打开新标签页
                    driver.execute_script(f"window.open('{url}', '_blank');")
                    time.sleep(2)
                    
                    # 切换到新标签页
                    new_handles = driver.window_handles
                    if len(new_handles) > original_handles_count:
                        wallet_window = new_handles[-1]
                        driver.switch_to.window(wallet_window)
                        current_url = driver.current_url
                        log_print(f"[{serial_number}]     → 已打开新标签页: {current_url}")
                        
                        # 检查页面是否有效（是否有授权按钮或密码输入框）
                        time.sleep(1)
                        has_password_input = len(driver.find_elements(By.CSS_SELECTOR, "input[type='password']")) > 0
                        has_okd_button = len(driver.find_elements(By.CSS_SELECTOR, "button[data-testid='okd-button']")) > 0
                        
                        if has_password_input or has_okd_button:
                            log_print(f"[{serial_number}]     ✓ 成功打开 OKX 钱包页面！")
                            break
                        else:
                            log_print(f"[{serial_number}]     ⚠ 此页面无效，尝试下一个 URL...")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            wallet_window = None
                    else:
                        log_print(f"[{serial_number}]     ⚠ 未能打开新标签页")
                        
                except Exception as e:
                    log_print(f"[{serial_number}]     ⚠ 打开 {url} 失败: {str(e)}")
                    continue
        
        # 如果还是没找到钱包窗口
        if not wallet_window:
            log_print(f"[{serial_number}]     ✗ 无法打开 OKX 钱包页面")
            return False
        
        # 执行授权操作
        log_print(f"[{serial_number}]     → 开始执行授权操作...")
        
        # 检查并解锁钱包
        log_print(f"[{serial_number}]     → 检查钱包是否需要解锁...")
        check_and_unlock_wallet(driver, serial_number, password)
        log_print(f"[{serial_number}]     ✓ 钱包解锁检查完成")
        
        # 点击第二个 okd-button
        log_print(f"[{serial_number}]     → 查找授权按钮...")
        okd_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='okd-button']")
        log_print(f"[{serial_number}]     → 找到 {len(okd_buttons)} 个授权按钮")
        
        if len(okd_buttons) >= 2:
            log_print(f"[{serial_number}]     → 点击第二个授权按钮...")
            okd_buttons[1].click()
            log_print(f"[{serial_number}]     ✓ 已点击第二个授权按钮")
            
            log_print(f"[{serial_number}]     → 等待 2 秒...")
            time.sleep(2)
            log_print(f"[{serial_number}]     ✓ 等待完成")
            
            log_print(f"[{serial_number}]     ✓ [子流程] OKX 钱包授权成功")
            return True
        elif len(okd_buttons) == 1:
            log_print(f"[{serial_number}]     → 只找到1个授权按钮，点击第一个...")
            okd_buttons[0].click()
            log_print(f"[{serial_number}]     ✓ 已点击授权按钮")
            
            log_print(f"[{serial_number}]     → 等待 2 秒...")
            time.sleep(2)
            log_print(f"[{serial_number}]     ✓ 等待完成")
            
            log_print(f"[{serial_number}]     ✓ [子流程] OKX 钱包授权成功")
            return True
        else:
            log_print(f"[{serial_number}]     ⚠ 未找到授权按钮")
            return False
            
    except Exception as e:
        log_print(f"[{serial_number}]     ✗ OKX 授权失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}]     错误详情:\n{traceback.format_exc()}")
        return False


def switch_language_to_english(driver, serial_number):
    """
    切换页面语言到英文
    """
    try:
        log_print(f"[{serial_number}]   → [子流程] 开始切换语言到英文...")
        
        # 点击语言选择按钮
        log_print(f"[{serial_number}]   → 查找语言选择按钮: button[id='radix-_r_6_']...")
        lang_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='radix-_r_6_']"))
        )
        log_print(f"[{serial_number}]   → 点击语言选择按钮...")
        lang_button.click()
        log_print(f"[{serial_number}]   ✓ 已点击语言选择按钮")
        
        log_print(f"[{serial_number}]   → 等待 1 秒...")
        time.sleep(1)

        # 点击倒数第二个 menuitem
        log_print(f"[{serial_number}]   → 查找菜单项...")
        menu_items = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='menuitem']"))
        )
        log_print(f"[{serial_number}]   → 找到 {len(menu_items)} 个菜单项")
        
        if len(menu_items) >= 2:
            log_print(f"[{serial_number}]   → 点击倒数第二个菜单项...")
            menu_items[-2].click()
            log_print(f"[{serial_number}]   ✓ 已点击倒数第二个菜单项")
            time.sleep(1)
        else:
            log_print(f"[{serial_number}]   ⚠ 菜单项数量不足")

        # 点击 English 选项
        log_print(f"[{serial_number}]   → 查找 English 选项...")
        english_spans = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[text()='English']"))
        )
        log_print(f"[{serial_number}]   → 找到 {len(english_spans)} 个 English 元素")
        
        if english_spans:
            log_print(f"[{serial_number}]   → 点击 English 选项...")
            grandparent = english_spans[0].find_element(By.XPATH, "../..")
            grandparent.click()
            log_print(f"[{serial_number}]   ✓ 已切换语言到 English")
            time.sleep(1)
        else:
            log_print(f"[{serial_number}]   ⚠ 未找到 English 选项")
        
        log_print(f"[{serial_number}]   ✓ [子流程] 语言切换完成")
            
    except TimeoutException:
        log_print(f"[{serial_number}]   ℹ 语言切换超时，可能已经是英文，继续执行...")
    except Exception as e:
        log_print(f"[{serial_number}]   ⚠ 语言切换失败: {str(e)}，继续执行...")


def check_extension_available(driver, serial_number, password, extension_id="mcohilncbfahbmgdjkbpemcciiolgcge"):
    """
    检查扩展是否可用
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        password: 钱包密码
        extension_id: 扩展ID
        
    Returns:
        bool: 扩展可用返回True，否则返回False
    """
    try:
        log_print(f"[{serial_number}] 检查 OKX 钱包扩展是否可用...")
        
        test_url = f"chrome-extension://{extension_id}/popup.html"
        original_window = driver.current_window_handle
        original_count = len(driver.window_handles)
        
        # 使用新的打开标签页方法
        if not open_new_tab_with_url(driver, test_url, serial_number):
            log_print(f"[{serial_number}] ✗ 无法打开新标签页测试扩展")
            return False
        
        time.sleep(1)
        
        # 检查是否成功打开了新窗口
        if len(driver.window_handles) > original_count:
            # 切换到新窗口检查URL
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    current_url = driver.current_url
                    
                    if extension_id in current_url:
                        log_print(f"[{serial_number}] ✓ OKX 钱包扩展可用")
                        
                        # 检查并解锁钱包
                        check_and_unlock_wallet(driver, serial_number, password)
                        
                        driver.close()
                        driver.switch_to.window(original_window)
                        return True
                    else:
                        log_print(f"[{serial_number}] ✗ 打开的页面URL不正确: {current_url}")
                        driver.close()
                        driver.switch_to.window(original_window)
                        return False
        else:
            log_print(f"[{serial_number}] ✗ 未能打开扩展页面")
            return False
            
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 扩展可用性检查失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False


def process_wallet_swap(driver, serial_number, ref_code, password):
    """
    执行钱包连接和兑换操作 (Type 2)
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        ref_code: 邀请码
        password: 钱包密码
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        wait = WebDriverWait(driver, 10)
        
        # 第一步：打开主页面
        log_print(f"[{serial_number}] 打开主页面: https://www.asterdex.com/en/stage2/team")
        driver.get("https://www.asterdex.com/en/stage2/team")
        time.sleep(3)
        
        # 预检查：验证扩展是否可用
        if not check_extension_available(driver, serial_number, password):
            log_print(f"[{serial_number}] ✗✗✗ OKX 钱包扩展不可用，终止操作")
            log_print(f"[{serial_number}] 请确保：")
            log_print(f"[{serial_number}]   1. OKX 钱包扩展已正确安装")
            log_print(f"[{serial_number}]   2. 扩展未被禁用")
            log_print(f"[{serial_number}]   3. 扩展ID正确: mcohilncbfahbmgdjkbpemcciiolgcge")
            return False
        
        # 保存主窗口句柄
        main_window = driver.current_window_handle
        log_print(f"[{serial_number}] 主窗口句柄: {main_window}")
        
        # 第二步：在新标签页打开钱包扩展
        log_print(f"[{serial_number}] 打开 OKX 钱包扩展")
        extension_url = "chrome-extension://mcohilncbfahbmgdjkbpemcciiolgcge/popup.html"
        
        window_count_before = len(driver.window_handles)
        log_print(f"[{serial_number}] 打开扩展前，窗口数量: {window_count_before}")
        
        # 使用多方法尝试打开新标签页
        if not open_new_tab_with_url(driver, extension_url, serial_number):
            log_print(f"[{serial_number}] ✗✗✗ 无法打开钱包扩展标签页！")
            log_print(f"[{serial_number}] 可能原因：")
            log_print(f"[{serial_number}]   1. OKX 钱包扩展未安装或已禁用")
            log_print(f"[{serial_number}]   2. 扩展ID不正确（当前使用: mcohilncbfahbmgdjkbpemcciiolgcge）")
            log_print(f"[{serial_number}]   3. 浏览器阻止了扩展页面打开")
            log_print(f"[{serial_number}]   4. 扩展没有 popup.html 页面")
            
            # 尝试获取浏览器控制台日志
            try:
                logs = driver.get_log('browser')
                if logs:
                    log_print(f"[{serial_number}] 浏览器控制台日志:")
                    for log in logs[-10:]:  # 只显示最后10条
                        log_print(f"[{serial_number}]   [{log['level']}] {log['message']}")
                else:
                    log_print(f"[{serial_number}] 浏览器控制台无日志")
            except Exception as log_error:
                log_print(f"[{serial_number}] 无法获取浏览器日志: {str(log_error)}")
            
            return False
        
        window_count_after = len(driver.window_handles)
        log_print(f"[{serial_number}] 打开扩展后，窗口数量: {window_count_after}")
        
        # 切换到新标签页
        wallet_window = None
        try:
            for i, handle in enumerate(driver.window_handles):
                driver.switch_to.window(handle)
                current_url = driver.current_url
                log_print(f"[{serial_number}] 窗口 {i}: 句柄={handle}, URL={current_url}")
                
                if handle != main_window:
                    wallet_window = handle
                    log_print(f"[{serial_number}] ✓ 找到新窗口，切换成功")
                    break
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 切换窗口时出错: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
            return False
        
        if not wallet_window:
            log_print(f"[{serial_number}] ✗ 无法打开钱包扩展标签页")
            log_print(f"[{serial_number}] 所有窗口句柄: {driver.window_handles}")
            return False
        
        # 检查并解锁钱包
        check_and_unlock_wallet(driver, serial_number, password)
        
        # 第三步：检查余额
        log_print(f"[{serial_number}] 检查钱包余额...")
        log_print(f"[{serial_number}] 当前页面URL: {driver.current_url}")
        try:
            balance_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='_balance_150zi_1']"))
            )
            balance_text = balance_div.text  # 例如："$109.11"
            log_print(f"[{serial_number}] 余额文本: {balance_text}")
            
            # 提取数字
            balance_match = re.search(r'[\d,.]+', balance_text)
            if balance_match:
                balance_value = float(balance_match.group().replace(',', ''))
                log_print(f"[{serial_number}] 当前余额: ${balance_value}")
                
                if balance_value <= 100:
                    log_print(f"[{serial_number}] ⚠ 余额不足100，跳过兑换操作")
                    driver.close()
                    driver.switch_to.window(main_window)
                    return False
            else:
                log_print(f"[{serial_number}] ✗ 无法解析余额文本: {balance_text}")
                return False
        except TimeoutException as e:
            log_print(f"[{serial_number}] ✗ 获取余额超时: 10秒内未找到余额元素")
            log_print(f"[{serial_number}] 页面源代码（前500字符）:\n{driver.page_source[:500]}")
            import traceback
            log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
            return False
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 获取余额失败: {str(e)}")
            log_print(f"[{serial_number}] 页面URL: {driver.current_url}")
            import traceback
            log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
            return False
        
        # 第3.5步：检查ASTER数量
        skip_swap = False
        log_print(f"[{serial_number}] 检查ASTER数量...")
        try:
            aster_divs = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[text()='ASTER']"))
            )
            if aster_divs:
                log_print(f"[{serial_number}] ✓ 找到ASTER div")
                # 获取父节点的父节点的父节点
                great_grandparent = aster_divs[0].find_element(By.XPATH, "../../..")
                # 获取所有子节点
                child_divs = great_grandparent.find_elements(By.XPATH, "./div")
                if child_divs:
                    # 获取最后一个div
                    last_div = child_divs[-1]
                    # 获取这个div的第一个子div
                    first_child = last_div.find_element(By.XPATH, "./div")
                    aster_amount_text = first_child.text
                    log_print(f"[{serial_number}] ASTER数量文本: {aster_amount_text}")
                    
                    # 提取数字
                    aster_match = re.search(r'[\d,.]+', aster_amount_text)
                    if aster_match:
                        aster_amount = float(aster_match.group().replace(',', ''))
                        log_print(f"[{serial_number}] 当前ASTER数量: {aster_amount}")
                        
                        if aster_amount > 4:
                            log_print(f"[{serial_number}] ✓ ASTER数量大于4，跳过兑换流程，直接进入绑定")
                            skip_swap = True
                        else:
                            log_print(f"[{serial_number}] ℹ ASTER数量不足4，需要执行兑换")
                    else:
                        log_print(f"[{serial_number}] ⚠ 无法解析ASTER数量，继续执行兑换")
                else:
                    log_print(f"[{serial_number}] ⚠ 未找到子节点，继续执行兑换")
            else:
                log_print(f"[{serial_number}] ℹ 未找到ASTER div，继续执行兑换")
        except TimeoutException:
            log_print(f"[{serial_number}] ℹ 5秒内未找到ASTER，继续执行兑换")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 检查ASTER数量时出错: {str(e)}，继续执行兑换")
        
        # 第四步：点击 Swap/兑换按钮（如果需要）
        if not skip_swap:
            log_print(f"[{serial_number}] 查找并点击 Swap 按钮...")
            try:
                swap_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Swap') or contains(text(), '兑换')]")
                log_print(f"[{serial_number}] 找到 {len(swap_elements)} 个包含 'Swap' 或 '兑换' 的元素")
                
                swap_clicked = False
                for i, elem in enumerate(swap_elements):
                    try:
                        is_displayed = elem.is_displayed()
                        elem_text = elem.text
                        log_print(f"[{serial_number}] 元素 {i}: 文本='{elem_text}', 可见={is_displayed}")
                        
                        if is_displayed:
                            parent = elem.find_element(By.XPATH, "./..")
                            parent.click()
                            swap_clicked = True
                            log_print(f"[{serial_number}] ✓ 点击了 Swap 按钮")
                            break
                    except Exception as elem_error:
                        log_print(f"[{serial_number}] 元素 {i} 检查失败: {str(elem_error)}")
                        continue
                
                if not swap_clicked:
                    log_print(f"[{serial_number}] ✗ 未找到可见的 Swap 按钮")
                    log_print(f"[{serial_number}] 页面URL: {driver.current_url}")
                    return False
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 点击 Swap 按钮失败: {str(e)}")
                import traceback
                log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
                return False
            
            # 等待页面跳转
            time.sleep(2)
            
            # 执行兑换流程
            if not execute_swap_flow(driver, serial_number):
                return False
        else:
            log_print(f"[{serial_number}] ℹ ASTER余额充足，跳过兑换流程")
        
        # 切换回主窗口
        driver.switch_to.window(main_window)
        time.sleep(1)
        
        # 执行钱包连接流程
        if not execute_wallet_connection(driver, serial_number, ref_code, password):
            return False
        
        log_print(f"[{serial_number}] ✓✓✓ Type 2 所有操作完成")
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] ✗ Type 2 处理失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        log_print(f"[{serial_number}] 当前页面URL: {driver.current_url if driver else 'driver 不可用'}")
        return False


def execute_swap_flow(driver, serial_number):
    """
    执行代币兑换流程
    """
    try:
        log_print(f"[{serial_number}] 开始执行兑换流程...")
        log_print(f"[{serial_number}] 当前页面URL: {driver.current_url}")
        
        # 1. 在10s内找到 data-monitor="token" 的 button（第一个）
        log_print(f"[{serial_number}] 查找第一个 token 按钮...")
        try:
            token_buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-monitor='token']"))
            )
            log_print(f"[{serial_number}] 找到 {len(token_buttons)} 个 token 按钮")
            
            if len(token_buttons) < 2:
                log_print(f"[{serial_number}] ✗ token 按钮数量不足（需要至少2个）")
                return False
            
            token_buttons[0].click()
            log_print(f"[{serial_number}] ✓ 点击了第一个 token 按钮")
            time.sleep(1)
        except TimeoutException:
            log_print(f"[{serial_number}] ✗ 超时: 10秒内未找到 token 按钮")
            log_print(f"[{serial_number}] 页面URL: {driver.current_url}")
            import traceback
            log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
            return False
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 查找/点击 token 按钮失败: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
            return False
        
        # 2. 在5s内找到包含 USDT 的 div 并点击其父节点的父节点的父节点的父节点
        log_print(f"[{serial_number}] 查找并选择 USDT...")
        usdt_elements = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'content-primary') and contains(text(), 'USDT')]"))
        )
        if usdt_elements:
            great_great_great_grandparent = usdt_elements[0].find_element(By.XPATH, "./../../..")
            great_great_great_grandparent.click()
            log_print(f"[{serial_number}] ✓ 选择了第一个 USDT")
        else:
            log_print(f"[{serial_number}] ✗ 未找到 USDT")
            return False
        
        time.sleep(1)
        
        # 3. 重新获取 token 按钮并点击第二个
        log_print(f"[{serial_number}] 查找第二个 token 按钮...")
        token_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-monitor='token']"))
        )
        if len(token_buttons) >= 2:
            token_buttons[1].click()
            log_print(f"[{serial_number}] ✓ 点击了第二个 token 按钮")
        else:
            log_print(f"[{serial_number}] ✗ 未找到第二个 token 按钮")
            return False
        
        time.sleep(1)
        
        # 4. 再次找到并选择 USDT
        log_print(f"[{serial_number}] 再次查找并选择 ASTER...")
        usdt_elements = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'content-primary') and contains(text(), 'ASTER')]"))
        )
        if usdt_elements:
            great_great_great_grandparent = usdt_elements[0].find_element(By.XPATH, "./../../..")
            great_great_great_grandparent.click()
            log_print(f"[{serial_number}] ✓ 选择了第二个 ASTER")
        else:
            log_print(f"[{serial_number}] ✗ 未找到第二个 ASTER")
            return False
        
        time.sleep(1)
        
        # 5. 找到输入框并输入随机值
        log_print(f"[{serial_number}] 输入兑换数量...")
        input_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='inputPanel-input']"))
        )
        random_value = random.uniform(3, 7)
        input_element.clear()
        input_element.send_keys(str(round(random_value, 2)))
        log_print(f"[{serial_number}] ✓ 输入数量: {round(random_value, 2)}")
        
        time.sleep(1)
        
        # 6. 点击第一个 okd-button
        log_print(f"[{serial_number}] 点击确认按钮...")
        okd_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
        )
        okd_button.click()
        log_print(f"[{serial_number}] ✓ 点击了确认按钮")
        
        time.sleep(1)
        
        # 7. 点击 "Set to unlimited" (可选步骤)
        log_print(f"[{serial_number}] 查找 Set to unlimited...")
        unlimited_found = False
        try:
            unlimited_elements = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'Set to unlimited')]"))
            )
            if unlimited_elements:
                unlimited_elements[0].click()
                log_print(f"[{serial_number}] ✓ 点击了 Set to unlimited")
                unlimited_found = True
                time.sleep(0.5)
            else:
                log_print(f"[{serial_number}] ℹ 未找到 Set to unlimited，跳过此步骤")
        except TimeoutException:
            log_print(f"[{serial_number}] ℹ 未找到 Set to unlimited（超时），跳过此步骤")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 查找 Set to unlimited 时出错: {str(e)}，跳过此步骤")
        
        # 8. 点击 "Confirm amount" (仅在找到 Set to unlimited 时执行)
        if unlimited_found:
            log_print(f"[{serial_number}] 查找 Confirm amount...")
            try:
                confirm_elements = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), 'Confirm amount')]"))
                )
                if confirm_elements:
                    parent = confirm_elements[0].find_element(By.XPATH, "./..")
                    parent.click()
                    log_print(f"[{serial_number}] ✓ 点击了 Confirm amount")
                    time.sleep(0.5)
                else:
                    log_print(f"[{serial_number}] ℹ 未找到 Confirm amount，跳过此步骤")
            except TimeoutException:
                log_print(f"[{serial_number}] ℹ 未找到 Confirm amount（超时），跳过此步骤")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 查找 Confirm amount 时出错: {str(e)}，跳过此步骤")
        else:
            log_print(f"[{serial_number}] ℹ 跳过 Confirm amount 步骤（因为没有 Set to unlimited）")
        
        # 9. 点击 okui-btn btn-lg btn-fill-highlight
        log_print(f"[{serial_number}] 查找高亮按钮...")
        highlight_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'okui-btn') and contains(@class, 'btn-lg') and contains(@class, 'btn-fill-highlight')]"))
        )
        highlight_button.click()
        log_print(f"[{serial_number}] ✓ 点击了高亮按钮")
        
        time.sleep(0.5)
        
        # 10. 再次点击 okd-button
        log_print(f"[{serial_number}] 再次点击 okd-button...")
        okd_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
        )
        okd_button.click()
        log_print(f"[{serial_number}] ✓ 再次点击了 okd-button")
        
        time.sleep(1)
        
        # 11. 点击 checkbox label (可选步骤)
        log_print(f"[{serial_number}] 查找并点击 checkbox...")
        checkbox_found = False
        try:
            checkbox_label = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "label[data-testid='okd-checkbox-label']"))
            )
            checkbox_label.click()
            log_print(f"[{serial_number}] ✓ 点击了 checkbox")
            checkbox_found = True
            time.sleep(1)
        except TimeoutException:
            log_print(f"[{serial_number}] ℹ 未找到 checkbox（超时），跳过此步骤")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 查找 checkbox 时出错: {str(e)}，跳过此步骤")
        
        # 12. 点击 btn-fill-primary (仅在找到 checkbox 时执行)
        if checkbox_found:
            log_print(f"[{serial_number}] 查找并点击 primary 按钮...")
            try:
                primary_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-fill-primary')]"))
                )
                primary_button.click()
                log_print(f"[{serial_number}] ✓ 点击了 primary 按钮")
                time.sleep(1)
            except TimeoutException:
                log_print(f"[{serial_number}] ℹ 未找到 primary 按钮（超时），跳过此步骤")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 查找 primary 按钮时出错: {str(e)}，跳过此步骤")
        else:
            log_print(f"[{serial_number}] ℹ 跳过 primary 按钮步骤（因为没有 checkbox）")
        
        # 13. 最后一次点击 okd-button (仅在找到 checkbox 时执行)
        if checkbox_found:
            log_print(f"[{serial_number}] 最后一次点击 okd-button...")
            try:
                okd_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
                )
                okd_button.click()
                log_print(f"[{serial_number}] ✓ 最后一次点击了 okd-button")
                time.sleep(2)
            except TimeoutException:
                log_print(f"[{serial_number}] ℹ 未找到最后的 okd-button（超时），跳过此步骤")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 查找最后的 okd-button 时出错: {str(e)}，跳过此步骤")
        else:
            log_print(f"[{serial_number}] ℹ 跳过最后的 okd-button 步骤（因为没有 checkbox）")
        
        log_print(f"[{serial_number}] ✓ 兑换流程完成")
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 兑换流程失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        log_print(f"[{serial_number}] 当前页面URL: {driver.current_url}")
        return False


def execute_wallet_connection(driver, serial_number, ref_code, password):
    """
    执行钱包连接和邀请码绑定流程
    """
    try:
        log_print(f"[{serial_number}] 开始钱包连接流程...")
        
        # 保存主窗口句柄
        main_window = driver.current_window_handle
        
        # 0. 切换语言到英文
        log_print(f"[{serial_number}] 切换语言到英文...")
        try:
            # 0.1 点击语言选择按钮
            log_print(f"[{serial_number}] 查找语言选择按钮...")
            lang_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='radix-_r_6_']"))
            )
            lang_button.click()
            log_print(f"[{serial_number}] ✓ 点击了语言选择按钮")
            time.sleep(1)

            # 0.2 点击倒数第二个 menuitem
            log_print(f"[{serial_number}] 查找并点击倒数第二个菜单项...")
            menu_items = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='menuitem']"))
            )
            if len(menu_items) >= 2:
                menu_items[-2].click()
                log_print(f"[{serial_number}] ✓ 点击了倒数第二个菜单项")
                time.sleep(1)
            else:
                log_print(f"[{serial_number}] ⚠ 菜单项数量不足")

            # 0.3 点击 English 选项
            log_print(f"[{serial_number}] 查找并点击 English 选项...")
            english_spans = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, "//span[text()='English']"))
            )
            if english_spans:
                # 点击其父节点的父节点
                grandparent = english_spans[0].find_element(By.XPATH, "../..")
                grandparent.click()
                log_print(f"[{serial_number}] ✓ 切换语言到 English")
                time.sleep(1)
            else:
                log_print(f"[{serial_number}] ⚠ 未找到 English 选项")
                
        except TimeoutException:
            log_print(f"[{serial_number}] ℹ 语言切换超时，可能已经是英文，继续执行...")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 语言切换失败: {str(e)}，继续执行...")
        
        # 1. 查找 Connect wallet 按钮 (最多重试2次)
        connect_found = False
        for attempt in range(2):
            try:
                log_print(f"[{serial_number}] 查找 Connect wallet 按钮... (尝试 {attempt + 1}/2)")
                connect_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Connect wallet']"))
                )
                connect_button.click()
                log_print(f"[{serial_number}] ✓ 找到并点击了 Connect wallet 按钮")
                connect_found = True
                break
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
        
        if not connect_found:
            log_print(f"[{serial_number}] ℹ 未找到 Connect wallet 按钮，跳过 OKX 钱包选择步骤...")
        
        
        # 2. 如果找到了 Connect wallet，则选择 OKX Wallet 并进行第一次授权
        if connect_found:
            time.sleep(2)
            
            # 2.1 点击 "OKX Wallet"
            okx_success = False
            try:
                log_print(f"[{serial_number}] 查找 OKX Wallet...")
                okx_elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), 'OKX Wallet')]"))
                )
                if okx_elements:
                    parent = okx_elements[0].find_element(By.XPATH, "./..")
                    parent.click()
                    log_print(f"[{serial_number}] ✓ 点击了 OKX Wallet")
                    okx_success = True
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 查找 OKX Wallet 失败: {str(e)}")
            
            # 2.2 第一次钱包授权
            if okx_success:
                log_print(f"[{serial_number}] 等待钱包扩展标签页进行第一次授权...")
                wallet_window = None
                for i in range(5):  # 10秒，每次2秒
                    time.sleep(2)
                    for handle in driver.window_handles:
                        driver.switch_to.window(handle)
                        if "mcohilncbfahbmgdjkbpemcciiolgcge" in driver.current_url:
                            wallet_window = handle
                            log_print(f"[{serial_number}] ✓ 找到钱包扩展标签页")
                            break
                    
                    if wallet_window:
                        try:
                            # 检查并解锁钱包
                            check_and_unlock_wallet(driver, serial_number, password)
                            
                            # 点击第二个 okd-button
                            okd_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='okd-button']")
                            if len(okd_buttons) >= 2:
                                okd_buttons[1].click()
                                log_print(f"[{serial_number}] ✓ 完成第一次钱包授权")
                                break
                        except Exception as e:
                            log_print(f"[{serial_number}] ⚠ 第一次授权过程出错: {str(e)}")
                
                # 切换回主窗口
                time.sleep(2)
                driver.switch_to.window(main_window)
        
        # 3. 查找 Send request 按钮 (最多重试2次)
        send_request_found = False
        for attempt in range(2):
            try:
                log_print(f"[{serial_number}] 查找 Send request 按钮... (尝试 {attempt + 1}/2)")
                time.sleep(1)
                driver.switch_to.window(main_window)
                send_buttons = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), 'Send request') or contains(text(), '发送请求')]"))
                )
                if send_buttons:
                    send_buttons[0].click()
                    log_print(f"[{serial_number}] ✓ 找到并点击了 Send request 按钮")
                    send_request_found = True
                    break
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
        
        if not send_request_found:
            log_print(f"[{serial_number}] ℹ 未找到 Send request 按钮，跳过第二次 OKX 授权步骤...")
        
        # 4. 如果找到了 Send request，进行第二次钱包授权
        if send_request_found:
            log_print(f"[{serial_number}] 等待钱包扩展标签页进行第二次授权...")
            wallet_window = None
            for i in range(5):  # 10秒，每次2秒
                time.sleep(2)
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    if "mcohilncbfahbmgdjkbpemcciiolgcge" in driver.current_url:
                        wallet_window = handle
                        log_print(f"[{serial_number}] ✓ 找到钱包扩展标签页")
                        break
                
                if wallet_window:
                    try:
                        # 检查并解锁钱包
                        check_and_unlock_wallet(driver, serial_number, password)
                        
                        # 点击第二个 okd-button
                        okd_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='okd-button']")
                        if len(okd_buttons) >= 2:
                            okd_buttons[1].click()
                            log_print(f"[{serial_number}] ✓ 完成第二次钱包授权")
                            break
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 第二次授权过程出错: {str(e)}")
            
            # 切换回主窗口
            time.sleep(2)
            driver.switch_to.window(main_window)
        
        # 5. 查找 Bind your invite code quickly (最多重试2次)
        bind_found = False
        for attempt in range(2):
            try:
                log_print(f"[{serial_number}] 查找 Bind your invite code quickly... (尝试 {attempt + 1}/2)")
                bind_elements = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(text(), 'Bind your invite code quickly')]"))
                )
                if bind_elements:
                    parent = bind_elements[0].find_element(By.XPATH, "./..")
                    parent.click()
                    log_print(f"[{serial_number}] ✓ 找到并点击了 Bind your invite code quickly")
                    bind_found = True
                    break
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
        
        if not bind_found:
            log_print(f"[{serial_number}] ℹ 未找到 Bind your invite code quickly，跳过填写邀请码步骤...")
        
        # 6. 如果找到了 Bind your invite code quickly，填写并确认邀请码
        if bind_found:
            try:
                log_print(f"[{serial_number}] 填写邀请码...")
                ref_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='refCode']"))
                )
                ref_input.clear()
                ref_input.send_keys(ref_code)
                log_print(f"[{serial_number}] ✓ 输入了邀请码: {ref_code}")
                
                time.sleep(1)
                
                # 点击 Confirm 按钮
                confirm_buttons = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), 'Confirm')]"))
                )
                if confirm_buttons:
                    confirm_buttons[0].click()
                    log_print(f"[{serial_number}] ✓ 点击了确认按钮")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 邀请码填写失败: {str(e)}")
        
        # 7. 检查绑定是否成功（查找 data-id="0" 和 data-id="1"）
        time.sleep(2)
        log_print(f"[{serial_number}] 检查绑定是否成功...")
        try:
            data_id_0 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-id='0']"))
            )
            data_id_1 = driver.find_element(By.CSS_SELECTOR, "div[data-id='1']")
            
            if data_id_0 and data_id_1:
                log_print(f"[{serial_number}] ✓✓✓ 绑定成功！找到 data-id='0' 和 data-id='1'")
            else:
                log_print(f"[{serial_number}] ⚠ 只找到部分元素")
        except Exception as e:
            log_print(f"[{serial_number}] ℹ 未找到绑定成功标识，可能需要手动检查")
        
        time.sleep(2)
        log_print(f"[{serial_number}] ✓ 钱包连接流程完成")
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 钱包连接流程失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        log_print(f"[{serial_number}] 当前页面URL: {driver.current_url}")
        return False


def collect_stage3_statistics(driver, serial_number):
    """
    采集 Stage 3 Statistics 页面数据 (Type 8)
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (success, failure_reason, data) - (是否成功, 失败原因, 采集的数据)
    """
    try:
        log_print(f"[{serial_number}] 开始采集 Stage 3 Statistics 数据...")
        
        # 1. 打开目标页面
        target_url = "https://www.asterdex.com/en/stage3/statistics"
        log_print(f"[{serial_number}] 打开页面: {target_url}")
        driver.get(target_url)
        
        # 2. 等待页面加载 - 查找 "Stage 3" h1标签
        log_print(f"[{serial_number}] 等待页面加载（最多20秒）...")
        page_loaded = False
        start_time = time.time()
        
        while time.time() - start_time < 20:
            try:
                result = driver.execute_script("""
                    const h1Tags = document.querySelectorAll('h1');
                    for (const h1 of h1Tags) {
                        if (h1.textContent.trim() === 'Stage 3') {
                            return true;
                        }
                    }
                    return false;
                """)
                
                if result:
                    page_loaded = True
                    log_print(f"[{serial_number}] ✓ 页面加载完成（找到 'Stage 3' 标题）")
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not page_loaded:
            log_print(f"[{serial_number}] ✗ 页面加载超时，未找到 'Stage 3' 标题")
            return False, "页面加载超时"
        
        time.sleep(5)
        # 3. 获取各项数据
        log_print(f"[{serial_number}] 开始获取数据...")
        
        script = """
        return (function() {
            const results = {
                currentPoints: '',
                ranking: '',
                yourShare: '',
                teamBoost: '',
                tradePoints: '',
                positionPoints: '',
                usdfAsBnbPoints: '',
                profitPoints: '',
                lossPoints: '',
                referralPoints: '',
                success: false,
                errors: []
            };
            
            const targets = [
                { key: 'currentPoints', text: 'Current points' },
                { key: 'ranking', text: 'Ranking' },
                { key: 'yourShare', text: 'Your share' },
                { key: 'teamBoost', text: 'Team boost' },
                { key: 'tradePoints', text: 'Trade points' },
                { key: 'positionPoints', text: 'Position points' },
                { key: 'usdfAsBnbPoints', text: 'USDF/asBNB points' },
                { key: 'profitPoints', text: 'Profit points' },
                { key: 'lossPoints', text: 'Loss points' },
                { key: 'referralPoints', text: 'Referral points' }
            ];
            
            try {
                for (const target of targets) {
                    const allDivs = document.querySelectorAll('div');
                    let found = false;
                    
                    for (const div of allDivs) {
                        const divText = (div.textContent || '').trim();
                        
                        // 检查div的内容是否等于目标文本
                        if (divText === target.text) {
                            // 找到父节点
                            const parent = div.parentElement;
                            if (parent) {
                                // 找到父节点的所有子div
                                const childDivs = parent.querySelectorAll(':scope > div');
                                if (childDivs && childDivs.length > 0) {
                                    // 获取最后一个子div的内容
                                    const lastDiv = childDivs[childDivs.length - 1];
                                    results[target.key] = (lastDiv.textContent || '').trim();
                                    found = true;
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (!found) {
                        results.errors.push(`未找到: ${target.text}`);
                    }
                }
                
                results.success = results.errors.length === 0;
                
            } catch (e) {
                results.errors.push('脚本执行异常: ' + e.message);
            }
            
            return results;
        })();
        """
        
        data = driver.execute_script(script)
        
        # 4. 打印采集结果
        log_print(f"[{serial_number}] 数据采集结果:")
        log_print(f"[{serial_number}]   Current points: {data.get('currentPoints')}")
        log_print(f"[{serial_number}]   Ranking: {data.get('ranking')}")
        log_print(f"[{serial_number}]   Your share: {data.get('yourShare')}")
        log_print(f"[{serial_number}]   Team boost: {data.get('teamBoost')}")
        log_print(f"[{serial_number}]   Trade points: {data.get('tradePoints')}")
        log_print(f"[{serial_number}]   Position points: {data.get('positionPoints')}")
        log_print(f"[{serial_number}]   USDF/asBNB points: {data.get('usdfAsBnbPoints')}")
        log_print(f"[{serial_number}]   Profit points: {data.get('profitPoints')}")
        log_print(f"[{serial_number}]   Loss points: {data.get('lossPoints')}")
        log_print(f"[{serial_number}]   Referral points: {data.get('referralPoints')}")
        
        if data.get('errors'):
            log_print(f"[{serial_number}] ⚠ 数据采集警告:")
            for error in data.get('errors'):
                log_print(f"[{serial_number}]   - {error}")
        
        if data.get('success'):
            log_print(f"[{serial_number}] ✓ Stage 3 Statistics 数据采集成功")
            return True, "", data
        else:
            log_print(f"[{serial_number}] ✗ Stage 3 Statistics 数据采集部分失败")
            return False, "部分数据采集失败", data
            
    except Exception as e:
        log_print(f"[{serial_number}] ✗ Stage 3 Statistics 数据采集异常: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False, "数据采集异常", None


def collect_trade_history(driver, serial_number):
    """
    采集 Trade history 数据 (Type 9)
    
    Args:
        driver: Selenium WebDriver
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (success, failure_reason, data) - (是否成功, 失败原因, 采集的数据列表)
    """
    try:
        log_print(f"[{serial_number}] 开始采集 Trade history 数据...")
        
        # 1. 等待2秒后点击 "Trade history" 按钮
        log_print(f"[{serial_number}] 等待 2 秒后点击 'Trade history' 按钮...")
        time.sleep(2)
        
        click_script = """
        return (function() {
            const results = {
                buttonFound: false,
                buttonClicked: false,
                clickError: ''
            };
            
            try {
                // 查找并点击 "Trade history" 按钮
                const allButtons = document.querySelectorAll('button');
                let tradeHistoryBtn = null;
                
                for (const btn of allButtons) {
                    const btnText = (btn.textContent || '').trim();
                    if (btnText === 'Trade history') {
                        tradeHistoryBtn = btn;
                        results.buttonFound = true;
                        break;
                    }
                }
                
                if (tradeHistoryBtn) {
                    try {
                        // 方式1: 滚动到可见区域
                        tradeHistoryBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
                        
                        // 方式2: 触发完整的鼠标事件链
                        const mouseDownEvent = new MouseEvent('mousedown', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            detail: 1
                        });
                        const mouseUpEvent = new MouseEvent('mouseup', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            detail: 1
                        });
                        const clickEvent = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            detail: 1
                        });
                        
                        tradeHistoryBtn.dispatchEvent(mouseDownEvent);
                        tradeHistoryBtn.dispatchEvent(mouseUpEvent);
                        tradeHistoryBtn.dispatchEvent(clickEvent);
                        
                        // 方式3: 触发 PointerEvent
                        const pointerDownEvent = new PointerEvent('pointerdown', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        const pointerUpEvent = new PointerEvent('pointerup', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        tradeHistoryBtn.dispatchEvent(pointerDownEvent);
                        tradeHistoryBtn.dispatchEvent(pointerUpEvent);
                        
                        // 方式4: 传统点击
                        tradeHistoryBtn.click();
                        
                        results.buttonClicked = true;
                    } catch (e) {
                        results.clickError = e.message;
                    }
                }
                
            } catch (e) {
                results.clickError = e.message;
            }
            
            return results;
        })();
        """
        
        click_result = driver.execute_script(click_script)
        
        log_print(f"[{serial_number}]   Trade history 按钮找到: {click_result.get('buttonFound')}")
        log_print(f"[{serial_number}]   按钮点击: {click_result.get('buttonClicked')}")
        
        if not click_result.get('buttonClicked'):
            log_print(f"[{serial_number}] ✗ Trade history 按钮点击失败")
            if click_result.get('clickError'):
                log_print(f"[{serial_number}]   错误: {click_result.get('clickError')}")
            return False, "Trade history 按钮点击失败", None
        
        # 2. 等待3秒后获取数据
        log_print(f"[{serial_number}] 等待 3 秒后获取数据...")
        time.sleep(3)
        
        get_data_script = """
        return (function() {
            const results = {
                tradeList: [],
                success: false,
                foundDataIds: []
            };
            
            try {
                // 循环获取 data-id="0" 到 data-id="5" 的数据
                const targetIndexes = [0, 2, 7, 9, 11, 13];
                
                for (let dataId = 0; dataId <= 5; dataId++) {
                    const dataDiv = document.querySelector(`div[data-id="${dataId}"]`);
                    
                    if (dataDiv) {
                        results.foundDataIds.push(dataId);
                        
                        // 获取该节点下的所有div
                        const allDivs = dataDiv.querySelectorAll('div');
                        
                        // 只有当div数量足够时才提取数据
                        if (allDivs.length >= 14) {
                            const tradeData = {
                                time: '',           // [0] 时间
                                symbol: '',         // [2] 币种+方向
                                price: '',          // [7] 价格
                                quantity: '',       // [9] 数量
                                fee: '',            // [11] 手续费
                                pnl: ''             // [13] 盈亏
                            };
                            
                            targetIndexes.forEach(targetIdx => {
                                if (allDivs[targetIdx]) {
                                    const text = (allDivs[targetIdx].textContent || '').trim();
                                    
                                    switch(targetIdx) {
                                        case 0:
                                            tradeData.time = text;
                                            break;
                                        case 2:
                                            tradeData.symbol = text;
                                            break;
                                        case 7:
                                            tradeData.price = text;
                                            break;
                                        case 9:
                                            tradeData.quantity = text;
                                            break;
                                        case 11:
                                            tradeData.fee = text;
                                            break;
                                        case 13:
                                            tradeData.pnl = text;
                                            break;
                                    }
                                }
                            });
                            
                            // 只添加有数据的记录
                            if (tradeData.time || tradeData.symbol) {
                                results.tradeList.push(tradeData);
                            }
                        }
                    }
                }
                
                results.success = results.tradeList.length > 0;
                
            } catch (e) {
                results.error = e.message;
            }
            
            return results;
        })();
        """
        
        data_result = driver.execute_script(get_data_script)
        
        log_print(f"[{serial_number}] Trade history 数据获取结果:")
        found_data_ids = data_result.get('foundDataIds', [])
        log_print(f"[{serial_number}]   找到的 data-id: {found_data_ids}")
        log_print(f"[{serial_number}]   交易记录数量: {len(data_result.get('tradeList', []))}")
        
        if data_result.get('success'):
            trade_list = data_result.get('tradeList', [])
            if trade_list:
                log_print(f"[{serial_number}] ✓ Trade history 数据采集成功，共 {len(trade_list)} 条记录")
                # 显示前3条记录作为示例
                for i, trade in enumerate(trade_list[:3]):
                    log_print(f"[{serial_number}]   记录 {i+1}: {trade.get('time')} | {trade.get('symbol')} | {trade.get('price')} | {trade.get('pnl')}")
                if len(trade_list) > 3:
                    log_print(f"[{serial_number}]   ... 还有 {len(trade_list) - 3} 条记录")
                return True, "", trade_list
            else:
                log_print(f"[{serial_number}] ⚠ 未获取到交易记录")
                return False, "未获取到交易记录", []
        else:
            log_print(f"[{serial_number}] ✗ Trade history 数据采集失败")
            if data_result.get('error'):
                log_print(f"[{serial_number}]   错误: {data_result.get('error')}")
            return False, "数据采集失败", None
            
    except Exception as e:
        log_print(f"[{serial_number}] ✗ Trade history 数据采集异常: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False, "数据采集异常", None


def process_browser(browser_config):
    """
    处理单个浏览器的完整流程
    
    Args:
        browser_config: 浏览器配置字典，包含 id 和 type
        
    Returns:
        tuple: (success, failure_reason) - (是否成功, 失败原因)
    """
    serial_number = browser_config.get("id")
    browser_type = browser_config.get("type")
    
    log_print(f"\n{'='*60}")
    log_print(f"[{serial_number}] 开始处理浏览器 (类型: {browser_type})")
    log_print(f"{'='*60}\n")
    
    driver = None
    success = False
    failure_reason = ""
    should_close_browser = True  # 默认关闭浏览器
    
    # Type 15 全局超时控制（防止执行时间过长导致系统资源耗尽）
    task_start_time = time.time()
    MAX_EXECUTION_TIME = 900 if browser_type == 15 else 1800  # Type 15: 15分钟，其他: 30分钟
    
    def check_timeout():
        """检查是否超时，超时则抛出异常"""
        elapsed = time.time() - task_start_time
        if elapsed > MAX_EXECUTION_TIME:
            raise TimeoutException(f"任务执行超时 ({elapsed/60:.1f}分钟 > {MAX_EXECUTION_TIME/60:.1f}分钟)")
        return elapsed
    
    try:
        # Type 3: 关闭多余标签页后关闭浏览器
        if browser_type == 3:
            log_print(f"[{serial_number}] Type 3: 关闭浏览器")
            
            # 先尝试连接到浏览器关闭多余标签页
            try:
                browser_data = get_running_browser_data(serial_number)
                if browser_data:
                    log_print(f"[{serial_number}] 连接到浏览器以关闭多余标签页...")
                    driver = create_selenium_driver(browser_data)
                    close_extra_tabs(driver, serial_number)
                    driver.quit()
                    log_print(f"[{serial_number}] ✓ 标签页清理完成")
                else:
                    log_print(f"[{serial_number}] ⚠ 浏览器未运行或无法连接，直接执行关闭")
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 关闭标签页失败: {str(e)}，继续关闭浏览器")
            
            # 关闭浏览器
            time.sleep(1)
            close_adspower_browser(serial_number)
            log_print(f"[{serial_number}] ✓✓✓ 浏览器已关闭")
            return True, ""
        
       
        # Type 9: 连接到已打开的浏览器，采集 Trade history 数据，完成后不关闭
        if browser_type == 9:
            log_print(f"[{serial_number}] Type 9: 连接已打开的浏览器并采集 Trade history 数据")
            
            # 获取已运行浏览器的连接信息
            browser_data = get_running_browser_data(serial_number)
            if not browser_data:
                log_print(f"[{serial_number}] ✗ 浏览器未运行，无法执行 Type 9 任务")
                return False, "浏览器未运行"
            
            # 创建Selenium驱动
            try:
                driver = create_selenium_driver(browser_data)
                log_print(f"[{serial_number}] ✓ Selenium驱动创建成功")
            except Exception as e:
                log_print(f"[{serial_number}] ✗✗✗ 创建Selenium驱动失败: {str(e)}")
                return False, "驱动创建失败"
            
            # 采集 Trade history 数据
            success, failure_reason, trade_list = collect_trade_history(driver, serial_number)
            
            # 清理 Selenium 驱动
            if driver:
                try:
                    driver.quit()
                    log_print(f"[{serial_number}] ✓ Selenium驱动已关闭")
                except:
                    pass
            
            log_print(f"[{serial_number}] ℹ 浏览器保持打开状态")
            
            # 提交数据到服务器
            if success and trade_list:
                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                max_upload_retries = 2
                upload_success = False
                
                for attempt in range(max_upload_retries):
                    try:
                        log_print(f"[{serial_number}] 正在提交交易历史数据... (尝试 {attempt + 1}/{max_upload_retries})")
                        
                        # 构建数据列表
                        order_history_list = []
                        for trade in trade_list:
                            order_data = {
                                "no": serial_number,                    # 浏览器编号
                                "a": trade.get('time', ''),             # [0] 时间
                                "b": trade.get('symbol', ''),           # [2] 币种+方向
                                "c": trade.get('price', ''),            # [7] 价格
                                "d": trade.get('quantity', ''),         # [9] 数量
                                "e": trade.get('fee', ''),              # [11] 手续费
                                "f": trade.get('pnl', ''),              # [13] 盈亏
                                "time": int(time.time() * 1000)         # 当前时间戳（毫秒）
                            }
                            order_history_list.append(order_data)
                        
                        response = requests.post(
                            f"{API_BASE_URL}/insertOrderHistoryList",
                            json=order_history_list,
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            code = result.get('code')
                            
                            if code == 0:
                                log_print(f"[{serial_number}] ✓ 交易历史数据提交成功 (code=0)")
                                upload_success = True
                                break
                            else:
                                log_print(f"[{serial_number}] ✗ 交易历史数据提交失败: code={code}, msg={result.get('msg')}")
                                if attempt < max_upload_retries - 1:
                                    log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                    time.sleep(2)
                        else:
                            log_print(f"[{serial_number}] ✗ 交易历史数据提交失败: HTTP状态码 {response.status_code}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                time.sleep(2)
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 交易历史数据提交异常: {str(e)}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] 等待 2 秒后重试...")
                            time.sleep(2)
                
                if upload_success:
                    log_print(f"[{serial_number}] ✓✓✓ Trade history 数据采集和提交完成，共 {len(trade_list)} 条记录")
                    return True, ""
                else:
                    log_print(f"[{serial_number}] ✗✗✗ 交易历史数据提交失败")
                    return False, "交易历史数据提交失败"
            else:
                if not success:
                    log_print(f"[{serial_number}] ✗✗✗ Trade history 数据采集失败: {failure_reason}")
                    return False, failure_reason
                else:
                    log_print(f"[{serial_number}] ✗✗✗ 无交易数据可提交")
                    return False, "无交易数据可提交"
        
        # Type 5: 连接到已经打开的浏览器并抓取数据，完成后不关闭
        if browser_type == 5:
            log_print(f"[{serial_number}] Type 5: 连接已打开的浏览器并收集数据")
            # 获取已运行浏览器的连接信息
            browser_data = get_running_browser_data(serial_number)
            if not browser_data:
                log_print(f"[{serial_number}] ✗ 浏览器未运行，无法执行 Type 5 任务")
                return False, "浏览器未运行"
            
            # 创建Selenium驱动
            try:
                driver = create_selenium_driver(browser_data)
                log_print(f"[{serial_number}] ✓ Selenium驱动创建成功")
            except Exception as e:
                log_print(f"[{serial_number}] ✗✗✗ 创建Selenium驱动失败: {str(e)}")
                return False, "驱动创建失败"
            
            # 切换到 asterdex 标签页并打开目标URL
            try:
                target_url = "https://www.asterdex.com/en/futures/v1/BTCUSDT"
                log_print(f"[{serial_number}] 查找包含 www.asterdex.com 的标签页...")
                
                # 获取所有窗口句柄
                all_windows = driver.window_handles
                asterdex_window = None
                
                # 查找包含 asterdex 的标签页
                for window_handle in all_windows:
                    try:
                        driver.switch_to.window(window_handle)
                        current_url = driver.current_url
                        if "www.asterdex.com" in current_url or "asterdex.com" in current_url:
                            asterdex_window = window_handle
                            log_print(f"[{serial_number}] ✓ 找到 asterdex 标签页: {current_url}")
                            break
                    except Exception as e:
                        # 某些标签页可能无法访问URL（如chrome://等系统页面），跳过继续查找
                        log_print(f"[{serial_number}] ⚠ 跳过无法访问的标签页: {str(e)}")
                        continue
                
                if asterdex_window:
                    # 切换到 asterdex 标签页
                    driver.switch_to.window(asterdex_window)
                    log_print(f"[{serial_number}] 打开目标URL: {target_url}")
                    driver.get(target_url)
                    log_print(f"[{serial_number}] ✓ 目标URL已打开")
                    time.sleep(2)  # 等待页面加载
                else:
                    log_print(f"[{serial_number}] ⚠ 未找到 asterdex 标签页，在当前标签页打开")
                    driver.get(target_url)
                    time.sleep(2)
                    
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 切换标签页失败: {str(e)}")
                # 继续执行，尝试在当前页面采集数据
            
            # 等待页面就绪（检查是否有 "Avbl" 或 "可用" 的 P 标签）
            is_ready, ready_msg = wait_for_page_ready(driver, serial_number, timeout=40)
            if not is_ready:
                log_print(f"[{serial_number}] ✗ 页面未就绪，跳过数据采集")
                # Type 5 不关闭浏览器
                should_close_browser = False
                if driver:
                    try:
                        driver.quit()
                        log_print(f"[{serial_number}] ✓ Selenium驱动已关闭")
                    except:
                        pass
                log_print(f"[{serial_number}] ℹ 浏览器保持打开状态")
                log_print(f"\n[{serial_number}] 处理完成\n")
                return False, ready_msg
            
            # 检查签名状态
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            if not is_signed:
                log_print(f"[{serial_number}] ✗ 钱包未签名，跳过数据采集")
                # Type 5 不关闭浏览器
                should_close_browser = False
                if driver:
                    try:
                        driver.quit()
                        log_print(f"[{serial_number}] ✓ Selenium驱动已关闭")
                    except:
                        pass
                log_print(f"[{serial_number}] ℹ 浏览器保持打开状态")
                log_print(f"\n[{serial_number}] 处理完成\n")
                return False, signature_msg
            
            # 收集并上传数据（与 Type 1 相同的逻辑）
            success, failure_reason = collect_and_submit_data(driver, serial_number)
            if success:
                log_print(f"[{serial_number}] ✓✓✓ 所有操作完成成功")
            
            # Type 5 不关闭浏览器
            should_close_browser = False
            
            # 清理 Selenium 驱动
            if driver:
                try:
                    driver.quit()
                    log_print(f"[{serial_number}] ✓ Selenium驱动已关闭")
                except:
                    pass
            
            log_print(f"[{serial_number}] ℹ 浏览器保持打开状态")
            log_print(f"\n[{serial_number}] 处理完成\n")
            return success, failure_reason
        
        # 其他类型需要启动浏览器
        # 对于 type=1 和 type=2，在启动浏览器前尝试获取并更新IP（3秒超时）
        if browser_type in [1, 2]:
            try_update_ip_before_start(serial_number)
        
        # 1. 启动浏览器
        browser_data = start_adspower_browser(serial_number)
        if not browser_data:
            failure_reason = "浏览器启动失败"
            return False, failure_reason
        
        # 2. 创建Selenium驱动
        try:
            driver = create_selenium_driver(browser_data)
            log_print(f"[{serial_number}] ✓ Selenium驱动创建成功")
        except Exception as e:
            log_print(f"[{serial_number}] ✗✗✗ 创建Selenium驱动失败: {str(e)}")
            failure_reason = "驱动创建失败"
            return False, failure_reason
        
        
        
        # 3. 根据 type 执行不同操作
        if browser_type == 1 or browser_type == 16:
            # Type 1: 获取数据、资产和仓位，完成后自动关闭浏览器
            log_print(f"[{serial_number}] Type 1: 收集数据")
            
            # 循环重试整个任务流程，直到成功或无法获取新IP
            retry_attempt = 0
            max_retry_attempts = 4  # 最大重试次数
            
            while retry_attempt < max_retry_attempts:
                if retry_attempt > 0:
                    log_print(f"[{serial_number}] ========== 重试第 {retry_attempt} 次 ==========")
                
                # 3.1 打开目标页面
                if not open_target_page(driver, serial_number):
                    log_print(f"[{serial_number}] ⚠ 页面打开失败，尝试更换IP重试...")
                    retry_attempt += 1
                    
                    # 尝试更换IP并重新打开浏览器
                    driver = retry_with_new_ip_and_reopen(serial_number, driver)
                    if not driver:
                        failure_reason = "页面打开失败，无法获取新IP"
                        return False, failure_reason
                    
                    # 继续下一次循环，重新尝试打开页面
                    continue
                
                # 页面打开成功，跳出循环继续后续逻辑
                if retry_attempt > 0:
                    log_print(f"[{serial_number}] ✓ 页面打开成功（重试 {retry_attempt} 次后）")
                break
            
            # 检查是否达到最大重试次数
            if retry_attempt >= max_retry_attempts:
                failure_reason = f"页面打开失败，已重试 {max_retry_attempts} 次"
                return False, failure_reason
            
            
            # 3.3 等待页面就绪（检查是否有 "Avbl" 或 "可用" 的 P 标签）
            is_ready, ready_msg = wait_for_page_ready(driver, serial_number, timeout=30)
            if not is_ready:
                log_print(f"[{serial_number}] ✗ 页面未就绪，跳过后续操作")
                failure_reason = ready_msg
                return False, failure_reason
            
            # 3.4 检查签名状态
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            
            # 3.2 处理钱包连接和签名流程
            password = get_browser_password(serial_number)  # 根据浏览器ID获取密码
            if password and not is_signed:
                log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                handle_wallet_connection_and_signature(driver, serial_number, password,1)
                
                # 刷新页面
                log_print(f"[{serial_number}] 刷新页面...")
                driver.refresh()
                time.sleep(2)
                
                # 等待页面加载完成
                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                log_print(f"[{serial_number}] ✓ 页面刷新完成")
                time.sleep(5)
            else:
                log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
                
                
            time.sleep(3)
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            if password and not is_signed:
                log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                handle_wallet_connection_and_signature(driver, serial_number, password,2)
                # 刷新页面
                log_print(f"[{serial_number}] 刷新页面...")
                driver.refresh()
                time.sleep(2)
                
                # 等待页面加载完成
                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                log_print(f"[{serial_number}] ✓ 页面刷新完成")
                time.sleep(5)
            else:
                log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
            
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            if not is_signed:
                log_print(f"[{serial_number}] ✗ 钱包未签名，跳过数据采集")
                failure_reason = signature_msg
                return False, failure_reason
            
 
            
            if browser_type == 1:
            # 3.5 收集并上传数据
                success, failure_reason = collect_and_submit_data(driver, serial_number)
                
                
                if success:
                    log_print(f"[{serial_number}] ✓✓✓ 所有操作完成成功")
            elif browser_type == 16:
                # Type 16: 获取 user-address 并更新配置字段 y
                log_print(f"[{serial_number}] Type 16: 开始获取用户地址并更新配置...")
                
                user_address = None
                
                # ========== 步骤1: 查找并获取 user-address ==========
                log_print(f"[{serial_number}] 步骤1: 查找包含 'user-address' 和 'text-subtitle1' 的 div...")
                
                max_find_retries = 10
                for find_retry in range(max_find_retries):
                    try:
                        # 查找同时包含 user-address 和 text-subtitle1 的 div
                        address_div = driver.find_element(By.XPATH, "//div[contains(@class, 'user-address') and contains(@class, 'text-subtitle1')]")
                        user_address = address_div.text.strip()
                        
                        if user_address:
                            log_print(f"[{serial_number}] ✓ 找到用户地址: {user_address}")
                            break
                        else:
                            log_print(f"[{serial_number}] ⚠ 找到元素但内容为空 (尝试 {find_retry + 1}/{max_find_retries})")
                            if find_retry < max_find_retries - 1:
                                time.sleep(2)
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 查找用户地址失败: {str(e)} (尝试 {find_retry + 1}/{max_find_retries})")
                        if find_retry < max_find_retries - 1:
                            time.sleep(2)
                
                if not user_address:
                    log_print(f"[{serial_number}] ✗ 未能获取用户地址")
                    failure_reason = "未能获取用户地址"
                    return False, failure_reason
                
                # ========== 步骤2: 更新配置字段 y ==========
                log_print(f"[{serial_number}] 步骤2: 更新账户配置字段 y...")
                
                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                user_no = str(serial_number)
                
                config_update_success = False
                max_config_retries = 3
                
                for config_attempt in range(max_config_retries):
                    try:
                        # 获取现有配置
                        log_print(f"[{serial_number}] 获取账户配置 (尝试 {config_attempt + 1}/{max_config_retries})...")
                        response = requests.get(
                            f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
                            headers={'Content-Type': 'application/json'},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            existing_data = result.get('data', {})
                            
                            if not existing_data:
                                log_print(f"[{serial_number}] ⚠ 未找到账户配置数据")
                                if config_attempt < max_config_retries - 1:
                                    time.sleep(2)
                                    continue
                                else:
                                    log_print(f"[{serial_number}] ✗ 无法获取账户配置，跳过更新")
                                    break
                            
                            log_print(f"[{serial_number}] ✓ 成功获取账户配置")
                            
                            # 只更新字段 y
                            existing_data['y'] = user_address
                            log_print(f"[{serial_number}] 设置 y={user_address}")
                            
                            # 提交更新
                            log_print(f"[{serial_number}] 提交配置更新...")
                            update_response = requests.post(
                                f"{API_BASE_URL}/addAccountConfig",
                                json=existing_data,
                                headers={'Content-Type': 'application/json'},
                                timeout=30
                            )
                            
                            if update_response.status_code == 200:
                                update_result = update_response.json()
                                code = update_result.get('code')
                                
                                if code == 0:
                                    log_print(f"[{serial_number}] ✓ 账户配置更新成功 (y={user_address})")
                                    config_update_success = True
                                    success = True
                                    break
                                else:
                                    log_print(f"[{serial_number}] ✗ 账户配置更新失败: code={code}, msg={update_result.get('msg')}")
                                    if config_attempt < max_config_retries - 1:
                                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                        time.sleep(2)
                            else:
                                log_print(f"[{serial_number}] ✗ 提交配置更新请求失败: HTTP {update_response.status_code}")
                                if config_attempt < max_config_retries - 1:
                                    time.sleep(2)
                        else:
                            log_print(f"[{serial_number}] ✗ 获取账户配置失败: HTTP {response.status_code}")
                            if config_attempt < max_config_retries - 1:
                                time.sleep(2)
                                
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 更新账户配置时出错: {str(e)}")
                        if config_attempt < max_config_retries - 1:
                            time.sleep(2)
                
                if not config_update_success:
                    log_print(f"[{serial_number}] ✗ 账户配置更新失败")
                    failure_reason = "配置更新失败"
                    return False, failure_reason
                else:
                    log_print(f"[{serial_number}] ✓✓✓ Type 16 所有操作完成成功")
            # Type 1 会自动关闭浏览器
        
        elif browser_type == 8:
            # Type 8: 先执行 Type 1 的所有逻辑，然后采集 Stage 3 Statistics 数据，最后关闭浏览器
            log_print(f"[{serial_number}] Type 8: 执行 Type 1 逻辑 + 采集 Stage 3 Statistics 数据")
            
            # ===== 第一部分：执行 Type 1 的所有逻辑 =====
            type1_success = False
            type1_failure_reason = ""
            
            try:
                log_print(f"[{serial_number}] [第1阶段] 开始执行 Type 1 逻辑...")
                
                # 循环重试整个任务流程，直到成功或无法获取新IP
                retry_attempt = 0
                max_retry_attempts = 4  # 最大重试次数
                
                while retry_attempt < max_retry_attempts:
                    if retry_attempt > 0:
                        log_print(f"[{serial_number}] ========== [第1阶段] 重试第 {retry_attempt} 次 ==========")
                    
                    # 3.1 打开目标页面
                    if not open_target_page(driver, serial_number):
                        log_print(f"[{serial_number}] ⚠ 页面打开失败，尝试更换IP重试...")
                        retry_attempt += 1
                        
                        # 尝试更换IP并重新打开浏览器
                        driver = retry_with_new_ip_and_reopen(serial_number, driver)
                        if not driver:
                            type1_failure_reason = "页面打开失败，无法获取新IP"
                            raise Exception(type1_failure_reason)
                        
                        # 继续下一次循环，重新尝试打开页面
                        continue
                    
                    # 页面打开成功，跳出循环继续后续逻辑
                    if retry_attempt > 0:
                        log_print(f"[{serial_number}] ✓ 页面打开成功（重试 {retry_attempt} 次后）")
                    break
                
                # 检查是否达到最大重试次数
                if retry_attempt >= max_retry_attempts:
                    type1_failure_reason = f"页面打开失败，已重试 {max_retry_attempts} 次"
                    raise Exception(type1_failure_reason)
                
                # 3.3 等待页面就绪（检查是否有 "Avbl" 或 "可用" 的 P 标签）
                is_ready, ready_msg = wait_for_page_ready(driver, serial_number, timeout=30)
                if not is_ready:
                    log_print(f"[{serial_number}] ✗ 页面未就绪，跳过后续操作")
                    type1_failure_reason = ready_msg
                    raise Exception(type1_failure_reason)
                
                # 3.4 检查签名状态
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                
                # 3.2 处理钱包连接和签名流程
                password = get_browser_password(serial_number)  # 根据浏览器ID获取密码
                if password and not is_signed:
                    log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                    handle_wallet_connection_and_signature(driver, serial_number, password, 1)
                    
                    # 刷新页面
                    log_print(f"[{serial_number}] 刷新页面...")
                    driver.refresh()
                    time.sleep(2)
                    
                    # 等待页面加载完成
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                    log_print(f"[{serial_number}] ✓ 页面刷新完成")
                    time.sleep(5)
                else:
                    log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
                
                time.sleep(3)
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                if password and not is_signed:
                    log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                    handle_wallet_connection_and_signature(driver, serial_number, password, 2)
                    # 刷新页面
                    log_print(f"[{serial_number}] 刷新页面...")
                    driver.refresh()
                    time.sleep(2)
                    
                    # 等待页面加载完成
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                    log_print(f"[{serial_number}] ✓ 页面刷新完成")
                    time.sleep(5)
                else:
                    log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
                
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                if not is_signed:
                    log_print(f"[{serial_number}] ✗ 钱包未签名，跳过数据采集")
                    type1_failure_reason = signature_msg
                    raise Exception(type1_failure_reason)
                
        
                
                # 3.5 收集并上传数据
                type1_success, type1_failure_reason = collect_and_submit_data(driver, serial_number)
                
                if type1_success:
                    log_print(f"[{serial_number}] [第1阶段] ✓✓✓ Type 1 逻辑执行成功")
                else:
                    log_print(f"[{serial_number}] [第1阶段] ✗✗✗ Type 1 逻辑执行失败: {type1_failure_reason}")
                    
            except Exception as e:
                type1_success = False
                if not type1_failure_reason:
                    type1_failure_reason = str(e)
                log_print(f"[{serial_number}] [第1阶段] ✗✗✗ Type 1 逻辑执行异常: {type1_failure_reason}")
            
            # ===== 第二部分：执行 Type 8 特有逻辑（采集 Stage 3 Statistics）=====
            # 若第1阶段失败，则不执行第2阶段，直接结束
            if not type1_success:
                success = False
                failure_reason = f"获取资产失败({type1_failure_reason})"
                log_print(f"[{serial_number}] [第2阶段] 跳过：第1阶段失败，不执行 Stage 3 Statistics 采集")
                return success, failure_reason

            type8_success = False
            type8_failure_reason = ""
            
            try:
                # 解析 tp1 作为随机停留区间（如 "5-10"），解析失败则使用 10~180
                raw_tp1 = str(browser_config.get("tp1", "")).strip()
                min_stay, max_stay = 5, 30
                if raw_tp1 and "-" in raw_tp1:
                    try:
                        a, b = raw_tp1.split("-", 1)
                        a = int(str(a).strip())
                        b = int(str(b).strip())
                        lo, hi = (a, b) if a <= b else (b, a)
                        # 合理边界：不小于1秒，且最大不超过 3600 秒
                        lo = max(1, lo)
                        hi = min(3600, hi)
                        if lo < hi:
                            min_stay, max_stay = lo, hi
                    except Exception:
                        pass

                # 初始随机停留
                wait_seconds = random.randint(min_stay, max_stay)
                log_print(f"[{serial_number}] [第2阶段] 随机等待 {wait_seconds} 秒后开始路径访问...")
                time.sleep(wait_seconds)

                # 从 RANDOM_PATH 中随机选择一组路径
                selected_group = random.choice(RANDOM_PATH)
                # 过滤掉统计页，随机抽取 >=2 条路径
                stats_url = "https://www.asterdex.com/en/stage3/statistics"
                other_urls = [u for u in selected_group if u != stats_url]
                if len(other_urls) < 2:
                    type8_failure_reason = "随机路径数量不足"
                    raise Exception(type8_failure_reason)

                # 抽取随机路径：至少2条，最多3条
                k = random.randint(2, min(3, len(other_urls)))
                random_urls = random.sample(other_urls, k)
                # 拼上统计页并随机排序
                visit_urls = random_urls + [stats_url]
                random.shuffle(visit_urls)

                log_print(f"[{serial_number}] [第2阶段] 本次将依次访问 {len(visit_urls)} 个页面")

                collected_data = None
                stage_success = False
                stage_failure_reason = ""

                for idx, url in enumerate(visit_urls, start=1):
                    log_print(f"[{serial_number}] [第2阶段] ({idx}/{len(visit_urls)}) 打开页面: {url}")
                    try:
                        driver.get(url)
                    except Exception as e:
                        log_print(f"[{serial_number}] [第2阶段] 打开页面失败: {str(e)}")
                        # 继续访问后续页面
                        pass

                    # 每页随机停留（使用解析后的区间）
                    stay_seconds = random.randint(min_stay, max_stay)
                    log_print(f"[{serial_number}] [第2阶段] 页面停留 {stay_seconds} 秒...")
                    time.sleep(stay_seconds)

                    # 如果是统计页，执行采集
                    if url == stats_url:
                        log_print(f"[{serial_number}] [第2阶段] 采集统计页数据...")
                        stage_success, stage_failure_reason, collected_data = collect_stage3_statistics(driver, serial_number)
                
                if not stage_success:
                    type8_failure_reason = stage_failure_reason
                    log_print(f"[{serial_number}] [第2阶段] ✗ Stage 3 Statistics 数据采集失败: {stage_failure_reason}")
                    raise Exception(stage_failure_reason)
                
                if not collected_data:
                    type8_failure_reason = "无数据可提交"
                    log_print(f"[{serial_number}] [第2阶段] ✗ 无数据可提交")
                    raise Exception(type8_failure_reason)
                
                # 提交数据到服务器
                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                max_upload_retries = 2
                upload_success = False
                
                for attempt in range(max_upload_retries):
                    try:
                        log_print(f"[{serial_number}] [第2阶段] 正在提交积分数据... (尝试 {attempt + 1}/{max_upload_retries})")
                        
                        # 构建数据对象
                        integral_data = {
                            "no": serial_number,  # 浏览器编号
                            "a": collected_data.get('currentPoints', ''),      # Current points
                            "b": collected_data.get('ranking', ''),            # Ranking
                            "c": collected_data.get('yourShare', ''),          # Your share
                            "d": collected_data.get('teamBoost', ''),          # Team boost
                            "e": collected_data.get('tradePoints', ''),        # Trade points
                            "f": collected_data.get('positionPoints', ''),     # Position points
                            "g": collected_data.get('usdfAsBnbPoints', ''),    # USDF/asBNB points
                            "h": collected_data.get('profitPoints', ''),       # Profit points
                            "i": collected_data.get('lossPoints', ''),         # Loss points
                            "j": collected_data.get('referralPoints', ''),     # Referral points
                            "time": int(time.time() * 1000)  # 当前时间戳（毫秒）
                        }
                        
                        # 包装成数组
                        integral_list = [integral_data]
                        
                        response = requests.post(
                            f"{API_BASE_URL}/insertIntegralList",
                            json=integral_list,
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            code = result.get('code')
                            
                            if code == 0:
                                log_print(f"[{serial_number}] [第2阶段] ✓ 积分数据提交成功 (code=0)")
                                upload_success = True
                                break
                            else:
                                log_print(f"[{serial_number}] [第2阶段] ✗ 积分数据提交失败: code={code}, msg={result.get('msg')}")
                                if attempt < max_upload_retries - 1:
                                    log_print(f"[{serial_number}] [第2阶段] 等待 2 秒后重试...")
                                    time.sleep(2)
                        else:
                            log_print(f"[{serial_number}] [第2阶段] ✗ 积分数据提交失败: HTTP状态码 {response.status_code}")
                            if attempt < max_upload_retries - 1:
                                log_print(f"[{serial_number}] [第2阶段] 等待 2 秒后重试...")
                                time.sleep(2)
                    except Exception as e:
                        log_print(f"[{serial_number}] [第2阶段] ✗ 积分数据提交异常: {str(e)}")
                        if attempt < max_upload_retries - 1:
                            log_print(f"[{serial_number}] [第2阶段] 等待 2 秒后重试...")
                            time.sleep(2)
                
                if upload_success:
                    log_print(f"[{serial_number}] [第2阶段] ✓ 积分数据提交成功")
                    
                    # 更新账户配置（g: currentPoints, h: 时间戳）
                    try:
                        log_print(f"[{serial_number}] [第2阶段] 正在更新账户配置...")
                        
                        # 1. 获取现有配置
                        response = requests.get(
                            f"{API_BASE_URL}/findAccountConfigByNo?no={serial_number}",
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            existing_data = response.json()
                            # 更新配置（只更新 g 和 h）
                            updated_config = existing_data.get('data', {})
                            updated_config.update({
                                "fingerprintNo": serial_number,
                                "g": collected_data.get('currentPoints', ''),  # g: currentPoints
                                "h": int(time.time() * 1000),  # h: 当前时间戳（毫秒）
                            })
                            
                            # 2. 提交更新
                            response = requests.post(
                                f"{API_BASE_URL}/addAccountConfig",
                                json=updated_config,
                                headers={'Content-Type': 'application/json'},
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                code = result.get('code')
                                if code == 0:
                                    log_print(f"[{serial_number}] [第2阶段] ✓ 账户配置更新成功 (g={collected_data.get('currentPoints', '')})")
                                    type8_success = True
                                else:
                                    log_print(f"[{serial_number}] [第2阶段] ✗ 账户配置更新失败: code={code}, msg={result.get('msg')}")
                                    type8_failure_reason = f"账户配置更新失败: {result.get('msg')}"
                            else:
                                log_print(f"[{serial_number}] [第2阶段] ✗ 账户配置更新失败: HTTP状态码 {response.status_code}")
                                type8_failure_reason = f"账户配置更新失败: HTTP {response.status_code}"
                        else:
                            log_print(f"[{serial_number}] [第2阶段] ✗ 获取账户配置失败: HTTP状态码 {response.status_code}")
                            type8_failure_reason = f"获取账户配置失败: HTTP {response.status_code}"
                    
                    except Exception as e:
                        log_print(f"[{serial_number}] [第2阶段] ✗ 账户配置更新异常: {str(e)}")
                        type8_failure_reason = f"账户配置更新异常: {str(e)}"
                    
                    if type8_success:
                        log_print(f"[{serial_number}] [第2阶段] ✓✓✓ Stage 3 Statistics 数据采集和提交完成")
                    else:
                        log_print(f"[{serial_number}] [第2阶段] ✗✗✗ 账户配置更新失败: {type8_failure_reason}")
                        raise Exception(type8_failure_reason)
                else:
                    type8_failure_reason = "积分数据提交失败"
                    log_print(f"[{serial_number}] [第2阶段] ✗✗✗ 积分数据提交失败")
                    raise Exception(type8_failure_reason)
                    
            except Exception as e:
                type8_success = False
                if not type8_failure_reason:
                    type8_failure_reason = str(e)
                log_print(f"[{serial_number}] [第2阶段] ✗✗✗ Type 8 逻辑执行异常: {type8_failure_reason}")
            
            # ===== 合并两个阶段的结果 =====
            # 成功状态取 & （两个都成功才算成功）
            success = type1_success and type8_success
            
            # 合并失败原因
            if not type1_success and not type8_success:
                failure_reason = f"获取资产失败({type1_failure_reason}) & 获取积分失败({type8_failure_reason})"
            elif not type1_success:
                failure_reason = f"获取资产失败({type1_failure_reason})"
            elif not type8_success:
                failure_reason = f"获取资产失败({type8_failure_reason})"
            else:
                failure_reason = ""
            
            # 输出最终结果
            if success:
                log_print(f"[{serial_number}] ✓✓✓ Type 8 所有操作完成成功 (Type1成功 & Type8成功)")
            else:
                log_print(f"[{serial_number}] ✗✗✗ Type 8 操作失败: {failure_reason}")
            
            # Type 8 会自动关闭浏览器（在 finally 块中处理）
        
        elif browser_type == 2:
           # Type 11: 先执行 Type 1 的操作，成功后不关闭浏览器，继续执行 Type 2 的操作
            log_print(f"[{serial_number}] Type 11: 执行 Type 1 + Type 2 组合任务")
            
            # ===== 第一部分：执行 Type 1 的所有逻辑 =====
            type1_success = False
            type1_failure_reason = ""
            
            try:
                log_print(f"[{serial_number}] [第1阶段] 开始执行 Type 1 逻辑...")
                
                # 循环重试整个任务流程，直到成功或无法获取新IP
                retry_attempt = 0
                max_retry_attempts = 3  # 最大重试次数
                time.sleep(5)
                while retry_attempt < max_retry_attempts:
                    if retry_attempt > 0:
                        log_print(f"[{serial_number}] ========== [第1阶段] 重试第 {retry_attempt} 次 ==========")
                    # 3.1 打开目标页面
                    if not open_target_page(driver, serial_number):
                        log_print(f"[{serial_number}] ⚠ 页面打开失败，尝试更换IP重试...")
                        retry_attempt += 1
                        
                        # 尝试更换IP并重新打开浏览器
                        driver = retry_with_new_ip_and_reopen(serial_number, driver)
                        if not driver:
                            type1_failure_reason = "页面打开失败，无法获取新IP"
                            raise Exception(type1_failure_reason)
                        
                        # 继续下一次循环，重新尝试打开页面
                        continue
                    
                    # 页面打开成功，跳出循环继续后续逻辑
                    if retry_attempt > 0:
                        log_print(f"[{serial_number}] ✓ 页面打开成功（重试 {retry_attempt} 次后）")
                    break
                
                # 检查是否达到最大重试次数
                if retry_attempt >= max_retry_attempts:
                    type1_failure_reason = f"页面打开失败，已重试 {max_retry_attempts} 次"
                    raise Exception(type1_failure_reason)
                
                # 3.3 等待页面就绪（检查是否有 "Avbl" 或 "可用" 的 P 标签）
                is_ready, ready_msg = wait_for_page_ready(driver, serial_number, timeout=30)
                if not is_ready:
                    log_print(f"[{serial_number}] ✗ 页面未就绪，跳过后续操作")
                    type1_failure_reason = ready_msg
                    raise Exception(type1_failure_reason)
                
                # 3.4 检查签名状态
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                
                # 3.2 处理钱包连接和签名流程
                password = get_browser_password(serial_number)
                if password and not is_signed:
                    log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                    handle_wallet_connection_and_signature(driver, serial_number, password, 1)
                    
                    # 刷新页面
                    log_print(f"[{serial_number}] 刷新页面...")
                    driver.refresh()
                    time.sleep(2)
                    
                    # 等待页面加载完成
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                    log_print(f"[{serial_number}] ✓ 页面刷新完成")
                    time.sleep(5)
                else:
                    log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
                
                time.sleep(3)
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                if password and not is_signed:
                    log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                    handle_wallet_connection_and_signature(driver, serial_number, password, 2)
                    # 刷新页面
                    log_print(f"[{serial_number}] 刷新页面...")
                    driver.refresh()
                    time.sleep(2)
                    
                    # 等待页面加载完成
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                    log_print(f"[{serial_number}] ✓ 页面刷新完成")
                    time.sleep(5)
                else:
                    log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
                
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                if not is_signed:
                    log_print(f"[{serial_number}] ✗ 钱包未签名，跳过数据采集")
                    type1_failure_reason = signature_msg
                    raise Exception(type1_failure_reason)
                
                # 3.5 收集并上传数据
                type1_success, type1_failure_reason = collect_and_submit_data(driver, serial_number)
                
                if not type1_success:
                    raise Exception(type1_failure_reason)
                
                log_print(f"[{serial_number}] ✓✓✓ [第1阶段] Type 1 逻辑执行成功")
                
            except Exception as e:
                log_print(f"[{serial_number}] ✗✗✗ [第1阶段] Type 1 逻辑执行失败: {str(e)}")
                # Type 1 失败，不执行 Type 2，关闭浏览器并返回失败
                success = False
                failure_reason = f"获取资产失败: {type1_failure_reason}"
                should_close_browser = True
                return False, failure_reason
            
            # ===== 第二部分：Type 1 成功后，执行 Type 2 的逻辑 =====
            log_print(f"[{serial_number}] [第2阶段] Type 1 成功，继续执行 Type 2 逻辑...")
            try:
                # Type 2 的逻辑：处理扩展页面和 asterdex 页面
                # 获取扩展ID
                extension_id = "nlhpgkjhfifbhmgiiliahafldechalmn"
                extension_url = f"chrome-extension://{extension_id}/popup.html"
                
                log_print(f"[{serial_number}] 查找包含扩展ID的标签页...")
                
                all_windows = driver.window_handles
                extension_window = None
                
                # 查找包含扩展ID的标签页
                for window_handle in all_windows:
                    try:
                        driver.switch_to.window(window_handle)
                        current_url = driver.current_url
                        if extension_id in current_url:
                            extension_window = window_handle
                            log_print(f"[{serial_number}] ✓ 找到扩展标签页: {current_url}")
                            break
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 跳过无法访问的标签页: {str(e)}")
                        continue
                
                if extension_window:
                    # log_print(f"[{serial_number}] 切换到扩展标签页并打开: {extension_url}")
                    # driver.switch_to.window(extension_window)
                    # driver.get(extension_url)
                    log_print(f"[{serial_number}] ✓ 扩展页面已打开")
                else:
                    log_print(f"[{serial_number}] 创建新标签页打开扩展页面: {extension_url}")
                    driver.switch_to.new_window('tab')
                    driver.get(extension_url)
                    log_print(f"[{serial_number}] ✓ 扩展页面已在新标签页打开")
                
                # 等待10秒
                log_print(f"[{serial_number}] 等待3秒...")
                time.sleep(3)
                
                # 处理 asterdex 标签页
                asterdex_url = "https://www.asterdex.com/en/futures/v1/BTCUSDT"
                log_print(f"[{serial_number}] 查找包含 asterdex 的标签页...")
                
                # 记录页面加载开始时间
                page_load_start_time = time.time()
                
                all_windows = driver.window_handles
                asterdex_window = None
                
                for window_handle in all_windows:
                    try:
                        driver.switch_to.window(window_handle)
                        current_url = driver.current_url
                        if "asterdex.com" in current_url:
                            asterdex_window = window_handle
                            log_print(f"[{serial_number}] ✓ 找到 asterdex 标签页: {current_url}")
                            break
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 跳过无法访问的标签页: {str(e)}")
                        continue
                
                if asterdex_window:
                    log_print(f"[{serial_number}] 切换到 asterdex 标签页")
                    driver.switch_to.window(asterdex_window)
                    time.sleep(2)
                    driver.get(asterdex_url)
                    log_print(f"[{serial_number}] ✓ 已切换到 asterdex 标签页")
                else:
                    log_print(f"[{serial_number}] 创建新标签页打开: {asterdex_url}")
                    driver.switch_to.new_window('tab')
                    driver.get(asterdex_url)
                    log_print(f"[{serial_number}] ✓ asterdex 页面已在新标签页打开")
                
                time.sleep(2)
                
                # 等待页面就绪（不使用重试，因为已经在 Type 1 中验证过）
                is_ready, ready_msg = wait_for_page_ready(driver, serial_number, timeout=20)
                if not is_ready:
                    log_print(f"[{serial_number}] ⚠ 页面未就绪: {ready_msg}")
                
                # 计算页面加载时间并上传
                page_load_time = time.time() - page_load_start_time
                log_print(f"[{serial_number}] 页面加载耗时: {page_load_time:.2f} 秒")
                
                # 定义 user_no
                user_no = str(serial_number)
                
                try:
                    upload_data = {
                        "number": user_no,
                        "openTime": round(page_load_time, 2)  # 保留2位小数
                    }
                    upload_response = requests.post(
                        "https://sg.bicoin.com.cn/99j/hedge/pageOpenTime",
                        json=upload_data,
                        timeout=10
                    )
                    if upload_response.status_code == 200:
                        log_print(f"[{serial_number}] ✓ 页面加载时间上传成功: {page_load_time:.2f}秒")
                    else:
                        log_print(f"[{serial_number}] ⚠ 页面加载时间上传失败: HTTP {upload_response.status_code}")
                except Exception as upload_error:
                    log_print(f"[{serial_number}] ⚠ 页面加载时间上传异常: {str(upload_error)}")
                
                    
                is_signed, signature_msg = check_wallet_signature(driver, serial_number)
                if not is_signed:
                        success = False  # Type 1 成功了
                        failure_reason = f"钱包连接失败: {signature_msg}"
                        should_close_browser = True  # 关闭浏览器  
       
                
                log_print(f"[{serial_number}] ✓✓✓ [第2阶段] Type 2 逻辑执行完成")
                success = True
                should_close_browser = False  # Type 11 不关闭浏览器
                
            except Exception as e:
                log_print(f"[{serial_number}] ✗ [第2阶段] Type 2 处理失败: {str(e)}")
                import traceback
                log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
                # Type 2 失败，但 Type 1 已成功，仍然算部分成功
                success = False  # Type 1 成功了
                failure_reason = f"打开插件失败"
                should_close_browser = True  # 关闭浏览器    
        
        elif browser_type == 14  or browser_type == 15:
            # Type 14: 执行 Airdrop 空投任务（Refund Commission），完成后自动关闭浏览器
            retry_attempt = 0
            max_retry_attempts = 2  # 最大重试次数
            
            while retry_attempt < max_retry_attempts:
                if retry_attempt > 0:
                    log_print(f"[{serial_number}] ========== 重试第 {retry_attempt} 次 ==========")
                # 3.1 打开目标页面
                if not open_target_page(driver, serial_number):
                    log_print(f"[{serial_number}] ⚠ 页面打开失败，尝试更换IP重试...")
                    retry_attempt += 1
                    # 尝试更换IP并重新打开浏览器
                    driver = retry_with_new_ip_and_reopen(serial_number, driver)
                    if not driver:
                        failure_reason = "页面打开失败，无法获取新IP"
                        return False, failure_reason
                    # 继续下一次循环，重新尝试打开页面
                    continue
                
                # 页面打开成功，跳出循环继续后续逻辑
                if retry_attempt > 0:
                    log_print(f"[{serial_number}] ✓ 页面打开成功（重试 {retry_attempt} 次后）")
                break
            
            # 检查是否达到最大重试次数
            if retry_attempt >= max_retry_attempts:
                failure_reason = f"页面打开失败，已重试 {max_retry_attempts} 次"
                return False, failure_reason
            
            
            # 3.3 等待页面就绪（检查是否有 "Avbl" 或 "可用" 的 P 标签）
            is_ready, ready_msg = wait_for_page_ready(driver, serial_number, timeout=30)
            if not is_ready:
                log_print(f"[{serial_number}] ✗ 页面未就绪，跳过后续操作")
                failure_reason = ready_msg
                return False, failure_reason
            
            # 保存主窗口句柄
            main_window = driver.current_window_handle
            log_print(f"[{serial_number}] 已保存主窗口句柄: {main_window}")
            
            # ==================== 预处理: 打开 OKX 钱包页面 ====================
            log_print(f"[{serial_number}] ")
            log_print(f"[{serial_number}] [预处理] 预先打开 OKX 钱包页面...")
            
            okx_extension_id = "mcohilncbfahbmgdjkbpemcciiolgcge"
            okx_popup_url = f"chrome-extension://{okx_extension_id}/popup.html"
            try:
                    # 使用 open_new_tab_with_url 方法打开 OKX 钱包
                    log_print(f"[{serial_number}] → 使用 open_new_tab_with_url 打开 OKX 钱包...")
                    success = open_new_tab_with_url(driver, okx_popup_url, serial_number)
                    
                    if success:
                        log_print(f"[{serial_number}] ✓ OKX 钱包页面已打开")
                    else:
                        log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包失败，继续执行...")
                        time.sleep(3)
                        
                    # 切换回主窗口
                    log_print(f"[{serial_number}] → 切换回主窗口: {main_window}")
                    driver.switch_to.window(main_window)
                    log_print(f"[{serial_number}] ✓ 已切换回主窗口")
                    
                    # 等待1秒
                    log_print(f"[{serial_number}] → 等待 1 秒...")
                    time.sleep(1)
                        
            except Exception as e:
                    log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包异常: {str(e)}，继续执行...")
                
            # 3.4 检查签名状态
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            
            # 3.2 处理钱包连接和签名流程
            password = get_browser_password(serial_number)  # 根据浏览器ID获取密码
            if password and not is_signed:
                log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                handle_wallet_connection_and_signature(driver, serial_number, password,1)
                
                # 刷新页面
                log_print(f"[{serial_number}] 刷新页面...")
                driver.refresh()
                time.sleep(2)
                
                # 等待页面加载完成
                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                log_print(f"[{serial_number}] ✓ 页面刷新完成")
                time.sleep(5)
            else:
                log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
                
                
            time.sleep(3)
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            if password and not is_signed:
                log_print(f"[{serial_number}] 开始处理钱包连接和签名...")
                handle_wallet_connection_and_signature(driver, serial_number, password,2)
                # 刷新页面
                log_print(f"[{serial_number}] 刷新页面...")
                driver.refresh()
                time.sleep(2)
                
                # 等待页面加载完成
                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-t-third.flex.gap-1")))
                log_print(f"[{serial_number}] ✓ 页面刷新完成")
                time.sleep(5)
            else:
                log_print(f"[{serial_number}] ⚠ 未提供钱包密码，跳过钱包连接流程")
            
            is_signed, signature_msg = check_wallet_signature(driver, serial_number)
            if not is_signed:
                log_print(f"[{serial_number}] ✗ 钱包未签名，跳过后续操作")
                failure_reason = signature_msg
                return False, failure_reason
            
            # ========== Type 15: 随机路径访问阶段 ==========
            log_print(f"[{serial_number}] [Type 15 - 第1阶段] 开始随机路径访问...")
            
            try:
                # 解析 tp1 作为随机停留区间（如 "5-10"），解析失败则使用 10~180
                raw_tp1 = str(browser_config.get("tp1", "")).strip()
                min_stay, max_stay = 5, 30
                if raw_tp1 and "-" in raw_tp1:
                    try:
                        a, b = raw_tp1.split("-", 1)
                        a = int(str(a).strip())
                        b = int(str(b).strip())
                        lo, hi = (a, b) if a <= b else (b, a)
                        # 合理边界：不小于1秒，且最大不超过 3600 秒
                        lo = max(1, lo)
                        hi = min(3600, hi)
                        if lo < hi:
                            min_stay, max_stay = lo, hi
                    except Exception:
                        pass

                # 初始随机停留
                wait_seconds = random.randint(min_stay, max_stay)
                log_print(f"[{serial_number}] [Type 15 - 第1阶段] 随机等待 {wait_seconds} 秒后开始路径访问...")
                time.sleep(wait_seconds)

                # 从 RANDOM_PATH 中随机选择一组路径
                selected_group = random.choice(RANDOM_PATH)
                # 过滤掉统计页和 airdrop 页，随机抽取 >=2 条路径
                stats_url = "https://www.asterdex.com/en/stage3/statistics"
                airdrop_url = "https://www.asterdex.com/en/airdrop"
                other_urls = [u for u in selected_group if u not in [stats_url, airdrop_url]]
                if len(other_urls) < 2:
                    log_print(f"[{serial_number}] [Type 15 - 第1阶段] ⚠ 随机路径数量不足，继续执行")
                    other_urls = [u for u in selected_group if u != airdrop_url][:2]

                # 抽取随机路径：至少2条，最多3条
                k = random.randint(2, min(3, len(other_urls)))
                random_urls = random.sample(other_urls, k) if len(other_urls) >= k else other_urls
                # 拼上 airdrop 页面并随机排序
                visit_urls = random_urls + [airdrop_url]
                random.shuffle(visit_urls)

                log_print(f"[{serial_number}] [Type 15 - 第1阶段] 本次将依次访问 {len(visit_urls)} 个页面")

                airdrop_page_reached = False
                
                for idx, url in enumerate(visit_urls, start=1):
                    log_print(f"[{serial_number}] [Type 15 - 第1阶段] ({idx}/{len(visit_urls)}) 打开页面: {url}")
                    try:
                        driver.get(url)
                    except Exception as e:
                        log_print(f"[{serial_number}] [Type 15 - 第1阶段] 打开页面失败: {str(e)}")
                        # 继续访问后续页面
                        pass

                    # 每页随机停留（使用解析后的区间）
                    stay_seconds = random.randint(min_stay, max_stay)
                    log_print(f"[{serial_number}] [Type 15 - 第1阶段] 页面停留 {stay_seconds} 秒...")
                    time.sleep(stay_seconds)

                    # 如果是 airdrop 页面，标记已到达并跳出循环
                    if url == airdrop_url:
                        log_print(f"[{serial_number}] [Type 15 - 第1阶段] ✓ 已到达 airdrop 页面，准备执行后续操作")
                        airdrop_page_reached = True
                        break
                
                if not airdrop_page_reached:
                    log_print(f"[{serial_number}] [Type 15 - 第1阶段] ⚠ 未能访问到 airdrop 页面，尝试直接打开")
                    try:
                        driver.get(airdrop_url)
                        log_print(f"[{serial_number}] ✓ 已打开 {airdrop_url}")
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 打开 airdrop 页面失败: {str(e)}")
                        failure_reason = "打开airdrop页面失败"
                        return False, failure_reason
                else:
                    log_print(f"[{serial_number}] ✓ 已在 airdrop 页面")
                    
            except Exception as e:
                log_print(f"[{serial_number}] [Type 15 - 第1阶段] ✗ 随机路径访问异常: {str(e)}")
                # 即使异常，也尝试打开 airdrop 页面
                try:
                    log_print(f"[{serial_number}] 尝试直接打开 airdrop 页面...")
                    driver.get(airdrop_url)
                    log_print(f"[{serial_number}] ✓ 已打开 {airdrop_url}")
                except Exception as e2:
                    log_print(f"[{serial_number}] ✗ 打开 airdrop 页面失败: {str(e2)}")
                    failure_reason = "打开airdrop页面失败"
                    return False, failure_reason
            
            # ========== Type 15: 开始 airdrop 页面操作 ==========
            log_print(f"[{serial_number}] [Type 15 - 第2阶段] 开始执行 airdrop 页面操作...")
            
            # 步骤1: 等待页面加载完成（检查 h1 标签），最多重试3次
            page_load_success = False
            for page_retry in range(3):
                log_print(f"[{serial_number}] 检查页面是否加载完成 (尝试 {page_retry + 1}/3)...")
                try:
                    wait = WebDriverWait(driver, 15)
                    h1_element = wait.until(
                        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Aster Airdrop on Stage 2')]"))
                    )
                    if h1_element:
                        log_print(f"[{serial_number}] ✓ 页面加载完成，找到目标 h1 标签")
                        page_load_success = True
                        break
                except Exception as e:
                    log_print(f"[{serial_number}] ⚠ 未找到目标 h1 标签 (尝试 {page_retry + 1}/3)")
                    if page_retry < 2:  # 不是最后一次尝试
                        log_print(f"[{serial_number}] 刷新页面重试...")
                        driver.refresh()
                        time.sleep(2)
            
            if not page_load_success:
                log_print(f"[{serial_number}] ✗ 页面加载失败，未找到目标 h1 标签（已重试3次）")
                failure_reason = "页面加载失败，未找到Aster Airdrop on Stage 2标题"
                return False, failure_reason
            
            # 页面加载成功，等待3秒
            log_print(f"[{serial_number}] 等待3秒...")
            time.sleep(3)
            
            # ========== Type 14 和 Type 15 的分支逻辑 ==========
            
                # 步骤2: 点击 "Check eligibility" 按钮，最多重试10次
            log_print(f"[{serial_number}] 开始处理 'Check eligibility' 按钮...")
            check_eligibility_clicked = False
            for eligibility_retry in range(10):
                    try:
                        # 查找内容等于 "Check eligibility" 的 span
                        check_span = driver.find_element(By.XPATH, "//span[text()='Check eligibility']")
                        if check_span:
                            # 找到 span 的父节点的父节点并点击
                            parent_parent = check_span.find_element(By.XPATH, "../..")
                            parent_parent.click()
                            log_print(f"[{serial_number}] ✓ 点击了 'Check eligibility' 按钮 (第 {eligibility_retry + 1} 次)")
                            check_eligibility_clicked = True
                            time.sleep(3)
                        else:
                            # 没有找到，说明已经点击完成
                            log_print(f"[{serial_number}] ✓ 没有找到 'Check eligibility' 按钮，已完成点击")
                            break
                    except Exception as e:
                        # 没有找到元素，说明已经点击完成
                        log_print(f"[{serial_number}] ✓ 'Check eligibility' 按钮处理完成")
                        break
            
            # 检查是否达到最大重试次数但仍有按钮
            try:
                    check_span = driver.find_element(By.XPATH, "//span[text()='Check eligibility']")
                    if check_span and eligibility_retry >= 9:
                        log_print(f"[{serial_number}] ✗ 'Check eligibility' 按钮点击失败（已重试10次）")
                        failure_reason = "Check eligibility按钮点击失败，重试10次仍存在"
                        return False, failure_reason
            except:
                    pass  # 没有找到按钮，正常情况
                
                # 步骤3: 查找 "Refund Commission" div
            log_print(f"[{serial_number}] 查找 'Refund Commission' 选项...")
            refund_commission_div = None
            refund_commission_button = None
                
            try:
                    refund_commission_div = driver.find_element(By.XPATH, "//div[text()='Refund Commission']")
                    log_print(f"[{serial_number}] ✓ 找到 'Refund Commission' div")
                    
                    # 找到其父节点的父节点（button）
                    refund_commission_button = refund_commission_div.find_element(By.XPATH, "../..")
                    log_print(f"[{serial_number}] ✓ 找到 'Refund Commission' 对应的 button")
                    
            except Exception as e:
                    # 检查是否既没有 "Check eligibility" 也没有 "Refund Commission"
                    has_check_eligibility = False
                    try:
                        driver.find_element(By.XPATH, "//span[text()='Check eligibility']")
                        has_check_eligibility = True
                    except:
                        pass
                    
                    if not has_check_eligibility:
                        log_print(f"[{serial_number}] ⚠ 既没有 'Check eligibility' 也没有 'Refund Commission'，检查是否不符合资格...")
                        
                        # 查找是否有 "You do not meet the eligibility requirements"
                        try:
                            not_eligible_element = driver.find_element(By.XPATH, "//*[contains(text(), 'You do not meet the eligibility requirements')]")
                            if not_eligible_element:
                                log_print(f"[{serial_number}] ⚠ 检测到不符合资格提示，更新配置 i=2...")
                                
                                # 更新配置 i=2
                                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                                user_no = str(serial_number)
                                
                                try:
                                    # 获取现有配置
                                    response = requests.get(
                                        f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
                                        headers={'Content-Type': 'application/json'},
                                        timeout=10
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        existing_data = result.get('data', {})
                                        
                                        if existing_data:
                                            # 更新字段 i=2
                                            existing_data['j'] = 2
                                            log_print(f"[{serial_number}] 设置字段 j=2 (不符合资格)")
                                            
                                            # 提交更新
                                            update_response = requests.post(
                                                f"{API_BASE_URL}/addAccountConfig",
                                                json=existing_data,
                                                headers={'Content-Type': 'application/json'},
                                                timeout=10
                                            )
                                            
                                            if update_response.status_code == 200:
                                                update_result = update_response.json()
                                                if update_result.get('code') == 0:
                                                    log_print(f"[{serial_number}] ✓ 账户配置更新成功 (i=2)")
                                                    success = True
                                                    failure_reason = "不符合资格要求"
                                                    return True, failure_reason
                                                else:
                                                    log_print(f"[{serial_number}] ✗ 账户配置更新失败: code={update_result.get('code')}")
                                        else:
                                            log_print(f"[{serial_number}] ⚠ 未找到账户配置数据")
                                    else:
                                        log_print(f"[{serial_number}] ✗ 获取账户配置失败: HTTP {response.status_code}")
                                        
                                except Exception as config_error:
                                    log_print(f"[{serial_number}] ✗ 更新配置时出错: {str(config_error)}")
                                
                                failure_reason = "不符合资格要求"
                                return False, failure_reason
                        except:
                            pass
                        
                        log_print(f"[{serial_number}] ✗ 页面状态异常，未找到预期的按钮或选项")
                        failure_reason = "页面状态异常，未找到预期的按钮或选项"
                        return False, failure_reason
            
            if browser_type == 14:
                # 步骤4: 点击 button 直到 data-state 等于 "active"
                if refund_commission_button:
                    log_print(f"[{serial_number}] 开始激活 'Refund Commission' 选项...")
                    max_active_retries = 20  # 最多重试20次
                    for active_retry in range(max_active_retries):
                        try:
                            data_state = refund_commission_button.get_attribute("data-state")
                            log_print(f"[{serial_number}] 当前 data-state: {data_state} (检查 {active_retry + 1}/{max_active_retries})")
                            
                            if data_state == "active":
                                log_print(f"[{serial_number}] ✓ 'Refund Commission' 已激活 (data-state=active)")
                                break
                            else:
                                # data-state 不是 active，点击按钮
                                log_print(f"[{serial_number}] data-state={data_state}，点击按钮...")
                                refund_commission_button.click()
                                time.sleep(3)
                                # 重新获取元素，避免 stale element
                                refund_commission_div = driver.find_element(By.XPATH, "//div[text()='Refund Commission']")
                                refund_commission_button = refund_commission_div.find_element(By.XPATH, "../..")
                        except Exception as e:
                            log_print(f"[{serial_number}] ⚠ 检查/点击按钮时出错: {str(e)}")
                            if active_retry < max_active_retries - 1:
                                time.sleep(3)
                                continue
                            else:
                                log_print(f"[{serial_number}] ✗ 激活 'Refund Commission' 失败")
                                failure_reason = "激活Refund Commission失败"
                                return False, failure_reason
                    
                    # 最后检查是否真的激活了
                    try:
                        data_state = refund_commission_button.get_attribute("data-state")
                        if data_state != "active":
                            log_print(f"[{serial_number}] ✗ 'Refund Commission' 未能激活 (data-state={data_state})")
                            failure_reason = "Refund Commission未能激活"
                            return False, failure_reason
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 检查激活状态失败: {str(e)}")
                        failure_reason = "检查Refund Commission激活状态失败"
                        return False, failure_reason
                
                # 步骤5: 点击 "Select" 按钮，直到出现 "Selected"
                log_print(f"[{serial_number}] 开始点击 'Select' 按钮...")
                max_select_retries = 20  # 最多重试20次
                select_success = False
                
                for select_retry in range(max_select_retries):
                    try:
                        # 先检查是否已经有 "Selected" 标签
                        try:
                            # 查找 "Refund Commission" div 下是否有 "Selected" span
                            # 只检查 Refund Commission 所在的 button 内，不检查同一父级的其他元素
                            refund_commission_div = driver.find_element(By.XPATH, "//div[text()='Refund Commission']")
                            refund_commission_button = refund_commission_div.find_element(By.XPATH, "../..")
                            # 在这个 button 内查找 Selected
                            selected_span = refund_commission_button.find_element(By.XPATH, ".//span[text()='Selected']")
                            if selected_span:
                                # 检查 class 中是否包含 hidden
                                span_class = selected_span.get_attribute("class") or ""
                                if "hidden" in span_class:
                                    log_print(f"[{serial_number}] ⚠ 找到 'Selected' 标签但其 class 包含 hidden，继续等待...")
                                else:
                                    log_print(f"[{serial_number}] ✓✓✓ 找到可见的 'Selected' 标签，操作成功完成！")
                                    select_success = True
                                    success = True
                                    break
                        except:
                            # 没有找到 Selected，继续点击 Select 按钮
                            pass
                        
                        # 查找并点击 "Select" 按钮
                        select_button = driver.find_element(By.XPATH, "//button[text()='Select']")
                        if select_button:
                            log_print(f"[{serial_number}] 点击 'Select' 按钮 (尝试 {select_retry + 1}/{max_select_retries})...")
                            select_button.click()
                            time.sleep(3)
                        else:
                            log_print(f"[{serial_number}] ⚠ 未找到 'Select' 按钮")
                            time.sleep(3)
                            
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 点击 'Select' 按钮时出错: {str(e)}")
                        if select_retry < max_select_retries - 1:
                            time.sleep(3)
                            continue
                        else:
                            break
                
                if not select_success:
                    log_print(f"[{serial_number}] ✗ 未能完成选择操作（未找到 'Selected' 标签）")
                    failure_reason = "未能完成选择操作，未找到Selected标签"
                    return False, failure_reason
                
                log_print(f"[{serial_number}] ✓✓✓ Type 14 所有操作完成成功")
                
                # ========== 更新账户配置（设置字段 i=1）==========
                log_print(f"[{serial_number}] 开始更新账户配置...")
                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                user_no = str(serial_number)
                
                config_update_success = False
                max_config_retries = 3
                
                for config_attempt in range(max_config_retries):
                    try:
                        # 1. 获取现有配置
                        log_print(f"[{serial_number}] 获取账户配置 (尝试 {config_attempt + 1}/{max_config_retries})...")
                        response = requests.get(
                            f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            existing_data = result.get('data', {})
                            
                            if not existing_data:
                                log_print(f"[{serial_number}] ⚠ 未找到账户配置数据")
                                if config_attempt < max_config_retries - 1:
                                    time.sleep(2)
                                    continue
                                else:
                                    log_print(f"[{serial_number}] ✗ 无法获取账户配置，跳过更新")
                                    break
                            
                            log_print(f"[{serial_number}] ✓ 成功获取账户配置")
                            
                            # 2. 更新字段 i=1
                            existing_data['j'] = 1
                            log_print(f"[{serial_number}] 设置字段 j=1")
                            
                            # 3. 提交更新
                            log_print(f"[{serial_number}] 提交配置更新...")
                            update_response = requests.post(
                                f"{API_BASE_URL}/addAccountConfig",
                                json=existing_data,
                                headers={'Content-Type': 'application/json'},
                                timeout=10
                            )
                            
                            if update_response.status_code == 200:
                                update_result = update_response.json()
                                code = update_result.get('code')
                                
                                if code == 0:
                                    log_print(f"[{serial_number}] ✓ 账户配置更新成功 (i=1)")
                                    config_update_success = True
                                    success = True
                                    break
                                else:
                                    log_print(f"[{serial_number}] ✗ 账户配置更新失败: code={code}, msg={update_result.get('msg')}")
                                    if config_attempt < max_config_retries - 1:
                                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                        time.sleep(2)
                            else:
                                log_print(f"[{serial_number}] ✗ 提交配置更新请求失败: HTTP {update_response.status_code}")
                                if config_attempt < max_config_retries - 1:
                                    time.sleep(2)
                        else:
                            log_print(f"[{serial_number}] ✗ 获取账户配置失败: HTTP {response.status_code}")
                            if config_attempt < max_config_retries - 1:
                                time.sleep(2)
                                
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 更新账户配置时出错: {str(e)}")
                        if config_attempt < max_config_retries - 1:
                            time.sleep(2)
                
                if not config_update_success:
                    log_print(f"[{serial_number}] ⚠ 账户配置更新失败，但主要操作已完成")
                    # 不影响主要任务的成功状态
                else:
                    log_print(f"[{serial_number}] ✓✓✓ Type 14 所有操作（包括配置更新）完成成功")
            
                # Type 14 完成后自动关闭浏览器（使用默认的 should_close_browser = True）
            
            elif browser_type == 15:
                # Type 15: 获取 Claim allocation 和 Refund Commission 的金额，并根据价值选择
                log_print(f"[{serial_number}] Type 15: 开始处理空投选项...")
                
                # 检查全局超时
                check_timeout()
                log_print(f"[{serial_number}] 任务已运行 {check_timeout()/60:.1f} 分钟")
                
                aster_value = 0
                refund_value = 0
                selected_option = None  # 'aster' 或 'refund'
                
                # ========== 步骤1: 激活并选择 Claim allocation ==========
                log_print(f"[{serial_number}] 步骤1: 查找并激活 'Claim allocation' 选项...")
                check_timeout()  # 超时检查
                claim_button = None
                max_claim_retries = 20
                
                for claim_retry in range(max_claim_retries):
                    try:
                        claim_div = driver.find_element(By.XPATH, "//div[text()='Claim allocation']")
                        claim_button = claim_div.find_element(By.XPATH, "../..")
                        data_state = claim_button.get_attribute("data-state")
                        log_print(f"[{serial_number}] 'Claim allocation' data-state: {data_state} (检查 {claim_retry + 1}/{max_claim_retries})")
                        
                        if data_state == "active":
                            log_print(f"[{serial_number}] ✓ 'Claim allocation' 已激活")
                            break
                        else:
                            log_print(f"[{serial_number}] 点击 'Claim allocation' 按钮...")
                            claim_button.click()
                            time.sleep(3)
                            # 重新获取元素，避免 stale element
                            claim_div = driver.find_element(By.XPATH, "//div[text()='Claim allocation']")
                            claim_button = claim_div.find_element(By.XPATH, "../..")
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 操作 'Claim allocation' 失败: {str(e)}")
                        if claim_retry < max_claim_retries - 1:
                            time.sleep(3)
                
                if not claim_button:
                    log_print(f"[{serial_number}] ✗ 未找到 'Claim allocation' 按钮")
                    failure_reason = "未找到Claim allocation按钮"
                    return False, failure_reason
                
                # 验证是否激活
                try:
                    data_state = claim_button.get_attribute("data-state")
                    if data_state != "active":
                        log_print(f"[{serial_number}] ✗ 'Claim allocation' 未能激活 (data-state={data_state})")
                        failure_reason = "Claim allocation未能激活"
                        return False, failure_reason
                except Exception as e:
                    log_print(f"[{serial_number}] ✗ 检查激活状态失败: {str(e)}")
                    failure_reason = "检查Claim allocation激活状态失败"
                    return False, failure_reason
                
                # ========== 步骤2: 检查并点击 Claim 按钮 ==========
                log_print(f"[{serial_number}] 步骤2: 检查 'Airdrop Claimed' 并执行 Claim 操作...")
                check_timeout()  # 超时检查
                log_print(f"[{serial_number}] 任务已运行 {check_timeout()/60:.1f} 分钟")
                
                claim_success = False
                max_claim_attempts = 3
                main_window = driver.current_window_handle  # 保存主窗口句柄
                
                for claim_attempt in range(max_claim_attempts):
                    try:
                        log_print(f"[{serial_number}] Claim 尝试 {claim_attempt + 1}/{max_claim_attempts}...")
                        
                        # 切换回主窗口（如果不在主窗口）
                        driver.switch_to.window(main_window)
                        time.sleep(1)
                        
                        # 检查是否已经存在 "Airdrop Claimed"
                        try:
                            airdrop_claimed_div = driver.find_element(By.XPATH, "//div[text()='Airdrop Claimed']")
                            if airdrop_claimed_div:
                                log_print(f"[{serial_number}] ✓ 检测到 'Airdrop Claimed'，空投已领取成功！")
                                claim_success = True
                                break
                        except:
                            log_print(f"[{serial_number}] 未检测到 'Airdrop Claimed'，继续执行 Claim 操作...")
                        
                        # 查找并点击 "Claim" 按钮
                        try:
                            claim_button = driver.find_element(By.XPATH, "//button[text()='Claim']")
                            log_print(f"[{serial_number}] 找到 'Claim' 按钮，准备点击...")
                            claim_button.click()
                            log_print(f"[{serial_number}] ✓ 已点击 'Claim' 按钮")
                            time.sleep(2)
                        except Exception as e:
                            log_print(f"[{serial_number}] ⚠ 未找到 'Claim' 按钮: {str(e)}")
                            # 如果没有Claim按钮，可能已经claimed了，再次检查
                            try:
                                airdrop_claimed_div = driver.find_element(By.XPATH, "//div[text()='Airdrop Claimed']")
                                if airdrop_claimed_div:
                                    log_print(f"[{serial_number}] ✓ 检测到 'Airdrop Claimed'，空投已领取成功！")
                                    claim_success = True
                                    break
                            except:
                                pass
                            
                            if claim_attempt < max_claim_attempts - 1:
                                log_print(f"[{serial_number}] 等待 3 秒后重试...")
                                time.sleep(3)
                                continue
                            else:
                                break
                        
                        # 执行 OKX 钱包授权
                        log_print(f"[{serial_number}] 开始执行 OKX 钱包授权...")
                        auth_result = authorize_okx_wallet(driver, serial_number, password)
                        
                        if not auth_result:
                            log_print(f"[{serial_number}] ⚠ OKX 钱包授权失败")
                            if claim_attempt < max_claim_attempts - 1:
                                log_print(f"[{serial_number}] 等待 3 秒后重试...")
                                time.sleep(3)
                                continue
                            else:
                                break
                        
                        log_print(f"[{serial_number}] ✓ OKX 钱包授权完成")
                        
                        # 等待 2 秒
                        log_print(f"[{serial_number}] 等待 2 秒...")
                        time.sleep(2)
                        
                        # 切换回主窗口
                        log_print(f"[{serial_number}] 切换回主窗口...")
                        driver.switch_to.window(main_window)
                        time.sleep(1)
                        
                        # 再次检查 "Airdrop Claimed"
                        try:
                            airdrop_claimed_div = driver.find_element(By.XPATH, "//div[text()='Airdrop Claimed']")
                            if airdrop_claimed_div:
                                log_print(f"[{serial_number}] ✓ 检测到 'Airdrop Claimed'，空投已领取成功！")
                                claim_success = True
                                break
                        except:
                            log_print(f"[{serial_number}] ⚠ 仍未检测到 'Airdrop Claimed'")
                            if claim_attempt < max_claim_attempts - 1:
                                log_print(f"[{serial_number}] 等待 3 秒后重试...")
                                time.sleep(3)
                        
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ Claim 操作过程出错: {str(e)}")
                        if claim_attempt < max_claim_attempts - 1:
                            log_print(f"[{serial_number}] 等待 3 秒后重试...")
                            time.sleep(3)
                
                if not claim_success:
                    log_print(f"[{serial_number}] ✗ 未能完成 Claim 操作（已尝试 {max_claim_attempts} 次）")
                    failure_reason = "未能完成Claim操作"
                    return False, failure_reason
                
                log_print(f"[{serial_number}] ✓ Claim 操作完成")
                
                # ========== 步骤3: 更新配置 ==========
                check_timeout()  # 超时检查
                log_print(f"[{serial_number}] 任务已运行 {check_timeout()/60:.1f} 分钟")
                
                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                user_no = str(serial_number)
               
                
                # ========== Type 15: 第3阶段 - 随机路径访问 BTCUSDT 页面 ==========
                log_print(f"[{serial_number}] [Type 15 - 第3阶段] 开始随机路径访问 BTCUSDT 页面...")
                check_timeout()  # 超时检查
                log_print(f"[{serial_number}] 任务已运行 {check_timeout()/60:.1f} 分钟")
                
                try:
                    # 解析 tp1 作为随机停留区间（复用之前的设置）
                    raw_tp1 = str(browser_config.get("tp1", "")).strip()
                    min_stay, max_stay = 5, 20
                    if raw_tp1 and "-" in raw_tp1:
                        try:
                            a, b = raw_tp1.split("-", 1)
                            a = int(str(a).strip())
                            b = int(str(b).strip())
                            lo, hi = (a, b) if a <= b else (b, a)
                            # 合理边界：不小于1秒，且最大不超过 3600 秒
                            lo = max(1, lo)
                            hi = min(3600, hi)
                            if lo < hi:
                                min_stay, max_stay = lo, hi
                        except Exception:
                            pass

                    # 初始随机停留
                    wait_seconds = random.randint(min_stay, max_stay)
                    log_print(f"[{serial_number}] [Type 15 - 第3阶段] 随机等待 {wait_seconds} 秒后开始路径访问...")
                    time.sleep(wait_seconds)

                    # 从 RANDOM_PATH 中随机选择一组路径
                    selected_group = random.choice(RANDOM_PATH)
                    # 过滤掉统计页和 airdrop 页，随机抽取 >=2 条路径
                    airdrop_url = "https://www.asterdex.com/en/airdrop"
                    btcusdt_url = "https://www.asterdex.com/en/futures/v1/BTCUSDT"
                    other_urls = [u for u in selected_group if u not in [ airdrop_url, btcusdt_url]]
                    if len(other_urls) < 2:
                        log_print(f"[{serial_number}] [Type 15 - 第3阶段] ⚠ 随机路径数量不足，继续执行")
                        other_urls = [u for u in selected_group if u not in [airdrop_url, btcusdt_url]][:2]

                    # 抽取随机路径：至少2条，最多3条
                    k = random.randint(2, min(3, len(other_urls)))
                    random_urls = random.sample(other_urls, k) if len(other_urls) >= k else other_urls
                    # 拼上 BTCUSDT 页面并随机排序
                    visit_urls = random_urls + [btcusdt_url]
                    random.shuffle(visit_urls)

                    log_print(f"[{serial_number}] [Type 15 - 第3阶段] 本次将依次访问 {len(visit_urls)} 个页面")

                    btcusdt_page_reached = False
                    
                    for idx, url in enumerate(visit_urls, start=1):
                        log_print(f"[{serial_number}] [Type 15 - 第3阶段] ({idx}/{len(visit_urls)}) 打开页面: {url}")
                        try:
                            driver.get(url)
                        except Exception as e:
                            log_print(f"[{serial_number}] [Type 15 - 第3阶段] 打开页面失败: {str(e)}")
                            # 继续访问后续页面
                            pass

                        # 每页随机停留（使用解析后的区间）
                        stay_seconds = random.randint(min_stay, max_stay)
                        log_print(f"[{serial_number}] [Type 15 - 第3阶段] 页面停留 {stay_seconds} 秒...")
                        time.sleep(stay_seconds)

                        # 如果是 BTCUSDT 页面，标记已到达并跳出循环
                        if url == btcusdt_url:
                            log_print(f"[{serial_number}] [Type 15 - 第3阶段] ✓ 已到达 BTCUSDT 页面，准备执行 Transfer 操作")
                            btcusdt_page_reached = True
                            break
                    
                    if not btcusdt_page_reached:
                        log_print(f"[{serial_number}] [Type 15 - 第3阶段] ⚠ 未能访问到 BTCUSDT 页面，尝试直接打开")
                        try:
                            driver.get(btcusdt_url)
                            log_print(f"[{serial_number}] ✓ 已打开 {btcusdt_url}")
                        except Exception as e:
                            log_print(f"[{serial_number}] ✗ 打开 BTCUSDT 页面失败: {str(e)}")
                            failure_reason = "打开BTCUSDT页面失败"
                            return False, failure_reason
                    else:
                        log_print(f"[{serial_number}] ✓ 已在 BTCUSDT 页面")
                        
                except Exception as e:
                    log_print(f"[{serial_number}] [Type 15 - 第3阶段] ✗ 随机路径访问异常: {str(e)}")
                    # 即使异常，也尝试打开 BTCUSDT 页面
                    try:
                        log_print(f"[{serial_number}] 尝试直接打开 BTCUSDT 页面...")
                        driver.get(btcusdt_url)
                        log_print(f"[{serial_number}] ✓ 已打开 {btcusdt_url}")
                    except Exception as e2:
                        log_print(f"[{serial_number}] ✗ 打开 BTCUSDT 页面失败: {str(e2)}")
                        failure_reason = "打开BTCUSDT页面失败"
                        return False, failure_reason
                
                # ========== Type 15: 第4阶段 - 执行 Transfer 操作 ==========
                log_print(f"[{serial_number}] [Type 15 - 第4阶段] 开始执行 Transfer 操作...")
                check_timeout()  # 超时检查
                log_print(f"[{serial_number}] 任务已运行 {check_timeout()/60:.1f} 分钟")
                
                try:
                    # 步骤1: 在20s内获取内容为 'Transfer' 的button
                    log_print(f"[{serial_number}] [第4阶段] 查找 'Transfer' 按钮（20秒超时）...")
                    transfer_button = None
                    wait = WebDriverWait(driver, 20)
                    try:
                        transfer_button = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//button[text()='Transfer']"))
                        )
                        log_print(f"[{serial_number}] ✓ 找到 'Transfer' 按钮")
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 未在20秒内找到 'Transfer' 按钮: {str(e)}")
                        failure_reason = "未找到Transfer按钮"
                        return False, failure_reason
                    
                    # 步骤2: 点击 Transfer 按钮
                    log_print(f"[{serial_number}] [第4阶段] 点击 'Transfer' 按钮...")
                    transfer_button.click()
                    time.sleep(1)
                    log_print(f"[{serial_number}] ✓ 已点击 'Transfer' 按钮")
                    
                    # 步骤3: 5秒内检测是否有内容为 "Max" 的button
                    log_print(f"[{serial_number}] [第4阶段] 查找 'Max' 按钮（5秒超时）...")
                    max_button = None
                    wait_short = WebDriverWait(driver, 5)
                    try:
                        max_button = wait_short.until(
                            EC.presence_of_element_located((By.XPATH, "//button[text()='Max']"))
                        )
                        log_print(f"[{serial_number}] ✓ 找到 'Max' 按钮")
                        
                        # 步骤4: 点击 Max 按钮
                        log_print(f"[{serial_number}] [第4阶段] 点击 'Max' 按钮...")
                        max_button.click()
                        log_print(f"[{serial_number}] ✓ 已点击 'Max' 按钮")
                        
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 未在5秒内找到 'Max' 按钮: {str(e)}")
                        log_print(f"[{serial_number}] 继续执行后续步骤...")
                    
                    # 步骤5: 等待3秒
                    log_print(f"[{serial_number}] [第4阶段] 等待3秒...")
                    time.sleep(3)
                    
                    # 步骤6: 查找内容为 "Transfer" 的span，找到其父节点并点击
                    log_print(f"[{serial_number}] [第4阶段] 查找 'Transfer' span 元素...")
                    try:
                        transfer_span = driver.find_element(By.XPATH, "//span[text()='Transfer']")
                        log_print(f"[{serial_number}] ✓ 找到 'Transfer' span")
                        
                        # 获取父节点
                        parent_element = transfer_span.find_element(By.XPATH, "..")
                        log_print(f"[{serial_number}] [第4阶段] 点击 'Transfer' span 的父节点...")
                        parent_element.click()
                        log_print(f"[{serial_number}] ✓ 已点击 'Transfer' span 的父节点")
                        
                        time.sleep(2)
                        log_print(f"[{serial_number}] ✓ Transfer 操作完成")
                        
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 未找到 'Transfer' span 或点击失败: {str(e)}")
                        failure_reason = "Transfer操作失败"
                        return False, failure_reason
                    
                except Exception as e:
                    log_print(f"[{serial_number}] [Type 15 - 第4阶段] ✗ Transfer 操作异常: {str(e)}")
                    failure_reason = "Transfer操作异常"
                    return False, failure_reason
                
                # ========== Type 15: 第5阶段 - 更新配置 j=6 ==========
                log_print(f"[{serial_number}] [Type 15 - 第5阶段] 开始更新账户配置 (j=6)...")
                check_timeout()  # 超时检查
                log_print(f"[{serial_number}] 任务已运行 {check_timeout()/60:.1f} 分钟")
                
                API_BASE_URL = "https://sg.bicoin.com.cn/98h/boost"
                user_no = str(serial_number)
                
                config_update_success = False
                max_config_retries = 3
                
                for config_attempt in range(max_config_retries):
                    try:
                        # 获取现有配置
                        log_print(f"[{serial_number}] 获取账户配置 (尝试 {config_attempt + 1}/{max_config_retries})...")
                        response = requests.get(
                            f"{API_BASE_URL}/findAccountConfigByNo?no={user_no}",
                            headers={'Content-Type': 'application/json'},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            existing_data = result.get('data', {})
                            
                            if not existing_data:
                                log_print(f"[{serial_number}] ⚠ 未找到账户配置数据")
                                if config_attempt < max_config_retries - 1:
                                    time.sleep(2)
                                    continue
                                else:
                                    log_print(f"[{serial_number}] ✗ 无法获取账户配置，跳过更新")
                                    break
                            
                            log_print(f"[{serial_number}] ✓ 成功获取账户配置")
                            
                            # 更新字段 j=6
                            existing_data['j'] = 6
                            log_print(f"[{serial_number}] 设置 j=6 (Transfer 完成)")
                            
                            # 提交更新
                            log_print(f"[{serial_number}] 提交配置更新...")
                            update_response = requests.post(
                                f"{API_BASE_URL}/addAccountConfig",
                                json=existing_data,
                                headers={'Content-Type': 'application/json'},
                                timeout=30
                            )
                            
                            if update_response.status_code == 200:
                                update_result = update_response.json()
                                code = update_result.get('code')
                                
                                if code == 0:
                                    log_print(f"[{serial_number}] ✓ 账户配置更新成功 (j=6)")
                                    config_update_success = True
                                    success = True
                                    break
                                else:
                                    log_print(f"[{serial_number}] ✗ 账户配置更新失败: code={code}, msg={update_result.get('msg')}")
                                    if config_attempt < max_config_retries - 1:
                                        log_print(f"[{serial_number}] 等待 2 秒后重试...")
                                        time.sleep(2)
                            else:
                                log_print(f"[{serial_number}] ✗ 提交配置更新请求失败: HTTP {update_response.status_code}")
                                if config_attempt < max_config_retries - 1:
                                    time.sleep(2)
                        else:
                            log_print(f"[{serial_number}] ✗ 获取账户配置失败: HTTP {response.status_code}")
                            if config_attempt < max_config_retries - 1:
                                time.sleep(2)
                                
                    except Exception as e:
                        log_print(f"[{serial_number}] ✗ 更新账户配置时出错: {str(e)}")
                        if config_attempt < max_config_retries - 1:
                            time.sleep(2)
                
                if not config_update_success:
                    log_print(f"[{serial_number}] ✗ 账户配置更新失败")
                    failure_reason = "配置更新失败"
                    return False, failure_reason
                else:
                    log_print(f"[{serial_number}] ✓✓✓ Type 15 所有操作（包括 Transfer 和配置更新）完成成功")
            
        elif browser_type == 4:
            # Type 4: 执行钱包连接和兑换操作
            log_print(f"[{serial_number}] Type 4: 执行兑换和绑定邀请码")
            ref_code = browser_config.get("refCode", "")
            password = browser_config.get("pwd", "")
            
            if not ref_code:
                log_print(f"[{serial_number}] ✗ Type 4 需要提供 refCode 参数")
                failure_reason = "缺少邀请码"
                return False, failure_reason
            
            if not password:
                log_print(f"[{serial_number}] ✗ Type 4 需要提供 pwd（钱包密码）参数")
                failure_reason = "缺少钱包密码"
                return False, failure_reason
            
            if process_wallet_swap(driver, serial_number, ref_code, password):
                log_print(f"[{serial_number}] ✓✓✓ 所有操作完成成功")
                success = True
            else:
                failure_reason = "钱包兑换失败"
        
        else:
            log_print(f"[{serial_number}] ⚠ 未知的浏览器类型: {browser_type}，跳过操作")
            failure_reason = "未知浏览器类型"
        
    except Exception as e:
        log_print(f"[{serial_number}] ✗✗✗ 处理过程中发生未预期的错误: {str(e)}")
        success = False
        should_close_browser = True 
        failure_reason = "处理异常"
    
    finally:
        # 清理资源
        if driver:
            try:
                # 如果需要关闭浏览器，先关闭多余的标签页
                if should_close_browser and browser_type != 3:
                    close_extra_tabs(driver, serial_number)
                
                driver.quit()
                log_print(f"[{serial_number}] ✓ Selenium驱动已关闭")
            except:
                pass
        
        # 根据任务类型决定是否关闭浏览器
        if should_close_browser and browser_type != 3:
            time.sleep(1)
            close_success = close_adspower_browser(serial_number)
            if close_success:
                log_print(f"[{serial_number}] ✓ 浏览器关闭确认")
            else:
                log_print(f"[{serial_number}] ⚠ 浏览器可能未完全关闭，请手动检查")
        elif browser_type == 2:
            log_print(f"[{serial_number}] ℹ 浏览器保持打开状态")
        
        log_print(f"\n[{serial_number}] 处理完成\n")

    return success, failure_reason


def query_browser_status():
    """
    查询所有浏览器的活跃状态 (Type 6)
    
    Returns:
        list: 活跃的浏览器编号列表
    """
    log_print(f"\n[系统] 开始查询所有浏览器状态...")
    
    # 检查映射数据是否已加载
    if not FINGERPRINT_TO_USERID:
        log_print(f"[系统] ✗ 浏览器映射数据未加载，请先初始化映射数据")
        return []
    
    log_print(f"[系统] 映射数据已加载，共 {len(FINGERPRINT_TO_USERID)} 个浏览器")
    
    # 获取所有用户ID
    all_user_ids = list(FINGERPRINT_TO_USERID.values())
    log_print(f"[系统] 需要查询 {len(all_user_ids)} 个浏览器的状态")
    
    # 创建反向映射 (userId -> fingerprintNo)
    userid_to_fingerprint = {v: k for k, v in FINGERPRINT_TO_USERID.items()}
    
    # 分批查询（每批100个）
    batch_size = 100
    active_user_ids = []
    
    for i in range(0, len(all_user_ids), batch_size):
        batch = all_user_ids[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_user_ids) + batch_size - 1) // batch_size
        
        log_print(f"[系统] 查询第 {batch_num}/{total_batches} 批 (共 {len(batch)} 个浏览器)...")
        
        # 调用 AdsPower API
        url = f"{ADSPOWER_BASE_URL}/api/v1/browser/cloud-active"
        user_ids_str = ",".join(batch)
        headers = {
            'Authorization': f'Bearer {ADSPOWER_API_KEY}'
        }
        
        try:
            response = requests.post(
                url,
                data={
                    "user_ids": user_ids_str
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    data = result.get("data", [])
                    log_print(f"[系统] ✓ 第 {batch_num} 批查询成功，找到 {len(data)} 个活跃浏览器")
                    
                    # 收集活跃的用户ID
                    for item in data:
                        user_id = item.get("user_id")
                        if user_id:
                            active_user_ids.append(user_id)
                else:
                    log_print(f"[系统] ⚠ 第 {batch_num} 批查询失败: code={result.get('code')}, msg={result.get('msg')}")
            else:
                log_print(f"[系统] ⚠ 第 {batch_num} 批查询失败: HTTP状态码 {response.status_code}")
        
        except Exception as e:
            log_print(f"[系统] ✗ 第 {batch_num} 批查询异常: {str(e)}")
        
        # 稍微延迟，避免请求过快
        if i + batch_size < len(all_user_ids):
            time.sleep(0.5)
    
    # 将活跃的用户ID映射回浏览器编号
    active_fingerprints = []
    for user_id in active_user_ids:
        fingerprint = userid_to_fingerprint.get(user_id)
        if fingerprint:
            active_fingerprints.append(fingerprint)
    
    log_print(f"\n[系统] 查询完成！")
    log_print(f"[系统] 总浏览器数: {len(all_user_ids)}")
    log_print(f"[系统] 活跃浏览器数: {len(active_fingerprints)}")
    log_print(f"[系统] 活跃浏览器编号: {', '.join(sorted(active_fingerprints, key=lambda x: int(x)))}")
    
    return active_fingerprints


def process_single_browser_task(browser_config, mission_id):
    """
    处理单个浏览器任务（在线程池中执行）
    
    Args:
        browser_config: 浏览器配置字典
        mission_id: 任务ID
        
    Returns:
        tuple: (browser_id, success, failure_reason)
    """
    browser_id = browser_config.get("id", "未知")
    success = False
    failure_reason = ""
    
    try:
        log_print(f"[{browser_id}] [任务{mission_id}] 开始处理...")
        success, failure_reason = process_browser(browser_config)
        
        if success:
            log_print(f"[{browser_id}] [任务{mission_id}] ✓ 处理成功")
        else:
            log_print(f"[{browser_id}] [任务{mission_id}] ✗ 处理失败: {failure_reason}")
            
    except Exception as e:
        log_print(f"[{browser_id}] [任务{mission_id}] ✗ 发生异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 异常详情:\n{traceback.format_exc()}")
        failure_reason = f"异常: {str(e)}"
        success = False
    
    finally:
        # 任务完成（无论成功或失败或异常）后，调用 /mission/addSucc 更新进度
        try:
            url = f"{SERVER_BASE_URL}/mission/addSucc"
            payload = {"id": mission_id}
            log_print(f"[{browser_id}] 任务完成，更新服务器进度...")
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and result.get("code") == 0:
                    log_print(f"[{browser_id}] ✓ 进度更新成功")
                else:
                    log_print(f"[{browser_id}] ⚠ 进度更新失败: {result}")
            else:
                log_print(f"[{browser_id}] ⚠ 进度更新失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            log_print(f"[{browser_id}] ⚠ 更新进度时出错: {str(e)}")
            # 不影响任务结果，只是记录日志
    
    return browser_id, success, failure_reason


def submit_mission_to_pool(mission_data):
    """
    将任务提交到全局线程池
    
    Args:
        mission_data: 任务数据字典
    """
    mission_id = mission_data.get("id")
    mission_type = mission_data.get("type")
    number_list = mission_data.get("numberList", "")
    
    log_print(f"\n[系统] 开始提交任务 ID: {mission_id} 到线程池")
    log_print(f"[系统] 任务类型: {mission_type}")
    
    # 解析浏览器ID列表
    if not number_list:
        log_print(f"[系统] ⚠ 任务 {mission_id} 没有浏览器列表")
        # 直接提交结果
        submit_mission_result(mission_id, 0, 0, {})
        return
    
    browser_ids = [bid.strip() for bid in number_list.split(",") if bid.strip()]
    log_print(f"[系统] 浏览器数量: {len(browser_ids)}")
    
    # 构建浏览器配置列表
    browser_configs = []
    for browser_id in browser_ids:
        config = {
            "id": browser_id,
            "type": mission_type,
            "refCode": mission_data.get("refCode", ""),
            "pwd": mission_data.get("pwd", ""),
            "tp1": mission_data.get("tp1", "")
        }
        browser_configs.append(config)
    
    # 初始化任务状态
    with active_tasks_lock:
        active_tasks[mission_id] = {
            'futures': [],
            'results': {},
            'total': len(browser_configs),
            'completed': 0,
            'type': mission_type
        }
    
    # 将每个浏览器任务提交到线程池
    for browser_config in browser_configs:
        future = global_thread_pool.submit(process_single_browser_task, browser_config, mission_id)
        with active_tasks_lock:
            active_tasks[mission_id]['futures'].append(future)
    
    log_print(f"[系统] ✓ 任务 {mission_id} 的 {len(browser_configs)} 个浏览器已提交到线程池")


def check_and_submit_completed_missions():
    """
    检查并提交已完成的任务
    """
    completed_missions = []
    
    with active_tasks_lock:
        for mission_id, task_info in list(active_tasks.items()):
            # 检查所有 future 是否完成
            all_done = all(f.done() for f in task_info['futures'])
            
            if all_done:
                # 收集结果
                success_count = 0
                failed_count = 0
                failed_info = {}
                
                for future in task_info['futures']:
                    try:
                        browser_id, success, failure_reason = future.result()
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                            failed_info[browser_id] = failure_reason
                    except Exception as e:
                        log_print(f"[系统] ✗ 获取任务 {mission_id} 结果时出错: {str(e)}")
                        failed_count += 1
                
                # 标记为已完成
                completed_missions.append((mission_id, success_count, failed_count, failed_info))
                
                log_print(f"[系统] ✓ 任务 {mission_id} 已完成: 成功 {success_count}/{task_info['total']}, 失败 {failed_count}")
    
    # 提交已完成的任务
    for mission_id, success_count, failed_count, failed_info in completed_missions:
        try:
            submit_mission_result(mission_id, success_count, failed_count, failed_info)
            with active_tasks_lock:
                del active_tasks[mission_id]
            log_print(f"[系统] ✓ 任务 {mission_id} 结果已提交并从队列中移除")
        except Exception as e:
            log_print(f"[系统] ✗ 提交任务 {mission_id} 结果时出错: {str(e)}")


def get_thread_pool_status():
    """
    获取线程池状态
    
    Returns:
        tuple: (active_count, pending_count)
    """
    with active_tasks_lock:
        active_count = len(active_tasks)
        pending_count = sum(
            sum(1 for f in task_info['futures'] if not f.done())
            for task_info in active_tasks.values()
        )
    return active_count, pending_count


def execute_type6_in_background(mission_data):
    """
    在后台线程中执行 type=6 任务
    
    Args:
        mission_data: 任务数据字典
    """
    global type6_task_running
    
    try:
        log_print(f"[系统] Type 6 任务开始在后台执行...")
        result = execute_mission(mission_data)
        
        if result is not None:
            success_count, failed_count, failed_info = result
            mission_id = mission_data.get("id")
            submit_mission_result(mission_id, success_count, failed_count, failed_info)
            log_print(f"[系统] ✓ Type 6 任务 {mission_id} 执行完成")
        
    except Exception as e:
        log_print(f"[系统] ✗ Type 6 任务执行出错: {str(e)}")
        import traceback
        log_print(f"[系统] 错误详情:\n{traceback.format_exc()}")
    finally:
        with type6_task_lock:
            type6_task_running = False
        log_print(f"[系统] Type 6 任务已结束，可以接收新的 Type 6 任务")


def is_type6_task_running():
    """
    检查是否有 type=6 任务正在运行
    
    Returns:
        bool: True 表示有任务在运行
    """
    with type6_task_lock:
        return type6_task_running


def start_type6_task(mission_data):
    """
    启动 type=6 任务（后台线程）
    
    Args:
        mission_data: 任务数据字典
        
    Returns:
        bool: 是否成功启动
    """
    global type6_task_running, type6_task_thread
    
    with type6_task_lock:
        if type6_task_running:
            return False
        
        type6_task_running = True
        type6_task_thread = threading.Thread(target=execute_type6_in_background, args=(mission_data,))
        type6_task_thread.daemon = True
        type6_task_thread.start()
        
    log_print(f"[系统] ✓ Type 6 任务已启动（后台执行）")
    return True


def execute_mission(mission_data):
    """
    执行单个任务
    
    Args:
        mission_data: 任务数据字典
        
    Returns:
        tuple: (success_count, failed_count, failed_browser_ids)
    """
    mission_id = mission_data.get("id")
    mission_type = mission_data.get("type")
    number_list = mission_data.get("numberList", "")
    
    # Type 6: 查询浏览器状态
    if mission_type == 6:
        log_print(f"\n[系统] 开始执行任务 ID: {mission_id}")
        log_print(f"[系统] 任务类型: 6 (查询浏览器状态)")
        
        # 查询所有活跃的浏览器
        active_fingerprints = query_browser_status()
        
        # 提交结果：msg内容为所有活跃浏览器编号（逗号分隔）
        active_browsers_str = ",".join(sorted(active_fingerprints, key=lambda x: int(x)))
        
        # 提交任务结果
        try:
            url = f"{SERVER_BASE_URL}/mission/saveResult"
            payload = {
                "id": mission_id,
                "status": 2,  # 2 代表已完成
                "msg": f"已打开的浏览器ID：{active_browsers_str}" if active_browsers_str else "已打开的浏览器ID：无"
            }
            
            log_print(f"\n[系统] 提交查询结果: {url}")
            log_print(f"[系统] 活跃浏览器数量: {len(active_fingerprints)}")
            log_print(f"[系统] 活跃浏览器: {active_browsers_str[:200]}{'...' if len(active_browsers_str) > 200 else ''}")
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and result.get("code") == 0:
                    log_print(f"[系统] ✓ 查询结果提交成功")
                else:
                    log_print(f"[系统] ✗ 查询结果提交失败: {result}")
            else:
                log_print(f"[系统] ✗ 查询结果提交失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            log_print(f"[系统] ✗ 提交查询结果失败: {str(e)}")
        
        log_print(f"\n[系统] 任务 {mission_id} 执行完成\n")
        # 返回 None 表示已经自己提交了结果，main 函数不需要再次提交
        return None
    
    # Type 7: 关闭再打开浏览器
    if mission_type == 7:
        log_print(f"\n[系统] 开始执行任务 ID: {mission_id}")
        log_print(f"[系统] 任务类型: 7 (关闭再打开浏览器)")
        
        # 解析浏览器ID列表
        if not number_list:
            log_print(f"[系统] ✗ 任务 {mission_id} 没有浏览器列表")
            return 0, 0, {}
        
        browser_ids = [bid.strip() for bid in number_list.split(",") if bid.strip()]
        log_print(f"[系统] 浏览器数量: {len(browser_ids)}")
        log_print(f"[系统] 浏览器列表: {browser_ids}")
        
        # 第一步：关闭所有浏览器
        log_print(f"\n[系统] 第一步：关闭所有浏览器...")
        close_results = {}
        for browser_id in browser_ids:
            try:
                log_print(f"[{browser_id}] 正在关闭浏览器...")
                success = close_adspower_browser(browser_id)
                close_results[browser_id] = success
                if success:
                    log_print(f"[{browser_id}] ✓ 浏览器已关闭")
                else:
                    log_print(f"[{browser_id}] ⚠ 浏览器关闭失败或已经关闭")
            except Exception as e:
                log_print(f"[{browser_id}] ✗ 关闭浏览器时出错: {str(e)}")
                close_results[browser_id] = False
        
        # 第二步：等待20秒
        log_print(f"\n[系统] 第二步：等待20秒...")
        time.sleep(20)
        
        # 第三步：执行 type=2 的逻辑（打开浏览器）
        log_print(f"\n[系统] 第三步：打开所有浏览器...")
        
        # 构建浏览器配置（使用 type=2）
        browser_configs = []
        for browser_id in browser_ids:
            config = {
                "id": browser_id,
                "type": 2,  # 使用 type=2 的逻辑
                "refCode": mission_data.get("refCode", ""),
                "pwd": mission_data.get("pwd", "")
            }
            browser_configs.append(config)
        
        # 创建线程列表
        threads = []
        results = {}  # 存储每个浏览器的执行结果：{browser_id: (success, failure_reason)}
        results_lock = threading.Lock()
        
        # 使用信号量控制最多同时运行N个线程（type==8 用 6，否则 4）
        max_concurrency = 4 if mission_type == 8 else 4
        semaphore = threading.Semaphore(max_concurrency)
        
        def thread_wrapper(browser_config):
            """线程包装器 - 带完整异常处理"""
            browser_id = browser_config.get("id", "未知")
            success = False
            failure_reason = ""
            
            try:
                with semaphore:
                    success, failure_reason = process_browser(browser_config)
                    
                    # 此处不再更新进度，统一放到 finally 中保证必定执行
                            
            except Exception as e:
                log_print(f"[{browser_id}] ✗✗✗ 线程执行发生严重错误: {str(e)}")
                import traceback
                log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
                success = False
                failure_reason = "线程执行异常"
            finally:
                # 无论如何都要记录结果
                try:
                    with results_lock:
                        results[browser_id] = (success, failure_reason)
                except Exception as e:
                    log_print(f"[{browser_id}] ✗ 记录结果时出错: {str(e)}")
                
                # 任务完成（无论成功或失败或异常）后，调用 /mission/addSucc 更新进度
                try:
                    url = f"{SERVER_BASE_URL}/mission/addSucc"
                    payload = {"id": mission_id}
                    log_print(f"[{browser_id}] 任务完成，更新服务器进度...")
                    response = requests.post(url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result and result.get("code") == 0:
                            log_print(f"[{browser_id}] ✓ 进度更新成功")
                        else:
                            log_print(f"[{browser_id}] ⚠ 进度更新失败: {result}")
                    else:
                        log_print(f"[{browser_id}] ⚠ 进度更新失败，HTTP状态码: {response.status_code}")
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 更新进度时出错: {str(e)}")
                    # 不影响任务结果，只是记录日志
        
        # 为每个浏览器创建线程
        for browser_config in browser_configs:
            try:
                thread = threading.Thread(target=thread_wrapper, args=(browser_config,))
                thread.daemon = True
                threads.append(thread)
                thread.start()
                time.sleep(0.5)
            except Exception as e:
                browser_id = browser_config.get("id", "未知")
                log_print(f"[{browser_id}] ✗ 创建线程失败: {str(e)}")
                with results_lock:
                    results[browser_id] = (False, "创建线程失败")
                # 任务未能启动也视为该浏览器已结束一次尝试，更新进度
                try:
                    url = f"{SERVER_BASE_URL}/mission/addSucc"
                    payload = {"id": mission_id}
                    log_print(f"[{browser_id}] 任务完成（创建线程失败），更新服务器进度...")
                    response = requests.post(url, json=payload, timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        if result and result.get("code") == 0:
                            log_print(f"[{browser_id}] ✓ 进度更新成功")
                        else:
                            log_print(f"[{browser_id}] ⚠ 进度更新失败: {result}")
                    else:
                        log_print(f"[{browser_id}] ⚠ 进度更新失败，HTTP状态码: {response.status_code}")
                except Exception as e2:
                    log_print(f"[{browser_id}] ⚠ 更新进度时出错: {str(e2)}")
        
        # 等待所有线程完成
        # 线程超时时间（秒），默认30分钟，可根据需要调整
        THREAD_JOIN_TIMEOUT_SECONDS = 1800
        for i, thread in enumerate(threads):
            try:
                thread.join(timeout=THREAD_JOIN_TIMEOUT_SECONDS)
                if thread.is_alive():
                    log_print(f"[系统] ⚠ 线程 {i+1} 执行超时（{THREAD_JOIN_TIMEOUT_SECONDS // 60}分钟），继续等待其他线程...")
            except Exception as e:
                log_print(f"[系统] ✗ 等待线程 {i+1} 时出错: {str(e)}")
        
        # 统计结果
        try:
            success_count = sum(1 for success, _ in results.values() if success)
            failed_count = len(results) - success_count
            failed_info = {bid: reason for bid, (success, reason) in results.items() if not success}
        except Exception as e:
            log_print(f"[系统] ✗ 统计结果时出错: {str(e)}")
            success_count = 0
            failed_count = len(browser_ids)
            failed_info = {bid: "统计异常" for bid in browser_ids}
        
        log_print(f"\n[系统] 任务 {mission_id} 执行完成")
        log_print(f"[系统] 成功: {success_count}个, 失败: {failed_count}个")
        if failed_info:
            log_print(f"[系统] 失败的浏览器: {', '.join(failed_info.keys())}")
            for bid, reason in failed_info.items():
                log_print(f"[系统]   - {bid}: {reason}")
        
        return success_count, failed_count, failed_info
    
    # 解析浏览器ID列表
    if not number_list:
        log_print(f"[系统] ✗ 任务 {mission_id} 没有浏览器列表")
        return 0, 0, []
    
    # 将 numberList 转换为浏览器配置列表
    browser_ids = [bid.strip() for bid in number_list.split(",") if bid.strip()]
    
    log_print(f"\n[系统] 开始执行任务 ID: {mission_id}")
    log_print(f"[系统] 任务类型: {mission_type}")
    log_print(f"[系统] 浏览器数量: {len(browser_ids)}")
    log_print(f"[系统] 浏览器列表: {browser_ids}")
    
    # 构建浏览器配置
    browser_configs = []
    for browser_id in browser_ids:
        config = {
            "id": browser_id,
            "type": mission_type,
            "refCode": "",  # Type 2 需要的参数，从任务数据中获取（如果有）
            "pwd": ""       # Type 2 需要的参数，从任务数据中获取（如果有）
        }
        
        # 如果任务类型是 2，需要从任务数据中获取 refCode 和 pwd
        if mission_type == 2:
            config["refCode"] = mission_data.get("refCode", "")
            config["pwd"] = mission_data.get("pwd", "")
        
        # 如果任务类型是 8，透传 tp1（页面停留随机区间，例如 "5-10"）
        if mission_type == 8:
            config["tp1"] = mission_data.get("tp1", "")
        
        browser_configs.append(config)
    
    # 创建线程列表
    threads = []
    results = {}  # 存储每个浏览器的执行结果：{browser_id: (success, failure_reason)}
    results_lock = threading.Lock()
    
    # 使用信号量控制最多同时运行N个线程（type==8 用 6，否则 4）
    max_concurrency = 4 if mission_type == 8 else 4
    semaphore = threading.Semaphore(max_concurrency)
    
    def thread_wrapper(browser_config):
        """线程包装器 - 带完整异常处理"""
        browser_id = browser_config.get("id", "未知")
        success = False
        failure_reason = ""
        
        try:
            with semaphore:
                    success, failure_reason = process_browser(browser_config)
                    
                    # 此处不再更新进度，统一放到 finally 中保证必定执行
                            
        except Exception as e:
            log_print(f"[{browser_id}] ✗✗✗ 线程执行发生严重错误: {str(e)}")
            import traceback
            log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
            success = False
            failure_reason = "线程执行异常"
        finally:
            # 无论如何都要记录结果
            try:
                with results_lock:
                    results[browser_id] = (success, failure_reason)
            except Exception as e:
                log_print(f"[{browser_id}] ✗ 记录结果时出错: {str(e)}")
            
            # 任务完成（无论成功或失败或异常）后，调用 /mission/addSucc 更新进度
            try:
                url = f"{SERVER_BASE_URL}/mission/addSucc"
                payload = {"id": mission_id}
                log_print(f"[{browser_id}] 任务完成，更新服务器进度...")
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result and result.get("code") == 0:
                        log_print(f"[{browser_id}] ✓ 进度更新成功")
                    else:
                        log_print(f"[{browser_id}] ⚠ 进度更新失败: {result}")
                else:
                    log_print(f"[{browser_id}] ⚠ 进度更新失败，HTTP状态码: {response.status_code}")
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 更新进度时出错: {str(e)}")
                # 不影响任务结果，只是记录日志
    
    # 为每个浏览器创建线程
    for browser_config in browser_configs:
        try:
            thread = threading.Thread(target=thread_wrapper, args=(browser_config,))
            thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
            threads.append(thread)
            thread.start()
            time.sleep(0.5)  # 稍微延迟启动，避免同时请求过多
        except Exception as e:
            browser_id = browser_config.get("id", "未知")
            log_print(f"[{browser_id}] ✗ 创建线程失败: {str(e)}")
            # 记录失败
            with results_lock:
                results[browser_id] = (False, "创建线程失败")
            # 任务未能启动也视为该浏览器已结束一次尝试，更新进度
            try:
                url = f"{SERVER_BASE_URL}/mission/addSucc"
                payload = {"id": mission_id}
                log_print(f"[{browser_id}] 任务完成（创建线程失败），更新服务器进度...")
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result and result.get("code") == 0:
                        log_print(f"[{browser_id}] ✓ 进度更新成功")
                    else:
                        log_print(f"[{browser_id}] ⚠ 进度更新失败: {result}")
                else:
                    log_print(f"[{browser_id}] ⚠ 进度更新失败，HTTP状态码: {response.status_code}")
            except Exception as e2:
                log_print(f"[{browser_id}] ⚠ 更新进度时出错: {str(e2)}")
    
    # 等待所有线程完成
    # 线程超时时间（秒），默认30分钟，可根据需要调整
    THREAD_JOIN_TIMEOUT_SECONDS = 1800
    for i, thread in enumerate(threads):
        try:
            thread.join(timeout=THREAD_JOIN_TIMEOUT_SECONDS)  # 超时避免线程永久挂起
            if thread.is_alive():
                log_print(f"[系统] ⚠ 线程 {i+1} 执行超时（{THREAD_JOIN_TIMEOUT_SECONDS // 60}分钟），继续等待其他线程...")
        except Exception as e:
            log_print(f"[系统] ✗ 等待线程 {i+1} 时出错: {str(e)}")
    
    # 统计结果
    try:
        success_count = sum(1 for success, _ in results.values() if success)
        failed_count = len(results) - success_count
        # 构建失败信息字典：{browser_id: failure_reason}
        failed_info = {bid: reason for bid, (success, reason) in results.items() if not success}
    except Exception as e:
        log_print(f"[系统] ✗ 统计结果时出错: {str(e)}")
        # 使用保守的统计
        success_count = 0
        failed_count = len(browser_ids)
        failed_info = {bid: "统计异常" for bid in browser_ids}
    
    log_print(f"\n[系统] 任务 {mission_id} 执行完成")
    log_print(f"[系统] 成功: {success_count}个, 失败: {failed_count}个")
    if failed_info:
        log_print(f"[系统] 失败的浏览器: {', '.join(failed_info.keys())}")
        for bid, reason in failed_info.items():
            log_print(f"[系统]   - {bid}: {reason}")
    
    return success_count, failed_count, failed_info


def main():
    """
    主函数 - 使用全局线程池的任务循环
    """
    log_print("\n" + "="*80)
    log_print("AdsPower浏览器自动化脚本启动 - 全局线程池模式")
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
            
            # 3. 如果线程池还有空闲（pending < MAX_WORKERS），尝试获取新任务
            if pending_count < MAX_WORKERS:
                log_print(f"[系统] 线程池状态: 活跃任务 {active_count} 个, 待处理浏览器 {pending_count}/{MAX_WORKERS}")
                log_print(f"[系统] 线程池有空闲，尝试获取新任务...")
                
                # 从服务器获取任务
                mission = get_mission_from_server()
                
                if mission:
                    mission_id = mission.get("id")
                    mission_type = mission.get("type")
                    
                    # Type 6 特殊处理（后台执行，不阻塞）
                    if mission_type == 6:
                        if is_type6_task_running():
                            log_print(f"[系统] ⚠ 任务 {mission_id} (type=6) 被跳过，因为已有 Type 6 任务正在执行")
                            log_print(f"[系统] 立即获取下一个任务...")
                            time.sleep(0.5)  # 短暂延迟，避免过于频繁请求
                            continue
                        else:
                            log_print(f"[系统] 任务 {mission_id} (type=6) 启动后台执行")
                            start_type6_task(mission)
                            log_print(f"[系统] Type 6 任务已启动，立即获取下一个任务...")
                            time.sleep(0.5)  # 短暂延迟，避免过于频繁请求
                            continue
                    
                    # Type 7 特殊处理（同步执行，不使用线程池）
                    elif mission_type == 7:
                        log_print(f"[系统] 任务 {mission_id} (type=7) 使用特殊处理")
                        result = execute_mission(mission)
                        if result is not None:
                            success_count, failed_count, failed_info = result
                            submit_mission_result(mission_id, success_count, failed_count, failed_info)
                    
                    # 其他类型任务提交到全局线程池
                    else:
                        submit_mission_to_pool(mission)
                else:
                    log_print(f"[系统] 暂无新任务")
            else:
                log_print(f"[系统] 线程池已满 ({pending_count}/{MAX_WORKERS})，等待任务完成...")
            
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
                        break
                    log_print(f"[系统] 还有 {active_count} 个任务未完成...")
                    time.sleep(2)
            
            log_print("[系统] 所有任务已完成，程序即将退出...")
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
    从 App.vue 中的 tmplistRaw 数据导入
    """
    global FINGERPRINT_TO_USERID
    
    # 映射数据（从 App.vue 中复制的完整 2000 条数据）
    # 格式: 浏览器编号\t用户ID
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
    for line in mapping_data.strip().split('\n'):
        parts = line.strip().split('\t')
        if len(parts) == 2:
            fingerprint_no = parts[0].strip()
            user_id = parts[1].strip()
            if fingerprint_no and user_id:
                FINGERPRINT_TO_USERID[fingerprint_no] = user_id
    
    log_print(f"[系统] 浏览器映射数据初始化完成，共加载 {len(FINGERPRINT_TO_USERID)} 条映射")
    
    if len(FINGERPRINT_TO_USERID) < 1900:
        log_print(f"[系统] ⚠ 警告：映射数据可能不完整（当前：{len(FINGERPRINT_TO_USERID)} 条）")
    else:
        log_print(f"[系统] ✓ 映射数据已完整加载")


def test_type2_local():
    """
    本地测试 Type 2 任务
    使用指定的 AdsPower 配置和浏览器编号 4001
    """
    print("\n" + "="*80)
    print("🧪 开始 Type 2 任务本地测试")
    print("="*80 + "\n")
    
    # 临时修改全局配置用于测试
    global ADSPOWER_BASE_URL, ADSPOWER_API_KEY
    
    # 保存原始配置
    original_base_url = ADSPOWER_BASE_URL
    original_api_key = ADSPOWER_API_KEY
    
    try:
        # 设置测试配置
        ADSPOWER_BASE_URL = "http://local.adspower.net:50325"
        ADSPOWER_API_KEY = "39151a16106b8ee0b2c8ce4179c3c759"
        
        log_print(f"[测试] 使用测试配置:")
        log_print(f"[测试] - ADSPOWER_BASE_URL: {ADSPOWER_BASE_URL}")
        log_print(f"[测试] - ADSPOWER_API_KEY: {ADSPOWER_API_KEY}")
        log_print(f"[测试] - 测试浏览器编号: 2201")
        log_print(f"[测试] - 任务类型: Type 1")
        log_print(f"[测试] - 默认密码: {PWD}")
        log_print(f"[测试] - 密码映射: {PASSWORD_MAP}\n")
        
        # 创建一个模拟的 Type 1 任务配置
        test_browser_config = {
            "id": 2201,           # 浏览器编号
            "type": 1,            # 任务类型
            "number": "2201",     # 浏览器编号字符串
            # 密码会通过 get_browser_password(id) 自动获取
        }
        
        log_print(f"[测试] 创建测试任务配置:")
        log_print(f"[测试] {test_browser_config}\n")
        
        # 执行 Type 1 任务
        log_print(f"[测试] 开始执行 Type 1 任务...\n")
        success, failure_reason = process_browser(test_browser_config)
        
        # 输出测试结果
        print("\n" + "="*80)
        if success:
            log_print(f"[测试] ✅ Type 2 任务执行成功！")
        else:
            log_print(f"[测试] ❌ Type 2 任务执行失败")
            log_print(f"[测试] 失败原因: {failure_reason}")
        print("="*80 + "\n")
        
        return success
        
    except Exception as e:
        log_print(f"[测试] ✗ 测试过程中发生异常: {str(e)}")
        import traceback
        log_print(f"[测试] 错误详情:\n{traceback.format_exc()}")
        return False
        
    finally:
        # 恢复原始配置
        ADSPOWER_BASE_URL = original_base_url
        ADSPOWER_API_KEY = original_api_key
        log_print(f"[测试] 已恢复原始配置")


if __name__ == "__main__":
    import sys
    
    # 检查是否是测试模式
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n🚀 启动测试模式...\n")
        # 初始化浏览器映射数据（测试也需要）
        initialize_fingerprint_mapping()
        # 运行测试
        test_type2_local()
    else:
        # 正常模式：初始化并启动主循环
        initialize_fingerprint_mapping()
        main()
