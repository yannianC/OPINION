import time
import random
import requests
import threading
import os
import json
import re
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


def read_computer_config():
    """
    从同级目录下的 COMPUTER.txt 文件读取电脑配置
    
    文件格式（逗号分隔）：电脑组,IP线程数,交易/仓位线程数
    示例：23,15,10
    
    如果只有一个值，则作为电脑组号，线程数使用默认值
    
    Returns:
        tuple: (电脑组号, IP线程数, 交易线程数)
    """
    # 默认值
    default_group = "0"
    default_ip_thread_count = 15
    default_trade_thread_count = 15
    
    try:
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        computer_file = os.path.join(script_dir, "COMPUTER.txt")
        
        if os.path.exists(computer_file):
            with open(computer_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # 解析配置，支持逗号分隔
                    parts = [p.strip() for p in content.split(',')]
                    
                    # 第一个值：电脑组
                    group = parts[0] if len(parts) > 0 and parts[0] else default_group
                    
                    # 第二个值：IP线程数
                    ip_thread_count = default_ip_thread_count
                    if len(parts) > 1 and parts[1]:
                        try:
                            ip_thread_count = int(parts[1])
                        except ValueError:
                            log_print(f"[系统] ⚠ IP线程数配置无效: {parts[1]}，使用默认值: {default_ip_thread_count}")
                    
                    # 第三个值：交易/仓位线程数
                    trade_thread_count = default_trade_thread_count
                    if len(parts) > 2 and parts[2]:
                        try:
                            trade_thread_count = int(parts[2])
                        except ValueError:
                            log_print(f"[系统] ⚠ 交易线程数配置无效: {parts[2]}，使用默认值: {default_trade_thread_count}")
                    
                    log_print(f"[系统] 从 COMPUTER.txt 读取配置: 电脑组={group}, IP线程数={ip_thread_count}, 交易线程数={trade_thread_count}")
                    return (group, ip_thread_count, trade_thread_count)
                else:
                    log_print(f"[系统] ⚠ COMPUTER.txt 文件为空，使用默认配置")
                    return (default_group, default_ip_thread_count, default_trade_thread_count)
        else:
            log_print(f"[系统] ⚠ 未找到 COMPUTER.txt 文件，使用默认配置")
            return (default_group, default_ip_thread_count, default_trade_thread_count)
    except Exception as e:
        log_print(f"[系统] ⚠ 读取 COMPUTER.txt 失败: {str(e)}，使用默认配置")
        return (default_group, default_ip_thread_count, default_trade_thread_count)


def read_computer_group():
    """
    从同级目录下的 COMPUTER.txt 文件读取电脑组号（兼容旧接口）
    
    Returns:
        str: 电脑组号，如果读取失败则返回 "0"
    """
    group, _, _ = read_computer_config()
    return group


def get_browser_password(browser_id):
    """
    根据浏览器ID获取对应的密码
    优先级：特定浏览器密码 > 电脑组默认密码
    
    Args:
        browser_id: 浏览器编号（int 或 str）
        
    Returns:
        str: 对应的密码
    """
    browser_id_str = str(browser_id)
    
    # 首先检查是否有特定浏览器ID的密码配置
    if browser_id_str in SPECIFIC_BROWSER_PASSWORDS:
        password = SPECIFIC_BROWSER_PASSWORDS[browser_id_str]
        log_print(f"[{browser_id}] 使用特定浏览器密码配置")
        return password
    
    # 如果没有特定配置，使用电脑组对应的默认密码
    group_password = GROUP_PASSWORDS.get(COMPUTER_GROUP)
    if group_password:
        log_print(f"[{browser_id}] 使用电脑组 {COMPUTER_GROUP} 的默认密码")
        return group_password
    
    # 如果电脑组也没有配置，使用全局默认密码
    log_print(f"[{browser_id}] ⚠ 电脑组 {COMPUTER_GROUP} 未配置密码，使用全局默认密码")
    return DEFAULT_PASSWORD


# ============================================================================
# 配置区域
# ============================================================================

# 电脑配置（从 COMPUTER.txt 文件读取）
# 格式：电脑组,IP线程数,交易线程数
COMPUTER_GROUP, IP_THREAD_COUNT, TRADE_THREAD_COUNT = read_computer_config()

# 特定浏览器ID的密码配置
# 格式：浏览器ID: 密码
# 这些浏览器将使用指定的密码，不受电脑组影响
SPECIFIC_BROWSER_PASSWORDS = {
    # 电脑组23的特定浏览器配置
    "1": "mj@w2ndJ*kX0g8!rnsf",  # 电脑组23的浏览器1,2,3,4
    "2":"mj@w2ndJ*kX0g8!rns",
    "3": "mj@w2ndJ*kX0g8!rnsf",
    "4": "mj@w2ndJ*kX0g8!rnsf",
    "9": "qwer1234",
    "10": "qwer1234",
    "6": "5cx2Wsn#0kQnj*w240L",
    "2060": "kaznb3969*m%",  # 电脑组23的浏览器2057,2058,2059,2060
    "2057": "kaznb3969*m%",
    "2058": "kaznb3969*m%",
    "2059": "kaznb3969*m%",
    "4001": "Ok123456",
    # 电脑组9的特定浏览器配置
    "941": "cx142359.",  # 电脑组9的浏览器941-1000
    "942": "cx142359.",
    "944": "cx142359.",
    "945": "cx142359.",
    "946": "cx142359.",
    "947": "cx142359.",
    "948": "cx142359.",
    "949": "cx142359.",
    "950": "cx142359.",
    "951": "cx142359.",
    "952": "cx142359.",
    "953": "cx142359.",
    "954": "cx142359.",
    "955": "cx142359.",
    "956": "cx142359.",
    "957": "cx142359.",
    "958": "cx142359.",
    "959": "cx142359.",
    "960": "cx142359.",
    "961": "cx142359.",
    "962": "cx142359.",
    "963": "cx142359.",
    "964": "cx142359.",
    "965": "cx142359.",
    "966": "cx142359.",
    "967": "cx142359.",
    "968": "cx142359.",
    "969": "cx142359.",
    "970": "cx142359.",
    "971": "cx142359.",
    "972": "cx142359.",
    "973": "cx142359.",
    "974": "cx142359.",
    "975": "cx142359.",
    "976": "cx142359.",
    "977": "cx142359.",
    "978": "cx142359.",
    "979": "cx142359.",
    "980": "cx142359.",
    "981": "cx142359.",
    "982": "cx142359.",
    "983": "cx142359.",
    "984": "cx142359.",
    "985": "cx142359.",
    "986": "cx142359.",
    "987": "cx142359.",
    "988": "cx142359.",
    "989": "cx142359.",
    "990": "cx142359.",
    "991": "cx142359.",
    "992": "cx142359.",
    "993": "cx142359.",
    "994": "cx142359.",
    "995": "cx142359.",
    "996": "cx142359.",
    "997": "cx142359.",
    "998": "cx142359.",
    "999": "cx142359.",
    "1000":"cx142359.",
    "206":"cx142359.",
    "207":"cx142359.",
    "208":"cx142359.",
    "209":"cx142359.",
    "210":"cx142359.",
    "211":"cx142359.",
    "212":"cx142359.",
    "213":"cx142359.",
    "214":"cx142359.",
    "215":"cx142359.",
    "216":"cx142359.",
    "217":"cx142359.",
    "218":"cx142359.",
    "219":"cx142359.",
    "220":"cx142359.",
    "221":"cx142359.",
    "222":"cx142359.",
    "223":"cx142359.",
}

# 电脑组对应的默认密码配置
# 格式：电脑组号: 密码
# 除了在 SPECIFIC_BROWSER_PASSWORDS 中指定的浏览器外，其他浏览器使用对应电脑组的密码
GROUP_PASSWORDS = {
    "0": "Ok123456",  # 电脑组0的密码
    "1": "qwer1234",  # 电脑组1的密码
    "2": "ywj000805*",  # 电脑组2的密码
    "3": "Qrfv*Fjh87gg",  # 电脑组3的密码
    "4": "@#nsgaSBF224",  # 电脑组4的密码
    "5": "Qsst-455fgdf8",  # 电脑组5的密码
    "6": "zxcvbnm123#",  # 电脑组6的密码
    "7": "cx142359.",  # 电脑组7的密码
    "8": "ywj000805*",  # 电脑组8的密码
    "9": "Qwer009qaz`",  # 电脑组9的密码（浏览器941-1000使用特定密码，其他使用此密码）
    "10": "yhCHG^&145",
    "11": "jhJ89891",  # 电脑组11的密码
    "12": "Hhgj*liu-khHy5",  # 电脑组12的密码
    "13": "shdjjeG@^68Jhg",  # 电脑组13的密码
    "14": "gkj^&HGkhh45",  # 电脑组14的密码
    "15": " kaznb3969*m%",  # 电脑组15的密码
    "16": "ggTG*h785Wunj",  # 电脑组16的密码
    "21": "kjakln3*zhjql3",  # 电脑组21的密码
    "22": "ttRo451YU*58",  # 电脑组22的密码
    "23": "mj@w2ndJ*kX0g8!rns",  # 电脑组23的密码（浏览器1,2,3,4使用特定密码）
    "24": "5cx2Wsn#0kQnj*w240",  # 电脑组24的密码
    "25": "kashg2*dk2F",  # 电脑组25的密码
    "26": "cxknwlJK&*f8",  # 电脑组26的密码
    "27": "kiIH78hjfi.*+*",  # 电脑组27的密码
    "900": "Ok123456",  # 电脑组0的密码
    "901": "qwer1234",  # 电脑组1的密码
    "902": "ywj000805*",  # 电脑组2的密码
    "903": "Qrfv*Fjh87gg",  # 电脑组3的密码
    "904": "@#nsgaSBF224",  # 电脑组4的密码
    "905": "Qsst-455fgdf8",  # 电脑组5的密码
    "906": "zxcvbnm123#",  # 电脑组6的密码
    "907": "cx142359.",  # 电脑组7的密码
    "908": "ywj000805*",  # 电脑组8的密码
    "909": "Qwer009qaz`",  # 电脑组9的密码（浏览器941-1000使用特定密码，其他使用此密码）
    "910": "yhCHG^&145",
    "911": "jhJ89891",  # 电脑组11的密码
    "912": "Hhgj*liu-khHy5",  # 电脑组12的密码
    "913": "shdjjeG@^68Jhg",  # 电脑组13的密码
    "914": "gkj^&HGkhh45",  # 电脑组14的密码
    "915": " kaznb3969*m%",  # 电脑组15的密码
    "916": "ggTG*h785Wunj",  # 电脑组16的密码
    "921": "kjakln3*zhjql3",  # 电脑组21的密码
    "922": "ttRo451YU*58",  # 电脑组22的密码
    "923": "mj@w2ndJ*kX0g8!rns",  # 电脑组23的密码（浏览器1,2,3,4使用特定密码）
    "924": "5cx2Wsn#0kQnj*w240",  # 电脑组24的密码
    "925": "kashg2*dk2F",  # 电脑组25的密码
    "926": "cxknwlJK&*f8",  # 电脑组26的密码
    "927": "kiIH78hjfi.*+*",  # 电脑组27的密码
}

# 全局默认密码（仅当电脑组未在 GROUP_PASSWORDS 中配置时使用）
DEFAULT_PASSWORD = "Ok123456"

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


def get_mission_info(mission_id):
    """
    获取任务完整信息（包括msg）
    
    Args:
        mission_id: 任务ID
        
    Returns:
        dict: 任务信息字典，包含status和msg等字段，失败返回None
    """
    try:
        url = f"{SERVER_BASE_URL}/mission/status"
        response = requests.get(url, params={"id": mission_id}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data') and data['data'].get('mission'):
                return data['data']['mission']
        return None
    except Exception as e:
        log_print(f"[系统] 获取任务信息失败: {str(e)}")
        return None


def get_mission_tp9(mission_id):
    """
    获取任务的tp9值（用于Type5任务二的状态同步）
    
    Args:
        mission_id: 任务ID
        
    Returns:
        int: tp9的值，失败或无值返回None
    """
    try:
        url = f"{SERVER_BASE_URL}/mission/status"
        response = requests.get(url, params={"id": mission_id}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data') and data['data'].get('mission'):
                tp9 = data['data']['mission'].get('tp9')
                if tp9 is not None:
                    try:
                        return int(tp9)
                    except (ValueError, TypeError):
                        return None
        return None
    except Exception as e:
        log_print(f"[系统] 获取任务tp9失败: {str(e)}")
        return None


def update_mission_tp(mission_id, tp5=None, tp6=None, tp8=None, tp9=None, price=None, amt=None):
    """
    更新任务数据（tp5, tp6, tp8, tp9, price）
    
    Args:
        mission_id: 任务ID
        tp5: tp5字段值（可选）- 挂单超过XX小时撤单
        tp6: tp6字段值（可选）- 用于存储使用的IP和代理方式，格式：ip|||http/socks5
        tp8: tp8字段值（可选）
        tp9: tp9字段值（可选）- 用于Type5任务二的状态同步
        price: price字段值（可选）
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    max_retries = 5
    retry_delay = 3  # 重试间隔秒数
    
    url = f"{SERVER_BASE_URL}/mission/updateMissionTp"
    payload = {"id": mission_id}
    
    if tp5 is not None:
        payload["tp5"] = tp5
    if tp6 is not None:
        payload["tp6"] = tp6
    if tp8 is not None:
        payload["tp8"] = tp8
    if tp9 is not None:
        payload["tp9"] = tp9
    if price is not None:
        payload["price"] = price
    if amt is not None:
        payload["amt"] = amt

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    log_print(f"[系统] ✓ 更新任务{mission_id}数据成功")
                    return True
                else:
                    log_print(f"[系统] ⚠ 更新任务{mission_id}数据失败: {data.get('msg', '未知错误')} (第{attempt + 1}/{max_retries}次)")
            else:
                log_print(f"[系统] ⚠ 更新任务{mission_id}数据失败，状态码: {response.status_code} (第{attempt + 1}/{max_retries}次)")
        except Exception as e:
            log_print(f"[系统] ⚠ 更新任务{mission_id}数据异常: {str(e)} (第{attempt + 1}/{max_retries}次)")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries - 1:
            log_print(f"[系统] 等待{retry_delay}秒后重试...")
            time.sleep(retry_delay)
    
    log_print(f"[系统] ✗ 更新任务{mission_id}数据失败，已重试{max_retries}次")
    return False


def save_recent_price(trending_id, outcome, price):
    """
    保存最近的价格到 /hedge/recentPrice 接口
    
    Args:
        trending_id: 交易主题ID
        outcome: 选项类型 ("YES" 或 "NO")
        price: 价格
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    max_retries = 3
    retry_delay = 2  # 重试间隔秒数
    
    url = f"{SERVER_BASE_URL}/hedge/recentPrice"
    payload = {
        "trendingId": trending_id,
        "outcome": outcome,
        "price": price
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    log_print(f"[系统] ✓ 保存最近价格成功: trendingId={trending_id}, outcome={outcome}, price={price}")
                    return True
                else:
                    log_print(f"[系统] ⚠ 保存最近价格失败: {data.get('msg', '未知错误')} (第{attempt + 1}/{max_retries}次)")
            else:
                log_print(f"[系统] ⚠ 保存最近价格失败，状态码: {response.status_code} (第{attempt + 1}/{max_retries}次)")
        except Exception as e:
            log_print(f"[系统] ⚠ 保存最近价格异常: {str(e)} (第{attempt + 1}/{max_retries}次)")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries - 1:
            log_print(f"[系统] 等待{retry_delay}秒后重试...")
            time.sleep(retry_delay)
    
    log_print(f"[系统] ✗ 保存最近价格失败，已重试{max_retries}次")
    return False


def send_fingerprint_monitor_request(browser_id):
    """
    发送 fingerprint 监控请求
    
    Args:
        browser_id: 浏览器ID
        
    Returns:
        bool: 成功返回True
    """
    try:
        url = "https://enstudyai.fatedreamer.com/t3/api/queue/monitor/submit"
        payload = {
            "fingerprintNo": str(browser_id),
            "count": 3,
            "interval": 120
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            log_print(f"[{browser_id}] ✓ 发送 fingerprint 监控请求成功")
            return True
        else:
            log_print(f"[{browser_id}] ⚠ 发送 fingerprint 监控请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 发送 fingerprint 监控请求异常: {str(e)}")
        return False


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
    retry_delay = 5  # 秒
    
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
            if msg == "":
                payload = {
                    "id": mission_id,
                    "status": status
                }
           
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                log_print(f"[系统] ✓ 保存任务{mission_id}结果成功 （第 {attempt + 1} 次尝试）")
                return True
            else:
                log_print(f"[系统] ⚠ 保存任务{mission_id}结果失败，状态码: {response.status_code}")
                
        except Exception as e:
            log_print(f"[系统] ⚠ 保存任务{mission_id}结果失败: {str(e)}")
        
        # 如果不是最后一次尝试，继续重试
        if attempt < max_retries:
            continue
        else:
            log_print(f"[系统] ✗✗✗ 保存任务{mission_id}结果失败，已重试 {max_retries} 次")
    
    return False

# 全局线程池配置（从 COMPUTER.txt 读取的 TRADE_THREAD_COUNT）
MAX_WORKERS = TRADE_THREAD_COUNT
global_thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks_lock = threading.Lock()
active_tasks = {}  # {mission_id: {'futures': [], 'results': {}, 'total': 0, 'completed': 0}}

# 正在执行 type=3 任务的浏览器ID映射 {browser_id: mission_id}
active_type3_browsers = {}
active_type3_browsers_lock = threading.Lock()

# 正在执行 type=2 任务的浏览器ID映射 {browser_id: mission_id}
active_type2_browsers = {}
active_type2_browsers_lock = threading.Lock()

# 全局浏览器锁机制（不区分任务类型）：正在执行任务的浏览器ID映射 {browser_id: mission_id}
active_browsers = {}
active_browsers_lock = threading.Lock()

# 浏览器等待队列：{browser_id: [task_data1, task_data2, ...]}
browser_waiting_queue = {}
browser_waiting_queue_lock = threading.Lock()

# AdsPower配置
ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"

# 全局字典：存储每个浏览器最后使用的代理配置
LAST_PROXY_CONFIG = {}

# 浏览器编号到用户ID的映射
FINGERPRINT_TO_USERID = {}

# 存储从 beijing_time.html 页面获取的时区信息
# 格式: {serial_number: timezone_name}
BEIJING_TIME_PAGE_TIMEZONE = {}

# 最大重试次数
MAX_RETRIES = 3


# ============================================================================
# 代理IP管理相关函数
# ============================================================================



def get_new_ip_for_browser(browser_id, timeout=15, ip_index=0, mission_id=None):
    """
    获取浏览器新代理配置的接口（从IP状态列表中按延迟选择）
    
    Args:
        browser_id: 浏览器编号
        timeout: 请求超时时间（秒），默认15秒
        ip_index: IP选择索引
            - 0: 获取延迟最低的IP及代理方式
            - 1: 获取延迟第二低的IP及代理方式
            - 依次类推
        mission_id: 任务ID（可选），如果传入则会将选择的IP和代理方式更新到任务的tp6字段
        
    Returns:
        dict: 代理配置信息，包含 ip, port, username, password, type, delay，失败返回None
    """
    try:
        log_print(f"[{browser_id}] 调用获取IP状态列表接口（超时: {timeout}秒，ip_index={ip_index}）...")
        
        url = "https://sg.bicoin.com.cn/99l/bro/ipStatusByNumber"
        params = {"number": browser_id}
        
        response = requests.get(url, params=params, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] IP状态列表接口返回: {result}")
            
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                ip_list = data.get("list", [])
                
                if not ip_list:
                    log_print(f"[{browser_id}] ⚠ 返回数据中没有IP列表")
                    return None
                
                # 筛选出每个IP能用的模式以及延迟（每个IP最多只选一个，如果http和socks5都通，选延迟低的）
                available_options = []
                
                for ip_item in ip_list:
                    ip = ip_item.get("ip")
                    username = ip_item.get("username")
                    password = ip_item.get("password")
                    # 获取端口字段：http使用port，socks5使用socketPort
                    http_port = ip_item.get("port")
                    socks5_port = ip_item.get("socketPort")
                    # 将端口转换为字符串，如果没有则使用默认值
                    http_port_str = str(http_port) if http_port is not None else "50100"
                    socks5_port_str = str(socks5_port) if socks5_port is not None else "50101"
                    
                    if not ip or not username or not password:
                        continue
                    
                    # 检查http代理（c字段=1表示可用，h字段表示延迟）
                    c_value = ip_item.get("c")
                    # 兼容字符串"1"和整数1
                    http_available = (str(c_value) == "1")
                    http_delay_str = ip_item.get("h") if http_available else None
                    # 将延迟转换为整数，如果转换失败则设为None
                    try:
                        http_delay = int(http_delay_str) if http_delay_str is not None and str(http_delay_str).strip() and str(http_delay_str) != "-1" else None
                    except (ValueError, TypeError):
                        http_delay = None
                    
                    # 检查socks5代理（f字段=1表示可用，i字段表示延迟）
                    f_value = ip_item.get("f")
                    # 兼容字符串"1"和整数1
                    socks5_available = (str(f_value) == "1")
                    socks5_delay_str = ip_item.get("i") if socks5_available else None
                    # 将延迟转换为整数，如果转换失败则设为None
                    try:
                        socks5_delay = int(socks5_delay_str) if socks5_delay_str is not None and str(socks5_delay_str).strip() and str(socks5_delay_str) != "-1" else None
                    except (ValueError, TypeError):
                        socks5_delay = None
                    
                    # 如果http和socks5都通，选择延迟较低的那个
                    if http_available and socks5_available:
                        if http_delay is not None and socks5_delay is not None:
                            if http_delay <= socks5_delay:
                                # http延迟更低或相等，选择http
                                available_options.append({
                                    "ip": ip,
                                    "port": http_port_str,
                                    "username": username,
                                    "password": password,
                                    "type": "http",
                                    "delay": http_delay
                                })
                            else:
                                # socks5延迟更低，选择socks5
                                available_options.append({
                                    "ip": ip,
                                    "port": socks5_port_str,
                                    "username": username,
                                    "password": password,
                                    "type": "socks5",
                                    "delay": socks5_delay
                                })
                        elif http_delay is not None:
                            # 只有http有延迟数据，选择http
                            available_options.append({
                                "ip": ip,
                                "port": http_port_str,
                                "username": username,
                                "password": password,
                                "type": "http",
                                "delay": http_delay
                            })
                        elif socks5_delay is not None:
                            # 只有socks5有延迟数据，选择socks5
                            available_options.append({
                                "ip": ip,
                                "port": socks5_port_str,
                                "username": username,
                                "password": password,
                                "type": "socks5",
                                "delay": socks5_delay
                            })
                    elif http_available and http_delay is not None:
                        # 只有http通，选择http
                        available_options.append({
                            "ip": ip,
                            "port": http_port_str,
                            "username": username,
                            "password": password,
                            "type": "http",
                            "delay": http_delay
                        })
                    elif socks5_available and socks5_delay is not None:
                        # 只有socks5通，选择socks5
                        available_options.append({
                            "ip": ip,
                            "port": socks5_port_str,
                            "username": username,
                            "password": password,
                            "type": "socks5",
                            "delay": socks5_delay
                        })
                    else:
                        # 如果都不通，检查是否有成功次数大于0的，用于优先级排序
                        # 解析字段b（http的成功失败次数，格式："成功次数,失败次数"）
                        http_success_count = 0
                        b_value = ip_item.get("b")
                        if b_value:
                            try:
                                b_parts = str(b_value).split(",")
                                if len(b_parts) >= 1:
                                    http_success_count = int(b_parts[0].strip())
                            except (ValueError, TypeError, AttributeError):
                                http_success_count = 0
                        
                        # 解析字段e（socks5的成功失败次数，格式："成功次数,失败次数"）
                        socks5_success_count = 0
                        e_value = ip_item.get("e")
                        if e_value:
                            try:
                                e_parts = str(e_value).split(",")
                                if len(e_parts) >= 1:
                                    socks5_success_count = int(e_parts[0].strip())
                            except (ValueError, TypeError, AttributeError):
                                socks5_success_count = 0
                        
                        # 判断是否有成功次数大于0的
                        has_success = (http_success_count > 0) or (socks5_success_count > 0)
                        
                        # 如果有成功次数，延迟设为999998（比999999小，排序时会排在前面）
                        # 如果没有成功次数，延迟设为999999（排在最后）
                        delay_value = 999998 if has_success else 999999
                        
                        # 优先选择http类型
                        available_options.append({
                            "ip": ip,
                            "port": http_port_str,
                            "username": username,
                            "password": password,
                            "type": "http",
                            "delay": delay_value
                        })
                
                if not available_options:
                    log_print(f"[{browser_id}] ⚠ 没有可用的IP代理配置")
                    return None
                
                # 按延迟从低到高排序
                available_options.sort(key=lambda x: x.get("delay", 999999))
                log_print(f"[{browser_id}] 筛选出{len(available_options)}个可用代理配置，已按延迟排序")
                
                # 根据ip_index选择
                if ip_index >= len(available_options):
                    log_print(f"[{browser_id}] ⚠ ip_index={ip_index} 超出可用配置数量({len(available_options)})")
                    return None
                
                selected_option = available_options[ip_index]
                log_print(f"[{browser_id}] ✓ 选择第{ip_index+1}个配置: IP={selected_option['ip']}, Port={selected_option['port']}, Type={selected_option['type']}, Delay={selected_option['delay']}")
                
                # 如果传入了mission_id，更新任务的tp6字段为 ip|||代理方式
                if mission_id is not None:
                    # 先获取任务的当前信息，检查tp6是否已有值
                    mission_info = get_mission_info(mission_id)
                    new_tp6_value = f"{selected_option['ip']}|||{selected_option['type']}"
                    
                    if mission_info and mission_info.get('tp6'):
                        # 如果tp6已有值，用分号拼接新值
                        existing_tp6 = mission_info.get('tp6')
                        tp6_value = f"{existing_tp6};{new_tp6_value}"
                    else:
                        # 如果tp6没有值，直接使用新值
                        tp6_value = new_tp6_value
                    
                    update_mission_tp(mission_id, tp6=tp6_value)
                    log_print(f"[{browser_id}] ✓ 已更新任务{mission_id}的tp6为: {tp6_value}")
                
                return selected_option
                    
            else:
                log_print(f"[{browser_id}] ⚠ 获取IP状态列表失败: code={code}, msg={result.get('msg')}")
                return None
        else:
            log_print(f"[{browser_id}] ✗ 获取IP状态列表请求失败: HTTP状态码 {response.status_code}")
            return None
        
    except requests.exceptions.Timeout:
        log_print(f"[{browser_id}] ✗ 获取IP状态列表请求超时（{timeout}秒）")
        return None
    except requests.exceptions.RequestException as e:
        log_print(f"[{browser_id}] ✗ 获取IP状态列表网络请求失败: {str(e)}")
        return None
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取IP状态列表异常: {str(e)}")
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


def call_change_ip_to_err(browser_id, current_ip, timeout=15):
    """
    调用 changeIpToErr 接口，标记IP为错误
    
    Args:
        browser_id: 浏览器编号
        current_ip: 当前使用的IP地址
        timeout: 请求超时时间（秒），默认15秒
        
    Returns:
        bool: 是否调用成功
    """
    try:
        if not current_ip:
            log_print(f"[{browser_id}] ⚠ 无法调用 changeIpToErr：current_ip 为空")
            return False
            
        log_print(f"[{browser_id}] 调用 changeIpToErr 接口（IP: {current_ip}，超时: {timeout}秒）...")
        
        url = "https://sg.bicoin.com.cn/99l/bro/changeIpToErr"
        payload = {
            "number": browser_id,
            "ip": current_ip
        }
        
        response = requests.post(url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] changeIpToErr 接口返回: {result}")
            
            code = result.get("code")
            if code == 0:
                log_print(f"[{browser_id}] ✓ 成功调用 changeIpToErr 接口")
                return True
            else:
                log_print(f"[{browser_id}] ⚠ changeIpToErr 调用失败: code={code}, msg={result.get('msg')}")
                return False
        else:
            log_print(f"[{browser_id}] ✗ changeIpToErr 请求失败: HTTP状态码 {response.status_code}")
            return False
        
    except requests.exceptions.Timeout:
        log_print(f"[{browser_id}] ✗ changeIpToErr 请求超时（{timeout}秒）")
        return False
    except requests.exceptions.RequestException as e:
        log_print(f"[{browser_id}] ✗ changeIpToErr 网络请求失败: {str(e)}")
        return False
    except Exception as e:
        log_print(f"[{browser_id}] ✗ changeIpToErr 异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False


def get_ip_list_by_number(browser_id, timeout=15):
    """
    获取浏览器IP状态列表
    
    Args:
        browser_id: 浏览器编号
        timeout: 请求超时时间（秒），默认15秒
        
    Returns:
        list: IP列表（已按delay排序），失败返回None
    """
    try:
        url = "https://sg.bicoin.com.cn/99l/bro/ipStatusByNumber"
        params = {"number": browser_id}
        
        response = requests.get(url, params=params, timeout=timeout)
        
        if response.status_code == 200:
            result = response.json()
            code = result.get("code")
            if code == 0:
                data = result.get("data", {})
                ip_list = data.get("list", [])
                # 按delay排序
                sorted_ip_list = sorted(ip_list, key=lambda x: x.get("delay", 999999))
                return sorted_ip_list
            else:
                log_print(f"[{browser_id}] ⚠ 获取IP列表失败: code={code}, msg={result.get('msg')}")
                return None
        else:
            log_print(f"[{browser_id}] ✗ 获取IP列表请求失败: HTTP状态码 {response.status_code}")
            return None
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取IP列表异常: {str(e)}")
        return None


def get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=None):
    """
    根据重试次数获取代理配置（支持多次IP更换）
    
    Args:
        browser_id: 浏览器编号
        retry_count: 当前重试次数（0=第一次更换，1=第二次更换，以此类推）
        timeout: 请求超时时间（秒），默认15秒
        mission_id: 任务ID（可选），如果传入则会将选择的IP和代理方式更新到任务的tp6字段
        
    Returns:
        dict: 代理配置信息，包含 ip, port, username, password, type, delay，失败返回None
    """
    # 使用 ip_index=retry_count+1 来选择IP
    ip_index = retry_count + 1
    log_print(f"[{browser_id}] 第{retry_count+1}次IP更换：使用 ip_index={ip_index}...")
    
    proxy_config = get_new_ip_for_browser(browser_id, timeout=timeout, ip_index=ip_index, mission_id=mission_id)
    
    if proxy_config:
        log_print(f"[{browser_id}] ✓ 第{retry_count+1}次IP更换成功: IP={proxy_config['ip']}, Port={proxy_config['port']}, Type={proxy_config['type']}, Delay={proxy_config.get('delay')}")
        return proxy_config
    else:
        log_print(f"[{browser_id}] ✗ 第{retry_count+1}次IP更换失败")
        return None


def try_update_ip_before_start(browser_id, bro_log_list=None, mission_id=None):
    """
    在打开浏览器前尝试获取并更新代理配置（8秒超时）
    
    Args:
        browser_id: 浏览器编号
        bro_log_list: 浏览器日志列表（可选），如果提供则记录日志
        mission_id: 任务ID（可选），如果传入则会将选择的IP和代理方式更新到任务的tp6字段
        
    Returns:
        tuple: (bool, str, int) - (是否成功更新了代理配置, 当前使用的IP, 延迟)
               如果未获取到新配置或更新失败，返回 (False, None, None)
    """
    try:
        log_print(f"[{browser_id}] 尝试在打开浏览器前获取新代理配置...")
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, "尝试在打开浏览器前获取新代理配置...")
        
        proxy_config = get_new_ip_for_browser(browser_id, timeout=8, ip_index=0, mission_id=mission_id)
        
        if proxy_config:
            current_ip = proxy_config.get("ip")
            current_delay = proxy_config.get("delay")
            log_print(f"[{browser_id}] 在8秒内获取到新代理配置: IP={current_ip}, Delay={current_delay}, 开始更新...")
            update_success = update_adspower_proxy(browser_id, proxy_config)
            
            if update_success:
                log_print(f"[{browser_id}] ✓ 代理配置更新成功")
                if bro_log_list is not None:
                    add_bro_log_entry(bro_log_list, browser_id, f"[0]初始IP更新成功: IP={current_ip}, Delay={current_delay}")
                return True, current_ip, current_delay
            else:
                log_print(f"[{browser_id}] ⚠ 代理配置更新失败，但仍保存获取到的代理配置信息")
                # 即使更新失败，也保存获取到的代理配置，以便后续使用
                LAST_PROXY_CONFIG[str(browser_id)] = proxy_config.copy()
                if bro_log_list is not None:
                    add_bro_log_entry(bro_log_list, browser_id, f"[0]代理配置更新失败，但已保存配置: IP={current_ip}, Delay={current_delay}")
                return False, current_ip, current_delay
        else:
            log_print(f"[{browser_id}] 8秒内未获取到新代理配置")
            # 尝试从LAST_PROXY_CONFIG获取当前使用的IP和延迟
            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
            if last_config:
                current_ip = last_config.get("ip")
                current_delay = last_config.get("delay")
                log_print(f"[{browser_id}] 使用上次的代理配置: IP={current_ip}, Delay={current_delay}")
                if bro_log_list is not None:
                    add_bro_log_entry(bro_log_list, browser_id, f"[0]初始IP（使用上次配置）: IP={current_ip}, Delay={current_delay}")
                return False, current_ip, current_delay
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, "[0]未获取到代理配置，IP信息未知")
            return False, None, None
            
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 尝试更新代理配置时发生异常: {str(e)}")
        # 尝试从LAST_PROXY_CONFIG获取当前使用的IP和延迟
        try:
            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
            if last_config:
                current_ip = last_config.get("ip")
                current_delay = last_config.get("delay")
                log_print(f"[{browser_id}] 异常时使用上次的代理配置: IP={current_ip}, Delay={current_delay}")
                if bro_log_list is not None:
                    add_bro_log_entry(bro_log_list, browser_id, f"[0]初始IP（异常时使用上次配置）: IP={current_ip}, Delay={current_delay}")
                return False, current_ip, current_delay
        except:
            pass
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, f"[0]获取初始IP时发生异常: {str(e)}")
        return False, None, None


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
    launch_args = [f"--window-size={1500},{1700}"]
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
            time.sleep(30 + 30 * attempt)
    
    log_print(f"[{serial_number}] ✗✗✗ 浏览器启动失败，已达到最大重试次数")
    return None


def send_feishu_message(serial_number):
    """
    发送飞书消息通知浏览器关闭失败
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    # 先获取 tenant_access_token
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_payload = {
        "app_id": "cli_a6010dfab0b1500b",
        "app_secret": "vwSJuuQLiPelg3QJQeQmrcTpSa2uQrW0"
    }
    
    tenant_access_token = None
    token_max_retries = 3
    for token_attempt in range(token_max_retries):
        try:
            log_print(f"[{serial_number}] 正在获取飞书访问令牌 (第 {token_attempt + 1}/{token_max_retries} 次)...")
            token_response = requests.post(token_url, json=token_payload, timeout=10)
            token_data = token_response.json()
            
            if token_data.get("code") != 0:
                log_print(f"[{serial_number}] ✗ 获取飞书访问令牌失败: {token_data.get('msg')}")
                if token_attempt < token_max_retries - 1:
                    time.sleep(2)
                continue
            
            tenant_access_token = token_data.get("tenant_access_token")
            if not tenant_access_token:
                log_print(f"[{serial_number}] ✗ 获取飞书访问令牌失败: 响应中未找到 tenant_access_token")
                if token_attempt < token_max_retries - 1:
                    time.sleep(2)
                continue
            
            log_print(f"[{serial_number}] ✓ 飞书访问令牌获取成功")
            break
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 获取飞书访问令牌时发生错误: {str(e)}")
            if token_attempt < token_max_retries - 1:
                time.sleep(2)
    
    if not tenant_access_token:
        log_print(f"[{serial_number}] ✗ 获取飞书访问令牌失败，已达到最大重试次数")
        return False
    
    # 使用获取到的 token 发送消息
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        'Authorization': f'Bearer {tenant_access_token}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    content_text = f"电脑组{COMPUTER_GROUP}浏览器编号{serial_number} 关闭失败，需要人工关闭"
    payload = {
        "receive_id": "oc_ce7c949dd73b573a28063d76f0d02e24",
        "msg_type": "text",
        "content": json.dumps({"text": content_text})
    }
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] 尝试发送飞书消息 (第 {attempt + 1}/{max_retries} 次)")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 飞书消息发送成功")
                return True
            else:
                log_print(f"[{serial_number}] ✗ 飞书消息发送失败: {data.get('msg')}")
                
                if attempt < max_retries - 1:
                    time.sleep(30)
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 发送飞书消息时发生错误: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(30)
    
    log_print(f"[{serial_number}] ✗ 飞书消息发送失败，已达到最大重试次数")
    return False


def send_feishu_custom_message(serial_number, message_text):
    """
    发送自定义飞书消息
    
    Args:
        serial_number: 浏览器序列号
        message_text: 要发送的消息内容
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    # 先获取 tenant_access_token
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_payload = {
        "app_id": "cli_a6010dfab0b1500b",
        "app_secret": "vwSJuuQLiPelg3QJQeQmrcTpSa2uQrW0"
    }
    
    tenant_access_token = None
    token_max_retries = 3
    for token_attempt in range(token_max_retries):
        try:
            log_print(f"[{serial_number}] 正在获取飞书访问令牌 (第 {token_attempt + 1}/{token_max_retries} 次)...")
            token_response = requests.post(token_url, json=token_payload, timeout=10)
            token_data = token_response.json()
            
            if token_data.get("code") != 0:
                log_print(f"[{serial_number}] ✗ 获取飞书访问令牌失败: {token_data.get('msg')}")
                if token_attempt < token_max_retries - 1:
                    time.sleep(2)
                continue
            
            tenant_access_token = token_data.get("tenant_access_token")
            if not tenant_access_token:
                log_print(f"[{serial_number}] ✗ 获取飞书访问令牌失败: 响应中未找到 tenant_access_token")
                if token_attempt < token_max_retries - 1:
                    time.sleep(2)
                continue
            
            log_print(f"[{serial_number}] ✓ 飞书访问令牌获取成功")
            break
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 获取飞书访问令牌时发生错误: {str(e)}")
            if token_attempt < token_max_retries - 1:
                time.sleep(2)
    
    if not tenant_access_token:
        log_print(f"[{serial_number}] ✗ 获取飞书访问令牌失败，已达到最大重试次数")
        return False
    
    # 使用获取到的 token 发送消息
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        'Authorization': f'Bearer {tenant_access_token}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    payload = {
        "receive_id": "oc_ce7c949dd73b573a28063d76f0d02e24",
        "msg_type": "text",
        "content": json.dumps({"text": message_text})
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] 尝试发送飞书消息 (第 {attempt + 1}/{max_retries} 次)")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 飞书消息发送成功")
                return True
            else:
                log_print(f"[{serial_number}] ✗ 飞书消息发送失败: {data.get('msg')}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 发送飞书消息时发生错误: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
    
    log_print(f"[{serial_number}] ✗ 飞书消息发送失败，已达到最大重试次数")
    return False


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
    errmsg = ''
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] 尝试关闭浏览器 (第 {attempt + 1}/{max_retries} 次)")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 浏览器关闭命令已发送")
                time.sleep(10)
                return True
            else:
                log_print(f"[{serial_number}] ✗ 关闭浏览器失败: {data.get('msg')}")
                errmsg = data.get('msg')
                if attempt < max_retries - 1:
                    time.sleep(10)
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 关闭浏览器时发生错误: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(10)
    
    log_print(f"[{serial_number}] ✗ 浏览器关闭失败，已达到最大重试次数")
    # 异步发送飞书消息通知，不阻塞主流程
    # if 'User_id is not open' not in errmsg:
    #     threading.Thread(target=send_feishu_message, args=(serial_number,), daemon=True).start()
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
    
    # 设置页面加载超时时间为60秒，防止页面加载卡死导致线程无法释放
    driver.set_page_load_timeout(75)
    driver.set_script_timeout(75)
    
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
        payload = {"groupNo": COMPUTER_GROUP,"typeList": [1,2,4,5,6,9]}
        
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


def submit_mission_result(mission_id, success_count, failed_count, failed_info, status=2, custom_msg=None):
    """
    提交任务结果到服务器（带重试机制）
    
    Args:
        mission_id: 任务ID
        success_count: 成功数量
        failed_count: 失败数量
        failed_info: 失败的浏览器信息字典 {browser_id: failure_reason}
        status: 任务状态，2=成功，3=失败
        custom_msg: 自定义消息（如果提供，将使用此消息而不是默认格式）
        
    Returns:
        bool: 提交成功返回True，失败返回False
    """
    url = f"{SERVER_BASE_URL}/mission/saveResult"
    
    # 构建消息
    if custom_msg:
        # 如果提供了自定义消息，直接使用
        msg = custom_msg
    else:
        # 否则使用默认格式
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


def call_remove_number_in_use(browser_id, log_prefix=""):
    """
    调用 removeNumberInUse 接口，带重试机制
    
    Args:
        browser_id: 浏览器ID
        log_prefix: 日志前缀（可选，用于区分不同的调用场景）
        
    Returns:
        bool: 调用成功返回True，失败返回False
    """
    remove_url = "https://sg.bicoin.com.cn/99l/hedge/removeNumberInUse"
    max_retries = 3
    retry_interval = 20  # 秒
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_print(f"[{browser_id}] {log_prefix}removeNumberInUse 第 {attempt + 1} 次重试...")
                time.sleep(retry_interval)
            else:
                log_print(f"[{browser_id}] {log_prefix}调用 removeNumberInUse 接口...")
            
            remove_resp = requests.post(remove_url, json={"number": browser_id, "group": COMPUTER_GROUP}, timeout=10)
            
            if remove_resp.status_code == 200:
                log_print(f"[{browser_id}] removeNumberInUse 响应成功: {remove_resp.status_code}")
                return True
            else:
                log_print(f"[{browser_id}] removeNumberInUse 响应状态码异常: {remove_resp.status_code}")
                if attempt < max_retries - 1:
                    continue
                return False
                
        except Exception as e:
            log_print(f"[{browser_id}] removeNumberInUse 调用失败: {str(e)}")
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


def refresh_page_with_opinion_check(driver, serial_number=""):
    """
    刷新页面前，检查当前网址是否包含 "app.opinion.trade"
    如果不包含，切换到包含 "app.opinion.trade" 的标签页，然后再刷新
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号（用于日志）
    """
    try:
        # 检查当前网址是否包含 "app.opinion.trade"
        current_url = driver.current_url
        if "app.opinion.trade" in current_url:
            # 当前页面已经是 opinion.trade，直接刷新
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ✓ 已刷新页面（当前已在 app.opinion.trade）")
            return
        
        # 当前页面不是 opinion.trade，需要切换到包含 "app.opinion.trade" 的标签页
        if serial_number:
            log_print(f"[{serial_number}] ⚠ 当前页面不是 app.opinion.trade ({current_url[:80]}...)，查找包含 app.opinion.trade 的标签页...")
        
        all_windows = driver.window_handles
        opinion_window = None
        
        # 查找包含 "app.opinion.trade" 的标签页
        for window_handle in all_windows:
            try:
                driver.switch_to.window(window_handle)
                window_url = driver.current_url
                if "app.opinion.trade" in window_url:
                    opinion_window = window_handle
                    if serial_number:
                        log_print(f"[{serial_number}] ✓ 找到 app.opinion.trade 标签页: {window_url[:80]}...")
                    break
            except Exception as e:
                # 某些标签页可能无法访问URL（如chrome://等系统页面），跳过继续查找
                continue
        
        if opinion_window:
            # 切换到 opinion.trade 标签页并刷新
            driver.switch_to.window(opinion_window)
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ✓ 已切换到 app.opinion.trade 标签页并刷新")
        else:
            # 如果没找到包含 "app.opinion.trade" 的标签页，在当前页面刷新（兜底）
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ⚠ 未找到包含 app.opinion.trade 的标签页，在当前页面刷新")
                
    except Exception as e:
        # 如果发生异常，尝试直接刷新（兜底）
        try:
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ⚠ 刷新页面时发生异常，已尝试直接刷新: {str(e)}")
        except:
            if serial_number:
                log_print(f"[{serial_number}] ✗ 刷新页面失败: {str(e)}")


def preopen_okx_wallet(driver, serial_number, current_ip=None, current_delay=None):
    """
    预先打开OKX钱包页面，解锁钱包并处理所有待确认的弹窗
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        current_ip: 当前使用的IP地址（可选）
        current_delay: 当前IP的延迟（可选，单位：毫秒）
        
    Returns:
        str: 主窗口句柄
    """
    log_print(f"[{serial_number}] [预处理] 检查并预打开 OKX 钱包页面...")
    
    # 保存主窗口句柄
    main_window = driver.current_window_handle
    
    # 先预打开 beijing_time.html 页面
    try:
        log_print(f"[{serial_number}] → 预打开 beijing_time.html 页面...")
        
        # 构建URL，包含IP和延迟参数
        beijing_time_url = f"https://oss.w3id.info/OpsStatistics/beijing_time.html?browser={serial_number}"
        if current_ip:
            beijing_time_url += f"&ip={current_ip}"
        if current_delay is not None:
            beijing_time_url += f"&delay={current_delay}"
        
        success = open_new_tab_with_url(driver, beijing_time_url, serial_number)
        if success:
            log_print(f"[{serial_number}] ✓ beijing_time.html 页面已打开")
            
            # 尝试从页面获取时区信息
            try:
                # 获取所有窗口句柄，找到新打开的窗口
                all_windows = driver.window_handles
                beijing_time_window = None
                for window in all_windows:
                    if window != main_window:
                        try:
                            driver.switch_to.window(window)
                            current_url = driver.current_url
                            if "beijing_time.html" in current_url:
                                beijing_time_window = window
                                break
                        except:
                            continue
                
                if beijing_time_window:
                    driver.switch_to.window(beijing_time_window)
                    
                    # 等待页面加载完成并获取时区信息
                    try:
                        # 首先等待页面 DOM 加载完成
                        WebDriverWait(driver, 15).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        log_print(f"[{serial_number}] → 页面 DOM 加载完成，等待 JavaScript 初始化...")
                        
                        # 等待 window.beijingTimePageInfo 对象存在（最多等待 20 秒）
                        def check_beijing_time_info_ready(driver):
                            try:
                                result = driver.execute_script("""
                                    if (typeof window.beijingTimePageInfo !== 'undefined') {
                                        return {
                                            exists: true,
                                            ready: window.beijingTimePageInfo.ready || false,
                                            hasBrowserTz: !!window.beijingTimePageInfo.browserTimezone,
                                            hasIpTz: !!window.beijingTimePageInfo.ipTimezone
                                        };
                                    }
                                    return { exists: false, ready: false };
                                """)
                                return result and result.get('exists', False)
                            except:
                                return False
                        
                        try:
                            WebDriverWait(driver, 20).until(check_beijing_time_info_ready)
                            log_print(f"[{serial_number}] → beijingTimePageInfo 对象已创建")
                        except Exception as wait_error:
                            log_print(f"[{serial_number}] ⚠ 等待 beijingTimePageInfo 对象超时: {str(wait_error)}")
                        
                        # 等待 ready 标志为 true（最多等待 15 秒，因为 IP 时区是异步获取的）
                        def check_ready_flag(driver):
                            try:
                                result = driver.execute_script("""
                                    return window.beijingTimePageInfo && window.beijingTimePageInfo.ready === true;
                                """)
                                return result is True
                            except:
                                return False
                        
                        try:
                            WebDriverWait(driver, 15).until(check_ready_flag)
                            log_print(f"[{serial_number}] → beijingTimePageInfo.ready 已为 true")
                        except Exception as wait_error:
                            log_print(f"[{serial_number}] ⚠ 等待 ready 标志超时，尝试直接获取时区信息...")
                        
                        # 执行 JavaScript 获取时区信息（带详细日志）
                        debug_info = driver.execute_script("""
                            if (typeof window.beijingTimePageInfo === 'undefined') {
                                return { error: 'beijingTimePageInfo 对象不存在' };
                            }
                            return {
                                exists: true,
                                ready: window.beijingTimePageInfo.ready,
                                browserTimezone: window.beijingTimePageInfo.browserTimezone,
                                ipTimezone: window.beijingTimePageInfo.ipTimezone,
                                browserTimezoneFull: window.beijingTimePageInfo.browserTimezoneFull
                            };
                        """)
                        
                        if debug_info and not debug_info.get('error'):
                            log_print(f"[{serial_number}] → 调试信息: ready={debug_info.get('ready')}, browserTz={debug_info.get('browserTimezone')}, ipTz={debug_info.get('ipTimezone')}")
                        
                        # 获取时区信息（优先使用IP时区，如果没有则使用浏览器时区）
                        timezone_info = driver.execute_script("""
                            if (window.beijingTimePageInfo) {
                                // 即使 ready 为 false，也尝试获取浏览器时区（它应该是立即可用的）
                                if (window.beijingTimePageInfo.ipTimezone) {
                                    return window.beijingTimePageInfo.ipTimezone;
                                }
                                if (window.beijingTimePageInfo.browserTimezone) {
                                    return window.beijingTimePageInfo.browserTimezone;
                                }
                            }
                            return null;
                        """)
                        
                        if timezone_info:
                            BEIJING_TIME_PAGE_TIMEZONE[serial_number] = timezone_info
                            log_print(f"[{serial_number}] ✓ 从 beijing_time.html 页面获取到时区: {timezone_info}")
                        else:
                            # 如果还是获取不到，再等待一下并重试
                            log_print(f"[{serial_number}] → 时区信息尚未准备好，等待 3 秒后重试...")
                            time.sleep(3)
                            
                            timezone_info = driver.execute_script("""
                                if (window.beijingTimePageInfo) {
                                    if (window.beijingTimePageInfo.ipTimezone) {
                                        return window.beijingTimePageInfo.ipTimezone;
                                    }
                                    if (window.beijingTimePageInfo.browserTimezone) {
                                        return window.beijingTimePageInfo.browserTimezone;
                                    }
                                }
                                return null;
                            """)
                            
                            if timezone_info:
                                BEIJING_TIME_PAGE_TIMEZONE[serial_number] = timezone_info
                                log_print(f"[{serial_number}] ✓ 从 beijing_time.html 页面获取到时区（重试成功）: {timezone_info}")
                            else:
                                # 最后尝试：即使 ready 为 false，也尝试获取浏览器时区
                                fallback_tz = driver.execute_script("""
                                    try {
                                        if (window.beijingTimePageInfo && window.beijingTimePageInfo.browserTimezone) {
                                            return window.beijingTimePageInfo.browserTimezone;
                                        }
                                        // 如果还是不行，直接从浏览器获取
                                        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
                                        return tz || null;
                                    } catch(e) {
                                        return null;
                                    }
                                """)
                                
                                if fallback_tz:
                                    BEIJING_TIME_PAGE_TIMEZONE[serial_number] = fallback_tz
                                    log_print(f"[{serial_number}] ✓ 使用备用方法获取到时区: {fallback_tz}")
                                else:
                                    log_print(f"[{serial_number}] ⚠ 无法从 beijing_time.html 页面获取时区，将使用IP查询方式")
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 获取页面时区信息失败: {str(e)}，将使用IP查询方式")
                        import traceback
                        log_print(f"[{serial_number}] 详细错误: {traceback.format_exc()}")
                    
                    # 切换回主窗口
                    driver.switch_to.window(main_window)
                else:
                    log_print(f"[{serial_number}] ⚠ 未找到 beijing_time.html 窗口，将使用IP查询方式")
                    driver.switch_to.window(main_window)
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 获取页面时区信息异常: {str(e)}，将使用IP查询方式")
                try:
                    driver.switch_to.window(main_window)
                except:
                    pass
        else:
            log_print(f"[{serial_number}] ⚠ 预打开 beijing_time.html 失败，继续执行...")
        # 确保切换回主窗口
        try:
            driver.switch_to.window(main_window)
        except:
            pass
        time.sleep(1)
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 预打开 beijing_time.html 异常: {str(e)}，继续执行...")
        try:
            driver.switch_to.window(main_window)
        except:
            pass
    
    okx_extension_id = "mcohilncbfahbmgdjkbpemcciiolgcge"
    okx_popup_url = f"chrome-extension://{okx_extension_id}/popup.html"
    okx_window = None
    
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
                    okx_window = window
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
                # 获取新打开的OKX窗口
                all_windows = driver.window_handles
                for window in all_windows:
                    if window != main_window:
                        try:
                            driver.switch_to.window(window)
                            if okx_extension_id in driver.current_url:
                                okx_window = window
                                break
                        except:
                            continue
            else:
                log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包失败，继续执行...")
                time.sleep(3)
        else:
            log_print(f"[{serial_number}] ✓ 使用现有的 OKX 钱包标签页")
        
        # 如果找到了OKX窗口，进行解锁和处理确认按钮
        if okx_window:
            try:
                # 切换到OKX窗口
                driver.switch_to.window(okx_window)
                log_print(f"[{serial_number}] → 切换到 OKX 钱包窗口进行解锁...")
                
                # 先解锁钱包
                unlock_okx_wallet(driver, serial_number, serial_number)
                
                # 在10秒内循环查找并点击确认按钮
                log_print(f"[{serial_number}] → 开始查找并处理确认按钮（10秒超时）...")
                start_time = time.time()
                buttons_clicked = 0
                
                while time.time() - start_time < 15:
                    try:
                        confirm_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        if confirm_buttons and len(confirm_buttons) > 0:
                            # 点击第一个按钮
                            confirm_buttons[0].click()
                            buttons_clicked += 1
                            log_print(f"[{serial_number}] ✓ 已点击第 {buttons_clicked} 个确认按钮")
                            time.sleep(0.5)  # 等待页面响应
                        else:
                            # 没有找到按钮，检查是否已经处理完毕
                            if buttons_clicked > 0:
                                log_print(f"[{serial_number}] ✓ 所有确认按钮已处理完毕，共点击 {buttons_clicked} 个")
                            else:
                                log_print(f"[{serial_number}] → 未找到确认按钮")
                            break
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 查找按钮时出错: {str(e)}")
                        time.sleep(0.5)
                
                if time.time() - start_time >= 10:
                    log_print(f"[{serial_number}] ⚠ 处理确认按钮超时（10秒），共点击 {buttons_clicked} 个")
                    
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 处理 OKX 钱包时出错: {str(e)}")
        
        # 切换回主窗口
        log_print(f"[{serial_number}] → 切换回主窗口")
        driver.switch_to.window(main_window)
        log_print(f"[{serial_number}] ✓ 已切换回主窗口")
        
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
            refresh_page_with_opinion_check(driver, serial_number)
            time.sleep(2)  # 刷新后等待2秒
        else:
            log_print(f"[{serial_number}] [OP] ✗ 页面加载失败，已达到最大重试次数 ({max_retries})")
            return None
    
    return None


def get_available_balance_from_tabs_content(tabs_content, browser_id):
    """
    从 tabs_content 中获取可用余额
    
    Args:
        tabs_content: tabs content div 元素
        browser_id: 浏览器编号
        
    Returns:
        str: 可用余额值，如果获取失败返回 None
    """
    try:
        log_print(f"[{browser_id}] 在 tabs_content 中查找可用余额...")
        
        # 1. 在 tabs_content 中找到内容为 "Balance" 的 P 标签
        p_tags = tabs_content.find_elements(By.TAG_NAME, "p")
        balance_p = None
        
        for p in p_tags:
            if p.text.strip() == "Balance":
                balance_p = p
                log_print(f"[{browser_id}] ✓ 找到内容为 'Balance' 的 P 标签")
                break
        
        if not balance_p:
            log_print(f"[{browser_id}] ⚠ 未找到内容为 'Balance' 的 P 标签")
            return None
        
        # 2. 找到该 P 标签的父节点
        parent = balance_p.find_element(By.XPATH, "..")
        log_print(f"[{browser_id}] ✓ 找到父节点")
        
        # 3. 找到父节点下的 div 子节点
        div_children = parent.find_elements(By.TAG_NAME, "div")
        if not div_children:
            log_print(f"[{browser_id}] ⚠ 父节点下未找到 div 子节点")
            return None
        
        # 使用第一个 div 子节点
        div_child = div_children[0]
        log_print(f"[{browser_id}] ✓ 找到 div 子节点")
        
        # 4. 获取 div 子节点下的 P 标签的内容
        p_in_div = div_child.find_elements(By.TAG_NAME, "p")
        if not p_in_div:
            log_print(f"[{browser_id}] ⚠ div 子节点下未找到 P 标签")
            return None
        
        available_balance = p_in_div[0].text.strip()
        if available_balance:
            log_print(f"[{browser_id}] ✓ 获取到可用余额: {available_balance}")
            return available_balance
        else:
            log_print(f"[{browser_id}] ⚠ 可用余额为空")
            return None
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取可用余额失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return None


def monitor_available_balance_change(driver, browser_id, initial_balance, trade_box, max_wait_time=180):
    """
    监控可用余额变化（在交易完成后）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器编号
        initial_balance: 初始可用余额
        trade_box: trade-box元素
        max_wait_time: 最大等待时间（秒），默认3分钟
        
    Returns:
        str: 最后的可用余额值
    """
    try:
        log_print(f"[{browser_id}] 开始监控可用余额变化（初始值: {initial_balance}，最大等待时间: {max_wait_time}秒）...")
        
        start_time = time.time()
        check_interval = 10  # 每10秒检查一次
        last_balance = initial_balance
        
        while time.time() - start_time < max_wait_time:
            try:
                # 重新获取 trade_box 和 tabs_content
                trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                if not trade_box_divs:
                    log_print(f"[{browser_id}] ⚠ 未找到 trade-box div，等待后重试...")
                    time.sleep(check_interval)
                    continue
                
                current_trade_box = trade_box_divs[0]
                
                # 点击 Buy 按钮以确保显示正确的 tabs_content
                if not click_opinion_trade_type_button(current_trade_box, "Buy", browser_id):
                    log_print(f"[{browser_id}] ⚠ 点击 Buy 按钮失败，等待后重试...")
                    time.sleep(check_interval)
                    continue
                
                # 重新获取 trade_box（点击后可能需要重新获取）
                trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                if not trade_box_divs:
                    log_print(f"[{browser_id}] ⚠ 未找到 trade-box div，等待后重试...")
                    time.sleep(check_interval)
                    continue
                
                current_trade_box = trade_box_divs[0]
                
                # 查找 tabs content div
                tabs_content_divs = current_trade_box.find_elements(By.CSS_SELECTOR, 
                    'div[data-scope="tabs"][data-part="content"][data-state="open"]')
                
                if not tabs_content_divs:
                    log_print(f"[{browser_id}] ⚠ 未找到 tabs content div，等待后重试...")
                    time.sleep(check_interval)
                    continue
                
                tabs_content = tabs_content_divs[0]
                
                # 获取当前可用余额
                current_balance = get_available_balance_from_tabs_content(tabs_content, browser_id)
                
                if current_balance is None:
                    log_print(f"[{browser_id}] ⚠ 无法获取当前可用余额，等待后重试...")
                    time.sleep(check_interval)
                    continue
                
                elapsed = int(time.time() - start_time)
                log_print(f"[{browser_id}] [{elapsed}s] 当前可用余额: {current_balance} (初始值: {initial_balance})")
                
                # 检查余额是否变化
                if current_balance != initial_balance:
                    log_print(f"[{browser_id}] ✓✓✓ 可用余额已变化！初始值: {initial_balance} -> 当前值: {current_balance}")
                    return current_balance
                
                last_balance = current_balance
                time.sleep(check_interval)
                
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 监控余额时发生异常: {str(e)}")
                time.sleep(check_interval)
                continue
        
        # 3分钟无变化，返回最后的可用余额
        elapsed = int(time.time() - start_time)
        log_print(f"[{browser_id}] ⚠ 3分钟内余额未变化，返回最后的可用余额: {last_balance} (已用时: {elapsed}秒)")
        return last_balance
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 监控可用余额变化失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return last_balance if 'last_balance' in locals() else initial_balance


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
                    log_print(f"[{serial_number}] [OP] {button.text.strip() }")
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


def get_closed_orders_latest_time(driver, serial_number):
    """
    获取 Closed Orders 的最新时间
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: 最新时间字符串，失败返回空字符串
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找并点击 'Closed Orders' 按钮...")
        
        # 查找并点击 Closed Orders 按钮
        closed_orders_clicked = False
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.text.strip() == "Closed Orders":
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 'Closed Orders' 按钮")
                        closed_orders_clicked = True
                        break
                if closed_orders_clicked:
                    break
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not closed_orders_clicked:
            log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到 'Closed Orders' 按钮")
            return ""
        
        time.sleep(3)  # 等待页面加载
        
        # 查找 id 包含 "closedOrders" 的 div
        log_print(f"[{serial_number}] [OP] 查找 id 包含 'closedOrders' 的 div...")
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        
        target_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'closedorders' in div_id.lower():
                target_div = div
                log_print(f"[{serial_number}] [OP] 找到目标 div，id: {div_id}")
                break
        
        if not target_div:
            log_print(f"[{serial_number}] [OP] ⚠ 未找到包含 'closedOrders' 的 div")
            return ""
        
        # 找到这个div下的第一个tr元素
        try:
            table = target_div.find_element(By.TAG_NAME, 'table')
            tbody = table.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            
            if not tr_list or len(tr_list) == 0:
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 tr 元素")
                return ""
            
            first_tr = tr_list[0]
            
            # 找到这个tr元素下的最后一个td下的p标签内容
            tds = first_tr.find_elements(By.TAG_NAME, "td")
            if len(tds) == 0:
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 td 元素")
                return ""
            
            last_td = tds[-1]  # 最后一个td
            p_tags = last_td.find_elements(By.TAG_NAME, "p")
            
            if not p_tags or len(p_tags) == 0:
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 p 标签")
                return ""
            
            latest_time = p_tags[0].text.strip()
            log_print(f"[{serial_number}] [OP] ✓ 获取到 Closed Orders 最新时间: {latest_time}")
            return latest_time
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Closed Orders 时间失败: {str(e)}")
            return ""
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ⚠ 获取 Closed Orders 最新时间失败: {str(e)}")
        return ""


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
            if div_id and 'openorders' in div_id.lower():
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
                            break
                except:
                    continue
            
            log_print(f"[{serial_number}] [OP] 有子标题情况下，匹配的tr数量: {matched_count}")
            return matched_count
        
        return count
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ⚠ 获取 table 行数失败: {str(e)}")
        return -1


def submit_opinion_order(driver, trade_box, trade_type, option_type, serial_number, browser_id, task_data=None, bro_log_list=None, trendingId=''):
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
        bro_log_list: 日志列表（用于记录日志）
        trendingId: 交易主题ID（用于更新时间戳）
        
    Returns:
        tuple: (success, should_retry_or_msg)
            - (True, True): 成功
            - (False, True): 失败，可以重试
            - (False, False): 失败，不应重试（如type=5点击取消）
            - (False, "msg"): 失败，不应重试，并带有具体失败原因
    """
    # 初始化日志列表（如果未提供）
    if bro_log_list is None:
        bro_log_list = []
    
    try:
        log_msg = f"[8] 查找提交订单按钮..."
        log_print(f"[{serial_number}] {log_msg}")
        add_bro_log_entry(bro_log_list, browser_id, log_msg)
        
     
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            text = p.text.strip()
            if trade_type in text:
                
                # 在3秒内检查是否有"Insufficient balance"提示
                log_msg = f"[8] 检查余额提示..."
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                start_time_balance = time.time()
                insufficient_balance_found = False
                
                while time.time() - start_time_balance < 3:
                    try:
                        # 使用XPath直接查找包含"Insufficient balance"文本的div元素（包括子元素文本）
                        elements = driver.find_elements(By.XPATH, "//div[contains(., 'Insufficient balance')]")
                        if elements:
                            insufficient_balance_found = True
                            div_text = elements[0].text.strip()
                            log_msg = f"[8] ✗ 检测到余额不足提示: {div_text}"
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                            break
                        time.sleep(0.2)  # 短暂等待后重试
                    except Exception as e:
                        # 查找过程中出现异常，继续尝试
                        time.sleep(0.2)
                        continue
                
                if insufficient_balance_found:
                    log_msg = f"[8] ✗ 余额不足"
                    log_print(f"[{serial_number}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    return False, "[8]余额不足"
                
                
                
                log_msg = f"[8] ✓ 找到提交按钮，文本: {text}"
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                parent = p.find_element(By.XPATH, "..")
                parent.click()
                log_msg = f"[8] ✓ 已点击提交订单按钮"
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                # 在3秒内检查是否有"Unusual Limit Price"提示
                log_msg = f"[8] 检查限价提示..."
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                start_time = time.time()
                unusual_limit_found = False
                
                while time.time() - start_time < 3:
                    try:
                        # 使用XPath直接查找包含"Unusual Limit Price"文本的h2元素（包括子元素文本）
                        h2_tags = driver.find_elements(By.XPATH, "//h2[contains(., 'Unusual Limit Price')]")
                        if h2_tags:
                            unusual_limit_found = True
                            h2_text = h2_tags[0].text.strip()
                            log_msg = f"[8] ✗ 检测到限价提示: {h2_text}"
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                            break
                        time.sleep(0.2)  # 短暂等待后重试
                    except Exception as e:
                        # 查找过程中出现异常，继续尝试
                        time.sleep(0.2)
                        continue
                
                if unusual_limit_found:
                    log_msg = f"[8] ✗ 限价距离市价差距过大"
                    log_print(f"[{serial_number}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    return False, "[7]限价距离市价差距过大"
                
                log_msg = f"[8] ✓ 未检测到限价提示，继续执行..."
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                

                
                log_msg = f"[8] ✓ 未检测到余额不足提示，继续执行..."
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                # 检查是否需要点击 Confirm 按钮
                log_msg = f"[8] 检查是否需要点击 Confirm 按钮..."
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                confirm_clicked = False
                start_time_confirm = time.time()
                
                while time.time() - start_time_confirm < 4:
                    try:
                        # 使用XPath直接查找包含"Securely trade on opinion.trade on"文本的元素
                        secure_elements = driver.find_elements(By.XPATH, 
                            "//*[self::h2 or self::div or self::p][contains(., 'Securely trade on opinion.trade on')]")
                        
                        if secure_elements:
                            log_msg = f"[OP8] ✓ 检测到安全交易提示"
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                            
                            # 使用XPath直接查找文本为"Confirm"的button
                            confirm_buttons = driver.find_elements(By.XPATH, "//button[normalize-space(.)='Confirm']")
                            if confirm_buttons:
                                log_msg = f"[8] ✓ 找到 Confirm 按钮，点击..."
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                confirm_buttons[0].click()
                                confirm_clicked = True
                                log_msg = f"[8] ✓ 已点击 Confirm 按钮"
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                break
                        
                        time.sleep(0.2)
                    except Exception as e:
                        log_msg = f"[8] ⚠ 检查 Confirm 按钮时出现异常: {str(e)}"
                        log_print(f"[{serial_number}] {log_msg}")
                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        time.sleep(0.2)
                        continue
                
                if not confirm_clicked:
                    log_msg = f"[8] ✓ 未检测到需要点击 Confirm 的情况"
                    log_print(f"[{serial_number}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                # 切换到OKX页面
                log_msg = f"[9] 切换到 OKX 钱包页面..."
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                all_windows = driver.window_handles
                
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                        log_msg = f"[9] ✓ 已切换到 OKX 页面"
                        log_print(f"[{serial_number}] {log_msg}")
                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        # 解锁
                        # unlock_okx_wallet(driver, serial_number, browser_id)
                        
                        # 如果之前点击了 Confirm，需要先点击两次第二个按钮（带检查逻辑）
                        if confirm_clicked:
                            log_msg = f"[9] 检测到已点击 Confirm，执行特殊按钮点击逻辑..."
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                            click_count = 0
                            max_clicks = 2
                            start_time_okx = time.time()
                            
                            while click_count < max_clicks and time.time() - start_time_okx < 10:
                                try:
                                    buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                                    
                                    if len(buttons) >= 2:
                                        # 检查是否需要跳过点击
                                        should_skip = False
                                        try:
                                            # 查找内容为 "primaryType" 的 div
                                            all_divs = driver.find_elements(By.TAG_NAME, "div")
                                            primary_type_div = None
                                            for div in all_divs:
                                                if div.text.strip() == "primaryType":
                                                    primary_type_div = div
                                                    break
                                            
                                            if primary_type_div:
                                                # 找到父节点
                                                parent = primary_type_div.find_element(By.XPATH, "..")
                                                # 找到父节点下的所有子 div
                                                child_divs = parent.find_elements(By.TAG_NAME, "div")
                                                
                                                if len(child_divs) >= 2:
                                                    second_child = child_divs[1]
                                                    if second_child.text.strip() == "Order":
                                                        should_skip = True
                                                        log_msg = f"[9] ✓ 检测到 Order，跳过点击"
                                                        log_print(f"[{serial_number}] {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        except Exception as e:
                                            log_msg = f"[9] ⚠ 检查 Order 时出现异常: {str(e)}，继续点击"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        
                                        if not should_skip:
                                            confirm_button = buttons[1]
                                            log_msg = f"[9] 点击第 {click_count + 1} 次第二个按钮..."
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            confirm_button.click()
                                            click_count += 1
                                            log_msg = f"[9] ✓ 已点击第 {click_count} 次"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        
                                        # 等待1秒后继续
                                        time.sleep(1)
                                    else:
                                        time.sleep(0.5)
                                except Exception as e:
                                    log_msg = f"[9] ⚠ 点击按钮时出现异常: {str(e)}"
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    time.sleep(0.5)
                                    continue
                            
                            log_msg = f"[9] ✓ 特殊按钮点击逻辑完成，共点击 {click_count} 次"
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        
                        # 点击确认按钮
                        log_msg = f"[9] 查找确认按钮..."
                        log_print(f"[{serial_number}] {log_msg}")
                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        
                        if len(buttons) >= 2:
                            # 检查第二个按钮（确认按钮）是否被禁用
                            confirm_button = buttons[1]
                            button_class = confirm_button.get_attribute("class") or ""
                            if "btn-disabled" in button_class:
                                log_msg = f"[9] ✗ OKX确认按钮被禁用，class: {button_class}"
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                
                                # message_text = f"电脑组{COMPUTER_GROUP}浏览器编号{browser_id} okx按钮被禁用，请复核"
                                # send_feishu_custom_message(browser_id, message_text)
                                # # 停留30秒
                                # log_print(f"[{serial_number}] 停留30秒等待人工检查...")
                                time.sleep(3)
                                # log_print(f"[{serial_number}] 发送飞书消息: {message_text}")
                           
                                buttons[0].click()  # 点击取消按钮
                                return False, "[9]okx确认交易按钮不能点击,检查okx是否正常"
                            
                            # Type 5 任务需要同步机制
                            mission = task_data.get('mission', {}) if task_data else {}
                            mission_type = mission.get('type')
                            log_msg = f"[9] 检测到任务类型: {mission_type}"
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                            
                            if task_data and mission_type == 5 :
                                log_msg = f"[9] Type 5 任务，启动同步机制..."
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                
                                mission_id = mission.get('id')
                                tp1 = mission.get('tp1')  # 任务一的ID
                                
                                if not tp1:
                                    # 任务一：先检查自己的状态，如果是3则直接取消
                                    log_msg = f"[9] 任务一: 检查自己的状态..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    current_status = get_mission_status(mission_id)
                                    if current_status == 3:
                                        log_msg = f"[9] ✗ 本任务正常，但任务二已失败"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        buttons[0].click()  # 点击取消按钮
                                        return False, "[9]本任务正常，但任务二已失败"
                                    
                                    # 任务一：设置自己状态为5（准备就绪），等待任务二通过tp9通知准备就绪
                                    log_msg = f"[9] 任务一: 设置状态为5（准备就绪）..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    save_result_success = save_mission_result(mission_id, 5)
                                    if not save_result_success:
                                        save_result_success = save_mission_result(mission_id, 5)
                                        if not save_result_success:
                                            log_msg = f"[9] ✗ 任务一设置状态5失败"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            return False, True  # 失败，可重试
                                    
                                    log_msg = f"[9] 任务一: 等待任务二准备就绪（tp9=6）..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    # 轮询等待tp9变为6（任务二通过tp9通知准备就绪）
                                    max_wait_time = 600  # 最多等待10分钟
                                    start_time = time.time()
                                    while True:
                                        if time.time() - start_time > max_wait_time:
                                            log_msg = f"[9] ✗ 本任务等待任务二超时，点击取消按钮"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            buttons[0].click()  # 点击取消按钮
                                            return False, "[9]本任务等待任务二超时"
                                        
                                        tp9_value = get_mission_tp9(mission_id)
                                        current_status = get_mission_status(mission_id)
                                        log_msg = f"[9] 任务一: 当前状态={current_status}, tp9={tp9_value}"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        
                                        if tp9_value == 6:
                                            log_msg = f"[9] ✓ 任务二已准备就绪（tp9=6）"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            break
                                        elif tp9_value == 3:
                                            log_msg = f"[9] 本任务正常，但任务二已失败"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            buttons[0].click()  # 点击取消按钮
                                            return False, "[9]本任务正常，但任务二已失败"
                                        elif current_status == 9:
                                            save_mission_result(mission_id, 5)
                                        time.sleep(10)
                                    
                                    # 在点击确认按钮之前，先调用 updateTrendingTime 接口
                                    log_msg = f"[10] 任务一: 开始轮询调用 updateTrendingTime 接口..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    
                                    update_trending_time_success = False
                                    update_trending_start_time = time.time()
                                    update_trending_timeout = 300  # 5分钟超时
                                    update_trending_interval = 20  # 每20秒请求一次
                                    first_request = True  # 标记是否为第一次请求
                                    
                                    while time.time() - update_trending_start_time < update_trending_timeout:
                                        try:
                                            # 如果不是第一次请求，等待20秒
                                            if not first_request:
                                                log_msg = f"[10] 任务一: 等待{update_trending_interval}秒后重试..."
                                                log_print(f"[{serial_number}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                time.sleep(update_trending_interval)
                                            first_request = False
                                            
                                            # 获取当前时间戳（毫秒）
                                            current_update_time = int(time.time() * 1000)
                                            
                                            # 构建请求
                                            update_trending_url = f"{SERVER_BASE_URL}/hedge/updateTrendingTime"
                                            update_trending_payload = {
                                                "trendingId": trendingId,
                                                "updateTime": current_update_time
                                            }
                                            
                                            log_msg = f"[10] 任务一: 调用 updateTrendingTime, trendingId={trendingId}, updateTime={current_update_time}"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            
                                            update_trending_response = requests.post(
                                                update_trending_url, 
                                                json=update_trending_payload, 
                                                timeout=20
                                            )
                                            
                                            if update_trending_response.status_code == 200:
                                                update_trending_result = update_trending_response.json()
                                                log_msg = f"[9] 任务一: updateTrendingTime 响应: {update_trending_result}"
                                                log_print(f"[{serial_number}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                
                                                if update_trending_result.get('code') == 0:
                                                    data = update_trending_result.get('data', {})
                                                    change_succ = data.get('changeSucc', 0)
                                                    update_time = data.get('updateTime', 0)
                                                    
                                                    if change_succ == 1:
                                                        log_msg = f"[9] ✓ 任务一: updateTrendingTime 成功，changeSucc=1"
                                                        log_print(f"[{serial_number}] {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                        update_trending_time_success = True
                                                        break
                                                    else:
                                                        log_msg = f"[9] 任务一: changeSucc={change_succ} update_time={update_time}，继续等待..."
                                                        log_print(f"[{serial_number}] {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                else:
                                                    log_msg = f"[9] ⚠ 任务一: updateTrendingTime 返回错误, code={update_trending_result.get('code')}"
                                                    log_print(f"[{serial_number}] {log_msg}")
                                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            else:
                                                log_msg = f"[9] ⚠ 任务一: updateTrendingTime HTTP错误: {update_trending_response.status_code}"
                                                log_print(f"[{serial_number}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                
                                        except Exception as update_trending_error:
                                            log_msg = f"[9] ⚠ 任务一: updateTrendingTime 请求异常: {str(update_trending_error)}"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    
                                    # 检查是否超时
                                    if not update_trending_time_success:
                                        log_msg = f"[9] ✗ 任务一: updateTrendingTime 5分钟超时，点击取消按钮"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        buttons[0].click()  # 点击取消按钮
                                        return False, "[9]插入事件时间超时"
                                    
                                    # 点击确认按钮
                                    log_msg = f"[11] 任务一: 点击OKX确认按钮..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    buttons[1].click()
                                    log_msg = f"[11] ✓ 任务一已点击 OKX 确认按钮"
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    update_browser_timestamp_q(browser_id, trendingId)
                                    # 更改状态为7（任务一已确认）
                                    log_msg = f"[11] 任务一: 设置状态为7（已确认）..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    save_result_success = save_mission_result(mission_id, 7)
                                    if not save_result_success:
                                        time.sleep(2)
                                        save_result_success = save_mission_result(mission_id, 7)
                                        if not save_result_success:
                                            time.sleep(5)
                                            save_result_success = save_mission_result(mission_id, 7)
                                            if not save_result_success:
                                                log_msg = f"[9] 连续10次设置任务状态失败，但已点击确认，请检查网络"
                                                send_feishu_custom_message(browser_id, log_msg)
                                                log_print(f"[{serial_number}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                
                                    # 轮询检查任务1状态，确保状态保持为7
                                    log_msg = f"[11] 任务一: 等待20秒后开始轮询检查状态..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    time.sleep(5)  # 先等待20秒
                                    
                                    max_poll_time = 30  # 1分钟内
                                    poll_interval = 10  # 每20秒执行一次
                                    start_poll_time = time.time()
                                    poll_count = 0
                                    
                                    while time.time() - start_poll_time < max_poll_time:
                                        poll_count += 1
                                        status = get_mission_status(mission_id)
                                        log_msg = f"[9] 任务一: 第{poll_count}次轮询，当前状态: {status}"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        
                                        if status == 7:
                                            log_msg = f"[9] ✓ 任务一状态为7，退出轮询"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            break
                                        elif status == 6 or status == 5:
                                            log_msg = f"[9] 任务一状态变为{status}，重新设置为7..."
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            save_result_success = save_mission_result(mission_id, 7)
                                            if not save_result_success:
                                                time.sleep(2)
                                                save_result_success = save_mission_result(mission_id, 7)
                                            if save_result_success:
                                                log_msg = f"[9] ✓ 任务一状态已重新设置为7"
                                                log_print(f"[{serial_number}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            
                                            # 等待下一次20秒轮询
                                            time.sleep(poll_interval)
                                            
                                            # 再次检查状态
                                            status = get_mission_status(mission_id)
                                            log_msg = f"[9] 任务一: 重新设置后检查状态: {status}"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            
                                            if status == 7:
                                                log_msg = f"[9] ✓ 任务一状态为7，退出轮询"
                                                log_print(f"[{serial_number}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                break
                                        else:
                                            # 其他状态，继续等待
                                            time.sleep(poll_interval)
                                    
                                    if time.time() - start_poll_time >= max_poll_time:
                                        log_msg = f"[11] 任务一: 轮询超时（1分钟），退出轮询"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    
                                    log_msg = f"[11] ✓ 任务一提交订单成功"
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    return True, True  # 成功
                                    
                                else:
                                    # 任务二：等待任务一准备就绪（status=5），然后通过tp9通知任务一
                                    log_msg = f"[9] 任务二: 等待任务一准备就绪（状态5）..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    # 轮询等待任务一状态为5
                                    max_wait_time = 600  # 最多等待10分钟
                                    start_time = time.time()
                                    while True:
                                        if time.time() - start_time > max_wait_time:
                                            log_msg = f"[9] ✗ 本任务正常，等待任务一超时"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            buttons[0].click() 
                                            return False, "[9]本任务正常，等待任务一超时"
                                        
                                        tp1_status = get_mission_status(tp1)
                                        if tp1_status == 5:
                                            log_msg = f"[9] ✓ 任务一已准备就绪（状态5）"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            break
                                        elif tp1_status == 3:
                                            log_msg = f"[9] ✗ 本任务正常，任务一已失败"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            buttons[0].click() 
                                            return False, "[9]本任务正常，任务一已失败"
                                        
                                        
                                    if mission_type != 9:
                                        # 任务二：设置任务一的tp9为6（通知任务一：任务二准备就绪）
                                        log_msg = f"[9] 任务二: 设置任务一tp9=6（任务二就绪）..."
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        tp_update_success = update_mission_tp(tp1, tp9=6)
                                        if not tp_update_success:
                                            time.sleep(2)
                                            tp_update_success = update_mission_tp(tp1, tp9=6)
                                            if not tp_update_success:
                                                time.sleep(5)
                                                tp_update_success = update_mission_tp(tp1, tp9=6)
                                                if not tp_update_success:
                                                    log_msg = f"[9] ✗ 连续3次设置tp9失败"
                                                    log_print(f"[{serial_number}] {log_msg}")
                                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                                    log_msg = f"[9] [{serial_number}] 连续3次设置tp9失败，请检查网络"
                                                    send_feishu_custom_message(browser_id, log_msg)
                                                    return False, True  # 失败，可重试
                                    

                                    tp11 = mission.get('tp11')
                                    if tp11:
                                        task_sync_polling_interval = int(tp11)
                                    else:
                                        task_sync_polling_interval = 5
                                    # 等待任务一点击确认（状态7）
                                    log_msg = f"[9] 任务二: 等待任务一点击确认（状态7）..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    start_time = time.time()
                                    while True:
                                        if time.time() - start_time > max_wait_time:
                                            log_msg = f"[9] ✗ 本任务正常，等待任务一确认超时"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            buttons[0].click()  # 点击取消按钮
                                            return False, "[9]本任务正常，等待任务一确认超时"
                                        
                                        tp1_status = get_mission_status(tp1)
                                        if tp1_status == 7 or tp1_status == 2 or tp1_status == 8 or tp1_status == 12:
                                            log_msg = f"[9] ✓ 任务一已点击确认（状态{tp1_status}）"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            break
                                        elif tp1_status == 3:
                                            log_msg = f"[9] 本任务正常，任务一确认失败，点击取消"
                                            log_print(f"[{serial_number}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                            buttons[0].click()  # 点击取消按钮
                                            return False, "[9]本任务正常，任务一确认失败"
                                        
                                        time.sleep(task_sync_polling_interval)
                                    

                                    # 点击确认按钮
                                    log_msg = f"[11] 任务二: 点击OKX确认按钮..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    buttons[1].click()
                                    log_msg = f"[11] ✓ 任务二已点击 OKX 确认按钮"
                                    update_browser_timestamp_q(browser_id, trendingId)
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    
                                    # 任务二：设置任务一的tp9为7（通知任务一：任务二已确认）
                                    log_msg = f"[11] 任务二: 设置任务一tp9=7（任务二已确认）..."
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    update_mission_tp(tp1, tp9=7)
                                    
                                    log_msg = f"[11] ✓ 任务二提交订单成功"
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    return True, True  # 成功
                            
                            elif  mission_type == 6 or mission_type == 9:
                                mission_id = mission.get('id')
                                
                                # 先将自己的状态改为 20
                                log_msg = f"[9] Type 6/9 任务: 设置状态为20..."
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                save_result_success = save_mission_result(mission_id, 20)
                                
                                
                                # 在10分钟内，每隔5秒请求一次自己的状态
                                max_wait_time = 300  # 5分钟
                                polling_interval = 5  # 每隔5秒
                                start_time = time.time()
                                
                                while True:
                                    # 检查是否超时
                                    if time.time() - start_time > max_wait_time:
                                        log_msg = f"[9] ✗ Type 6/9 任务等待超时（10分钟）"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        buttons[0].click()
                                        return False, "[9]等待超时或已被通知失败，取消点击确认按钮"
                                    
                                    # 请求自己的状态
                                    current_status = get_mission_status(mission_id)
                                    log_msg = f"[9] Type 6/9 任务: 当前状态={current_status}"
                                    log_print(f"[{serial_number}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                    
                                    if current_status == 9 or current_status == 0 or current_status == 21:
                                        # 如果状态为 9 或 0，改状态为 20
                                        log_msg = f"[9] Type 6/9 任务: 状态为{current_status}，重新设置为20..."
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        save_mission_result(mission_id, 20)
                                    elif current_status == 31:
                                        # 如果状态为 31 buttons[1].click()，返回 True
                                        log_msg = f"[9] ✓ Type 6/9 任务: 状态为21，点击确认按钮"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        buttons[1].click()
                                        log_msg = f"[11] ✓ Type 6/9 任务已点击 OKX 确认按钮"
                                        update_browser_timestamp_q(browser_id, trendingId)
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        log_msg = f"[11] ✓ Type 6/9 任务提交订单成功"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        return True, True  # 成功
                                    elif current_status == 3:
                                        # 如果状态为 3，执行 buttons[2].click()，返回 False
                                        log_msg = f"[9] ✗ Type 6/9 任务: 状态为3（已被通知失败）"
                                        log_print(f"[{serial_number}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                        buttons[0].click()
                                        return False, "[9]等待超时或已被通知失败，没有点击确认按钮"
                                    
                                    # 等待下一次轮询
                                    time.sleep(polling_interval)
                            else:
                                # 普通任务（Type 1），直接点击确认
                                buttons[1].click()
                                log_msg = f"[11] ✓ 已点击 OKX 确认按钮"
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                log_msg = f"[11] ✓ 提交订单成功"
                                log_print(f"[{serial_number}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                                return True, True  # 成功
                        else:
                            log_msg = f"[9] ⚠ OKX 按钮数量不足: {len(buttons)}"
                            log_print(f"[{serial_number}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                            return False, True  # 失败，可重试
                
                log_msg = f"[9] ⚠ 未找到 OKX 页面"
                log_print(f"[{serial_number}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                return False, True  # 失败，可重试
        
        log_msg = f"[9] ✗ 未找到提交订单按钮"
        log_print(f"[{serial_number}] {log_msg}")
        add_bro_log_entry(bro_log_list, browser_id, log_msg)
        return False, True  # 失败，可重试
        
    except Exception as e:
        log_msg = f"[9] ✗ 提交订单失败: {str(e)}"
        log_print(f"[{serial_number}] {log_msg}")
        add_bro_log_entry(bro_log_list, browser_id, log_msg)
        import traceback
        error_detail = traceback.format_exc()
        log_print(f"[{serial_number}] 错误详情:\n{error_detail}")
        add_bro_log_entry(bro_log_list, browser_id, f"错误详情: {error_detail[:500]}")
        return False, True  # 失败，可重试


def check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type="Buy"):
    """
    检查 Transactions 中的交易费和成交价格，判断任务是否真正成功
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        task_label: 任务标签（任务一/任务二）
        is_task1: 是否是任务一
        trade_type: 买卖方向（"Buy" 或 "Sell"）
        
    Returns:
        tuple: (transaction_fee, filled_price, success)
            - transaction_fee: 交易费字符串（例如 "$0.5" 或 "-"）
            - filled_price: 成交价格字符串（例如 "14.0" 或 "-"）
            - success: 检查是否成功（任务一：交易费为0或空为成功；任务二：交易费>0为成功）
    """
    max_retry = 6 # 最多重试3次
    
    for retry_count in range(max_retry):
        try:
            if retry_count > 0:
                log_print(f"[{serial_number}] [{task_label}] 第 {retry_count + 1}/{max_retry} 次尝试检查 Transactions...")
            time.sleep(60)
            # 先刷新页面
            log_print(f"[{serial_number}] [{task_label}] 刷新页面...")
            refresh_page_with_opinion_check(driver, serial_number)
            time.sleep(2)
            log_print(f"[{serial_number}] [{task_label}] ✓ 页面已刷新")
            
            # 等待 Transactions 按钮出现（超时30秒）
            log_print(f"[{serial_number}] [{task_label}] 等待 Transactions 按钮出现（超时30秒）...")
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            need_retry = False
            try:
                # 使用显式等待查找 Transactions 按钮
                transactions_button = WebDriverWait(driver, 60).until(
                    lambda d: next(
                        (btn for btn in d.find_elements(By.TAG_NAME, "button") 
                         if btn.text.strip() == "Transactions"),
                        None
                    )
                )
                
                if transactions_button:
                    log_print(f"[{serial_number}] [{task_label}] ✓ Transactions 按钮已出现")
                else:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 等待超时，未找到 Transactions 按钮")
                    need_retry = True
                    
            except Exception as wait_error:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 等待 Transactions 按钮超时: {str(wait_error)}")
                need_retry = True
            
            # 如果需要重试
            if need_retry:
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(10)
                    continue  # 继续下一次重试
                else:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 已达到最大重试次数")
                    return "-", "-", is_task1  # 任务一找不到按钮算成功，任务二算失败
            
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
            
            time.sleep(3)
            if not transactions_button_found:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到 Transactions 按钮")
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue
                else:
                    return "-", "-", is_task1  # 任务一找不到按钮算成功，任务二算失败
            
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
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue
                else:
                    return "-", "-", is_task1  # 任务一找不到div算成功，任务二算失败
            
            # 获取 tbody 和第一个 tr
            tbody = transactions_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            
            if not tr_list or len(tr_list) == 0:
                log_print(f"[{serial_number}] [{task_label}] ⚠ Transactions 中没有 tr")
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue
                else:
                    return "-", "-", is_task1  # 任务一没有tr算成功，任务二算失败
            
            # 获取第一个 tr
            first_tr = tr_list[0]
            tds = first_tr.find_elements(By.TAG_NAME, "td")
            
            if len(tds) < 6:
                log_print(f"[{serial_number}] [{task_label}] ⚠ Transactions 第一个 tr 的 td 数量不足6个（实际: {len(tds)}）")
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue
                else:
                    return "-", "-", is_task1
            
            # 检查第一个 td 的 p 标签内容是否与买卖方向一致
            td1 = tds[0]
            td1_ps = td1.find_elements(By.TAG_NAME, "p")
            td1_text = td1_ps[0].text.strip() if td1_ps else ""
            log_print(f"[{serial_number}] [{task_label}] 第一个 td 内容: {td1_text}, 期望买卖方向: {trade_type}")
            
            if trade_type not in td1_text:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 买卖方向不一致（期望: {trade_type}, 实际: {td1_text}）")
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue  # 继续下一次重试
                else:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 已达到最大重试次数，买卖方向仍不一致")
                    return "-", "-", is_task1
            
            log_print(f"[{serial_number}] [{task_label}] ✓ 买卖方向一致")
            
            # 第5个td（index=4）- 获取 filled_price
            td5 = tds[4]
            td5_ps = td5.find_elements(By.TAG_NAME, "p")
            filled_price_text = td5_ps[0].text.strip() if td5_ps else "-"
            
            log_print(f"[{serial_number}] [{task_label}] Transactions 成交价格: {filled_price_text}")
            
            # 解析 filled_price 数字（格式如 "14.0¢"）
            filled_price_value = "-"
            try:
                # 移除 ¢ 符号和其他非数字字符，只保留数字和小数点
                import re
                price_number_str = re.sub(r'[^\d.]', '', filled_price_text)
                if price_number_str and price_number_str != '':
                    filled_price_value = price_number_str
                else:
                    # 解析结果为空，需要重试
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 解析成交价格为空，原始文本: {filled_price_text}")
                    if retry_count < max_retry - 1:
                        log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                        time.sleep(2)
                        continue
                log_print(f"[{serial_number}] [{task_label}] 解析后的成交价格: {filled_price_value}")
            except Exception as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 解析成交价格失败: {str(e)}，原始文本: {filled_price_text}")
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue
                filled_price_value = "-"
            
            # 第6个td（index=5）- 获取交易费
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
                if retry_count < max_retry - 1:
                    log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                    time.sleep(2)
                    continue
                fee_value = 0.0
            
            # 判断逻辑
            if is_task1:
                # 任务一：交易费为0、空、"-" 或无法解析数字 → 成功；反之失败
                if transaction_fee_text == "-" or transaction_fee_text == "" or fee_value == 0:
                    log_print(f"[{serial_number}] [{task_label}] ✓ 任务一：交易费为0或空，检查通过")
                    return transaction_fee_text, filled_price_value, True
                else:
                    log_print(f"[{serial_number}] [{task_label}] ✗ 任务一：交易费不为0（{fee_value}），检查失败")
                    return transaction_fee_text, filled_price_value, False
            else:
                # 任务二：交易费有值且大于0 → 成功；反之失败
                if transaction_fee_text != "-" and transaction_fee_text != "" and fee_value > 0:
                    log_print(f"[{serial_number}] [{task_label}] ✓ 任务二：交易费大于0（{fee_value}），检查通过")
                    return transaction_fee_text, filled_price_value, True
                else:
                    log_print(f"[{serial_number}] [{task_label}] ✗ 任务二：交易费为0或空，检查失败")
                    return transaction_fee_text, filled_price_value, False
            
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ✗ 检查 Transactions 失败: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] [{task_label}] 错误详情:\n{traceback.format_exc()}")
            
            if retry_count < max_retry - 1:
                log_print(f"[{serial_number}] [{task_label}] → 准备重试...")
                time.sleep(2)
                continue
            else:
                return "-", "-", is_task1  # 异常时，任务一算成功，任务二算失败
    
    # 如果所有重试都失败
    return "-", "-", is_task1


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
        position_buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in position_buttons:
            if btn.text.strip() == "Position":
                btn.click()
                time.sleep(7)
                break
        
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        position_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'content-position' in div_id.lower():
                position_div = div
                break
        
        if not position_div:
            log_print(f"[{serial_number}] ] ⚠ 未找到Position div")
            return ""
        # 查找tbody
        tbody = position_div.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        if not tr_list or len(tr_list) == 0:
            log_print(f"[{serial_number}] ⚠ 没有Position数据")
            return ""
        
        time.sleep(3)
        
        filled_amount = ""
        filled_price = ""
        
        if trending_part1:
            # 有子标题：找到包含子标题的tr
            log_print(f"[{serial_number}] ] 有子标题，查找包含 '{trending_part1}' 的行...")
            for tr in tr_list:
                try:
                    # 获取第一个td的div下的p标签
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) > 0:
                        first_td_ps = tds[0].find_elements(By.TAG_NAME, "p")
                        first_td_text = " ".join([p.text.strip() for p in first_td_ps])
                        if trending_part1 in first_td_text:
                            log_print(f"[{serial_number}] [] ✓ 找到包含子标题的行")
                            # 【DEBUG】打印所有td的详细内容
                            log_print(f"[{serial_number}] [] === 开始打印该tr下所有td的详细内容 ===")
                            for td_idx, td in enumerate(tds):
                                # 方法1：直接获取td.text
                                td_text = td.text.strip()
                                # 方法2：查找p标签
                                td_ps = td.find_elements(By.TAG_NAME, "p")
                                td_p_texts = [p.text.strip() for p in td_ps]
                                # 方法3：查找div标签
                                td_divs = td.find_elements(By.TAG_NAME, "div")
                                # 方法4：获取innerHTML
                       
                                log_print(f"[{serial_number}] [] TD[{td_idx}]:")
                                log_print(f"[{serial_number}] []   - td.text: '{td_text}'")
                                log_print(f"[{serial_number}] []   - p标签: {td_p_texts}")
                                log_print(f"[{serial_number}] []   - div数量: {len(td_divs)}")
              
                            log_print(f"[{serial_number}] [] === 打印完毕 ===")
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
                    log_print(f"[{serial_number}] [] ⚠ 解析Position行失败: {str(e)}")
                    continue
        else:
            # 无子标题：第一个tr
            log_print(f"[{serial_number}] [] 无子标题，获取第一行数据...")
            try:
                first_tr = tr_list[0]
                tds = first_tr.find_elements(By.TAG_NAME, "td")
                # 【DEBUG】打印所有td的详细内容
                log_print(f"[{serial_number}] [] === 开始打印该tr下所有td的详细内容 ===")
                for td_idx, td in enumerate(tds):
                    # 方法1：直接获取td.text
                    td_text = td.text.strip()
                    # 方法2：查找p标签
                    td_ps = td.find_elements(By.TAG_NAME, "p")
                    td_p_texts = [p.text.strip() for p in td_ps]
                    # 方法3：查找div标签
                    td_divs = td.find_elements(By.TAG_NAME, "div")
       
                    
                    log_print(f"[{serial_number}] [] TD[{td_idx}]:")
                    log_print(f"[{serial_number}] []   - td.text: '{td_text}'")
                    log_print(f"[{serial_number}] []   - p标签: {td_p_texts}")
                    log_print(f"[{serial_number}] []   - div数量: {len(td_divs)}")
 
                log_print(f"[{serial_number}] [] === 打印完毕 ===")
                # 第2个td（index=1）：已成交数量
                if len(tds) > 1:
                    td2_ps = tds[1].find_elements(By.TAG_NAME, "p")
                    filled_amount = td2_ps[0].text.strip() if td2_ps else ""
                # 第4个td（index=3）：价格
                if len(tds) > 3:
                    td4_ps = tds[3].find_elements(By.TAG_NAME, "p")
                    filled_price = td4_ps[0].text.strip() if td4_ps else ""
            except Exception as e:
                log_print(f"[{serial_number}] [] ⚠ 获取Position数据失败: {str(e)}")
        
        return filled_amount
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 获取Position已成交数量失败: {str(e)}")
        return ""


def get_position_from_api(serial_number, trending, option_type):
    """
    通过API获取链上仓位数据
    
    Args:
        serial_number: 浏览器序列号
        trending: 完整的交易主题（包含###）
        option_type: YES 或 NO
        
    Returns:
        float: 仓位数量，失败返回None
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            url = "https://enstudyai.fatedreamer.com/t3/api/fingerprint/position"
            payload = {
                "fingerprintNo": str(serial_number),
                "title": trending
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                position = data.get("position", {})
                
                if option_type == "YES":
                    amount = position.get("yes_amount")
                else:  # NO
                    amount = position.get("no_amount")
                
                if amount is not None:
                    return float(amount)
                else:
                    if attempt < max_retries - 1:
                        log_print(f"[{serial_number}] ⚠ 未获取到仓位数据，{15}秒后重试 ({attempt + 1}/{max_retries})")
                        time.sleep(15)
                        continue
                    return None
            else:
                if attempt < max_retries - 1:
                    log_print(f"[{serial_number}] ⚠ API请求失败，状态码: {response.status_code}，{15}秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(15)
                    continue
                else:
                    log_print(f"[{serial_number}] ⚠ API请求失败，状态码: {response.status_code}")
                    return None
        except Exception as e:
            if attempt < max_retries - 1:
                log_print(f"[{serial_number}] ⚠ 获取链上仓位数据失败: {str(e)}，{15}秒后重试 ({attempt + 1}/{max_retries})")
                time.sleep(15)
                continue
            else:
                log_print(f"[{serial_number}] ⚠ 获取链上仓位数据失败: {str(e)}")
                return None
    
    return None


def wait_for_type5_order_and_collect_data(driver, mission_type, initial_position_count, serial_number, trending_part1, task_data, trade_type, option_type, trending="", amount=None, initial_open_orders_count=0, initial_closed_orders_time="", bro_log_list=None):
    """
    Type 5 任务专用：等待订单成功并收集数据
    
    Args:
        driver: Selenium WebDriver对象
        initial_position_count: 初始 Position 行数（Buy时是tr数量，Sell时是实际持仓数量）
        serial_number: 浏览器序列号
        trending_part1: 子标题（用于筛选）
        task_data: 任务数据
        trade_type: Buy 或 Sell
        option_type: YES 或 NO
        trending: 完整的交易主题（用于API调用，可选）
        amount: 下单数量（可选，用于计算差额）
        initial_open_orders_count: 初始 Open Orders 数量（可选，用于检测挂单变化）
        initial_closed_orders_time: 初始 Closed Orders 最新时间（可选，用于检测挂单变化）
        
    Returns:
        tuple: (success, msg)
    """
    
        # 初始化日志列表（如果未提供）
    if bro_log_list is None:
        bro_log_list = []
        
    
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
    log_print(f"[{serial_number}] [{task_label}] 初始 Open Orders 数量: {initial_open_orders_count}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Closed Orders 最新时间: {initial_closed_orders_time}")
    
    
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
        return False, "[11]切换页面失败"
    
    # 第一阶段：检测Position变化（10分钟超时）
    if trade_type == "Buy":
        log_print(f"[{serial_number}] [{task_label}] ========== 第一阶段：检测Position数量增加 ==========")
    else:
        log_print(f"[[]{serial_number}] [{task_label}] ========== 第一阶段：检测Position已成交数量变化 ==========")
    
    add_bro_log_entry(bro_log_list, serial_number, f"[12][{serial_number}] [{task_label}] ========== 第一阶段：检测Position数量增加 ==========")
    
    
    phase1_timeout = 480  # 8分钟
    check_interval = 20  # 每20秒检查
    refresh_interval = 120  # 每2分钟刷新一次
    
    phase1_start_time = time.time()
    last_refresh_time = phase1_start_time
    position_changed = False
    use_api_data = False  # 标记是否使用链上数据（如果链上数据先检测到变化，则后续使用链上数据）
    api_detected_first = False  # 标记链上数据是否先检测到变化
    hava_order = False
    
    # 对于Buy类型，如果使用链上数据，需要记录初始链上仓位数量
    initial_position_count_api = None
    if trade_type == "Buy" and trending:
        initial_position_count_api = get_position_from_api(serial_number, trending, option_type)
        if initial_position_count_api is not None:
            log_print(f"[{serial_number}] [{task_label}] 初始链上仓位数量: {initial_position_count_api}")
    
    while time.time() - phase1_start_time < phase1_timeout:
        try:
            elapsed = int(time.time() - phase1_start_time)
            log_print(f"[{serial_number}] [{task_label}] 检查Position（已用时 {elapsed}秒）...")
            
            # 对于Buy和Sell类型，每2分钟刷新
            if time.time() - last_refresh_time >= refresh_interval:
                log_print(f"[{serial_number}] [{task_label}] 2分钟无变化，刷新页面...")
                refresh_page_with_opinion_check(driver, serial_number)
                time.sleep(30)
                last_refresh_time = time.time()
            
            if trade_type == "Buy":
                # Buy类型：检查Position数量是否增加
                # 方式1：本地抓取
                current_position_count_local = check_position_count(driver, serial_number, trending_part1, trade_type, option_type)
                
                # 方式2：链上API（如果提供了trending参数）
                current_position_count_api = None
                if trending:
                    current_position_count_api = get_position_from_api(serial_number, trending, option_type)
                    if current_position_count_api is not None:
                        log_print(f"[{serial_number}] [{task_label}] 链上仓位数量: {current_position_count_api}")
                
                # 判断是否检测到变化，并记录是哪种方式先检测到的
                position_changed_detected = False
                local_detected = False
                api_detected = False
                
                # 检查本地数据（tr数量）
                if current_position_count_local == -2:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 检测到对向仓位，跳过本次检查")
                elif current_position_count_local >= 0:
                    log_print(f"[{serial_number}] [{task_label}] 本地持仓数量(tr): {current_position_count_local} (初始: {initial_position_count})")
                    # 本地数据需要大于 initial + 1 才算变化
                    if current_position_count_local > initial_position_count + 1:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 本地数据检测到持仓数量增加！")
                        
                        add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}] 本地数据检测到持仓数量增加！=")
                        local_detected = True
                        position_changed_detected = True
                
                # 检查链上数据（仓位数量）
                if current_position_count_api is not None and initial_position_count_api is not None:
                    log_print(f"[{serial_number}] [{task_label}] 链上持仓数量: {current_position_count_api} (初始: {initial_position_count_api})")
                    # 链上数据需要大于 initial + 1 才算变化（因为链上数据小数位数较多）
                    if current_position_count_api > initial_position_count_api + 1:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 链上数据检测到持仓数量增加！")
                        add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}] 链上数据检测到持仓数量增!")
                        api_detected = True
                        position_changed_detected = True
   
                
                # 只有当本地也检测到变化时，才执行后续步骤
                if position_changed_detected and (local_detected or (api_detected and local_detected)):
                    position_changed = True
                    
                    if api_detected_first:
                        log_print(f"[{serial_number}] [{task_label}] ✓ 本地数据也已检测到变化，可以继续执行")
                    
                    # 更新任务状态（任务一修改status，任务二修改tp9）
                    current_status = get_mission_status(target_mission_id)
                    current_tp9 = get_mission_tp9(target_mission_id)
                    log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}, tp9: {current_tp9}")
                    
                    if is_task1 and mission_type == 5:
                            # 任务一检测到变化，通过tp9判断任务二的进度
                                if current_tp9 == 13 or current_tp9 == 14:
                                    # 任务二也检测到变化了，设置状态为14
                                    log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，更改状态为14...")
                                    save_mission_result(target_mission_id, 14)
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] tp9为{current_tp9}，更改状态为14...")
                                elif current_status is not None:
                                    # 任务一检测到变化，设置状态为12
                                    log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为12...")
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 任务一检测到变化，更改状态为12...")
                                    save_mission_result(target_mission_id, 12)
                    elif mission_type == 5 :
                                # 任务二检测到变化，修改任务一的tp9
                                if current_status == 12 or current_status == 14:
                                    # 任务一也检测到变化了，设置tp9为14
                                    log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                                    update_mission_tp(target_mission_id, tp9=14)
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 任务一状态为{current_status}，设置tp9为14...")
                                elif current_status is not None and current_status != 2:
                                    # 任务二检测到变化，设置tp9为13
                                    log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，设置任务一tp9为13...")
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 任务二检测到变化，设置tp9为13...")
                                    update_mission_tp(target_mission_id, tp9=13)
                    
                    break
                
                # Buy类型：Position未变化，检查Open Orders数量是否有变化
                if not position_changed_detected:
                    log_print(f"[{serial_number}] [{task_label}] Position未变化，检查Open Orders数量是否有变化...")
                    current_open_orders_count = get_opinion_table_row_count(driver, serial_number, need_click_open_orders=True, trending_part1=trending_part1)
                    
                    if current_open_orders_count < 0:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Open Orders 数量，设为 0")
                        current_open_orders_count = 0
                    
                    log_print(f"[{serial_number}] [{task_label}] 当前 Open Orders 数量: {current_open_orders_count} (初始: {initial_open_orders_count})")
                    
                    # 检查Open Orders数量是否有变化
                    if current_open_orders_count > initial_open_orders_count:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Open Orders数量变化！")
                        
                        add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 检测到Open Orders数量变化！")
                        
                        # 更新任务状态（任务一修改status，任务二修改tp9）
                        current_status = get_mission_status(target_mission_id)
                        current_tp9 = get_mission_tp9(target_mission_id)
                        log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}, tp9: {current_tp9}")
                        if is_task1 and mission_type == 5:
                            # 任务一检测到变化，通过tp9判断任务二的进度
                                if current_tp9 == 13 or current_tp9 == 14:
                                    # 任务二也检测到变化了，设置状态为14
                                    log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，更改状态为14...")
                                    save_mission_result(target_mission_id, 14)
                                elif current_status is not None:
                                    # 任务一检测到变化，设置状态为12
                                    log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为12...")
                                    save_mission_result(target_mission_id, 12)
                        elif mission_type == 5:
                                # 任务二检测到变化，修改任务一的tp9
                                if current_status == 12 or current_status == 14:
                                    # 任务一也检测到变化了，设置tp9为14
                                    log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                                    update_mission_tp(target_mission_id, tp9=14)
                                elif current_status is not None and current_status != 2:
                                    # 任务二检测到变化，设置tp9为13
                                    log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，设置任务一tp9为13...")
                                    update_mission_tp(target_mission_id, tp9=13)
                        hava_order = True
                        time.sleep(check_interval)
                        continue;

                    else:
                        # Open Orders数量也未变化，检查Closed Orders时间
                        log_print(f"[{serial_number}] [{task_label}] Open Orders数量未变化，检查Closed Orders时间是否有变化...")
                        current_closed_orders_time = get_closed_orders_latest_time(driver, serial_number)
                        
                        if not current_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Closed Orders 时间")
                            current_closed_orders_time = ""
                        
                        log_print(f"[{serial_number}] [{task_label}] 当前 Closed Orders 最新时间: {current_closed_orders_time} (初始: {initial_closed_orders_time})")
                        
                        # 检查Closed Orders时间是否有变化
                        if current_closed_orders_time and current_closed_orders_time != initial_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Closed Orders时间变化！")
                            add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 检测到Closed Orders时间变化！")
                            # 更新任务状态（任务一修改status，任务二修改tp9）
                            current_status = get_mission_status(target_mission_id)
                            current_tp9 = get_mission_tp9(target_mission_id)
                            log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}, tp9: {current_tp9}")
                            
                            if is_task1 and mission_type == 5:
                            # 任务一检测到变化，通过tp9判断任务二的进度
                                if current_tp9 == 13 or current_tp9 == 14:
                                    # 任务二也检测到变化了，设置状态为14
                                    log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，更改状态为14...")
                                    save_mission_result(target_mission_id, 14)
                                elif current_status is not None:
                                    # 任务一检测到变化，设置状态为12
                                    log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为12...")
                                    save_mission_result(target_mission_id, 12)
                            elif mission_type == 5:
                                # 任务二检测到变化，修改任务一的tp9
                                if current_status == 12 or current_status == 14:
                                    # 任务一也检测到变化了，设置tp9为14
                                    log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                                    update_mission_tp(target_mission_id, tp9=14)
                                elif current_status is not None and current_status != 2:
                                    # 任务二检测到变化，设置tp9为13
                                    log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，设置任务一tp9为13...")
                                    update_mission_tp(target_mission_id, tp9=13)
                            hava_order = True
                            break
                      # 继续等待，不退出循环
                    time.sleep(check_interval)
                    continue
                    
            else:
                # Sell类型：检查已成交数量是否变化
                # 方式1：本地抓取
                current_filled_amount_local = get_position_filled_amount(driver, serial_number, trending_part1)
                
                # 方式2：链上API（如果提供了trending参数）
                current_filled_amount_api = None
                if trending:
                    current_filled_amount_api = get_position_from_api(serial_number, trending, option_type)
                    if current_filled_amount_api is not None:
                        log_print(f"[{serial_number}] [{task_label}] 链上已成交数量: {current_filled_amount_api}")
                
                # 判断是否检测到变化，并记录是哪种方式先检测到的
                position_changed_detected = False
                local_detected = False
                api_detected = False
                
                # 检查本地数据
                if current_filled_amount_local:
                    log_print(f"[{serial_number}] [{task_label}] 本地已成交数量: {current_filled_amount_local} (初始: {initial_position_count})")
                    # 处理文本：去掉逗号并转换为数字，与initial_position_count比较
                    try:
                        # 移除逗号和其他非数字字符，只保留数字和小数点
                        amount_str = ''.join(c for c in current_filled_amount_local if c.isdigit() or c == '.')
                        if amount_str:
                            current_filled_amount_float = float(amount_str)
                            # 链上数据需要大于1才算变化
                            if abs(current_filled_amount_float - float(initial_position_count)) > 1:
                                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 本地数据检测到已成交数量变化！")
                                add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 本地数据检测到已成交数量变化！")
                                local_detected = True
                                position_changed_detected = True
                            else:
                                log_print(f"[{serial_number}] [{task_label}] 本地已成交数量未变化")
                        else:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 无法从文本中提取数字: {current_filled_amount_local}")
                    except (ValueError, TypeError) as e:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 数量转换失败: {current_filled_amount_local}, 错误: {str(e)}")
                else:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取本地已成交数量")
                
                # 检查链上数据
                if current_filled_amount_api is not None:
                    log_print(f"[{serial_number}] [{task_label}] 链上已成交数量: {current_filled_amount_api} (初始: {initial_position_count})")
                    # 链上数据需要大于1才算变化
                    if abs(current_filled_amount_api - float(initial_position_count)) > 1:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 链上数据检测到已成交数量变化！")
                        add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 链上数据检测到已成交数量变化！！")
                        api_detected = True
                        position_changed_detected = True
                
                
                # 只有当本地也检测到变化时，才执行后续步骤
                if position_changed_detected and (local_detected or (api_detected and local_detected)):
                    position_changed = True
                    
                    if api_detected_first:
                        log_print(f"[{serial_number}] [{task_label}] ✓ 本地数据也已检测到变化，可以继续执行")
                    
                    # 更新任务状态（任务一修改status，任务二修改tp9）
                    current_status = get_mission_status(target_mission_id)
                    current_tp9 = get_mission_tp9(target_mission_id)
                    log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}, tp9: {current_tp9}")
                    
                    if is_task1 and mission_type == 5:
                            # 任务一检测到变化，通过tp9判断任务二的进度
                                if current_tp9 == 13 or current_tp9 == 14:
                                    # 任务二也检测到变化了，设置状态为14
                                    log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，更改状态为14...")
                                    save_mission_result(target_mission_id, 14)
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] tp9为{current_tp9}，更改状态为14..")
                                elif current_status is not None:
                                    # 任务一检测到变化，设置状态为12
                                    log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为12...")
                                    save_mission_result(target_mission_id, 12)
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 任务一检测到变化，更改状态为12...")
                    elif mission_type == 5:
                                # 任务二检测到变化，修改任务一的tp9
                                if current_status == 12 or current_status == 14:
                                    # 任务一也检测到变化了，设置tp9为14
                                    log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                                    update_mission_tp(target_mission_id, tp9=14)
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 任务一状态为{current_status}，设置tp9为14...")
                                elif current_status is not None  and current_status != 2:
                                    # 任务二检测到变化，设置tp9为13
                                    log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，设置任务一tp9为13...")
                                    update_mission_tp(target_mission_id, tp9=13)
                                    add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}] 任务二检测到变化，设置tp9为13...")
                    
                    break
                
                # Sell类型：Position未变化，检查Open Orders数量是否有变化
                if not position_changed_detected:
                    log_print(f"[{serial_number}] [{task_label}] Position未变化，检查Open Orders数量是否有变化...")
                    current_open_orders_count = get_opinion_table_row_count(driver, serial_number, need_click_open_orders=True, trending_part1=trending_part1)
                    
                    if current_open_orders_count < 0:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Open Orders 数量，设为 0")
                        current_open_orders_count = 0
                    
                    log_print(f"[{serial_number}] [{task_label}] 当前 Open Orders 数量: {current_open_orders_count} (初始: {initial_open_orders_count})")
                    
                    # 检查Open Orders数量是否有变化
                    if current_open_orders_count > initial_open_orders_count:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Open Orders数量变化！")
                        add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}]  检测到Open Orders数量变化！")
                        # 更新任务状态（任务一修改status，任务二修改tp9）
                        current_status = get_mission_status(target_mission_id)
                        current_tp9 = get_mission_tp9(target_mission_id)
                        log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}, tp9: {current_tp9}")
                        
                        if is_task1 and mission_type == 5:
                            # 任务一检测到变化，通过tp9判断任务二的进度
                                if current_tp9 == 13 or current_tp9 == 14:
                                    # 任务二也检测到变化了，设置状态为14
                                    log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，更改状态为14...")
                                    save_mission_result(target_mission_id, 14)
                                elif current_status is not None:
                                    # 任务一检测到变化，设置状态为12
                                    log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为12...")
                                    save_mission_result(target_mission_id, 12)
                        elif mission_type == 5:
                                # 任务二检测到变化，修改任务一的tp9
                                if current_status == 12 or current_status == 14:
                                    # 任务一也检测到变化了，设置tp9为14
                                    log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                                    update_mission_tp(target_mission_id, tp9=14)
                                elif current_status is not None and current_status != 2:
                                    # 任务二检测到变化，设置tp9为13
                                    log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，设置任务一tp9为13...")
                                    update_mission_tp(target_mission_id, tp9=13)
                        hava_order = True
                        # 继续等待，不退出循环
                        time.sleep(check_interval)
                        continue
                    else:
                        # Open Orders数量也未变化，检查Closed Orders时间
                        log_print(f"[{serial_number}] [{task_label}] Open Orders数量未变化，检查Closed Orders时间是否有变化...")
                        current_closed_orders_time = get_closed_orders_latest_time(driver, serial_number)
                        
                        if not current_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Closed Orders 时间")
                            current_closed_orders_time = ""
                        
                        log_print(f"[{serial_number}] [{task_label}] 当前 Closed Orders 最新时间: {current_closed_orders_time} (初始: {initial_closed_orders_time})")
                        
                        # 检查Closed Orders时间是否有变化
                        if current_closed_orders_time and current_closed_orders_time != initial_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Closed Orders时间变化！")
                            add_bro_log_entry(bro_log_list, serial_number, f"[14][{serial_number}]  检测到Closed Orders时间变化！")
                            # 更新任务状态（任务一修改status，任务二修改tp9）
                            current_status = get_mission_status(target_mission_id)
                            current_tp9 = get_mission_tp9(target_mission_id)
                            log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}, tp9: {current_tp9}")
                            
                            if is_task1 and mission_type == 5:
                            # 任务一检测到变化，通过tp9判断任务二的进度
                                if current_tp9 == 13 or current_tp9 == 14:
                                    # 任务二也检测到变化了，设置状态为14
                                    log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，更改状态为14...")
                                    save_mission_result(target_mission_id, 14)
                                elif current_status is not None:
                                    # 任务一检测到变化，设置状态为12
                                    log_print(f"[{serial_number}] [{task_label}] 任务一检测到变化，更改状态为12...")
                                    save_mission_result(target_mission_id, 12)
                            elif mission_type == 5:
                                # 任务二检测到变化，修改任务一的tp9
                                if current_status == 12 or current_status == 14:
                                    # 任务一也检测到变化了，设置tp9为14
                                    log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                                    update_mission_tp(target_mission_id, tp9=14)
                                elif current_status is not None and current_status != 2:
                                    # 任务二检测到变化，设置tp9为13
                                    log_print(f"[{serial_number}] [{task_label}] 任务二检测到变化，设置任务一tp9为13...")
                                    update_mission_tp(target_mission_id, tp9=13)
                            hava_order = True
                            # 继续等待，不退出循环
                            break
            
            time.sleep(check_interval)
            
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 检查Position时出错: {str(e)}")
            time.sleep(check_interval)
    
    
    both_hava_order = False
     
    if not hava_order and not position_changed:
        add_bro_log_entry(bro_log_list, serial_number, f"[15][{serial_number}]  检测仓位变化超时，且无挂单无ClosedOrder！")
        return False, "[15]检测仓位变化超时，且无挂单无ClosedOrder"
    if hava_order or position_changed:
        # 在10分钟内，每隔30秒检测一次任务一的状态
        log_print(f"[{serial_number}] [{task_label}] 开始10分钟内的定期检测（每隔30秒检测一次任务状态）...")
        phase2_timeout = 480
        phase2_check_interval = 30  # 30秒
        phase2_start_time = time.time()
        
        while time.time() - phase2_start_time < phase2_timeout:
            try:
                elapsed = int(time.time() - phase2_start_time)
                # 获取任务一的状态和tp9
                current_status = get_mission_status(target_mission_id)
                current_tp9 = get_mission_tp9(target_mission_id)
                log_print(f"[{serial_number}] [{task_label}] phase2轮询: status={current_status}, tp9={current_tp9}")
                
                if is_task1 and mission_type == 5:
                    # 任务一：通过tp9判断任务二的进度
                    if current_tp9 == 13 or current_tp9 == 14 or current_tp9 == 2:
                        # 任务二也检测到变化了，设置状态为14
                        log_print(f"[{serial_number}] [{task_label}] tp9为{current_tp9}，任务二也检测到变化，设置状态为14...")
                        save_mission_result(target_mission_id, 14)
                        both_hava_order = True
                        break;
                    elif current_status == 12:
                        continue;
                    elif current_tp9 == 3:
                        break;
                       
                elif mission_type == 5:
                    # 任务二：通过status判断任务一的进度
                    if current_status == 14 or current_status == 2 or current_status == 12:
                        both_hava_order = True
                        # 任务一也检测到变化了，设置tp9为14
                        log_print(f"[{serial_number}] [{task_label}] 任务一状态为{current_status}，任务一也检测到变化，设置tp9为14...")
                        update_mission_tp(target_mission_id, tp9=14)
                        break;
                    elif current_tp9 == 13:
                        continue;
                    elif current_status == 3:
                        break;
                elif mission_type == 9:
                    # 任务二：通过status判断任务一的进度
                    if current_status == 14:
                        both_hava_order = True
                        break;
                    elif current_status == 3:
                        break;
                
                # 等待30秒后继续下一次检测
                time.sleep(phase2_check_interval)
                
            except Exception as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 检测任务一状态时出错: {str(e)}")
                time.sleep(phase2_check_interval)
    
    log_print(f"[{serial_number}] [{task_label}] 600s定期检测结束")
    
    
    
    if  not both_hava_order: 
  
        try:
            # 点击Open Orders按钮
            log_print(f"[{serial_number}] [{task_label}] 点击Open Orders按钮...")
            open_orders_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in open_orders_buttons:
                if btn.text.strip() == "Open Orders":
                    btn.click()
                    time.sleep(7)
                    break
            
            # 获取Open Orders数据
            log_print(f"[{serial_number}] [{task_label}] 获取Open Orders数据...")
            
            # 查找 Open Orders div  CCCCCCC
            tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
            open_orders_div = None
            for div in tabs_divs:
                div_id = div.get_attribute('id')
                if div_id and 'openorders' in div_id.lower():
                    open_orders_div = div
                    break
            
            if not open_orders_div:
                add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交")
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Open Orders div")
                return False, "[16]检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交"
            # 获取 tbody 和 tr
            try:
                tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            except:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到tbody或tr，可能没有挂单")
                add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交")
                return False, "[16]检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交"
            
            if not tr_list or len(tr_list) == 0:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 没有挂单")
                add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交")
                return False, "[16]检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交"
            
            current_status = get_mission_status(target_mission_id)
            log_print(f"[{serial_number}] [{task_label}] 当前任务一状态: {current_status}")
            
            # 找到第一个tr的最后一个td下的svg并点击
            first_tr = tr_list[0]
            tds = first_tr.find_elements(By.TAG_NAME, "td")
            if len(tds) == 0:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到td")
                add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交")
                return False, "[16]检测对方挂单超时或失败,尝试取消自己挂单,未找到挂单,可能已成交"
            
            last_td = tds[-1]  # 最后一个td
            svg_elements = last_td.find_elements(By.TAG_NAME, "svg")
            
            if not svg_elements or len(svg_elements) == 0:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到svg元素")
                add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,挂单取消失败,可能已成交")
                return False, "[16]检测对方挂单超时或失败,尝试取消自己挂单，挂单取消失败,可能已成交"
            
            log_print(f"[{serial_number}] [{task_label}] 点击svg取消按钮...")
            svg_elements[0].click()
            time.sleep(2)
            
            # 在10秒内找到"Confirm"按钮并点击
            log_print(f"[{serial_number}] [{task_label}] 查找Confirm按钮...")
            confirm_found = False
            confirm_timeout = 10
            confirm_start_time = time.time()
            
            while time.time() - confirm_start_time < confirm_timeout:
                try:
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in all_buttons:
                        if btn.text.strip() == "Confirm":
                            log_print(f"[{serial_number}] [{task_label}] ✓ 找到Confirm按钮，点击...")
                            btn.click()
                            confirm_found = True
                            break
                    
                    if confirm_found:
                        break
                    
                    time.sleep(0.5)
                except Exception as e:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 查找Confirm按钮时出错: {str(e)}")
                    time.sleep(0.5)
            
            if not confirm_found:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Confirm按钮")
                add_bro_log_entry(bro_log_list, serial_number, f"[16][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,挂单取消失败,可能已成交")
                return False, "[16]检测对方挂单超时或失败,尝试取消自己挂单，挂单取消失败,可能已成交"
            
            # 等待10秒
            log_print(f"[{serial_number}] [{task_label}] 等待10秒后重新检查挂单...")
            time.sleep(10)
            
            # 重新获取open_orders_div
            tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
            open_orders_div = None
            for div in tabs_divs:
                div_id = div.get_attribute('id')
                if div_id and 'openorders' in div_id.lower():
                    open_orders_div = div
                    break
            
            if not open_orders_div:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 重新获取时未找到Open Orders div")
                add_bro_log_entry(bro_log_list, serial_number, f"[17][{serial_number}]  检测对方挂单超时或失败，有挂单，已成功取消挂单")
                return False, "[17]检测对方挂单超时或失败，有挂单，已成功取消挂单"
            
            # 重新获取tbody和tr
            try:
                tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            except:
                # 没有tbody或tr，说明挂单已取消
                log_print(f"[{serial_number}] [{task_label}] ✓ 挂单已取消（无tbody/tr）")
                add_bro_log_entry(bro_log_list, serial_number, f"[17][{serial_number}]  检测对方挂单超时或失败，有挂单，已成功取消挂单")
                return False, "[17]检测对方挂单超时或失败，有挂单，已成功取消挂单"
            
            if not tr_list or len(tr_list) == 0:
                # 没有tr，说明挂单已取消
                log_print(f"[{serial_number}] [{task_label}] ✓ 挂单已取消（无tr）")
                add_bro_log_entry(bro_log_list, serial_number, f"[17][{serial_number}]  检测对方挂单超时或失败，有挂单，已成功取消挂单")
                return False, "[17]检测对方挂单超时或失败，有挂单，已成功取消挂单"
            else:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 挂单仍然存在")
                add_bro_log_entry(bro_log_list, serial_number, f"[18][{serial_number}]  检测对方挂单超时或失败,尝试取消自己挂单,但取消挂单失败")
                return False, "[18]检测对方挂单超时或失败,尝试取消自己挂单,但取消挂单失败"
                
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 取消挂单时出错: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] [{task_label}] 错误详情:\n{traceback.format_exc()}")
            add_bro_log_entry(bro_log_list, serial_number, f"[18][{serial_number}]  [18]检测对方挂单超时或失败,尝试取消自己挂单,且取消挂单出错")
            return False, "[18]检测对方挂单超时或失败,尝试取消自己挂单,且取消挂单出错"
    
        
    # 第三阶段：获取Position和Open Orders的详细数据
    log_print(f"[{serial_number}] [{task_label}] ========== 第三阶段：收集数据 ==========")
    
    try:
        # === 新增：15分钟内每2分钟检测仓位变化 ===
        log_print(f"[{serial_number}] [{task_label}] 开始15分钟仓位变化检测（每2分钟检测一次）...")
        add_bro_log_entry(bro_log_list, serial_number, f"[19][{serial_number}] 开始15分钟仓位变化检测")
        
        phase3_timeout = 900  # 15分钟
        phase3_check_interval = 90  # 2分钟
        phase3_start_time = time.time()
        phase3_position_change_detected = False
        phase3_use_api_data = False  # 标记最终使用哪种数据
        phase3_filled_amount = ""
        phase3_filled_price = ""
        
        while time.time() - phase3_start_time < phase3_timeout:
            try:
                elapsed = int(time.time() - phase3_start_time)
                log_print(f"[{serial_number}] [{task_label}] 第三阶段检测仓位（已用时 {elapsed}秒）...")
                
                # 记录本次检测的变化量
                local_change_amount = 0
                api_change_amount = 0
                local_position_valid = False
                api_position_valid = False
                
                if trade_type == "Buy":
                    # Buy类型：检查Position数量变化
                    # 方式1：本地抓取
                    log_print(f"[{serial_number}] [{task_label}] 点击Position按钮...")
                    position_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in position_buttons:
                        if btn.text.strip() == "Position":
                            btn.click()
                            time.sleep(7)
                            break
                    
                    current_position_count_local = check_position_count(driver, serial_number, trending_part1, trade_type, option_type)
                    
                    if current_position_count_local >= 0 and current_position_count_local != -2:
                        local_change_amount = abs(current_position_count_local - initial_position_count)
                        local_position_valid = True
                        log_print(f"[{serial_number}] [{task_label}] 本地仓位数量: {current_position_count_local} (初始: {initial_position_count}), 变化量: {local_change_amount}")
                    
                    # 方式2：链上API
                    if trending:
                        current_position_count_api = get_position_from_api(serial_number, trending, option_type)
                        if current_position_count_api is not None and initial_position_count_api is not None:
                            api_change_amount = abs(current_position_count_api - initial_position_count_api)
                            api_position_valid = True
                            log_print(f"[{serial_number}] [{task_label}] 链上仓位数量: {current_position_count_api} (初始: {initial_position_count_api}), 变化量: {api_change_amount}")
                
                else:
                    # Sell类型：检查已成交数量变化
                    # 方式1：本地抓取
                    log_print(f"[{serial_number}] [{task_label}] 点击Position按钮...")
                    position_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in position_buttons:
                        if btn.text.strip() == "Position":
                            btn.click()
                            time.sleep(7)
                            break
                    
                    current_filled_amount_local = get_position_filled_amount(driver, serial_number, trending_part1)
                    
                    if current_filled_amount_local:
                        try:
                            amount_str = ''.join(c for c in current_filled_amount_local if c.isdigit() or c == '.')
                            if amount_str:
                                current_filled_amount_float = float(amount_str)
                                local_change_amount = abs(current_filled_amount_float - float(initial_position_count))
                                local_position_valid = True
                                log_print(f"[{serial_number}] [{task_label}] 本地已成交数量: {current_filled_amount_float} (初始: {initial_position_count}), 变化量: {local_change_amount}")
                        except (ValueError, TypeError) as e:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 本地数量转换失败: {str(e)}")
                    
                    # 方式2：链上API
                    if trending:
                        current_filled_amount_api = get_position_from_api(serial_number, trending, option_type)
                        if current_filled_amount_api is not None:
                            api_change_amount = abs(current_filled_amount_api - float(initial_position_count))
                            api_position_valid = True
                            log_print(f"[{serial_number}] [{task_label}] 链上已成交数量: {current_filled_amount_api} (初始: {initial_position_count}), 变化量: {api_change_amount}")
                
                # 检查是否有变化
                has_change = (local_position_valid and local_change_amount > 1) or (api_position_valid and api_change_amount > 1)
                
                if not has_change:
                    log_print(f"[{serial_number}] [{task_label}] 仓位未变化，刷新页面...")
                    refresh_page_with_opinion_check(driver, serial_number)
                    time.sleep(30)
                else:
                    # 有变化，检查变化量是否满足条件
                    if amount is not None:
                        amount_threshold = float(amount) * 0.8  # 下单量的80%
                        log_print(f"[{serial_number}] [{task_label}] 下单数量: {amount}, 80%阈值: {amount_threshold}")
                        log_print(f"[{serial_number}] [{task_label}] 本地变化量: {local_change_amount if local_position_valid else 'N/A'}")
                        log_print(f"[{serial_number}] [{task_label}] 链上变化量: {api_change_amount if api_position_valid else 'N/A'}")
                        
                        # 判断哪个数据源满足条件
                        local_meets_threshold = local_position_valid and local_change_amount >= amount_threshold
                        api_meets_threshold = api_position_valid and api_change_amount >= amount_threshold
                        
                        if local_meets_threshold or api_meets_threshold:
                            log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 仓位变化量满足条件（>=80%）！")
                            add_bro_log_entry(bro_log_list, serial_number, f"[20][{serial_number}] 仓位变化量满足条件，提前结束检测")
                            
                            # 选择使用哪个数据源（优先使用满足条件的，都满足则优先链上）
                            if api_meets_threshold:
                                phase3_use_api_data = True
                                phase3_filled_amount = str(current_position_count_api if trade_type == "Buy" else current_filled_amount_api)
                                log_print(f"[{serial_number}] [{task_label}] 使用链上数据: {phase3_filled_amount}")
                            elif local_meets_threshold:
                                phase3_use_api_data = False
                                if trade_type == "Buy":
                                    phase3_filled_amount = str(current_position_count_local)
                                else:
                                    phase3_filled_amount = current_filled_amount_local
                                log_print(f"[{serial_number}] [{task_label}] 使用本地数据: {phase3_filled_amount}")
                            
                            phase3_filled_price = "--"
                            phase3_position_change_detected = True
                            break
                        else:
                            log_print(f"[{serial_number}] [{task_label}] 仓位有变化但未达到80%阈值，继续检测...")
                    else:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 未提供下单数量，无法判断阈值")
                
                # 等待下一次检测
                time.sleep(phase3_check_interval)
                
            except Exception as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 第三阶段检测仓位时出错: {str(e)}")
                time.sleep(phase3_check_interval)
        
        # 如果15分钟内检测到满足条件的变化，直接返回成功
        if phase3_position_change_detected:
            log_print(f"[{serial_number}] [{task_label}] 第三阶段检测成功，直接返回...")
            
            # 获取交易费
            transaction_fee, price_from_fee, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type)
            
            # 如果有价格信息，使用交易费检查返回的价格
            if price_from_fee and price_from_fee != "--":
                phase3_filled_price = price_from_fee
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": phase3_filled_amount,
                "filled_price": phase3_filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 第三阶段检测结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {phase3_filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {phase3_filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   数据来源: {'链上API' if phase3_use_api_data else '本地抓取'}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 第三阶段检测成功且交易费检查通过，任务成功！")
                add_bro_log_entry(bro_log_list, serial_number, f"[21][{serial_number}] 第三阶段检测成功，任务完成")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 第三阶段检测成功但交易费检查失败，任务失败")
                add_bro_log_entry(bro_log_list, serial_number, f"[22][{serial_number}] 第三阶段检测成功但交易费检查失败")
                return True, msg
        
        log_print(f"[{serial_number}] [{task_label}] 15分钟检测超时或未满足条件，继续执行原流程...")
        add_bro_log_entry(bro_log_list, serial_number, f"[23][{serial_number}] 15分钟检测超时，继续原流程")
        # === 新增逻辑结束 ===
        
        filled_amount = ""
        filled_price = ""
        
        # 如果前面是链上数据先检测到变化，直接使用链上数据，跳过本地抓取
        if use_api_data and trending:
            log_print(f"[{serial_number}] [{task_label}] 前面链上数据先检测到变化，直接使用链上数据...")
            api_position_amount = get_position_from_api(serial_number, trending, option_type)
            if api_position_amount is not None:
                filled_amount = str(api_position_amount)
                filled_price = "--"
                log_print(f"[{serial_number}] [{task_label}] 链上数据 - 已成交数量: {filled_amount}, 价格: {filled_price}")
            else:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 获取链上数据失败，改用本地抓取")
                use_api_data = False  # 如果链上数据获取失败，改用本地抓取
        
        # 如果使用本地数据，进行本地抓取
        if not use_api_data:
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
                filled_amount = "0"
                filled_price = "--"
                log_print(f"[{serial_number}] [{task_label}] 设置 filled_amount = 0，跳过获取tr数据")
            else:
                # 获取 tbody 和 tr
                try:
                    tbody = position_div.find_element(By.TAG_NAME, "tbody")
                    tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    if not tr_list or len(tr_list) == 0:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ Position中没有tr")
                        filled_amount = "0"
                        filled_price = "--"
                        log_print(f"[{serial_number}] [{task_label}] 设置 filled_amount = 0，跳过获取tr数据")
                    else:
                        # 等待tr中的内容完全加载
                        log_print(f"[{serial_number}] [{task_label}] 等待tr内容加载...")
                        time.sleep(3)
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
                except Exception as e:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 获取tbody或tr失败: {str(e)}")
                    filled_amount = "0"
                    filled_price = "--"
                    log_print(f"[{serial_number}] [{task_label}] 设置 filled_amount = 0，跳过获取tr数据")
        
        # 如果提供了trending参数（前面使用了链上数据），重新获取链上数据
        if trending:
            log_print(f"[{serial_number}] [{task_label}] 检测到使用链上数据，重新获取链上仓位数据...")
            api_position_amount = get_position_from_api(serial_number, trending, option_type)
            if api_position_amount is not None:
                filled_amount = str(api_position_amount)
                filled_price = "--"
                log_print(f"[{serial_number}] [{task_label}] 链上数据 - 已成交数量: {filled_amount}, 价格: {filled_price}")
            else:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 获取链上数据失败，使用本地数据")
        
        log_print(f"[{serial_number}] [{task_label}] Position数据 - 已成交数量: {filled_amount}, 价格: {filled_price}")
        
        # 计算差额，如果差额绝对值小于5，跳过获取Open Orders数据
        skip_open_orders = False
        if amount is not None and filled_amount:
            try:
                # 将 filled_amount 转换为数字（处理可能包含逗号的情况）
                filled_amount_str = str(filled_amount).replace(',', '').strip()
                # 处理 "<0.01" 这种情况
                if '<' in filled_amount_str:
                    filled_amount_float = 0.0
                else:
                    filled_amount_float = float(filled_amount_str)
                
                # 计算变化值：filled_amount - initial_position_count
                position_change = filled_amount_float - float(initial_position_count)
                # 获取变化值的绝对值
                position_change_abs = abs(position_change)
                
                # 计算差额：下单数量 - 变化值
                difference = float(amount) - position_change_abs
                difference_abs = abs(difference)
                
                log_print(f"[{serial_number}] [{task_label}] 差额计算:")
                log_print(f"[{serial_number}] [{task_label}]   下单数量: {amount}")
                log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount_float}")
                log_print(f"[{serial_number}] [{task_label}]   初始数量: {initial_position_count}")
                log_print(f"[{serial_number}] [{task_label}]   变化值: {position_change} (绝对值: {position_change_abs})")
                log_print(f"[{serial_number}] [{task_label}]   差额: {difference} (绝对值: {difference_abs})")
                
                # 计算下单数量的10%作为阈值
                amount_threshold = float(amount) * 0.2
                log_print(f"[{serial_number}] [{task_label}]   下单数量的40%: {amount_threshold}")
                
                # 如果差额绝对值小于下单数量的10%，跳过获取Open Orders数据
                if difference_abs < amount_threshold:
                    log_print(f"[{serial_number}] [{task_label}] ✓ 差额绝对值 ({difference_abs}) < 下单数量的10% ({amount_threshold})，跳过获取Open Orders数据")
                    skip_open_orders = True
                else:
                    log_print(f"[{serial_number}] [{task_label}] 差额绝对值 ({difference_abs}) >= 下单数量的10% ({amount_threshold})，继续获取Open Orders数据")
            except (ValueError, TypeError) as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 计算差额时出错: {str(e)}，继续获取Open Orders数据")
        
        # 如果跳过Open Orders，直接返回成功
        if skip_open_orders:
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 差额检查通过且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 差额检查通过但交易费检查失败，任务失败")
                return True, msg
        
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
            if div_id and 'openorders' in div_id.lower():
                open_orders_div = div
                break
        
        if not open_orders_div:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Open Orders div")
            # 没找到div，检查 Transactions
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 无挂单且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 无挂单但交易费检查失败，任务失败")
                return True, msg
        
        # 获取 tbody 和 tr
        try:
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        except:
            # 没有tbody或tr，说明没有挂单
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 无挂单且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 无挂单但交易费检查失败，任务失败")
                return True, msg
        
        if not tr_list or len(tr_list) == 0:
            # 没有tr，说明没有挂单
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE5_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            if fee_check_success:
                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 无挂单且交易费检查通过，任务成功！")
                return True, msg
            else:
                log_print(f"[{serial_number}] [{task_label}] ✗ 无挂单但交易费检查失败，任务失败")
                return True, msg
        
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
        transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, is_task1, trade_type)
        
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
            msg_data["initial_filled_amount"] = str(initial_position_count)
        
        msg = json.dumps(msg_data, ensure_ascii=False)
        log_print(f"[{serial_number}] [{task_label}] ✗ 有挂单，任务失败")
        log_print(f"[{serial_number}] [{task_label}] 结果详情:")
        if trade_type == "Sell":
            log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
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
        return False, f"[16]收集数据失败: {str(e)}"


def wait_for_type6_order_and_collect_data(driver, initial_position_count, serial_number, trending_part1, task_data, trade_type, option_type, trending="", amount=None, initial_open_orders_count=0, initial_closed_orders_time=""):
    """
    Type 6 任务专用：等待订单成功并收集数据
    
    Args:
        driver: Selenium WebDriver对象
        initial_position_count: 初始 Position 行数（Buy时是tr数量，Sell时是实际持仓数量）
        serial_number: 浏览器序列号
        trending_part1: 子标题（用于筛选）
        task_data: 任务数据
        trade_type: Buy 或 Sell
        option_type: YES 或 NO
        trending: 完整的交易主题（用于API调用，可选）
        amount: 下单数量（可选，用于计算差额）
        initial_open_orders_count: 初始 Open Orders 数量（可选，用于检测挂单变化）
        initial_closed_orders_time: 初始 Closed Orders 最新时间（可选，用于检测挂单变化）
        
    Returns:
        tuple: (success, msg)
    """
    mission = task_data.get('mission', {})
    mission_id = mission.get('id')
    task_label = "Type6"
    
    # 获取 tp14 值（取消挂单延迟时间，秒），如果没有则默认 60 秒
    tp2 = mission.get('tp14')
    if tp2 is not None:
        try:
            tp2_time = int(tp2) if isinstance(tp2, (int, str)) and str(tp2).isdigit() else 60
        except:
            tp2_time = 60
    else:
        tp2_time = 60
    
    log_print(f"[{serial_number}] [{task_label}] Type 6 专用等待流程开始...")
    log_print(f"[{serial_number}] [{task_label}] 交易类型: {trade_type}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Position 数量: {initial_position_count}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Open Orders 数量: {initial_open_orders_count}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Closed Orders 最新时间: {initial_closed_orders_time}")
    log_print(f"[{serial_number}] [{task_label}] 取消挂单延迟时间: {tp2_time} 秒")
    
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
        return False, "[11]切换页面失败"
    

    time.sleep(tp2_time)

    # 无论什么状态退出，都要执行撤单逻辑（不直接返回，只记录状态）
    log_print(f"[{serial_number}] [{task_label}] ========== 执行撤单逻辑 ==========")
    cancel_status = "无挂单"  # 默认值：有挂单取消失败、有挂单取消成功、无挂单
    
    try:
        # 点击Open Orders按钮
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
            if div_id and 'openorders' in div_id.lower():
                open_orders_div = div
                break
        
        if not open_orders_div:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Open Orders div，可能已成交")
            cancel_status = "无挂单"
        else:
            # 获取 tbody 和 tr
            try:
                tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            except:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到tbody或tr，可能没有挂单")
                cancel_status = "无挂单"
                tr_list = []
            
            if not tr_list or len(tr_list) == 0:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 没有挂单")
                cancel_status = "无挂单"
            else:
                # 有挂单，尝试取消
                log_print(f"[{serial_number}] [{task_label}] 发现挂单，尝试取消...")
                try:
                    # 找到第一个tr的最后一个td下的svg并点击
                    first_tr = tr_list[0]
                    tds = first_tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) == 0:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到td")
                        cancel_status = "有挂单取消失败"
                    else:
                        last_td = tds[-1]  # 最后一个td
                        svg_elements = last_td.find_elements(By.TAG_NAME, "svg")
                        
                        if not svg_elements or len(svg_elements) == 0:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到svg元素")
                            cancel_status = "有挂单取消失败"
                        else:
                            log_print(f"[{serial_number}] [{task_label}] 点击svg取消按钮...")
                            svg_elements[0].click()
                            time.sleep(2)
                            
                            # 在10秒内找到"Confirm"按钮并点击
                            log_print(f"[{serial_number}] [{task_label}] 查找Confirm按钮...")
                            confirm_found = False
                            confirm_timeout = 10
                            confirm_start_time = time.time()
                            
                            while time.time() - confirm_start_time < confirm_timeout:
                                try:
                                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                    for btn in all_buttons:
                                        if btn.text.strip() == "Confirm":
                                            log_print(f"[{serial_number}] [{task_label}] ✓ 找到Confirm按钮，点击...")
                                            btn.click()
                                            confirm_found = True
                                            break
                                    
                                    if confirm_found:
                                        break
                                    
                                    time.sleep(0.5)
                                except Exception as e:
                                    log_print(f"[{serial_number}] [{task_label}] ⚠ 查找Confirm按钮时出错: {str(e)}")
                                    time.sleep(0.5)
                            
                            if not confirm_found:
                                log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Confirm按钮")
                                cancel_status = "有挂单取消失败"
                            else:
                                # 等待10秒后重新检查挂单
                                log_print(f"[{serial_number}] [{task_label}] 等待10秒后重新检查挂单...")
                                time.sleep(10)
                                
                                # 重新获取open_orders_div
                                tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
                                open_orders_div = None
                                for div in tabs_divs:
                                    div_id = div.get_attribute('id')
                                    if div_id and 'openorders' in div_id.lower():
                                        open_orders_div = div
                                        break
                                
                                if not open_orders_div:
                                    log_print(f"[{serial_number}] [{task_label}] ✓ 挂单已取消（无Open Orders div）")
                                    cancel_status = "有挂单取消成功"
                                else:
                                    # 重新获取tbody和tr
                                    try:
                                        tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                                        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                                    except:
                                        log_print(f"[{serial_number}] [{task_label}] ✓ 挂单已取消（无tbody/tr）")
                                        cancel_status = "有挂单取消成功"
                                        tr_list = []
                                    
                                    if not tr_list or len(tr_list) == 0:
                                        log_print(f"[{serial_number}] [{task_label}] ✓ 挂单已取消（无tr）")
                                        cancel_status = "有挂单取消成功"
                                    else:
                                        log_print(f"[{serial_number}] [{task_label}] ⚠ 挂单仍然存在")
                                        cancel_status = "有挂单取消失败"
                except Exception as e:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 取消挂单操作时出错: {str(e)}")
                    cancel_status = "有挂单取消失败"
                    
    except Exception as e:
        log_print(f"[{serial_number}] [{task_label}] ⚠ 撤单逻辑执行时出错: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [{task_label}] 错误详情:\n{traceback.format_exc()}")
        cancel_status = "无挂单"  # 异常情况视为无挂单
    
    log_print(f"[{serial_number}] [{task_label}] 撤单状态: {cancel_status}")

    # 第三阶段：无论什么状态都要执行收集数据逻辑
    log_print(f"[{serial_number}] [{task_label}] ========== 第三阶段：收集数据 ==========")
    
    # 初始化数据变量
    current_position_amount = None
    position_change_value = None
    progress = ""
    has_error = False
    error_msg = ""
    
    try:
        # === 15分钟内循环检测仓位变化 ===
        log_print(f"[{serial_number}] [{task_label}] 开始15分钟仓位变化检测（每30秒检测一次，每90秒刷新页面）...")
        
        phase3_timeout = 900  # 15分钟
        phase3_check_interval = 30  # 30秒检测一次
        phase3_refresh_interval = 90  # 90秒刷新一次页面
        phase3_start_time = time.time()
        phase3_last_refresh_time = time.time()
        phase3_position_change_detected = False
        phase3_change_value = None
        
        while time.time() - phase3_start_time < phase3_timeout:
            try:
                elapsed = int(time.time() - phase3_start_time)
                log_print(f"[{serial_number}] [{task_label}] 第三阶段检测仓位（已用时 {elapsed}秒）...")
                
                # 检查是否需要刷新页面（每90秒刷新一次）
                if time.time() - phase3_last_refresh_time >= phase3_refresh_interval:
                    log_print(f"[{serial_number}] [{task_label}] 90秒已到，刷新页面...")
                    refresh_page_with_opinion_check(driver, serial_number)
                    phase3_last_refresh_time = time.time()
                    time.sleep(5)  # 等待页面加载
                
                # 记录本次检测的变化量
                local_change_amount = 0
                api_change_amount = 0
                local_position_valid = False
                api_position_valid = False
                current_position_local = None
                current_position_api = None
                
                if trade_type == "Buy":
                    # Buy类型：检查Position数量变化
                    # 方式1：本地抓取
                    log_print(f"[{serial_number}] [{task_label}] 点击Position按钮...")
                    position_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in position_buttons:
                        if btn.text.strip() == "Position":
                            btn.click()
                            time.sleep(7)
                            break
                    
                    current_position_count_local = check_position_count(driver, serial_number, trending_part1, trade_type, option_type)
                    
                    if current_position_count_local >= 0 and current_position_count_local != -2:
                        local_change_amount = abs(current_position_count_local - float(initial_position_count))
                        local_position_valid = True
                        current_position_local = current_position_count_local
                        log_print(f"[{serial_number}] [{task_label}] 本地仓位数量: {current_position_count_local} (初始: {initial_position_count}), 变化量: {local_change_amount}")
                    
                    # 方式2：链上API
                    if trending:
                        current_position_count_api = get_position_from_api(serial_number, trending, option_type)
                        if current_position_count_api is not None:
                            api_change_amount = abs(current_position_count_api - float(initial_position_count))
                            api_position_valid = True
                            current_position_api = current_position_count_api
                            log_print(f"[{serial_number}] [{task_label}] 链上仓位数量: {current_position_count_api} (初始: {initial_position_count}), 变化量: {api_change_amount}")
                
                else:
                    # Sell类型：检查已成交数量变化
                    # 方式1：本地抓取
                    log_print(f"[{serial_number}] [{task_label}] 点击Position按钮...")
                    position_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in position_buttons:
                        if btn.text.strip() == "Position":
                            btn.click()
                            time.sleep(7)
                            break
                    
                    current_filled_amount_local = get_position_filled_amount(driver, serial_number, trending_part1)
                    
                    if current_filled_amount_local:
                        try:
                            amount_str = ''.join(c for c in current_filled_amount_local if c.isdigit() or c == '.')
                            if amount_str:
                                current_filled_amount_float = float(amount_str)
                                local_change_amount = abs(current_filled_amount_float - float(initial_position_count))
                                local_position_valid = True
                                current_position_local = current_filled_amount_float
                                log_print(f"[{serial_number}] [{task_label}] 本地已成交数量: {current_filled_amount_float} (初始: {initial_position_count}), 变化量: {local_change_amount}")
                        except (ValueError, TypeError) as e:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 本地数量转换失败: {str(e)}")
                    
                    # 方式2：链上API
                    if trending:
                        current_filled_amount_api = get_position_from_api(serial_number, trending, option_type)
                        if current_filled_amount_api is not None:
                            api_change_amount = abs(current_filled_amount_api - float(initial_position_count))
                            api_position_valid = True
                            current_position_api = current_filled_amount_api
                            log_print(f"[{serial_number}] [{task_label}] 链上已成交数量: {current_filled_amount_api} (初始: {initial_position_count}), 变化量: {api_change_amount}")
                
                # 检查变化量是否满足条件（>=60%）
                if amount is not None:
                    amount_threshold = float(amount) * 0.6  # 下单量的60%
                    log_print(f"[{serial_number}] [{task_label}] 下单数量: {amount}, 60%阈值: {amount_threshold}")
                    log_print(f"[{serial_number}] [{task_label}] 本地变化量: {local_change_amount if local_position_valid else 'N/A'}")
                    log_print(f"[{serial_number}] [{task_label}] 链上变化量: {api_change_amount if api_position_valid else 'N/A'}")
                    
                    # 判断哪个数据源满足条件
                    local_meets_threshold = local_position_valid and local_change_amount >= amount_threshold
                    api_meets_threshold = api_position_valid and api_change_amount >= amount_threshold
                    
                    if local_meets_threshold or api_meets_threshold:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 仓位变化量满足条件（>=60%）！")
                        
                        # 选择使用哪个数据源（优先使用满足条件的，都满足则优先链上）
                        if api_meets_threshold:
                            current_position_amount = current_position_api
                            phase3_change_value = api_change_amount
                            log_print(f"[{serial_number}] [{task_label}] 使用链上数据: {current_position_amount}")
                        elif local_meets_threshold:
                            current_position_amount = current_position_local
                            phase3_change_value = local_change_amount
                            log_print(f"[{serial_number}] [{task_label}] 使用本地数据: {current_position_amount}")
                        
                        phase3_position_change_detected = True
                        break
                    else:
                        log_print(f"[{serial_number}] [{task_label}] 仓位变化量未达到60%阈值，继续检测...")
                else:
                    # 未提供下单数量，直接检查是否有变化
                    has_change = (local_position_valid and local_change_amount > 1) or (api_position_valid and api_change_amount > 1)
                    if has_change:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 未提供下单数量，但检测到仓位变化")
                        if api_position_valid:
                            current_position_amount = current_position_api
                            phase3_change_value = api_change_amount
                        elif local_position_valid:
                            current_position_amount = current_position_local
                            phase3_change_value = local_change_amount
                        phase3_position_change_detected = True
                        break
                    else:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 未提供下单数量，仓位无明显变化，继续检测...")
                
                # 等待下一次检测
                time.sleep(phase3_check_interval)
                
            except Exception as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 第三阶段检测仓位时出错: {str(e)}")
                time.sleep(phase3_check_interval)
        
        # 计算仓位变化值
        if current_position_amount is not None:
            try:
                initial_amount = float(initial_position_count)
                position_change_value = current_position_amount - initial_amount
                log_print(f"[{serial_number}] [{task_label}] 仓位变化值: {position_change_value} (当前: {current_position_amount}, 初始: {initial_amount})")
            except (ValueError, TypeError) as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 计算仓位变化值失败: {str(e)}")
        else:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 15分钟超时，无法获取满足条件的仓位数据")
        
        # 第二步：获取挂单进度（如果有）
        log_print(f"[{serial_number}] [{task_label}] 第二步：获取挂单进度...")
        try:
            # 点击Open Orders按钮
            open_orders_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in open_orders_buttons:
                if btn.text.strip() == "Open Orders":
                    btn.click()
                    time.sleep(7)
                    break
            
            # 查找 Open Orders div
            tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
            open_orders_div = None
            for div in tabs_divs:
                div_id = div.get_attribute('id')
                if div_id and 'openorders' in div_id.lower():
                    open_orders_div = div
                    break
            
            if open_orders_div:
                try:
                    tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                    tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    if tr_list and len(tr_list) > 0:
                        # 有挂单，获取进度
                        if trending_part1:
                            # 有子标题：找到包含子标题的tr
                            for tr in tr_list:
                                try:
                                    tds = tr.find_elements(By.TAG_NAME, "td")
                                    if len(tds) > 1:
                                        second_td_ps = tds[1].find_elements(By.TAG_NAME, "p")
                                        second_td_text = " ".join([p.text.strip() for p in second_td_ps])
                                        if trending_part1 in second_td_text:
                                            # 第6个td（index=5）：进度
                                            if len(tds) > 5:
                                                td6_ps = tds[5].find_elements(By.TAG_NAME, "p")
                                                progress = " ".join([p.text.strip() for p in td6_ps])
                                            break
                                except:
                                    continue
                        else:
                            # 无子标题：第一个tr
                            try:
                                first_tr = tr_list[0]
                                tds = first_tr.find_elements(By.TAG_NAME, "td")
                                # 第6个td（index=5）：进度
                                if len(tds) > 5:
                                    td6_ps = tds[5].find_elements(By.TAG_NAME, "p")
                                    progress = " ".join([p.text.strip() for p in td6_ps])
                            except:
                                pass
                        
                        if progress:
                            log_print(f"[{serial_number}] [{task_label}] 挂单进度: {progress}")
                except:
                    pass
            
            if not progress:
                log_print(f"[{serial_number}] [{task_label}] 无挂单或无法获取进度")
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 获取挂单进度失败: {str(e)}")
        
        # 第三步：获取交易费
        log_print(f"[{serial_number}] [{task_label}] 第三步：获取交易费...")
        transaction_fee = "未知"
        try:
            transaction_fee, price_from_fee, fee_check_success = check_transaction_fee(driver, serial_number, task_label, False, trade_type)
            log_print(f"[{serial_number}] [{task_label}] 交易费: {transaction_fee}, 检查结果: {'✓ 通过' if fee_check_success else '✗ 失败'}")
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 获取交易费失败: {str(e)}")
        
        # 构建返回消息
        position_change_str = str(position_change_value) if position_change_value is not None else "未知"
        progress_str = progress if progress else "无"
        transaction_fee_str = transaction_fee if transaction_fee else "未知"
        
        msg = f"{cancel_status},仓位变化值为:{position_change_str}, 挂单:{progress_str}, 手续费:{transaction_fee_str}"
        log_print(f"[{serial_number}] [{task_label}] 最终结果: {msg}")
        
        # 返回成功+已有数据
        return True, msg
        
    except Exception as e:
        log_print(f"[{serial_number}] [{task_label}] ✗ 收集数据时发生异常: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [{task_label}] 错误详情:\n{traceback.format_exc()}")
        
        # 异常情况：返回失败+已有数据
        position_change_str = str(position_change_value) if position_change_value is not None else "未知"
        progress_str = progress if progress else "无"
        msg = f"{cancel_status},仓位变化值为:{position_change_str}, 挂单:{progress_str}, 手续费:未知"
        return False, msg

def wait_for_opinion_order_success(driver, initial_open_orders_count, initial_position_count, trade_type, serial_number, trending_part1='', option_type='YES', timeout=600, trending='', amount=None, initial_closed_orders_time=''):
    """
    Type 1 任务专用：等待订单成功并收集数据（与 Type 5 流程一致）
    
    Args:
        driver: Selenium WebDriver对象
        initial_open_orders_count: 初始 Open Orders 行数
        initial_position_count: 初始 Position 行数（Buy时是tr数量，Sell时是实际持仓数量）
        trade_type: 交易类型（Buy/Sell）
        serial_number: 浏览器序列号
        trending_part1: 子标题（用于筛选）
        option_type: 期权类型（YES/NO）
        timeout: 超时时间（默认10分钟）
        trending: 完整的交易主题（用于API调用，可选）
        amount: 下单数量（可选，用于计算差额）
        initial_closed_orders_time: 初始 Closed Orders 最新时间（可选，用于检测挂单变化）
        
    Returns:
        tuple: (success, msg)
    """
    task_label = "Type1"
    
    log_print(f"[{serial_number}] [{task_label}] Type 1 专用等待流程开始...")
    log_print(f"[{serial_number}] [{task_label}] 交易类型: {trade_type}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Position 数量: {initial_position_count}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Open Orders 数量: {initial_open_orders_count}")
    log_print(f"[{serial_number}] [{task_label}] 初始 Closed Orders 最新时间: {initial_closed_orders_time}")
    
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
    
    # 第一阶段：检测Position变化（10分钟超时）
    if trade_type == "Buy":
        log_print(f"[{serial_number}] [{task_label}] ========== 第一阶段：检测Position数量增加 ==========")
    else:
        log_print(f"[{serial_number}] [{task_label}] ========== 第一阶段：检测Position已成交数量变化 ==========")
    
    phase1_timeout = 600  # 10分钟
    check_interval = 20 if trade_type == "Sell" else 60  # Sell每20秒检查，Buy每60秒检查
    refresh_interval = 120  # 每2分钟刷新一次
    
    phase1_start_time = time.time()
    last_refresh_time = phase1_start_time
    position_changed = False
    use_api_data = False  # 标记是否使用链上数据（如果链上数据先检测到变化，则后续使用链上数据）
    current_position_value = None  # 记录检测到变化时的当前数量
    
    # 对于Buy类型，如果使用链上数据，需要记录初始链上仓位数量
    initial_position_count_api = None
    if trade_type == "Buy" and trending:
        initial_position_count_api = get_position_from_api(serial_number, trending, option_type)
        if initial_position_count_api is not None:
            log_print(f"[{serial_number}] [{task_label}] 初始链上仓位数量: {initial_position_count_api}")
    
    while time.time() - phase1_start_time < phase1_timeout:
        try:
            elapsed = int(time.time() - phase1_start_time)
            log_print(f"[{serial_number}] [{task_label}] 检查Position（已用时 {elapsed}秒）...")
            
            # 对于Buy和Sell类型，每2分钟刷新
            if time.time() - last_refresh_time >= refresh_interval:
                log_print(f"[{serial_number}] [{task_label}] 2分钟无变化，刷新页面...")
                refresh_page_with_opinion_check(driver, serial_number)
                time.sleep(5)
                last_refresh_time = time.time()
            
            if trade_type == "Buy":
                # Buy类型：检查Position数量是否增加
                # 方式1：本地抓取
                current_position_count_local = check_position_count(driver, serial_number, trending_part1, trade_type, option_type)
                
                # 方式2：链上API（如果提供了trending参数）
                current_position_count_api = None
                if trending:
                    current_position_count_api = get_position_from_api(serial_number, trending, option_type)
                    if current_position_count_api is not None:
                        log_print(f"[{serial_number}] [{task_label}] 链上仓位数量: {current_position_count_api}")
                
                # 判断是否检测到变化，并记录是哪种方式先检测到的
                position_changed_detected = False
                local_detected = False
                api_detected = False
                
                # 检查本地数据（tr数量）
                if current_position_count_local == -2:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 检测到对向仓位，跳过本次检查")
                elif current_position_count_local >= 0:
                    log_print(f"[{serial_number}] [{task_label}] 本地持仓数量(tr): {current_position_count_local} (初始: {initial_position_count})")
                    # 本地数据需要大于 initial + 1 才算变化
                    if current_position_count_local > initial_position_count + 1:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 本地数据检测到持仓数量增加！")
                        local_detected = True
                        position_changed_detected = True
                        current_position_value = current_position_count_local
                
                # 检查链上数据（仓位数量）
                if current_position_count_api is not None and initial_position_count_api is not None:
                    log_print(f"[{serial_number}] [{task_label}] 链上持仓数量: {current_position_count_api} (初始: {initial_position_count_api})")
                    # 链上数据需要大于 initial + 1 才算变化（因为链上数据小数位数较多）
                    if current_position_count_api > initial_position_count_api + 1:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 链上数据检测到持仓数量增加！")
                        api_detected = True
                        position_changed_detected = True
                        if current_position_value is None:
                            current_position_value = current_position_count_api
                
                # 如果链上数据先检测到变化，标记后续使用链上数据
                if api_detected and not local_detected:
                    use_api_data = True
                    log_print(f"[{serial_number}] [{task_label}] 链上数据先检测到变化，后续将使用链上数据")
                
                if position_changed_detected:
                    position_changed = True
                    log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到持仓数量变化！当前数量: {current_position_value}")
                    break
                
                # Buy类型：Position未变化，检查Open Orders数量是否有变化
                if not position_changed_detected:
                    log_print(f"[{serial_number}] [{task_label}] Position未变化，检查Open Orders数量是否有变化...")
                    current_open_orders_count = get_opinion_table_row_count(driver, serial_number, need_click_open_orders=True, trending_part1=trending_part1)
                    
                    if current_open_orders_count < 0:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Open Orders 数量，设为 0")
                        current_open_orders_count = 0
                    
                    log_print(f"[{serial_number}] [{task_label}] 当前 Open Orders 数量: {current_open_orders_count} (初始: {initial_open_orders_count})")
                    
                    # 检查Open Orders数量是否有变化
                    if current_open_orders_count > initial_open_orders_count:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Open Orders数量变化！")
                        position_changed = True
                        break
                    else:
                        # Open Orders数量也未变化，检查Closed Orders时间
                        log_print(f"[{serial_number}] [{task_label}] Open Orders数量未变化，检查Closed Orders时间是否有变化...")
                        current_closed_orders_time = get_closed_orders_latest_time(driver, serial_number)
                        
                        if not current_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Closed Orders 时间")
                            current_closed_orders_time = ""
                        
                        log_print(f"[{serial_number}] [{task_label}] 当前 Closed Orders 最新时间: {current_closed_orders_time} (初始: {initial_closed_orders_time})")
                        
                        # 检查Closed Orders时间是否有变化
                        if current_closed_orders_time and current_closed_orders_time != initial_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Closed Orders时间变化！")
                            position_changed = True
                            break
            else:
                # Sell类型：检查已成交数量是否变化
                # 方式1：本地抓取
                current_filled_amount_local = get_position_filled_amount(driver, serial_number, trending_part1)
                
                # 方式2：链上API（如果提供了trending参数）
                current_filled_amount_api = None
                if trending:
                    current_filled_amount_api = get_position_from_api(serial_number, trending, option_type)
                    if current_filled_amount_api is not None:
                        log_print(f"[{serial_number}] [{task_label}] 链上已成交数量: {current_filled_amount_api}")
                
                # 判断是否检测到变化，并记录是哪种方式先检测到的
                position_changed_detected = False
                local_detected = False
                api_detected = False
                
                # 检查本地数据
                if current_filled_amount_local:
                    log_print(f"[{serial_number}] [{task_label}] 本地已成交数量: {current_filled_amount_local} (初始: {initial_position_count})")
                    # 处理文本：去掉逗号并转换为数字，与initial_position_count比较
                    try:
                        # 移除逗号和其他非数字字符，只保留数字和小数点
                        amount_str = ''.join(c for c in current_filled_amount_local if c.isdigit() or c == '.')
                        if amount_str:
                            current_filled_amount_float = float(amount_str)
                            # 链上数据需要大于1才算变化
                            if abs(current_filled_amount_float - float(initial_position_count)) > 1:
                                log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 本地数据检测到已成交数量变化！")
                                local_detected = True
                                position_changed_detected = True
                                current_position_value = current_filled_amount_float
                            else:
                                log_print(f"[{serial_number}] [{task_label}] 本地已成交数量未变化")
                        else:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 无法从文本中提取数字: {current_filled_amount_local}")
                    except (ValueError, TypeError) as e:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 数量转换失败: {current_filled_amount_local}, 错误: {str(e)}")
                else:
                    log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取本地已成交数量")
                
                # 检查链上数据
                if current_filled_amount_api is not None:
                    log_print(f"[{serial_number}] [{task_label}] 链上已成交数量: {current_filled_amount_api} (初始: {initial_position_count})")
                    # 链上数据需要大于1才算变化
                    if abs(current_filled_amount_api - float(initial_position_count)) > 1:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 链上数据检测到已成交数量变化！")
                        api_detected = True
                        position_changed_detected = True
                        if current_position_value is None:
                            current_position_value = current_filled_amount_api
                
                # 如果链上数据先检测到变化，标记后续使用链上数据
                if api_detected and not local_detected:
                    use_api_data = True
                    log_print(f"[{serial_number}] [{task_label}] 链上数据先检测到变化，后续将使用链上数据")
                
                if position_changed_detected:
                    position_changed = True
                    log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到已成交数量变化！当前数量: {current_position_value}")
                    break
                
                # Sell类型：Position未变化，检查Open Orders数量是否有变化
                if not position_changed_detected:
                    log_print(f"[{serial_number}] [{task_label}] Position未变化，检查Open Orders数量是否有变化...")
                    current_open_orders_count = get_opinion_table_row_count(driver, serial_number, need_click_open_orders=True, trending_part1=trending_part1)
                    
                    if current_open_orders_count < 0:
                        log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Open Orders 数量，设为 0")
                        current_open_orders_count = 0
                    
                    log_print(f"[{serial_number}] [{task_label}] 当前 Open Orders 数量: {current_open_orders_count} (初始: {initial_open_orders_count})")
                    
                    # 检查Open Orders数量是否有变化
                    if current_open_orders_count > initial_open_orders_count:
                        log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Open Orders数量变化！")
                        position_changed = True
                        break
                    else:
                        # Open Orders数量也未变化，检查Closed Orders时间
                        log_print(f"[{serial_number}] [{task_label}] Open Orders数量未变化，检查Closed Orders时间是否有变化...")
                        current_closed_orders_time = get_closed_orders_latest_time(driver, serial_number)
                        
                        if not current_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ⚠ 无法获取当前 Closed Orders 时间")
                            current_closed_orders_time = ""
                        
                        log_print(f"[{serial_number}] [{task_label}] 当前 Closed Orders 最新时间: {current_closed_orders_time} (初始: {initial_closed_orders_time})")
                        
                        # 检查Closed Orders时间是否有变化
                        if current_closed_orders_time and current_closed_orders_time != initial_closed_orders_time:
                            log_print(f"[{serial_number}] [{task_label}] ✓✓✓ 检测到Closed Orders时间变化！")
                            position_changed = True
                            break
            
            time.sleep(check_interval)
            
        except Exception as e:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 检查Position时出错: {str(e)}")
            time.sleep(check_interval)
    
    # 第二阶段：获取Position和Open Orders的详细数据（与Type 5一致）
    log_print(f"[{serial_number}] [{task_label}] ========== 第二阶段：收集数据 ==========")
    
    # 如果Position未检测到变化，超时，需要检查Open Orders
    position_timeout = not position_changed
    if position_timeout:
        log_print(f"[{serial_number}] [{task_label}] ✗ Position未检测到变化，超时，将检查Open Orders")
        return False,"挂单失败!10分钟未检测到挂单或仓位变化"
    
    try:
        filled_amount = ""
        filled_price = ""
        
        # 如果Position超时，跳过获取Position数据，直接检查Open Orders
        if position_timeout:
            log_print(f"[{serial_number}] [{task_label}] Position超时，跳过获取Position数据，直接检查Open Orders")
        # 如果前面是链上数据先检测到变化，直接使用链上数据，跳过本地抓取
        elif use_api_data and trending:
            log_print(f"[{serial_number}] [{task_label}] 前面链上数据先检测到变化，直接使用链上数据...")
            api_position_amount = get_position_from_api(serial_number, trending, option_type)
            if api_position_amount is not None:
                filled_amount = str(api_position_amount)
                filled_price = "--"
                log_print(f"[{serial_number}] [{task_label}] 链上数据 - 已成交数量: {filled_amount}, 价格: {filled_price}")
            else:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 获取链上数据失败，改用本地抓取")
                use_api_data = False  # 如果链上数据获取失败，改用本地抓取
        
        # 如果使用本地数据，进行本地抓取（且不是超时情况）
        if not position_timeout and not use_api_data:
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
        
        # 计算差额，如果差额绝对值小于5，跳过获取Open Orders数据
        skip_open_orders = False
        if amount is not None and filled_amount:
            try:
                # 将 filled_amount 转换为数字（处理可能包含逗号的情况）
                filled_amount_str = str(filled_amount).replace(',', '').strip()
                # 处理 "<0.01" 这种情况
                if '<' in filled_amount_str:
                    filled_amount_float = 0.0
                else:
                    filled_amount_float = float(filled_amount_str)
                
                # 计算变化值：filled_amount - initial_position_count
                position_change = filled_amount_float - float(initial_position_count)
                # 获取变化值的绝对值
                position_change_abs = abs(position_change)
                
                # 计算差额：下单数量 - 变化值
                difference = float(amount) - position_change_abs
                difference_abs = abs(difference)
                
                log_print(f"[{serial_number}] [{task_label}] 差额计算:")
                log_print(f"[{serial_number}] [{task_label}]   下单数量: {amount}")
                log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount_float}")
                log_print(f"[{serial_number}] [{task_label}]   初始数量: {initial_position_count}")
                log_print(f"[{serial_number}] [{task_label}]   变化值: {position_change} (绝对值: {position_change_abs})")
                log_print(f"[{serial_number}] [{task_label}]   差额: {difference} (绝对值: {difference_abs})")
                
                # 计算下单数量的10%作为阈值
                amount_threshold = float(amount) * 0.4
                log_print(f"[{serial_number}] [{task_label}]   下单数量的10%: {amount_threshold}")
                
                # 如果差额绝对值小于下单数量的10%，跳过获取Open Orders数据
                if difference_abs < amount_threshold:
                    log_print(f"[{serial_number}] [{task_label}] ✓ 差额绝对值 ({difference_abs}) < 下单数量的10% ({amount_threshold})，跳过获取Open Orders数据")
                    skip_open_orders = True
                else:
                    log_print(f"[{serial_number}] [{task_label}] 差额绝对值 ({difference_abs}) >= 下单数量的10% ({amount_threshold})，继续获取Open Orders数据")
            except (ValueError, TypeError) as e:
                log_print(f"[{serial_number}] [{task_label}] ⚠ 计算差额时出错: {str(e)}，继续获取Open Orders数据")
        
        # 如果跳过Open Orders，直接返回成功
        if skip_open_orders:
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, False, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE1_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            return True, msg
        
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
            if div_id and 'openorders' in div_id.lower():
                open_orders_div = div
                break
        
        if not open_orders_div:
            log_print(f"[{serial_number}] [{task_label}] ⚠ 未找到Open Orders div")
            
            # 没找到div，检查 Transactions
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, False, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE1_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            return True, msg
        
        # 获取 tbody 和 tr
        try:
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        except:
            # 没有tbody或tr，说明没有挂单
            # 如果是Position超时，返回失败消息
            if position_timeout:
                log_print(f"[{serial_number}] [{task_label}] ✗ 检测仓位超时，且无挂单")
                return False, "检测仓位超时，且无挂单"
            
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, False, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE1_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            return True, msg
        
        if not tr_list or len(tr_list) == 0:
            
            transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, False, trade_type)
            
            import json
            msg_data = {
                "type": "TYPE1_SUCCESS",
                "filled_amount": filled_amount,
                "filled_price": filled_price,
                "transaction_fee": transaction_fee
            }
            
            # Sell类型添加原数量
            if trade_type == "Sell":
                msg_data["initial_filled_amount"] = str(initial_position_count)
            
            msg = json.dumps(msg_data, ensure_ascii=False)
            
            log_print(f"[{serial_number}] [{task_label}] 结果详情:")
            if trade_type == "Sell":
                log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
            log_print(f"[{serial_number}] [{task_label}]   已成交数量: {filled_amount}")
            log_print(f"[{serial_number}] [{task_label}]   成交价格: {filled_price}")
            log_print(f"[{serial_number}] [{task_label}]   交易费: {transaction_fee}")
            log_print(f"[{serial_number}] [{task_label}]   交易费检查: {'✓ 通过' if fee_check_success else '✗ 失败'}")
            
            return True, msg

        
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
        transaction_fee, filled_price, fee_check_success = check_transaction_fee(driver, serial_number, task_label, False, trade_type)
        
        # 有挂单，任务失败
        import json
        msg_data = {
            "type": "TYPE1_PARTIAL",
            "filled_amount": filled_amount,
            "filled_price": filled_price,
            "pending_price": pending_price,
            "progress": progress,
            "transaction_fee": transaction_fee
        }
        
        # Sell类型添加原数量
        if trade_type == "Sell":
            msg_data["initial_filled_amount"] = str(initial_position_count)
        
        msg = json.dumps(msg_data, ensure_ascii=False)
        log_print(f"[{serial_number}] [{task_label}] ✗ 有挂单，任务失败")
        log_print(f"[{serial_number}] [{task_label}] 结果详情:")
        if trade_type == "Sell":
            log_print(f"[{serial_number}] [{task_label}]   原数量: {initial_position_count}")
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


# ============================================================================
# Polymarket 特定函数
# ============================================================================

def check_driver_session_valid(driver, serial_number):
    """
    检查driver会话是否有效
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        bool: 会话有效返回True，否则返回False
    """
    try:
        # 尝试获取当前窗口句柄，如果会话失效会抛出异常
        _ = driver.current_window_handle
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid session id" in error_msg or "session not created" in error_msg or "no such window" in error_msg:
            log_print(f"[{serial_number}] ⚠ Driver会话已失效: {str(e)}")
            return False
        # 其他异常可能是正常的，返回True
        return True


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
                refresh_page_with_opinion_check(driver, serial_number)
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

def add_bro_log_entry(log_list, browser_id, log_message):
    """
    添加日志条目到日志列表
    
    Args:
        log_list: 日志列表
        browser_id: 浏览器编号
        log_message: 日志消息
    """
    current_time_ms = int(time.time() * 1000)  # 毫秒时间戳
    log_entry = {
        "number": str(browser_id),
        "time": current_time_ms,
        "log": log_message
    }
    log_list.append(log_entry)


def upload_bro_logs(log_list, browser_id):
    """
    上传日志到服务器
    
    Args:
        log_list: 日志列表
        browser_id: 浏览器编号（用于日志输出）
    
    Returns:
        bool: 上传成功返回True，失败返回False
    """
    if not log_list:
        return True
    
    try:
        url = f"{SERVER_BASE_URL}/bro/addBroLog"
        payload = {"list": log_list}
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                log_print(f"[{browser_id}] ✓ 日志上传成功，共 {len(log_list)} 条")
                return True
            else:
                msg = result.get("msg", "未知错误")
                log_print(f"[{browser_id}] ✗ 日志上传失败: {msg}")
                return False
        else:
            log_print(f"[{browser_id}] ✗ 日志上传失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 日志上传异常: {str(e)}")
        return False


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
    # 初始化日志列表
    bro_log_list = []
    
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
    trendingId = mission.get("trendingId", "")
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
    
    # 记录开始日志
    start_log_message = f"[0]开始处理交易任务{exchange_type}，任务ID: {mission_id} 交易所: {exchange_name} 买卖类型: {trade_type} 价格类型: {price_type} 种类: {option_type}页面URL: {target_url} 价格: {price if price else '市价'} 数量: {amount}"
    add_bro_log_entry(bro_log_list, browser_id, start_log_message)
    
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
    current_ip = None
    current_delay = None
    
    try:
        # 1. 检查IP并更新代理（仅在第一次进入且需要启动浏览器时更新，重试时跳过因为已经在重试流程中更新过了）
        if retry_count == 0:
            # 第一次进入，检查浏览器是否已经运行
            add_bro_log_entry(bro_log_list, browser_id, "[0]步骤1: 启动浏览器")
            log_print(f"[{browser_id}] 步骤1: 检查浏览器状态...")
            is_active, browser_data = check_browser_active(browser_id)
            
            if is_active and browser_data:
                add_bro_log_entry(bro_log_list, browser_id, "[0]浏览器已在运行，直接使用")
                log_print(f"[{browser_id}] ✓ 浏览器已在运行，直接使用")
                is_new_browser = False
                # 从 LAST_PROXY_CONFIG 获取当前使用的IP和延迟
                last_config = LAST_PROXY_CONFIG.get(str(browser_id))
                if last_config:
                    current_ip = last_config.get("ip")
                    current_delay = last_config.get("delay")
                    add_bro_log_entry(bro_log_list, browser_id, f"[0]使用已存在的代理配置: IP={current_ip}, Delay={current_delay}")
                    log_print(f"[{browser_id}] 使用已存在的代理配置: IP={current_ip}, Delay={current_delay}")
                else:
                    log_print(f"[{browser_id}] ⚠ 无法从 LAST_PROXY_CONFIG 获取IP信息，尝试更新...")
                    _, current_ip, current_delay = try_update_ip_before_start(browser_id, bro_log_list, mission_id=mission_id)
                    if current_ip:
                        add_bro_log_entry(bro_log_list, browser_id, f"[0]更新IP完成: IP={current_ip}, Delay={current_delay}")
            else:
                # 浏览器未运行，需要更新IP并启动浏览器
                add_bro_log_entry(bro_log_list, browser_id, "[0]步骤2: 检查IP并更新代理")
                log_print(f"[{browser_id}] 步骤2: 检查IP并更新代理...")
                _, current_ip, current_delay = try_update_ip_before_start(browser_id, bro_log_list, mission_id=mission_id)
    
                
                # 3. 启动浏览器
                add_bro_log_entry(bro_log_list, browser_id, "[0]步骤3: 启动浏览器")
                log_print(f"[{browser_id}] 步骤3: 启动浏览器...")
                browser_data = start_adspower_browser(browser_id)
                
                if not browser_data:
                    add_bro_log_entry(bro_log_list, browser_id, "[0]浏览器启动失败，任务终止")
                    log_print(f"[{browser_id}] ✗ 浏览器启动失败，任务终止")
                    if keep_browser_open:
                        return False, "[1]浏览器启动失败", None, None, None, None
                    else:
                        return False, "[1]浏览器启动失败"
                
                is_new_browser = True
                add_bro_log_entry(bro_log_list, browser_id, "[0]浏览器已新启动")
                log_print(f"[{browser_id}] ✓ 浏览器已新启动")
        else:
            log_print(f"[{browser_id}] 步骤1: 跳过IP更新（重试中，IP已在重试流程中更新）...")
            # 从 LAST_PROXY_CONFIG 获取当前使用的IP和延迟
            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
            if last_config:
                current_ip = last_config.get("ip")
                current_delay = last_config.get("delay")
                add_bro_log_entry(bro_log_list, browser_id, f"[0]使用已更新的代理配置: IP={current_ip}, Delay={current_delay}")
                log_print(f"[{browser_id}] 使用已更新的代理配置: IP={current_ip}, Delay={current_delay}")
            else:
                log_print(f"[{browser_id}] ⚠ 无法从 LAST_PROXY_CONFIG 获取IP信息，尝试更新...")
                _, current_ip, current_delay = try_update_ip_before_start(browser_id, bro_log_list, mission_id=mission_id)
                if current_ip:
                    add_bro_log_entry(bro_log_list, browser_id, f"[0]更新IP完成: IP={current_ip}, Delay={current_delay}")
            
            # 检查浏览器状态（重试时浏览器应该已关闭，需要重新启动）
            add_bro_log_entry(bro_log_list, browser_id, "[0]步骤2: 检查浏览器状态")
            log_print(f"[{browser_id}] 步骤2: 检查浏览器状态...")
            is_active, browser_data = check_browser_active(browser_id)
            
            if is_active and browser_data:
                add_bro_log_entry(bro_log_list, browser_id, "[0]浏览器已在运行，直接使用")
                log_print(f"[{browser_id}] ✓ 浏览器已在运行，直接使用")
                is_new_browser = False
            else:
                # 启动浏览器
                add_bro_log_entry(bro_log_list, browser_id, "[0]步骤3: 启动浏览器")
                log_print(f"[{browser_id}] 步骤3: 启动浏览器...")
                browser_data = start_adspower_browser(browser_id)
                
                if not browser_data:
                    add_bro_log_entry(bro_log_list, browser_id, "[0]浏览器启动失败，任务终止")
                    log_print(f"[{browser_id}] ✗ 浏览器启动失败，任务终止")
                    if keep_browser_open:
                        return False, "[1]浏览器启动失败", None, None, None, None
                    else:
                        return False, "[1]浏览器启动失败"
                
                is_new_browser = True
                add_bro_log_entry(bro_log_list, browser_id, "[0]浏览器已新启动")
                log_print(f"[{browser_id}] ✓ 浏览器已新启动")
        
        # 确保 current_ip 和 current_delay 已初始化（用于后续代码使用）
        if current_ip is None:
            log_print(f"[{browser_id}] ⚠ current_ip 为 None，尝试从 LAST_PROXY_CONFIG 获取...")
            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
            if last_config:
                current_ip = last_config.get("ip")
                current_delay = last_config.get("delay")
        
        # 4. 创建Selenium驱动
        add_bro_log_entry(bro_log_list, browser_id, "[0]步骤4: 创建Selenium驱动")
        log_print(f"[{browser_id}] 步骤4: 创建Selenium驱动...")
        driver = None
        driver_created = False
        last_driver_error = None
        
        # 第一次尝试创建驱动
        try:
            driver = create_selenium_driver(browser_data)
            driver_created = True
            add_bro_log_entry(bro_log_list, browser_id, "[0]Selenium驱动创建成功")
            log_print(f"[{browser_id}] ✓ Selenium驱动创建成功")
        except Exception as e:
            last_driver_error = e
            error_msg = str(e)
            add_bro_log_entry(bro_log_list, browser_id, f"[0]创建Selenium驱动失败: {error_msg}")
            log_print(f"[{browser_id}] ✗ 创建Selenium驱动失败: {error_msg}")
            log_print(f"[{browser_id}] 等待3秒后重试...")
            time.sleep(3)
            
            # 重试一次
            try:
                driver = create_selenium_driver(browser_data)
                driver_created = True
                add_bro_log_entry(bro_log_list, browser_id, "[0]Selenium驱动创建成功（重试）")
                log_print(f"[{browser_id}] ✓ Selenium驱动创建成功（重试）")
            except Exception as e2:
                last_driver_error = e2
                error_msg2 = str(e2)
                add_bro_log_entry(bro_log_list, browser_id, f"[0]创建Selenium驱动重试失败: {error_msg2}")
                log_print(f"[{browser_id}] ✗ 创建Selenium驱动重试失败: {error_msg2}")
        
        # 如果两次都失败，返回错误
        if not driver_created:
            error_message = "[1]浏览器启动失败，注意检测该浏览器是否已卡死"
            add_bro_log_entry(bro_log_list, browser_id, error_message)
            log_print(f"[{browser_id}] ✗ {error_message}")
            if keep_browser_open:
                return False, error_message, None, None, None, None
            else:
                return False, error_message
        
        # 4.5 等待4秒后再进入目标页面
        add_bro_log_entry(bro_log_list, browser_id, "[1]等待15秒后进入目标页面")
        log_print(f"[{browser_id}] 等待4秒...")
        time.sleep(15)
        
        # 5. 打开目标页面（带重试机制）
        add_bro_log_entry(bro_log_list, browser_id, f"[1] 打开目标页面 {target_url}")
        log_print(f"[{browser_id}] 步骤5: 打开目标页面")
        page_load_success = False
        last_error = None
        max_page_retries = 3
        
        for page_retry in range(1, max_page_retries + 1):
            try:
                if page_retry > 1:
                    add_bro_log_entry(bro_log_list, browser_id, f"[1]重试打开页面 (第 {page_retry}/{max_page_retries} 次)")
                    log_print(f"[{browser_id}] 重试打开页面 (第 {page_retry}/{max_page_retries} 次)...")
                    time.sleep(2)  # 重试前等待2秒
                driver.get(target_url)
                page_load_success = True
                add_bro_log_entry(bro_log_list, browser_id, "[1]页面加载成功")
                log_print(f"[{browser_id}] ✓ 页面加载成功")
                break
            except (WebDriverException, TimeoutException) as e:
                last_error = e
                error_msg = str(e)
                add_bro_log_entry(bro_log_list, browser_id, f"[1]打开页面失败 (第 {page_retry}/{max_page_retries} 次): {error_msg}")
                log_print(f"[{browser_id}] ✗ 打开页面失败 (第 {page_retry}/{max_page_retries} 次): {error_msg}")
                
                # 如果还有重试机会，继续循环
                if page_retry < max_page_retries:
                    continue
                else:
                    # 3次都失败了，记录最后错误并跳出循环
                    add_bro_log_entry(bro_log_list, browser_id, f"[1]页面加载失败，已重试 {max_page_retries} 次")
                    log_print(f"[{browser_id}] ✗ 页面加载失败，已重试 {max_page_retries} 次")
        
        # 如果页面加载失败（3次重试都失败），执行换IP重试（仅type=5任务且未重试过）
        if not page_load_success:
                error_msg = str(last_error) if last_error else "未知错误"
                add_bro_log_entry(bro_log_list, browser_id, f"[1]检测到页面加载错误（代理或超时）: {error_msg}")
                log_print(f"[{browser_id}] ✗ 检测到页面加载错误（代理或超时）: {error_msg}")
                mission_type = mission.get("type")
                if mission_type == 5 and retry_count < 2:
                    add_bro_log_entry(bro_log_list, browser_id, f"[1]Type=5 任务页面加载失败，需要换IP重试（第{retry_count+1}次），开始执行重试流程")
                    log_print(f"[{browser_id}] Type=5 任务页面加载失败，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                    
                    # 1. 关闭浏览器
                    add_bro_log_entry(bro_log_list, browser_id, "[1]步骤1: 关闭浏览器")
                    log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                    try:
                        if driver:
                            driver.quit()
                    except:
                        pass
                    close_adspower_browser(browser_id)
                    add_bro_log_entry(bro_log_list, browser_id, "[1]Type=5 任务换IP：关闭浏览器后等待1分钟")
                    log_print(f"[{browser_id}] Type=5 任务换IP：关闭浏览器后等待1分钟...")
                    time.sleep(60)  # Type=5任务等待2分钟
                    
                    # 2. 根据重试次数获取IP
                    add_bro_log_entry(bro_log_list, browser_id, f"[1]步骤2: 更换IP（第{retry_count+1}次）")
                    log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                    proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                    
                    if not proxy_config:
                        add_bro_log_entry(bro_log_list, browser_id, "[1]获取新IP失败")
                        log_print(f"[{browser_id}] ✗ 获取新IP失败")
                        if keep_browser_open:
                            return False, "[2]换IP失败", None, None, None, None
                        else:
                            return False, "[2]换IP失败"
                    
                    add_bro_log_entry(bro_log_list, browser_id, f"[1]获取新IP: {proxy_config['ip']}")
                    log_print(f"[{browser_id}] ✓ 获取新IP: {proxy_config['ip']}")
                    
                    # 3. 更新代理配置
                    add_bro_log_entry(bro_log_list, browser_id, "[1]步骤3: 更新代理配置")
                    log_print(f"[{browser_id}] 步骤3: 更新代理配置...")
                    if not update_adspower_proxy(browser_id, proxy_config):
                        add_bro_log_entry(bro_log_list, browser_id, "[1]更新代理失败")
                        log_print(f"[{browser_id}] ✗ 更新代理失败")
                        if keep_browser_open:
                            return False, "[2]更新代理失败", None, None, None, None
                        else:
                            return False, "[2]更新代理失败"
                    
                    add_bro_log_entry(bro_log_list, browser_id, "[1]代理配置已更新")
                    log_print(f"[{browser_id}] ✓ 代理配置已更新")
                    time.sleep(10)
                    
                    # 4. 递归重试任务（retry_count+1）
                    add_bro_log_entry(bro_log_list, browser_id, f"[1]步骤4: 重新执行任务（重试次数: {retry_count+1}）")
                    log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                    return process_trading_mission(task_data, keep_browser_open, retry_count=retry_count+1)
                else:
                    # 不是type=5任务或已重试过2次，直接抛出错误
                    raise last_error
        
        # 5.5 检查并点击 "I Understand and Agree" p标签（如果存在）
        add_bro_log_entry(bro_log_list, browser_id, "[2]步骤5.5: 检查是否存在 'I Understand and Agree' p标签")
        log_print(f"[{browser_id}] 步骤5.5: 检查是否存在 'I Understand and Agree' p标签...")
        if check_and_click_understand_agree(driver, browser_id, timeout=5):
            # 如果存在并点击了，需要换IP重试（仅type=5任务且重试次数小于2）
            mission_type = mission.get("type")
            if mission_type == 5 and retry_count < 2:
                add_bro_log_entry(bro_log_list, browser_id, f"[2]交易任务检测到 'I Understand and Agree'，需要换IP重试（第{retry_count+1}次），开始执行重试流程")
                log_print(f"[{browser_id}] Type=5 任务检测到 'I Understand and Agree'，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                
                # 获取 current_ip（如果未定义，从 LAST_PROXY_CONFIG 获取）
                ip_to_report = current_ip
                if not ip_to_report:
                    last_config = LAST_PROXY_CONFIG.get(str(browser_id))
                    if last_config:
                        ip_to_report = last_config.get("ip")
                
                # 调用 changeIpToErr 接口
                call_change_ip_to_err(browser_id, ip_to_report)
                
                # 1. 关闭浏览器
                add_bro_log_entry(bro_log_list, browser_id, "[2]步骤1: 关闭浏览器")
                log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                try:
                    if driver:
                        driver.quit()
                except:
                    pass
                close_adspower_browser(browser_id)
                add_bro_log_entry(bro_log_list, browser_id, "[2]Type=5 任务换IP：关闭浏览器后等待1分钟")
                log_print(f"[{browser_id}] Type=5 任务换IP：关闭浏览器后等待1分钟...")
                time.sleep(60)  # Type=5任务等待2分钟
                
                # 2. 根据重试次数获取IP
                add_bro_log_entry(bro_log_list, browser_id, f"[2]步骤2: 更换IP（第{retry_count+1}次）")
                log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                
                if not proxy_config:
                    add_bro_log_entry(bro_log_list, browser_id, "[2]获取新IP失败")
                    log_print(f"[{browser_id}] ✗ 获取新IP失败")
                    if keep_browser_open:
                        return False, "[2]换IP失败", None, None, None, None
                    else:
                        return False, "[2]换IP失败"
                
                add_bro_log_entry(bro_log_list, browser_id, f"[2]获取新IP: {proxy_config['ip']}")
                log_print(f"[{browser_id}] ✓ 获取新IP: {proxy_config['ip']}")
                
                # 3. 更新代理配置
                add_bro_log_entry(bro_log_list, browser_id, "[2]步骤3: 更新代理配置")
                log_print(f"[{browser_id}] 步骤3: 更新代理配置...")
                if not update_adspower_proxy(browser_id, proxy_config):
                    add_bro_log_entry(bro_log_list, browser_id, "[2]更新代理失败")
                    log_print(f"[{browser_id}] ✗ 更新代理失败")
                    if keep_browser_open:
                        return False, "[2]更新代理失败", None, None, None, None
                    else:
                        return False, "[2]更新代理失败"
                
                add_bro_log_entry(bro_log_list, browser_id, "[2]代理配置已更新")
                log_print(f"[{browser_id}] ✓ 代理配置已更新")
                time.sleep(10)
                
                # 4. 递归重试任务（retry_count+1）
                add_bro_log_entry(bro_log_list, browser_id, f"[2]步骤4: 重新执行任务（重试次数: {retry_count+1}）")
                log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                return process_trading_mission(task_data, keep_browser_open, retry_count=retry_count+1)
        
        # 根据交易所类型选择不同的处理流程
        add_bro_log_entry(bro_log_list, browser_id, f"[3]步骤6: 开始处理{exchange_type}交易流程")
        if exchange_type == "OP":
            success, failure_reason, available_balance = process_opinion_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, trending_part1, task_data, retry_count, trending, target_url, current_ip, current_delay, bro_log_list, trendingId)
        else:
            success, failure_reason = process_polymarket_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, current_ip, current_delay)
            available_balance = None  # Polymarket 暂不支持
        
        if success:
            add_bro_log_entry(bro_log_list, browser_id, f"[11]交易流程处理成功")
        else:
            add_bro_log_entry(bro_log_list, browser_id, f"[根据上一条]交易流程处理失败: {failure_reason}")
        
        # 处理 available_balance 并更新 p 字段
        if available_balance is not None:
            try:
                # 提取数字和小数点，去掉其他所有字符
                cleaned_balance = re.sub(r'[^\d.]', '', str(available_balance))
                
                # 尝试转换为数字
                if cleaned_balance:
                    numeric_balance = float(cleaned_balance)
              
                    log_print(f"[{browser_id}] 提取到可用余额: {numeric_balance}")
                    
                    # 更新浏览器配置的 p 字段
                    log_print(f"[{browser_id}] 更新浏览器配置的 p 字段...")
                    
                    # 1. 获取现有配置
                    get_url = f"{SERVER_BASE_URL}/boost/findAccountConfigByNo"
                    params = {"no": browser_id, "computeGroup": COMPUTER_GROUP}
                    
                    response = requests.get(get_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result and result.get('data'):
                            account_config = result['data']
                            
                            # 2. 更新 p 字段为转化后的正确数字
                            account_config['p'] = str(numeric_balance)
                            
                  
                            log_print(f"[{browser_id}] 更新 p 字段: {numeric_balance}")
                            
                            # 3. 上传更新（带重试机制）
                            success_upload, result_upload, error_msg = upload_account_config_with_retry(
                                account_config, 
                                browser_id=browser_id, 
                                timeout=10
                            )
                            
                            if success_upload:
                                log_print(f"[{browser_id}] ✓ p 字段更新成功")
                            else:
                                log_print(f"[{browser_id}] ✗ 上传 p 字段失败: {error_msg}")
                        else:
                            log_print(f"[{browser_id}] ⚠ 账户配置不存在，跳过更新 p 字段")
                    else:
                
                        log_print(f"[{browser_id}] ✗ 获取账户配置失败: HTTP {response.status_code}")
                else:
                   
                    log_print(f"[{browser_id}] ⚠ available_balance 提取后为空，跳过更新")
            except ValueError:
             
                log_print(f"[{browser_id}] ⚠ available_balance 无法转换为数字: {available_balance}")
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 更新 p 字段异常: {str(e)}")
        
        # 检查是否需要换IP重试（仅type=5或type=1任务且重试次数小于2）
        if not success and failure_reason == "NEED_IP_RETRY" and retry_count < 2:
            mission_type = mission.get("type")
            if mission_type == 5 or mission_type == 1:
                add_bro_log_entry(bro_log_list, browser_id, f"[8]Type={mission_type} 任务需要换IP重试（第{retry_count+1}次），开始执行重试流程")
                log_print(f"[{browser_id}] Type={mission_type} 任务需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                
                # 1. 关闭浏览器
                add_bro_log_entry(bro_log_list, browser_id, "[8]步骤1: 关闭浏览器")
                log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                try:
                    if driver:
                        driver.quit()
                except:
                    pass
                close_adspower_browser(browser_id)
                time.sleep(15)
                
                # 2. 根据重试次数获取IP
                add_bro_log_entry(bro_log_list, browser_id, f"[8]步骤2: 更换IP（第{retry_count+1}次）")
                log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                
                if not proxy_config:
                    add_bro_log_entry(bro_log_list, browser_id, "[8]获取新IP失败")
                    log_print(f"[{browser_id}] ✗ 获取新IP失败")
                    if keep_browser_open:
                        return False, "[2]换IP失败", None, None, None, None
                    else:
                        return False, "[2]换IP失败"
                
                add_bro_log_entry(bro_log_list, browser_id, f"[8]获取新IP: {proxy_config['ip']}")
                log_print(f"[{browser_id}] ✓ 获取新IP: {proxy_config['ip']}")
                
                # 3. 更新代理配置
                add_bro_log_entry(bro_log_list, browser_id, "[8]步骤3: 更新代理配置")
                log_print(f"[{browser_id}] 步骤3: 更新代理配置...")
                if not update_adspower_proxy(browser_id, proxy_config):
                    add_bro_log_entry(bro_log_list, browser_id, "[8]更新代理失败")
                    log_print(f"[{browser_id}] ✗ 更新代理失败")
                    if keep_browser_open:
                        return False, "[2]更新代理失败", None, None, None, None
                    else:
                        return False, "[2]更新代理失败"
                
                add_bro_log_entry(bro_log_list, browser_id, "[8]代理配置已更新")
                log_print(f"[{browser_id}] ✓ 代理配置已更新")
                time.sleep(10)
                
                # 4. 递归重试任务（retry_count+1）
                add_bro_log_entry(bro_log_list, browser_id, f"[8]步骤4: 重新执行任务（重试次数: {retry_count+1}）")
                log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                return process_trading_mission(task_data, keep_browser_open, retry_count=retry_count+1)
        
        # 根据 keep_browser_open 返回不同的格式
        if keep_browser_open:
            if success:
                add_bro_log_entry(bro_log_list, browser_id, "[15]任务成功，保持浏览器打开以收集数据")
                log_print(f"[{browser_id}] 任务成功，保持浏览器打开以收集数据...")
            else:
                add_bro_log_entry(bro_log_list, browser_id, f"{failure_reason}")
                log_print(f"[{browser_id}] 任务执行失败，返回结果到上层处理: {failure_reason}")
            return success, failure_reason, driver, browser_id, exchange_name, available_balance
        else:
            if success:
                add_bro_log_entry(bro_log_list, browser_id, "任务执行成功")
            else:
                add_bro_log_entry(bro_log_list, browser_id, f"任务执行失败: {failure_reason}")
            return success, failure_reason
        
    except Exception as e:
        error_msg = str(e)
        add_bro_log_entry(bro_log_list, browser_id, f"任务执行异常")
        log_print(f"[{browser_id}] ✗✗✗ 任务执行异常: {error_msg}")
        import traceback
        error_detail = traceback.format_exc()
        log_print(f"[{browser_id}] 错误详情:\n{error_detail}")
        add_bro_log_entry(bro_log_list, browser_id, f"错误详情: {error_detail[:200]}")  # 限制长度避免过长
        
        # 如果是新启动的浏览器且发生异常，需要关闭浏览器
        if is_new_browser:
            add_bro_log_entry(bro_log_list, browser_id, "检测到异常且浏览器是新启动的，立即关闭浏览器")
            log_print(f"[{browser_id}] 检测到异常且浏览器是新启动的，立即关闭浏览器...")
            try:
                if driver:
                    driver.quit()
            except:
                pass
            close_adspower_browser(browser_id)
        
        if keep_browser_open:
            return False, f"[3]执行异常: {error_msg}", None, None, None, None
        else:
            return False, f"[3]执行异常: {error_msg}"
        
    finally:
        # 上传日志
        try:
            upload_bro_logs(bro_log_list, browser_id)
        except Exception as e:
            log_print(f"[{browser_id}] ⚠ 上传日志时发生异常: {str(e)}")
        
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


def check_and_click_understand_agree(driver, browser_id, timeout=5):
    """
    检查是否存在内容等于 "I Understand and Agree" 的p标签，如果存在则点击其父节点
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        timeout: 检查超时时间（秒）
        
    Returns:
        bool: 如果找到并点击了返回True，否则返回False
    """
    try:
        log_print(f"[{browser_id}] 在{timeout}秒内检查是否存在 'I Understand and Agree' p标签...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                for p in p_tags:
                    if p.text.strip() == "I Understand and Agree":
                        log_print(f"[{browser_id}] ✓ 检测到 'I Understand and Agree' p标签存在")
                        try:
                            # 获取父节点并点击
                            parent = p.find_element(By.XPATH, "..")
                            log_print(f"[{browser_id}] → 点击 'I Understand and Agree' 的父节点...")
                            parent.click()
                            log_print(f"[{browser_id}] ✓ 已点击父节点")
                            time.sleep(1)
                            return True
                        except Exception as e:
                            log_print(f"[{browser_id}] ⚠ 点击父节点时出错: {str(e)}")
                            return False
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{browser_id}] ✓ 未检测到 'I Understand and Agree' p标签")
        return False
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查 'I Understand and Agree' p标签时出错: {str(e)}")
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
        time.sleep(10)
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
            
            # 在10秒内等待并点击确认按钮（第二个按钮）
            log_print(f"[{browser_id}] → 查找确认按钮（10秒超时）...")
            start_time = time.time()
            button_clicked = False
            
            while time.time() - start_time < 10:
                try:
                    confirm_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                    if len(confirm_buttons) >= 2:
                        confirm_buttons[1].click()
                        log_print(f"[{browser_id}] ✓ 已点击确认按钮（第二个）")
                        button_clicked = True
                        break
                    else:
                        time.sleep(0.5)  # 等待后重试
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 查找按钮时出错: {str(e)}")
                    time.sleep(0.5)
            
            if not button_clicked:
                log_print(f"[{browser_id}] ⚠ 未找到足够的确认按钮或超时")
            
            # 切换回主窗口
            driver.switch_to.window(main_window)
            log_print(f"[{browser_id}] ✓ 已切换回主窗口")
        
        return True
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 连接钱包失败: {str(e)}")
        return True  # 即使失败也继续执行


def check_wallet_connected(driver, browser_id):
    """
    检查钱包是否已连接（仅检查，不进行连接操作）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        bool: 已连接返回True，未连接返回False
    """
    try:
        log_print(f"[{browser_id}] 检查钱包是否已连接...")
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
                        log_print(f"[{browser_id}] ✓ 找到 Connect Wallet 按钮，钱包未连接")
                        break
                
                # 查找 OKX Wallet 的 p 标签
                if not connect_wallet_button:
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    for p in p_tags:
                        if p.text.strip() == "OKX Wallet":
                            okx_wallet_p = p
                            log_print(f"[{browser_id}] ✓ 找到 OKX Wallet 选项，钱包未连接")
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
        else:
            log_print(f"[{browser_id}] ✗ 钱包未连接")
            return False
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查钱包连接状态时出现异常: {str(e)}")
        return False


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
        
        while time.time() - start_time < 45:
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
                refresh_page_with_opinion_check(driver, browser_id)
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


def get_position_amount_from_tr(tr, browser_id, option_type='YES'):
    """
    从Position的tr元素中获取实际持仓数量
    
    Args:
        tr: tr元素
        browser_id: 浏览器ID
        option_type: 期权类型，'YES'或'NO'
        
    Returns:
        int: 实际持仓数量，失败返回-1
    """
    try:
        tds = tr.find_elements(By.TAG_NAME, "td")
        if not tds or len(tds) < 2:
            log_print(f"[{browser_id}] ⚠ tr中td数量不足")
            return -1
        
        # 第2个td包含持仓数量信息
        td = tds[1]
        p_tags = td.find_elements(By.TAG_NAME, "p")
        
        if not p_tags:
            log_print(f"[{browser_id}] ⚠ td中没有p标签")
            return -1
        
        # 第一个p标签包含数量
        amount_text = p_tags[0].text.strip()
        log_print(f"[{browser_id}] Position持仓数量文本: {amount_text}")
        
        # 提取数字部分
        try:
            # 处理 "<0.01" 这种情况
            if '<' in amount_text:
                # 对于 "<0.01" 这种情况，表示持仓数量小于 0.01，应该视为 0
                # 因为实际持仓太小，无法进行有效交易
                log_print(f"[{browser_id}] ⚠ 持仓数量文本为 '{amount_text}'，表示持仓小于显示值，视为 0")
                return 0.0
            else:
                # 移除逗号和其他非数字字符，只保留数字和小数点
                amount_str = ''.join(c for c in amount_text if c.isdigit() or c == '.')
            
            if amount_str:
                amount = float(amount_str)
                log_print(f"[{browser_id}] ✓ 获取到持仓数量: {amount}")
                return amount
            else:
                log_print(f"[{browser_id}] ⚠ 无法从文本中提取数字: {amount_text}")
                return -1
        except ValueError as e:
            log_print(f"[{browser_id}] ⚠ 数量转换失败: {amount_text}, 错误: {str(e)}")
            return -1
            
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 获取持仓数量失败: {str(e)}")
        return -1


def fetch_orderbook_data(token_id):
    """
    请求订单薄数据
    
    Args:
        token_id: token ID (trendingPart1 或 trendingPart2)
        
    Returns:
        dict: 订单薄数据，失败返回None
    """
    ORDERBOOK_API_URL = 'https://proxy.opinion.trade:8443/openapi/token/orderbook'
    ORDERBOOK_API_KEY = 'xbR1ek3ekhnhykU8aZdvyAb6vRFcmqpU'
    
    try:
        response = requests.get(ORDERBOOK_API_URL, params={'token_id': token_id}, headers={'apikey': ORDERBOOK_API_KEY}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('errno') == 0 and data.get('result'):
                return data.get('result')
        return None
    except Exception as e:
        log_print(f"[系统] 获取订单薄数据失败: {str(e)}")
        return None


def get_best_bid_ask(orderbook_data):
    """
    从订单薄数据中获取买一价和卖一价
    
    Args:
        orderbook_data: 订单薄数据字典，包含 bids 和 asks
        
    Returns:
        tuple: (best_bid_price, best_bid_depth, best_ask_price, best_ask_depth)
               失败返回 (None, None, None, None)
    """
    if not orderbook_data:
        return None, None, None, None
    
    bids = orderbook_data.get('bids', [])
    asks = orderbook_data.get('asks', [])
    
    if not bids or not asks:
        return None, None, None, None
    
    # 买一价：bids 中 price 最大的那一个
    best_bid = max(bids, key=lambda x: float(x.get('price', 0)))
    best_bid_price = float(best_bid.get('price', 0)) * 100  # 转换为百分比
    best_bid_depth = float(best_bid.get('size', 0))  # 使用 size 字段
    
    # 卖一价：asks 中 price 最小的那一个
    best_ask = min(asks, key=lambda x: float(x.get('price', 0)))
    best_ask_price = float(best_ask.get('price', 0)) * 100  # 转换为百分比
    best_ask_depth = float(best_ask.get('size', 0))  # 使用 size 字段
    
    return best_bid_price, best_bid_depth, best_ask_price, best_ask_depth


def save_exchange_config_blacklist(exchange_config_id, trending, trending_part1, trending_part2, trending_part3, op_url, poly_url, op_topic_id, weight, is_open):
    """
    保存exchangeConfig的a字段为1（拉黑事件）
    
    Args:
        exchange_config_id: exchangeConfig的ID
        其他字段: 保持原有值
        
    Returns:
        bool: 成功返回True
    """
    try:
        url = "https://sg.bicoin.com.cn/99l/mission/exchangeConfig"
        payload = {
            "list": [{
                "id": exchange_config_id,
                "trending": trending,
                "trendingPart1": trending_part1 or None,
                "trendingPart2": trending_part2 or None,
                "trendingPart3": trending_part3 or None,
                "opUrl": op_url or '',
                "polyUrl": poly_url or '',
                "opTopicId": op_topic_id or '',
                "weight": weight or 0,
                "isOpen": is_open if is_open is not None else 1,
                "a": "1"  # 拉黑状态：1=拉黑
            }]
        }
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('code') == 0:
                return True
        return False
    except Exception as e:
        log_print(f"[系统] 保存exchangeConfig拉黑状态失败: {str(e)}")
        return False


def cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list=None):
    """
    简单取消Open Orders中的第一个挂单（用于tp2检查场景）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        bro_log_list: 日志列表（可选）
        
    Returns:
        str: 取消订单的详细结果
            - "未找到挂单"：没有挂单
            - "有挂单，已取消挂单"：有挂单并成功取消
            - "有挂单，取消挂单失败"：有挂单但取消失败
    """
    try:
        # 点击Open Orders按钮
        log_msg = f"[{browser_id}] 点击Open Orders按钮..."
        log_print(log_msg)
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
        
        open_orders_clicked = False
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.text.strip() == "Open Orders":
                        button.click()
                        log_msg = f"[{browser_id}] ✓ 已点击 Open Orders 按钮"
                        log_print(log_msg)
                        if bro_log_list is not None:
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        open_orders_clicked = True
                        break
                if open_orders_clicked:
                    break
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not open_orders_clicked:
            log_msg = f"[{browser_id}] ⚠ 10秒内未找到 Open Orders 按钮"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "未找到挂单"
        
        time.sleep(7)
        
        # 查找 Open Orders div
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        open_orders_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'openorders' in div_id.lower():
                open_orders_div = div
                break
        
        if not open_orders_div:
            log_msg = f"[{browser_id}] ⚠ 未找到Open Orders div"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "未找到挂单"
        
        # 检查是否有 "No data yet"
        all_p_tags_in_div = open_orders_div.find_elements(By.TAG_NAME, "p")
        for p in all_p_tags_in_div:
            if "No data yet" in p.text:
                log_msg = f"[{browser_id}] ✓ 没有挂单"
                log_print(log_msg)
                if bro_log_list is not None:
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                return "没有挂单"
        
        # 获取 tbody 和 tr 列表
        try:
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        except:
            log_msg = f"[{browser_id}] ⚠ 未找到 tbody 或 tr 列表"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "未找到挂单"
        
        if not tr_list or len(tr_list) == 0:
            log_msg = f"[{browser_id}] ✓ 没有挂单"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "未找到挂单"
        
        # 有挂单，继续取消流程
        log_msg = f"[{browser_id}] 检测到有挂单，开始取消..."
        log_print(log_msg)
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
        
        # 取消第一个挂单
        first_tr = tr_list[0]
        tds = first_tr.find_elements(By.TAG_NAME, "td")
        if len(tds) == 0:
            log_msg = f"[{browser_id}] ⚠ 未找到td"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "未找到挂单"
        
        last_td = tds[-1]
        svg_elements = last_td.find_elements(By.TAG_NAME, "svg")
        if not svg_elements or len(svg_elements) == 0:
            log_msg = f"[{browser_id}] ⚠ 未找到svg元素"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "有挂单，取消挂单失败"
        
        log_msg = f"[{browser_id}] 点击svg取消按钮..."
        log_print(log_msg)
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
        svg_elements[0].click()
        time.sleep(2)
        
        # 查找并点击Confirm按钮
        confirm_found = False
        confirm_timeout = 10
        confirm_start_time = time.time()
        while time.time() - confirm_start_time < confirm_timeout:
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    if btn.text.strip() == "Confirm":
                        log_msg = f"[{browser_id}] ✓ 找到Confirm按钮，点击..."
                        log_print(log_msg)
                        if bro_log_list is not None:
                            add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        btn.click()
                        confirm_found = True
                        break
                if confirm_found:
                    break
                time.sleep(0.5)
            except Exception as e:
                log_msg = f"[{browser_id}] ⚠ 查找Confirm按钮时出错: {str(e)}"
                log_print(log_msg)
                if bro_log_list is not None:
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                time.sleep(0.5)
        
        if not confirm_found:
            log_msg = f"[{browser_id}] ⚠ 未找到Confirm按钮"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "有挂单，取消挂单失败"
        
        # 等待10秒后重新检查挂单
        log_msg = f"[{browser_id}] 等待10秒后重新检查挂单..."
        log_print(log_msg)
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
        time.sleep(10)
        
        # 重新获取open_orders_div
        tabs_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-scope="tabs"]')
        open_orders_div = None
        for div in tabs_divs:
            div_id = div.get_attribute('id')
            if div_id and 'openorders' in div_id.lower():
                open_orders_div = div
                break
        
        if not open_orders_div:
            # 未找到Open Orders div，说明挂单已取消
            log_msg = f"[{browser_id}] ✓ 挂单已取消（未找到Open Orders div）"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "有挂单，已取消挂单"
        
        # 重新获取tbody和tr
        try:
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        except:
            # 没有tbody或tr，说明挂单已取消
            log_msg = f"[{browser_id}] ✓ 挂单已取消（无tbody/tr）"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "有挂单，已取消挂单"
        
        if not tr_list or len(tr_list) == 0:
            # 没有tr，说明挂单已取消
            log_msg = f"[{browser_id}] ✓ 挂单已取消（无tr）"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "有挂单，已取消挂单"
        else:
            # 挂单仍然存在，取消失败
            log_msg = f"[{browser_id}] ⚠ 挂单仍然存在，取消失败"
            log_print(log_msg)
            if bro_log_list is not None:
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return "有挂单，取消挂单失败，可能已成交"
        
    except Exception as e:
        log_msg = f"[{browser_id}] ⚠ 取消挂单时出错: {str(e)}"
        log_print(log_msg)
        if bro_log_list is not None:
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
        return "有挂单，取消挂单失败，可能已成交"


def check_tp2_position_and_orderbook(driver, browser_id, task_data, initial_position_count, trade_type, option_type, trending_part1, amount, bro_log_list):
    """
    在tp2时间段内检查订单薄，判断自己是否仍然是买一价或卖一价
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        task_data: 任务数据
        initial_position_count: 初始仓位数量（不再使用）
        trade_type: Buy 或 Sell
        option_type: YES 或 NO
        trending_part1: 子标题（不再使用）
        amount: 下单数量（不再使用）
        bro_log_list: 日志列表
        
    Returns:
        tuple: (success, msg) - success为False表示需要取消并返回，True表示继续流程
    """
    mission = task_data.get('mission', {})
    exchange_config = task_data.get('exchangeConfig', {})
    tp2 = mission.get('tp2')
    
    if not tp2:
        return True, ""  # 没有tp2，直接继续流程
    
    tp2_time = int(tp2) if isinstance(tp2, (int, str)) and str(tp2).isdigit() else 0
    if tp2_time <= 0:
        return True, ""  # tp2无效，直接继续流程
    
    log_msg = f"[OP] 任务一: 开始tp2时间段检查（{tp2_time}秒）..."
    log_print(f"[{browser_id}] {log_msg}")
    add_bro_log_entry(bro_log_list, browser_id, log_msg)
    
    # 根据YES/NO方向选择token_id
    if option_type == "YES":
        token_id = exchange_config.get('trendingPart1', '')
    else:
        token_id = exchange_config.get('trendingPart2', '')
    
    if not token_id:
        log_msg = f"[OP] 任务一: ⚠ 无法获取token_id"
        log_print(f"[{browser_id}] {log_msg}")
        add_bro_log_entry(bro_log_list, browser_id, log_msg)
        return True, ""  # 无法获取token_id，继续流程
    
    mission_price = float(mission.get('price', 0))
    mission_side = mission.get('side', 0)  # 1=买，2=卖
    is_buy = (trade_type == "Buy" or mission_side == 1)
    
    check_interval = 30  # 每30秒检查一次
    start_time = time.time()
    check_count = 0
    max_orderbook_retries = 5
    
    time.sleep(10);
    
    # 立即先运行一次
    check_count += 1
    log_msg = f"[OP] 任务一: 第{check_count}次检查（立即执行）..."
    log_print(f"[{browser_id}] {log_msg}")
    add_bro_log_entry(bro_log_list, browser_id, log_msg)
    
    # 获取订单薄数据（最多重试5次）
    orderbook_data = None
    orderbook_retry_count = 0
    
    while orderbook_data is None and orderbook_retry_count < max_orderbook_retries:
        orderbook_data = fetch_orderbook_data(token_id)
        if orderbook_data is None:
            orderbook_retry_count += 1
            if orderbook_retry_count < max_orderbook_retries:
                log_msg = f"[OP] 任务一: 订单薄数据获取失败，重试中... ({orderbook_retry_count}/{max_orderbook_retries})"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                time.sleep(2)
    
    if orderbook_data is None:
        log_msg = f"[OP] 任务一: ⚠ 订单薄数据获取失败，继续流程"
        log_print(f"[{browser_id}] {log_msg}")
        add_bro_log_entry(bro_log_list, browser_id, log_msg)
        # 获取失败，继续流程
    else:
        # 检查价格
        best_bid_price, best_bid_depth, best_ask_price, best_ask_depth = get_best_bid_ask(orderbook_data)
        
        if is_buy:
            # 买入（开仓）：检查是否是买一价
            if best_bid_price is not None:
                is_best_bid = abs(best_bid_price - mission_price) < 0.01
                
                log_msg = f"[OP] 任务一: 买一价: {best_bid_price:.1f}, 我的价格: {mission_price:.1f}, 是否相等: {is_best_bid}"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                if not is_best_bid:
                    # 不是买一价，取消订单并返回失败
                    log_msg = f"[OP] 任务一: ✗ 已不是买一价，取消订单"
                    log_print(f"[{browser_id}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    
                    cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                    fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                    return False, fail_msg
            else:
                # 没有买盘数据，取消订单并返回失败
                log_msg = f"[OP] 任务一: ✗ 没有买盘数据，取消订单"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                return False, fail_msg
        else:
            # 卖出（平仓）：检查是否是卖一价
            if best_ask_price is not None:
                is_best_ask = abs(best_ask_price - mission_price) < 0.01
                
                log_msg = f"[OP] 任务一: 卖一价: {best_ask_price:.1f}, 我的价格: {mission_price:.1f}, 是否相等: {is_best_ask}"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                if not is_best_ask:
                    # 不是卖一价，取消订单并返回失败
                    log_msg = f"[OP] 任务一: ✗ 已不是卖一价，取消订单"
                    log_print(f"[{browser_id}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    
                    cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                    fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                    return False, fail_msg
            else:
                # 没有卖盘数据，取消订单并返回失败
                log_msg = f"[OP] 任务一: ✗ 没有卖盘数据，取消订单"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                
                cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                return False, fail_msg
    
    # 在tp2时间内，每隔30s检查一次
    next_check_time = start_time + check_interval
    
    while time.time() - start_time < tp2_time:
        current_time = time.time()
        
        # 检查是否到了检查时间
        if current_time >= next_check_time:
            check_count += 1
            next_check_time = current_time + check_interval
            
            log_msg = f"[OP] 任务一: 第{check_count}次检查..."
            log_print(f"[{browser_id}] {log_msg}")
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
            
            # 获取订单薄数据（最多重试5次）
            orderbook_data = None
            orderbook_retry_count = 0
            
            while orderbook_data is None and orderbook_retry_count < max_orderbook_retries:
                orderbook_data = fetch_orderbook_data(token_id)
                if orderbook_data is None:
                    orderbook_retry_count += 1
                    if orderbook_retry_count < max_orderbook_retries:
                        log_msg = f"[OP] 任务一: 订单薄数据获取失败，重试中... ({orderbook_retry_count}/{max_orderbook_retries})"
                        log_print(f"[{browser_id}] {log_msg}")
                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        time.sleep(2)
            
            if orderbook_data is None:
                log_msg = f"[OP] 任务一: ⚠ 订单薄数据获取失败，继续等待..."
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                continue
            
            # 检查价格
            best_bid_price, best_bid_depth, best_ask_price, best_ask_depth = get_best_bid_ask(orderbook_data)
            
            if is_buy:
                # 买入（开仓）：检查是否是买一价
                if best_bid_price is not None:
                    is_best_bid = abs(best_bid_price - mission_price) < 0.01
                    
                    log_msg = f"[OP] 任务一: 买一价: {best_bid_price:.1f}, 我的价格: {mission_price:.1f}, 是否相等: {is_best_bid}"
                    log_print(f"[{browser_id}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    
                    if not is_best_bid:
                        # 不是买一价，取消订单并返回失败
                        log_msg = f"[OP] 任务一: ✗ 已不是买一价，取消订单"
                        log_print(f"[{browser_id}] {log_msg}")
                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        
                        cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                        fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                        return False, fail_msg
                else:
                    # 没有买盘数据，取消订单并返回失败
                    log_msg = f"[OP] 任务一: ✗ 没有买盘数据，取消订单"
                    log_print(f"[{browser_id}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    
                    cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                    fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                    return False, fail_msg
            else:
                # 卖出（平仓）：检查是否是卖一价
                if best_ask_price is not None:
                    is_best_ask = abs(best_ask_price - mission_price) < 0.01
                    
                    log_msg = f"[OP] 任务一: 卖一价: {best_ask_price:.1f}, 我的价格: {mission_price:.1f}, 是否相等: {is_best_ask}"
                    log_print(f"[{browser_id}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    
                    if not is_best_ask:
                        # 不是卖一价，取消订单并返回失败
                        log_msg = f"[OP] 任务一: ✗ 已不是卖一价，取消订单"
                        log_print(f"[{browser_id}] {log_msg}")
                        add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        
                        cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                        fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                        return False, fail_msg
                else:
                    # 没有卖盘数据，取消订单并返回失败
                    log_msg = f"[OP] 任务一: ✗ 没有卖盘数据，取消订单"
                    log_print(f"[{browser_id}] {log_msg}")
                    add_bro_log_entry(bro_log_list, browser_id, log_msg)
                    
                    cancel_result = cancel_opinion_open_orders_simple(driver, browser_id, bro_log_list)
                    fail_msg = f"[11]先挂方已不是买一或卖一，取消挂单，{cancel_result}"
                    return False, fail_msg
        
        time.sleep(1)  # 每秒检查一次是否到了检查时间
    
    # tp2时间结束，检查最终状态
    log_msg = f"[OP] 任务一: tp2时间结束，检查最终状态..."
    log_print(f"[{browser_id}] {log_msg}")
    add_bro_log_entry(bro_log_list, browser_id, log_msg)
    
    # 最后一次获取订单薄数据
    orderbook_data = None
    orderbook_retry_count = 0
    
    while orderbook_data is None and orderbook_retry_count < max_orderbook_retries:
        orderbook_data = fetch_orderbook_data(token_id)
        if orderbook_data is None:
            orderbook_retry_count += 1
            if orderbook_retry_count < max_orderbook_retries:
                log_msg = f"[OP] 任务一: 订单薄数据获取失败，重试中... ({orderbook_retry_count}/{max_orderbook_retries})"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                time.sleep(2)
    
    if orderbook_data is None:
        log_msg = f"[OP] 任务一: ⚠ tp2时间结束，订单薄数据获取失败，继续流程"
        log_print(f"[{browser_id}] {log_msg}")
        add_bro_log_entry(bro_log_list, browser_id, log_msg)
        return True, ""
    
    # 检查最终状态
    best_bid_price, best_bid_depth, best_ask_price, best_ask_depth = get_best_bid_ask(orderbook_data)
    
    if is_buy:
        # 买入（开仓）：检查是否仍然是买一价
        if best_bid_price is not None:
            is_best_bid = abs(best_bid_price - mission_price) < 0.01
            
            log_msg = f"[OP] 任务一: tp2时间结束，买一价: {best_bid_price:.1f}, 我的价格: {mission_price:.1f}, 是否相等: {is_best_bid}"
            log_print(f"[{browser_id}] {log_msg}")
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
            
            if is_best_bid:
                # 仍然是买一价，保存状态22并继续流程
                log_msg = "任务一延迟时间结束后，仍然是买一或卖一"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                save_mission_result(mission.get('id'), 22, log_msg)
                return True, ""
        else:
            # 没有买盘数据，继续流程
            log_msg = f"[OP] 任务一: tp2时间结束，没有买盘数据，继续流程"
            log_print(f"[{browser_id}] {log_msg}")
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return True, ""
    else:
        # 卖出（平仓）：检查是否仍然是卖一价
        if best_ask_price is not None:
            is_best_ask = abs(best_ask_price - mission_price) < 0.01
            
            log_msg = f"[OP] 任务一: tp2时间结束，卖一价: {best_ask_price:.1f}, 我的价格: {mission_price:.1f}, 是否相等: {is_best_ask}"
            log_print(f"[{browser_id}] {log_msg}")
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
            
            if is_best_ask:
                # 仍然是卖一价，保存状态22并继续流程
                log_msg = "任务一延迟时间结束后，仍然是买一或卖一"
                log_print(f"[{browser_id}] {log_msg}")
                add_bro_log_entry(bro_log_list, browser_id, log_msg)
                save_mission_result(mission.get('id'), 22, log_msg)
                return True, ""
        else:
            # 没有卖盘数据，继续流程
            log_msg = f"[OP] 任务一: tp2时间结束，没有卖盘数据，继续流程"
            log_print(f"[{browser_id}] {log_msg}")
            add_bro_log_entry(bro_log_list, browser_id, log_msg)
            return True, ""
    
    # 如果到这里，说明条件符合，继续流程
    log_msg = f"[OP] 任务一: ✓ tp2时间结束，继续流程"
    log_print(f"[{browser_id}] {log_msg}")
    add_bro_log_entry(bro_log_list, browser_id, log_msg)
    return True, ""


def check_position_count(driver, browser_id, trending_part1='', trade_type='Buy', option_type='YES'):
    """
    检查 Position 标签页中是否有仓位
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        trending_part1: 子标题名称，如果有，需要检查tr内p标签内容
        trade_type: 交易类型，'Buy'或'Sell'
        option_type: 期权类型，'YES'或'NO'
        
    Returns:
        int: Buy时返回实际持仓数量，Sell时返回实际持仓数量，失败返回-1，Buy时如果已有对向仓位且数量>=10返回-2
    """
    # 辅助函数：检查 p_text 是否匹配 option_type
    # 如果 option_type == 'YES'，还兼容 'Monad' 和 'Gold'
    def matches_option_type(p_text, opt_type):
        if opt_type == 'YES':
            log_print(f"[{browser_id}] 检查 p_text {p_text}  {opt_type}仓位...")
            return opt_type in p_text or 'Monad' in p_text or 'Gold' in p_text or 'MONAD' in p_text or 'GOLD' in p_text or 'Yes' in p_text or 'yes' in p_text
        elif opt_type == 'NO':
            log_print(f"[{browser_id}] 检查 p_text {p_text}  {opt_type}仓位...")
            return 'YES' not in p_text and 'Monad' not in p_text and  'Gold' not in p_text and 'MONAD' not in p_text and  'GOLD' not in p_text and 'Yes' not in p_text and 'yes' not in p_text
      
    
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
            matched_tr = None  # 自己方向的tr（包含子标题和option_type）
            opposite_tr = None  # 对向的tr（包含子标题但不包含option_type）
            for tr in tr_list:
                try:
                    # 获取tr内所有p标签
                    p_tags = tr.find_elements(By.TAG_NAME, "p")
                    found_matched = False  # 是否有p标签同时包含子标题和option_type
                    found_opposite = False  # 是否有p标签包含子标题但不包含option_type
                    # 检查p标签内容
                    for p in p_tags:
                        p_text = p.text.strip()
                        # 检查是否包含子标题
                        if trending_part1 in p_text:
                            # 检查同一个p标签中是否匹配option_type（兼容Monad和Gold）
                            if matches_option_type(p_text, option_type):
                                # 同一个p标签同时包含子标题和option_type，是自己方向的tr
                                found_matched = True
                            else:
                                # 同一个p标签包含子标题但不包含option_type，是对向的tr
                                found_opposite = True
                    
                    # 记录匹配的tr
                    if found_matched:
                        matched_count += 1
                        matched_tr = tr
                    # 记录对向的tr（优先使用第一个找到的）
                    elif found_opposite and opposite_tr is None:
                        opposite_tr = tr
                except:
                    continue
            
            log_print(f"[{browser_id}] 有子标题情况下，匹配的仓位数量: {matched_count}")
            if opposite_tr:
                log_print(f"[{browser_id}] ✓ 找到对向的tr（包含子标题但不包含option_type）")
            
            # 如果是Sell，需要获取实际持仓数量
            if trade_type == 'Sell' and matched_tr:
                return get_position_amount_from_tr(matched_tr, browser_id, option_type)
            
            if trade_type == 'Buy' and matched_tr:    
                # 如果存在匹配的option_type，获取实际持仓数量
                return get_position_amount_from_tr(matched_tr, browser_id, option_type)
            
            # 如果是Buy，需要检查匹配的tr中是否有对应option_type的p标签
            if trade_type == 'Buy' and opposite_tr:
                log_print(f"[{browser_id}] Buy类型：检查匹配tr中是否包含 '{option_type}' 的p标签...")
                # 使用对向的tr来获取对向仓位的数量
                if opposite_tr:
                        opposite_amount = get_position_amount_from_tr(opposite_tr, browser_id, option_type)
                        if opposite_amount >= 0:
                            if opposite_amount < 10:
                                log_print(f"[{browser_id}] ✓ 对向仓位数量 {opposite_amount} < 10，视为无对向仓位，可以继续执行")
                                return 0
                            else:
                                log_print(f"[{browser_id}] ⚠ 对向仓位数量 {opposite_amount} >= 10，不能继续执行")
                                return -2  # 返回-2表示已有对向仓位且数量 >= 10
                        else:
                            log_print(f"[{browser_id}] ⚠ 无法获取对向仓位数量，返回 -2")
                            return -2
                else:
                        log_print(f"[{browser_id}] ⚠ 未找到对向的tr，返回 -2")
                        return -2
                    
            
            
            # Buy类型但无匹配tr，返回0
            if trade_type == 'Buy':
                return 0
            
            return matched_count
        
        # 如果无子标题，遍历所有tr，找到包含option_type的tr和不包含的tr
        if not trending_part1 and count > 0:
            log_print(f"[{browser_id}] 无子标题，遍历所有tr查找包含 '{option_type}' 的tr...")
            matched_tr = None  # 自己方向的tr（包含option_type）
            opposite_tr = None  # 对向的tr（不包含option_type）
            
            for tr in tr_list:
                try:
                    # 获取tr内所有p标签
                    p_tags = tr.find_elements(By.TAG_NAME, "p")
                    has_option_type = False
                    # 检查是否有p标签匹配option_type（兼容Monad和Gold）
                    for p in p_tags:
                        p_text = p.text.strip()
                        if matches_option_type(p_text, option_type):
                            has_option_type = True
                            log_print(f"[{browser_id}] ✓ 找到包含 '{option_type}' 的p标签: {p_text}")
                            break
                    
                    if has_option_type:
                        # 找到包含option_type的tr（自己方向的）
                        matched_tr = tr
                    else:
                        # 找到不包含option_type的tr（对向的，优先使用第一个找到的）
                        if opposite_tr is None:
                            opposite_tr = tr
                except:
                    continue
            
            # 如果是Sell，返回自己方向的tr的数量
            if trade_type == 'Sell':
                if matched_tr:
                    return get_position_amount_from_tr(matched_tr, browser_id, option_type)
                else:
                    log_print(f"[{browser_id}] ⚠ Sell类型：未找到包含 '{option_type}' 的tr")
                    return 0
            
            # 如果是Buy，需要检查对向仓位数量
            if trade_type == 'Buy':
                log_print(f"[{browser_id}] Buy类型（无子标题）：检查对向仓位...")
                if opposite_tr:
                    log_print(f"[{browser_id}] ✓ 找到对向的tr（不包含 '{option_type}'）")
                    # 获取对向仓位的数量
                    opposite_amount = get_position_amount_from_tr(opposite_tr, browser_id, option_type)
                    if opposite_amount >= 0:
                        if opposite_amount >= 10:
                            log_print(f"[{browser_id}] ⚠ 对向仓位数量 {opposite_amount} >= 10，不能继续执行")
                            return -2  # 返回-2表示已有对向仓位且数量 >= 10
                        else:
                            log_print(f"[{browser_id}] ✓ 对向仓位数量 {opposite_amount} < 10，视为无对向仓位，可以继续执行")
                    else:
                        log_print(f"[{browser_id}] ⚠ 无法获取对向仓位数量，返回 -2")
                        return -2
                else:
                    log_print(f"[{browser_id}] ✓ Buy类型：未找到对向的tr，可以继续执行")
                
                # 如果存在匹配的option_type，获取实际持仓数量
                if matched_tr:
                    return get_position_amount_from_tr(matched_tr, browser_id, option_type)
                else:
                    return 0
        
        # Buy类型但无仓位，返回0
        if trade_type == 'Buy':
            return 0
        
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
        tuple: (success: bool, error_type: str or None)
            - success: 成功返回True，失败返回False
            - error_type: 错误类型，成功时为None，失败时为 "NO_ACCORDION"（未找到 Accordion div）或 "NO_MATCH"（未找到匹配的子主题）或 "EXCEPTION"（异常）
    """
    try:
        if not trending_part1:
            log_print(f"[{browser_id}] trendingPart1 为空，跳过子主题选择")
            return True, None
        
        log_print(f"[{browser_id}] 查找并点击子主题: {trending_part1}")
        
        # 找到 data-sentry-element="Accordion" 的 div
        accordion_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-sentry-element="Accordion"]')
        
        if not accordion_divs:
            log_print(f"[{browser_id}] ⚠ 未找到 Accordion div")
            return False, "NO_ACCORDION"
        
        log_print(f"[{browser_id}] ✓ 找到 {len(accordion_divs)} 个 Accordion div")
        
        # 在 Accordion div 中查找内容等于 trending_part1 的 p 标签
        for accordion_div in accordion_divs:
            p_tags = accordion_div.find_elements(By.TAG_NAME, "p")
            
            for p in p_tags:
                log_print(f"[{browser_id}] ✓ 子主题内容 {p.text.strip()}")
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
                    return True, None
        
        log_print(f"[{browser_id}] ⚠ 未找到匹配的子主题: {trending_part1}")
        return False, "NO_MATCH"
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 点击子主题失败: {str(e)}")
        return False, "EXCEPTION"


def process_opinion_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, trending_part1='', task_data=None, retry_count=0, trending='', target_url='', current_ip=None, current_delay=None, bro_log_list=None, trendingId=''):
    """
    处理 Opinion Trade 交易流程
    
    Args:
        is_new_browser: 是否是新启动的浏览器
        trending_part1: 子主题名称（如果有）
        task_data: 任务数据（用于type=5的同步机制）
        retry_count: 当前重试次数
        trending: 完整的交易主题（用于API调用）
        bro_log_list: 日志列表（用于记录日志）
        trendingId: 交易主题ID（用于更新时间戳）
    
    Returns:
        tuple: (success, failure_reason, available_balance)
    """
    # 初始化日志列表（如果未提供）
    if bro_log_list is None:
        bro_log_list = []
    
    # 初始化可用余额变量
    initial_available_balance = None
    
    try:
        # 5. 等待页面加载
        add_bro_log_entry(bro_log_list, browser_id, "[4]步骤5: 等待交易页面加载")
        log_print(f"[{browser_id}] 步骤5: 等待页面加载...")
        trade_box = wait_for_opinion_trade_box(driver, browser_id, max_retries=3)
        
        if not trade_box:
            add_bro_log_entry(bro_log_list, browser_id, "[4]交易页面加载失败，需要换IP重试")
            return False, "NEED_IP_RETRY", None
        
        # 5.5 检查地区限制（Trading is not available）
        add_bro_log_entry(bro_log_list, browser_id, "[5]步骤5.5: 检查地区限制（Trading is not available）")
        log_print(f"[{browser_id}] 步骤5.5: 检查地区限制（Trading is not available）...")
        try:
            start_time = time.time()
            trading_restricted = False
            while time.time() - start_time < 3:
                try:
                    # 查找所有p标签
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    for p in p_tags:
                        p_text = p.text.strip()
                        if "Trading is not available to persons located in the" in p_text:
                            trading_restricted = True
                            log_print(f"[{browser_id}] ✗ 检测到地区限制提示: {p_text[:100]}...")
                            break
                    if trading_restricted:
                        break
                    time.sleep(0.2)  # 短暂等待后重试
                except Exception as e:
                    # 查找过程中出现异常，继续尝试
                    time.sleep(0.2)
                    continue
            
            if trading_restricted:
                add_bro_log_entry(bro_log_list, browser_id, "[5]检测到地区限制，需要换IP")
                log_print(f"[{browser_id}] ✗ 检测到地区限制，需要换IP")
                return False, "NEED_IP_RETRY", None
            else:
                add_bro_log_entry(bro_log_list, browser_id, "[5]未检测到地区限制")
                log_print(f"[{browser_id}] ✓ 未检测到地区限制")
        except Exception as e:
            add_bro_log_entry(bro_log_list, browser_id, f"[5]检查地区限制时出现异常: {str(e)}，继续执行")
            log_print(f"[{browser_id}] ⚠ 检查地区限制时出现异常: {str(e)}，继续执行...")
        
        # 6. 预打开OKX钱包并连接（仅在新启动的浏览器时执行）
        if is_new_browser:
            add_bro_log_entry(bro_log_list, browser_id, "[5]步骤6: 预打开OKX钱包（浏览器新启动）")
            log_print(f"[{browser_id}] 步骤6: 预打开OKX钱包（浏览器新启动）...")
            preopen_okx_wallet(driver, browser_id, current_ip, current_delay)
        else:
            add_bro_log_entry(bro_log_list, browser_id, "[5]步骤6: 跳过预打开OKX钱包（浏览器已在运行）")
            log_print(f"[{browser_id}] 步骤6: 跳过预打开OKX钱包（浏览器已在运行）")
        
        # 6.1 检查并连接钱包
        add_bro_log_entry(bro_log_list, browser_id, "[5]步骤6.1: 检查并连接钱包")
        log_print(f"[{browser_id}] 步骤6.1: 检查并连接钱包...")
        connect_wallet_if_needed(driver, browser_id)
        
        # 6.1.1 检查并切换到包含 app.opinion.trade 的标签页
        log_print(f"[{browser_id}] 步骤6.1.1: 检查并切换到 app.opinion.trade 标签页...")
        try:
            current_url = driver.current_url
            if "https://app.opinion.trade" not in current_url:
                log_print(f"[{browser_id}] 当前URL不包含 app.opinion.trade: {current_url}")
                # 查找包含 app.opinion.trade 的标签页
                all_windows = driver.window_handles
                opinion_window = None
                
                for window_handle in all_windows:
                    try:
                        driver.switch_to.window(window_handle)
                        window_url = driver.current_url
                        if "https://app.opinion.trade" in window_url or "app.opinion.trade" in window_url:
                            opinion_window = window_handle
                            log_print(f"[{browser_id}] ✓ 找到包含 app.opinion.trade 的标签页: {window_url}")
                            break
                    except Exception as e:
                        # 某些标签页可能无法访问URL（如chrome://等系统页面），跳过继续查找
                        log_print(f"[{browser_id}] ⚠ 跳过无法访问的标签页: {str(e)}")
                        continue
                
                if opinion_window:
                    # 切换到包含 app.opinion.trade 的标签页
                    driver.switch_to.window(opinion_window)
                    log_print(f"[{browser_id}] ✓ 已切换到包含 app.opinion.trade 的标签页")
                    time.sleep(2)  # 等待页面加载
                else:
                    log_print(f"[{browser_id}] ⚠ 未找到包含 app.opinion.trade 的标签页，在当前标签页打开")
                    driver.get("https://app.opinion.trade")
                    time.sleep(2)
            else:
                log_print(f"[{browser_id}] ✓ 当前标签页已包含 app.opinion.trade")
        except Exception as e:
            log_print(f"[{browser_id}] ⚠ 检查并切换标签页时出现异常: {str(e)}，继续执行...")
        
        # 6.1.2 检查地区限制
        add_bro_log_entry(bro_log_list, browser_id, "[5]步骤6.1.2: 检查地区限制")
        log_print(f"[{browser_id}] 步骤6.1.2: 检查地区限制...")
        try:
            start_time = time.time()
            region_restricted = False
            while time.time() - start_time < 3:
                try:
                    # 查找所有div元素
                    all_divs = driver.find_elements(By.TAG_NAME, "div")
                    for div in all_divs:
                        div_text = div.text
                        if "API is not available to persons located in the" in div_text:
                            region_restricted = True
                            log_print(f"[{browser_id}] ✗ 检测到地区限制提示: {div_text[:100]}...")
                            break
                    if region_restricted:
                        break
                    time.sleep(0.2)  # 短暂等待后重试
                except Exception as e:
                    # 查找过程中出现异常，继续尝试
                    time.sleep(0.2)
                    continue
            
            if region_restricted:
                add_bro_log_entry(bro_log_list, browser_id, "[5]IP通畅，但地区不符合，需要换IP")
                log_print(f"[{browser_id}] ✗ IP通畅，但地区不符合")
                # 调用 changeIpToErr 接口
                call_change_ip_to_err(browser_id, current_ip)
                return False, "NEED_IP_RETRY", None
            else:
                add_bro_log_entry(bro_log_list, browser_id, "[5]未检测到地区限制")
                log_print(f"[{browser_id}] ✓ 未检测到地区限制")
        except Exception as e:
            add_bro_log_entry(bro_log_list, browser_id, f"[5]检查地区限制时出现异常: {str(e)}，继续执行")
            log_print(f"[{browser_id}] ⚠ 检查地区限制时出现异常: {str(e)}，继续执行...")
        
        # 6.1.5 等待Position按钮出现（带重试机制）
        add_bro_log_entry(bro_log_list, browser_id, "[6]步骤6.1.5: 等待Position按钮出现")
        log_print(f"[{browser_id}] 步骤6.1.5: 等待Position按钮出现...")
        if not wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
            # 检查是否是 type=5 任务且重试次数小于2
            mission = task_data.get('mission', {}) if task_data else {}
            mission_type = mission.get('type')
            
            if mission_type == 5 and retry_count < 2:
                add_bro_log_entry(bro_log_list, browser_id, f"[6]Type=5 任务Position按钮未出现，需要换IP重试（第{retry_count+1}次）")
                log_print(f"[{browser_id}] Type=5 任务Position按钮未出现，需要换IP重试（第{retry_count+1}次）...")
                return False, "NEED_IP_RETRY", None
            else:
                add_bro_log_entry(bro_log_list, browser_id, "[6]Position按钮未出现，页面加载可能失败")
                log_print(f"[{browser_id}] ✗ Position按钮未出现，页面加载可能失败")
                
                time.sleep(3)
                # 发送飞书消息
                # message_text = f"电脑组{COMPUTER_GROUP}浏览器编号{browser_id} Position按钮未出现。请人工复核"
                # log_print(f"[{browser_id}] 发送飞书消息: {message_text}")
                # send_feishu_custom_message(browser_id, message_text)
                return False, "[4]Position按钮未出现，页面加载可能失败", None
        
        time.sleep(7)
        # 6.1.3 再次检查钱包是否已连接
        add_bro_log_entry(bro_log_list, browser_id, "[6]步骤6.1.5.1: 再次检查钱包是否已连接")
        log_print(f"[{browser_id}] 步骤6.1.3: 再次检查钱包是否已连接...")
        try:
            wallet_connected = check_wallet_connected(driver, browser_id)
            if wallet_connected:
                add_bro_log_entry(bro_log_list, browser_id, "[6]钱包已连接")
                log_print(f"[{browser_id}] ✓ 钱包已连接")
            else:
                add_bro_log_entry(bro_log_list, browser_id, "[6]钱包未连接，再次尝试连接钱包")
                log_print(f"[{browser_id}] ✗ 钱包未连接，需要重新连接")
                # 可以在这里选择是否重新连接钱包
                connect_wallet_if_needed(driver, browser_id)
                time.sleep(20)
                wallet_connected = check_wallet_connected(driver, browser_id)
                if wallet_connected:
                    add_bro_log_entry(bro_log_list, browser_id, "[6]钱包已连接")
                    log_print(f"[{browser_id}] ✓ 钱包已连接")
                    time.sleep(30)
                else:
                    add_bro_log_entry(bro_log_list, browser_id, "[6]钱包未连接，再次尝试连接钱包")
                    return False, "[5]钱包多次连接未成功", None
        except Exception as e:
            add_bro_log_entry(bro_log_list, browser_id, f"[6]检查钱包连接状态时出现异常: {str(e)}，继续执行")
            log_print(f"[{browser_id}] ⚠ 检查钱包连接状态时出现异常: {str(e)}，继续执行...")
        
        
        
        # 6.1.6 如果有 trendingPart1，点击子主题
        if trending_part1:
            add_bro_log_entry(bro_log_list, browser_id, f"[7]步骤6.1.6: 检查并点击子主题 {trending_part1}")
            log_print(f"[{browser_id}] 步骤6.1.6: 检查并点击子主题 {trending_part1}...")
            success, error_type = click_trending_part1_if_needed(driver, browser_id, trending_part1)
            if not success:
                time.sleep(10)
                success, error_type = click_trending_part1_if_needed(driver, browser_id, trending_part1)
                if not success:
                    time.sleep(20)
                    success, error_type = click_trending_part1_if_needed(driver, browser_id, trending_part1)
                    if not success:
                        time.sleep(40)
                        success, error_type = click_trending_part1_if_needed(driver, browser_id, trending_part1)
                        if not success:
                            # 根据错误类型返回不同的错误信息
                            if error_type == "NO_ACCORDION":
                                error_msg = "[7]加载子主题内容超时"
                            else:
                                error_msg = "[7]点击子主题失败！查看配置是否正确"
                            add_bro_log_entry(bro_log_list, browser_id, error_msg)
                            return False, error_msg, None
            
        # 6.2 检查仓位和挂单，记录初始数量
        add_bro_log_entry(bro_log_list, browser_id, "[7]步骤6.2: 检查并记录初始仓位和挂单数量")
        log_print(f"[{browser_id}] 步骤6.2: 检查并记录初始仓位和挂单数量...")
        
        # 检查 Position 数量
        # Buy: 返回实际持仓数量；Sell: 返回实际持仓数量
        # Buy时如果已有对向仓位且数量>=10返回-2
        initial_position_count = check_position_count(driver, browser_id, trending_part1, trade_type, option_type)
        
        # Buy类型：如果返回-2，表示已有对向仓位且数量>=10，不能继续执行
        if trade_type == "Buy" and initial_position_count == -2:
            add_bro_log_entry(bro_log_list, browser_id, f"[7]{browser_id}已有对向仓位且数量>=10")
            return False, f"[5]{browser_id}已有对向仓位且数量>=10", None
        
        if initial_position_count < 0:
            log_print(f"[{browser_id}] ⚠ 无法获取 Position 数量，设为 0")
            initial_position_count = 0
        
        if trade_type == "Sell":
            log_print(f"[{browser_id}] 初始持仓数量: {initial_position_count}")
        else:
            log_print(f"[{browser_id}] 初始持仓数量: {initial_position_count}")
        
        add_bro_log_entry(bro_log_list, browser_id, f"[7]初始持仓数量: {initial_position_count}")
        
        # Buy 类型：允许有同向仓位，可以继续执行后面的逻辑
        
        # Sell 类型：如果没有仓位则不能下单
        if trade_type == "Sell" and initial_position_count == 0:
            add_bro_log_entry(bro_log_list, browser_id, f"[7]{browser_id}无仓位可平")
            return False, f"[7]{browser_id}无仓位可平", None
        
        # 检查 Open Orders 数量
        add_bro_log_entry(bro_log_list, browser_id, "[7]步骤6.3: 检查 Open Orders")
        log_print(f"[{browser_id}] 步骤6.3: 检查 Open Orders...")
        initial_open_orders_count = get_opinion_table_row_count(driver, browser_id, need_click_open_orders=True, trending_part1=trending_part1)
        
        if initial_open_orders_count < 0:
            log_print(f"[{browser_id}] ⚠ 无法获取 Open Orders 数量，设为 0")
            initial_open_orders_count = 0
        
        log_print(f"[{browser_id}] 初始 Open Orders 数量: {initial_open_orders_count}")
        add_bro_log_entry(bro_log_list, browser_id, f"[7]初始 Open Orders 数量: {initial_open_orders_count}")
        
        # 获取 Closed Orders 的最新时间
        add_bro_log_entry(bro_log_list, browser_id, "[7]步骤6.4: 检查 Closed Orders")
        log_print(f"[{browser_id}] 步骤6.4: 检查 Closed Orders...")
        initial_closed_orders_time = get_closed_orders_latest_time(driver, browser_id)
        
        if not initial_closed_orders_time:
            log_print(f"[{browser_id}] ⚠ 无法获取 Closed Orders 最新时间，设为空字符串")
            initial_closed_orders_time = ""
        
        log_print(f"[{browser_id}] 初始 Closed Orders 最新时间: {initial_closed_orders_time}")
        add_bro_log_entry(bro_log_list, browser_id, f"[7]初始 Closed Orders 最新时间: {initial_closed_orders_time}")
        
        # Buy 和 Sell 类型：如果已有挂单则不能下单
        if initial_open_orders_count > 0:
            add_bro_log_entry(bro_log_list, browser_id, f"{browser_id}已有挂单")
            return False, f"[7]{browser_id}已有挂单", None
        
        if trade_type == "Buy":
            add_bro_log_entry(bro_log_list, browser_id, "[7]Buy 类型检查通过：无仓位，无挂单")
            log_print(f"[{browser_id}] ✓ Buy 类型检查通过：无仓位，无挂单")
        else:
            add_bro_log_entry(bro_log_list, browser_id, "[7]Sell 类型检查通过：有仓位，无挂单")
            log_print(f"[{browser_id}] ✓ Sell 类型检查通过：有仓位，无挂单")
        
        # 重试机制：第7-12步最多重试2次（总共3次尝试）
        max_retry_attempts = 2
        retry_count = 0
        last_failure_step = None  # 跟踪最后失败的步骤
        
        while retry_count <= max_retry_attempts:
            try:
                if retry_count > 0:
                    # 检查当前是否在OKX界面，如果是则切换回主页面
          
                    log_print(f"[{browser_id}] ⚠ 第{retry_count}次重试，检查当前窗口...")
                    all_windows = driver.window_handles
                    current_url = driver.current_url
                    
                    # 如果当前在OKX界面，切换回主页面
                    if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                        log_print(f"[{browser_id}] ⚠ 当前在OKX界面，切换回主页面...")
                        for window in all_windows:
                            driver.switch_to.window(window)
                            current_url = driver.current_url
                            if "app.opinion.trade" in current_url:
                                log_print(f"[{browser_id}] ✓ 已切换回主页面")
                                break
                        time.sleep(2)  # 等待页面切换完成
                    
                
                    log_print(f"[{browser_id}] ⚠ 第{retry_count}次重试，先导航到目标页面...")
                    try:
                        driver.get(target_url)
                        log_print(f"[{browser_id}] ✓ 已导航到目标页面")
                        time.sleep(2)  # 等待页面加载
                    except Exception as e:
                   
                        log_print(f"[{browser_id}] ✗ 导航到目标页面失败: {str(e)}")
                    
                    log_print(f"[{browser_id}] 刷新页面...")
                    refresh_page_with_opinion_check(driver, browser_id)
                    
                    # 重新等待页面加载
                    log_print(f"[{browser_id}] 等待页面重新加载...")
                    trade_box = wait_for_opinion_trade_box(driver, browser_id, max_retries=3)
                    if not trade_box:
                        add_bro_log_entry(bro_log_list, browser_id, "[8]页面重新加载失败")
                        log_print(f"[{browser_id}] ✗ 页面重新加载失败")
                        last_failure_step = "[8]页面重新加载失败"
                        retry_count += 1
                        continue
                    
                    # 重新检查并连接钱包
                    add_bro_log_entry(bro_log_list, browser_id, "[8]重新检查并连接钱包")
                    log_print(f"[{browser_id}] 重新检查并连接钱包...")
                    connect_wallet_if_needed(driver, browser_id)
                    
                    # 重新等待Position按钮出现
                    add_bro_log_entry(bro_log_list, browser_id, "[8]重新等待Position按钮")
                    log_print(f"[{browser_id}] 重新等待Position按钮...")
                    if not wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
                        add_bro_log_entry(bro_log_list, browser_id, "[8]Position按钮未出现")
                        log_print(f"[{browser_id}] ✗ Position按钮未出现")
                        last_failure_step = "Position按钮未出现"
                        retry_count += 1
                        continue
                    
                    # 如果有 trendingPart1，重新点击子主题
                    if trending_part1:
                        add_bro_log_entry(bro_log_list, browser_id, f"[8]重新点击子主题 {trending_part1}")
                        log_print(f"[{browser_id}] 重新点击子主题 {trending_part1}...")
                        success, error_type = click_trending_part1_if_needed(driver, browser_id, trending_part1)
                        if not success:
                            add_bro_log_entry(bro_log_list, browser_id, "[8]点击子主题失败，继续执行")
                            log_print(f"[{browser_id}] ⚠ 点击子主题失败，继续执行...")
                            retry_count += 1
                            continue
                
                
                
                add_bro_log_entry(bro_log_list, browser_id, "[8]步骤7.1: 选择买卖类型 Buy")
                log_print(f"[{browser_id}] 步骤7.1: 选择买卖类型 Buy...")
                if not click_opinion_trade_type_button(trade_box, "Buy", browser_id):
                    add_bro_log_entry(bro_log_list, browser_id, f"[8]未找到{trade_type}按钮")
                    log_print(f"[{browser_id}] ✗ 未找到{trade_type}按钮")
                    last_failure_step = f"[8]选择买卖类型{trade_type}失败"
                    retry_count += 1
                    continue
                
                trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
        
                if not trade_box_divs:
                    add_bro_log_entry(bro_log_list, browser_id, "未找到 trade-box div")
                    log_print(f"[{browser_id}] ⚠ 未找到 trade-box div")
                    return False, "[8]未找到 trade-box div", None
                
                trade_box1 = trade_box_divs[0]
                log_print(f"[{browser_id}] ✓ 找到 trade-box div")
                
                # 在 trade-box 中查找 tabs content div
                log_print(f"[{browser_id}] 查找 tabs content div...")
                tabs_content_divs = trade_box1.find_elements(By.CSS_SELECTOR, 
                    'div[data-scope="tabs"][data-part="content"][data-state="open"]')
                
                if not tabs_content_divs:
                    add_bro_log_entry(bro_log_list, browser_id, "[8]未找到 tabs content div")
                    log_print(f"[{browser_id}] ⚠ 未找到 tabs content div")
                    return False, "[8]未找到 tabs content div", None
                
                tabs_content = tabs_content_divs[0]
                log_print(f"[{browser_id}] ✓ 找到 tabs content div")
                
                # 获取初始可用余额
                initial_available_balance = get_available_balance_from_tabs_content(tabs_content, browser_id)
                if initial_available_balance:
                    add_bro_log_entry(bro_log_list, browser_id, f"[8]获取到初始可用余额: {initial_available_balance}")
                    log_print(f"[{browser_id}] ✓ 获取到初始可用余额: {initial_available_balance}")
                else:
                    add_bro_log_entry(bro_log_list, browser_id, "[8]未能获取初始可用余额，将使用 None")
                    log_print(f"[{browser_id}] ⚠ 未能获取初始可用余额，将使用 None")
                    initial_available_balance = None
                
                
                
                
                # 7. 点击买卖类型按钮
                add_bro_log_entry(bro_log_list, browser_id, f"[8]步骤7: 选择买卖类型 {trade_type}")
                log_print(f"[{browser_id}] 步骤7: 选择买卖类型 {trade_type}...")
                if not click_opinion_trade_type_button(trade_box, trade_type, browser_id):
                    add_bro_log_entry(bro_log_list, browser_id, f"[8]未找到{trade_type}按钮")
                    log_print(f"[{browser_id}] ✗ 未找到{trade_type}按钮")
                    last_failure_step = f"[8]选择买卖类型{trade_type}失败"
                    retry_count += 1
                    continue
                
                
                # 8. 选择价格类型
                add_bro_log_entry(bro_log_list, browser_id, f"[8]步骤8: 选择价格类型 {price_type}")
                log_print(f"[{browser_id}] 步骤8: 选择价格类型 {price_type}...")
                if not select_opinion_price_type(trade_box, price_type, browser_id):
                    add_bro_log_entry(bro_log_list, browser_id, f"[8]选择价格类型{price_type}失败")
                    log_print(f"[{browser_id}] ✗ 选择价格类型{price_type}失败")
                    last_failure_step = f"[8]选择价格类型{price_type}失败"
                    retry_count += 1
                    continue
                
                
                
                trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
        
                if not trade_box_divs:
                    log_print(f"[{browser_id}] ⚠ 未找到 trade-box div")
                    return False, "[8]未找到 trade-box div", None
                
                trade_box1 = trade_box_divs[0]
                log_print(f"[{browser_id}] ✓ 找到 trade-box div")
                
                # 在 trade-box 中查找 tabs content div
                log_print(f"[{browser_id}] 查找 tabs content div...")
                tabs_content_divs = trade_box1.find_elements(By.CSS_SELECTOR, 
                    'div[data-scope="tabs"][data-part="content"][data-state="open"]')
                
                if not tabs_content_divs:
                    log_print(f"[{browser_id}] ⚠ 未找到 tabs content div")
                    return False, "[8]未找到 tabs content div", None
                
                tabs_content = tabs_content_divs[0]
                log_print(f"[{browser_id}] ✓ 找到 tabs content div")
                
                
                # 9. 选择种类
                add_bro_log_entry(bro_log_list, browser_id, f"[8]步骤9: 选择种类 {option_type}")
                log_print(f"[{browser_id}] 步骤9: 选择种类 {option_type}...")
                if not select_opinion_option_type(tabs_content, option_type, browser_id):
                    add_bro_log_entry(bro_log_list, browser_id, f"[8]选择种类{option_type}失败")
                    log_print(f"[{browser_id}] ✗ 选择种类{option_type}失败")
                    last_failure_step = f"[8]选择种类{option_type}失败"
                    retry_count += 1
                    continue
                
                
                
                # 7.5 Type 5 任务特殊处理：订单薄检查和价格调整
                if task_data:
                    mission = task_data.get('mission', {})
                    exchange_config = task_data.get('exchangeConfig', {})
                    mission_type = mission.get('type')
                    
                    
                    if mission_type == 5 or mission_type == 9 or mission_type == 6:
                        add_bro_log_entry(bro_log_list, browser_id, "[8]步骤7.5: Type 5 任务 - 订单薄检查和价格调整")
                        log_print(f"[{browser_id}] 步骤7.5: Type 5 任务 - 订单薄检查和价格调整...")
                        
                        tp10 = mission.get('tp10')
                        tp1 = mission.get('tp1')
                        is_task1 = not tp1  # 如果tp1为空，则是任务一
                        
                        # Type 9/6 任务特殊处理：等待同步价格
                        if mission_type == 9 or mission_type == 6:
                            mission_id = mission.get('id')
                            log_msg = "[5]开始等待同步价格..."
                            log_print(f"[{browser_id}] {log_msg}")
                            add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                            
                            # 先把任务状态改为 18
                            save_mission_result(mission_id, 18, "[5]等待同步价格")
                            
                            # 5分钟内每隔10秒检查状态
                            sync_start_time = time.time()
                            sync_timeout = 420  # 7分钟
                            sync_check_interval = 10  # 10秒
                            sync_success = False
                            
                            while time.time() - sync_start_time < sync_timeout:
                                # 获取自己的状态
                                my_info = get_mission_info(mission_id)
                                if my_info:
                                    my_status = my_info.get('status')
                                    
                                    if my_status == 9 or my_status == 0:
                                        # 状态是9或0，保存状态为18
                                        log_msg = f"[5]当前状态为{my_status}，继续等待同步..."
                                        log_print(f"[{browser_id}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                        save_mission_result(mission_id, 18, "[5]等待同步价格")
                                    elif my_status == 19:
                                        # 状态是19，继续下面的流程
                                        log_msg = "[5]状态为19，同步价格完成"
                                        log_print(f"[{browser_id}] ✓ {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                        sync_success = True
                                        break
                                    elif my_status == 3:
                                        # 状态是3，返回失败
                                        fail_msg = "[5]等待同步价格失败"
                                        log_print(f"[{browser_id}] ✗ {fail_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                        return False, fail_msg, None
                                
                                time.sleep(sync_check_interval)
                            
                            # 检查是否超时
                            if not sync_success:
                                fail_msg = "[5]等待同步价格超时"
                                log_print(f"[{browser_id}] ✗ {fail_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                return False, fail_msg, None
                        
                        if is_task1:
                            # 【1】任务一的逻辑
                            log_print(f"[{browser_id}] [任务一] 开始订单薄检查...")
                            add_bro_log_entry(bro_log_list, browser_id, "[8][任务一] 开始订单薄检查")
                            
                            # 判断交易方向（YES/NO）
                            ps_side = mission.get('psSide', 1)  # 1=YES, 2=NO
                            if ps_side == 1:
                                # YES方向，获取trendingPart1
                                token_id = exchange_config.get('trendingPart1', '')
                            else:
                                # NO方向，获取trendingPart2
                                token_id = exchange_config.get('trendingPart2', '')
                            
                            if not token_id:
                                log_msg = f"[5]订单薄获取失败"
                                log_print(f"[{browser_id}] ✗ {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                save_mission_result(mission.get('id'), 21, log_msg)
                                # 继续后面的步骤
                            else:
                                # 获取订单薄数据（最多重试5次）
                                orderbook_data = None
                                max_orderbook_retries = 5
                                orderbook_retry_count = 0
                                
                                while orderbook_data is None and orderbook_retry_count < max_orderbook_retries:
                                    orderbook_data = fetch_orderbook_data(token_id)
                                    if orderbook_data is None:
                                        orderbook_retry_count += 1
                                        if orderbook_retry_count < max_orderbook_retries:
                                            log_msg = f"[5]订单薄数据获取失败，重试中... ({orderbook_retry_count}/{max_orderbook_retries})"
                                            log_print(f"[{browser_id}] {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                            time.sleep(2)
                                
                                if orderbook_data is None:
                                    # 5次都失败，保存状态并继续
                                    log_msg = "[5]订单薄获取失败"
                                    log_print(f"[{browser_id}] ✗ {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                    save_mission_result(mission.get('id'), 21, log_msg)
                                    # 继续后面的步骤
                                else:
                                    # 解析订单薄数据
                                    best_bid_price, best_bid_depth, best_ask_price, best_ask_depth = get_best_bid_ask(orderbook_data)
                                    best_bid_value =(best_bid_price*best_bid_depth)/100
                                    best_ask_value =(best_ask_price*best_ask_depth)/100
                                    
                                    if best_bid_price is None or best_ask_price is None:
                                        log_msg = "[5]订单薄获取失败"
                                        log_print(f"[{browser_id}] ✗ {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                        save_mission_result(mission.get('id'), 21, log_msg)
                                        # 继续后面的步骤
                                    else:
                                        # 获取买一价和卖一价（已在 get_best_bid_ask 中转换为百分比）
                                        
                                        # 计算深度差（卖一价减去买一价的绝对值）
                                        depth_diff = abs(best_ask_price - best_bid_price)
                                        
                                        current_price = float(mission.get('price', 0))
                                        price_changed = False
                                        new_price = current_price
                                        
                                        log_msg = f"[5]订单薄数据: 买一价={best_bid_price:.1f}, 买一深度={best_bid_depth:.2f}, 卖一价={best_ask_price:.1f}, 卖一深度={best_ask_depth:.2f}, 深度差={depth_diff:.2f}, 当前价格={current_price:.1f}"
                                        log_print(f"[{browser_id}] {log_msg}")
                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                        
                                        if depth_diff > 0.15:
                                            # 【1.1】深度差大于0.15
                                            # 判断价格是否在买一价和卖一价之间（不包含等于）
                                            if best_bid_price < current_price < best_ask_price:
                                                # 【1.1.1】价格在中间，成功
                                                log_msg = "[5]订单薄符合条件"
                                                log_print(f"[{browser_id}] ✓ {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                                save_mission_result(mission.get('id'), 21, log_msg)
                                            else:
                                                # 【1.1.2】价格不在中间，需要调整
                                                # 新价格 = (买一价 + 卖一价) / 2，保留一位小数
                                                new_price = round((best_bid_price + best_ask_price) / 2, 1)
                                                price_changed = True
                                                
                                                log_msg = f"[5]价格需要调整: {current_price:.1f} -> {new_price:.1f}"
                                                log_print(f"[{browser_id}] {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                        else:
                                            # 【1.2】深度差小于等于0.15
                                            # 获取tp4，如果不存在默认为100
                                            tp4 = float(mission.get('tp4', 200))
                                            log_print(f"[{browser_id}] tp4 {tp4}")
                                            if trade_type == "Buy":
                                                # 【1.2.1】开仓（买）
                                                is_best_bid = abs(current_price - best_bid_price) < 0.01
                                                
                                                if is_best_bid:
                                                    # 【1.2.1.1】是买一价
                                                    if best_bid_value > tp4:
                                                        # 深度大于tp4，返回失败
                                                        fail_msg = f"[5]-11订单薄不符合条件{{买一价{best_bid_price:.1f}，买一价深度{best_bid_depth:.2f};卖一价{best_ask_price:.1f}，卖一价深度{best_ask_depth:.2f}}}"
                                                        log_print(f"[{browser_id}] ✗ {fail_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"{fail_msg}")
                                                        return False, fail_msg, None
                                                    else:
                                                        # 深度小于等于tp4，成功
                                                        log_msg = "[5]-12订单薄符合条件"
                                                        log_print(f"[{browser_id}] ✓ {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                                        save_mission_result(mission.get('id'), 21, log_msg)
                                                else:
                                                    # 【1.2.1.2】不是买一价
                                                    if best_bid_price > current_price:
                                                        # 买一价大于我的价格
                                                        fail_msg = f"[5]-13订单薄不符合条件{{买一价{best_bid_price:.1f}，买一价深度{best_bid_depth:.2f};卖一价{best_ask_price:.1f}，卖一价深度{best_ask_depth:.2f}}}"
                                                        log_print(f"[{browser_id}] ✗ {fail_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                                        return False, fail_msg, None
                                                    else:
                                                        # 买一价小于我的价格
                                                        if best_ask_value > tp4:
                                                            fail_msg = f"[5]-14订单薄不符合条件{{买一价{best_bid_price:.1f}，买一价深度{best_bid_depth:.2f};卖一价{best_ask_price:.1f}，卖一价深度{best_ask_depth:.2f}}}"
                                                            log_print(f"[{browser_id}] ✗ {fail_msg}")
                                                            add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                                            return False, fail_msg, None
                                                        else:
                                                            log_msg = f"[5]-15符合条件"
                                                            log_print(f"[{browser_id}] {log_msg}")
                                                            add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                            else:
                                                # 【1.2.2】平仓（卖）
                                                is_best_ask = abs(current_price - best_ask_price) < 0.01
                                                
                                                if is_best_ask:
                                                    # 【1.2.2.1】是卖一价
                                                    if best_ask_value > tp4:
                                                        # 深度大于tp4，返回失败
                                                        fail_msg = f"[5]-1订单薄不符合条件{{买一价{best_bid_price:.1f}，买一价深度{best_bid_depth:.2f};卖一价{best_ask_price:.1f}，卖一价深度{best_ask_depth:.2f}}}"
                                                        log_print(f"[{browser_id}] ✗ {fail_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"{fail_msg}")
                                                        return False, fail_msg, None
                                                    else:
                                                        # 深度小于等于tp4，成功
                                                        log_msg = "[5]-3订单薄符合条件"
                                                        log_print(f"[{browser_id}] ✓ {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                        save_mission_result(mission.get('id'), 21, log_msg)
                                                else:
                                                    # 【1.2.2.2】不是卖一价
                                                    if best_ask_price < current_price:
                                                        fail_msg = f"[5]-3订单薄不符合条件{{买一价{best_bid_price:.1f}，买一价深度{best_bid_depth:.2f};卖一价{best_ask_price:.1f}，卖一价深度{best_ask_depth:.2f}}}"
                                                        log_print(f"[{browser_id}] ✗ {fail_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"{fail_msg}")
                                                        return False, fail_msg, None
                                                    else:
                                                        # 卖一价大于我的价格
                                                        if best_bid_value > tp4:
                                                            fail_msg = f"[5]-4订单薄不符合条件{{买一价{best_bid_price:.1f}，买一价深度{best_bid_depth:.2f};卖一价{best_ask_price:.1f}，卖一价深度{best_ask_depth:.2f}，卖一价价值{best_ask_value:.2f}}}"
                                                            log_print(f"[{browser_id}] ✗ {fail_msg}")
                                                            add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                                            return False, fail_msg, None
                                                        else:
                                                            log_msg = f"[5]-5符合条件"
                                                            log_print(f"[{browser_id}] {log_msg}")
                                                            add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                 
                                        
                                        # 如果价格需要更改，调用updateMissionTp更新价格
                                        if price_changed:
                                            mission_id = mission.get('id')
                                            update_success = update_mission_tp(mission_id, price=new_price)
                                            
                                            if update_success:
                                                # 等待3秒后验证价格是否已更新
                                                time.sleep(3)
                                                
                                                # 最多重试3次验证价格
                                                max_verify_retries = 3
                                                verify_retry_count = 0
                                                price_verified = False
                                                
                                                while verify_retry_count < max_verify_retries:
                                                    updated_mission = get_mission_info(mission_id)
                                                    if updated_mission:
                                                        updated_price = float(updated_mission.get('price', 0))
                                                        if abs(updated_price - new_price) < 0.01:
                                                            price_verified = True
                                                            break
                                                    
                                                    verify_retry_count += 1
                                                    if verify_retry_count < max_verify_retries:
                                                        log_msg = f"[5]价格验证失败，重试中... ({verify_retry_count}/{max_verify_retries})"
                                                        log_print(f"[{browser_id}] {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                        time.sleep(3)
                                                
                                                if price_verified:
                                                    log_msg = "[5]已更改价格"
                                                    log_print(f"[{browser_id}] ✓ {log_msg}")
                                                    add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                    save_mission_result(mission_id, 21, log_msg)
                                                    # 更新price变量，用于后续步骤
                                                    price = new_price
                                                    # 同时更新task_data中的价格，确保后续检查使用新价格
                                                    mission['price'] = new_price
                                                    
                                                    # 调用 /hedge/recentPrice 保存最近的价格
                                                   
                                                    ps_side = mission.get('psSide', 1)
                                                    outcome = "YES" if ps_side == 1 else "NO"
                                                    if trendingId:
                                                        save_price_success = save_recent_price(trendingId, outcome, new_price)
                                                        if save_price_success:
                                                            log_msg = f"[5]已保存最近价格: trendingId={trendingId}, outcome={outcome}, price={new_price}"
                                                            log_print(f"[{browser_id}] ✓ {log_msg}")
                                                            add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                        else:
                                                            log_msg = f"[5]保存最近价格失败，但继续执行"
                                                            log_print(f"[{browser_id}] ⚠ {log_msg}")
                                                            add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                    else:
                                                        log_msg = f"[5]trendingId为空，跳过保存最近价格"
                                                        log_print(f"[{browser_id}] ⚠ {log_msg}")
                                                        add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                else:
                                                    log_msg = f"[5]价格更新后验证失败，但继续执行"
                                                    log_print(f"[{browser_id}] ⚠ {log_msg}")
                                                    add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                            else:
                                                log_msg = f"[5]价格更新接口调用失败"
                                                log_print(f"[{browser_id}] ⚠ {log_msg}")
                                                add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                                return False, fail_msg, None
                            
                            # 任务1改价逻辑完成后，重新获取任务数据，更新amt
                            log_print(f"[{browser_id}] [任务一] 改价逻辑完成，重新获取任务数据...")
                            updated_task_data = get_mission_info(mission.get('id'))
                            if updated_task_data:
                                new_amt = updated_task_data.get('amt', 0)
                                old_amt = mission.get('amt', 0)
                                if new_amt != old_amt:
                                    log_msg = f"[5]amt已更新: {old_amt} -> {new_amt}"
                                    log_print(f"[{browser_id}] ✓ {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                    # 更新mission中的amt
                                    mission['amt'] = new_amt
                                    # 更新amount变量，确保后续下单使用新的amt
                                    amount = new_amt
                                else:
                                    log_print(f"[{browser_id}] [任务一] amt未变化: {old_amt}")
                            else:
                                log_print(f"[{browser_id}] ⚠ [任务一] 重新获取任务数据失败，继续使用原amt")
                        else:
                            # 【2】任务二的逻辑
                            log_print(f"[{browser_id}] [任务二] 开始等待任务一确认订单薄...")
                            add_bro_log_entry(bro_log_list, browser_id, "[8][任务二] 开始等待任务一确认订单薄")
                            
                            task1_id = tp1
                            start_time = time.time()
                            timeout = 600  # 10分钟 = 600秒
                            if mission_type == 6 or mission_type == 9:
                                timeout = 60 # 1分钟
                            check_interval = 15  # 每20秒检查一次
                            
                            task1_price_updated = False
                            
                            while time.time() - start_time < timeout:
                                # 获取任务1的状态
                                task1_info = get_mission_info(task1_id)
                                
                                if not task1_info:
                                    log_msg = f"[5]无法获取任务一信息，继续等待..."
                                    log_print(f"[{browser_id}] {log_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, f"{log_msg}")
                                    time.sleep(check_interval)
                                    continue
                                
                                task1_status = task1_info.get('status')
                                
                                if task1_status == 21 or task1_status == 5 or task1_status == 20:
                                    # 任务1状态是21或5，获取任务1的price和psSide
                                    task1_price = float(task1_info.get('price', 0))
                                    task1_psSide = task1_info.get('psSide')
                                    
                                    # 获取自己的psSide
                                    my_psSide = mission.get('psSide')
                                    
                                    # 根据psSide判断价格计算方式
                                    if task1_psSide is not None and my_psSide is not None and task1_psSide == my_psSide:
                                        # psSide一致，价格与任务1一致
                                        calculated_price = task1_price
                                    else:
                                        # psSide不一致，价格为 100 - 任务1的价格（四舍五入保留1位小数）
                                        calculated_price = round(100 - task1_price, 1)
                                    
                                    # 获取自己任务的当前price
                                    current_price = float(mission.get('price', 0))
                                    
                                    # 判断price是否已变化（考虑精度误差）
                                    if abs(calculated_price - current_price) >= 0.01:
                                        # price已变化，调用updateMissionTp更新
                                        mission_id = mission.get('id')
                                        update_success = update_mission_tp(mission_id, price=calculated_price)
                                        
                                        if update_success:
                                            psSide_info = f"任务一psSide={task1_psSide}, 自己psSide={my_psSide}"
                                            log_msg = f"[5]价格已更新: {current_price:.1f} -> {calculated_price:.1f} (任务一价格: {task1_price:.1f}, {psSide_info})"
                                            log_print(f"[{browser_id}] ✓ {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                            price = calculated_price  # 更新price变量
                                            # 同时更新task_data中的价格，确保后续检查使用新价格
                                            mission['price'] = calculated_price
                                            task1_price_updated = True
                                        else:
                                            log_msg = f"[5]价格更新失败，但继续执行"
                                            log_print(f"[{browser_id}] ⚠ {log_msg}")
                                            add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")
                                    
                                    # 继续后面的步骤
                                    break
                                elif task1_status == 3:
                                    # 任务1状态变为3，返回失败
                                    fail_msg = "[5]等待任务一确认订单薄，任务一失败"
                                    log_print(f"[{browser_id}] ✗ {fail_msg}")
                                    add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                    return False, fail_msg, None
                                
                                # 等待20秒后再次检查
                                time.sleep(check_interval)
                            
                            # 检查是否超时
                            if time.time() - start_time >= timeout:
                                fail_msg = "[5]等待任务一确认订单超时"
                                log_print(f"[{browser_id}] ✗ {fail_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, f"[8]{fail_msg}")
                                return False, fail_msg, None
                            
                            if not task1_price_updated:
                                log_msg = f"[5]价格无变化，继续执行"
                                log_print(f"[{browser_id}] {log_msg}")
                                add_bro_log_entry(bro_log_list, browser_id, f"[8]{log_msg}")

                            if tp10 == "1":
                                if trade_type == "Buy":
                                    ncalculated_price =  round(price + 0.1, 1)  
                                else:
                                    ncalculated_price =  round(price - 0.1, 1)  
                                price = ncalculated_price  # 更新price变量
                                mission['price'] = ncalculated_price
                
                
                
                   
                # 10. 点击 Amount 标签
                add_bro_log_entry(bro_log_list, browser_id, "[8]步骤10: 点击 Amount 标签")
                log_print(f"[{browser_id}] 步骤10: 点击 Amount 标签...")
                click_opinion_amount_tab(tabs_content, browser_id)
                
                
                time.sleep(6)

                # 11. 填入价格和数量
                add_bro_log_entry(bro_log_list, browser_id, f"[8]步骤11: 填入价格和数量（模式：{price_type}）")
                log_print(f"[{browser_id}] 步骤11: 填入价格和数量（模式：{price_type}）...")
                # Market模式传None，Limit模式传price
                fill_price = None if price_type == "Market" else price
                if not fill_opinion_price_and_amount(tabs_content, fill_price, amount, browser_id):
                    add_bro_log_entry(bro_log_list, browser_id, "[8]填入价格/数量失败")
                    log_print(f"[{browser_id}] ✗ 填入价格/数量失败")
                    last_failure_step = "[8]填入价格/数量失败"
                    retry_count += 1
                    continue
                
                # 12. 提交订单
                add_bro_log_entry(bro_log_list, browser_id, "[8]步骤12: 提交订单")
                log_print(f"[{browser_id}] 步骤12: 提交订单...")
                submit_success, should_retry = submit_opinion_order(driver, tabs_content, trade_type, option_type, browser_id, browser_id, task_data, bro_log_list, trendingId)
                if not submit_success:
                    add_bro_log_entry(bro_log_list, browser_id, "[9]提交订单失败")
                    log_print(f"[{browser_id}] ✗ 提交订单失败")
                    if not should_retry:
                        # type=5点击取消按钮，不应重试
                        add_bro_log_entry(bro_log_list, browser_id, "[9]Type 5 任务已取消，不进行重试")
                        log_print(f"[{browser_id}] ✗ Type 5 任务已取消，不进行重试")
                        return False, "[9]另一个任务已失败", None
                    elif isinstance(should_retry, str):
                        # should_retry是字符串，表示具体的失败原因
                        add_bro_log_entry(bro_log_list, browser_id, f"[9]Type 5 任务失败: {should_retry}")
                        log_print(f"[{browser_id}] ✗ Type 5 任务失败: {should_retry}")
                        return False, should_retry, None
                    last_failure_step = "[9]提交订单失败"
                    retry_count += 1
                    continue
                
                # 如果所有步骤都成功，跳出循环
                add_bro_log_entry(bro_log_list, browser_id, "[11]步骤7-12执行成功")
                log_print(f"[{browser_id}] ✓ 步骤7-12执行成功")
                break
                
            except Exception as e:
                add_bro_log_entry(bro_log_list, browser_id, f"[9]步骤7-12执行异常: {str(e)}")
                log_print(f"[{browser_id}] ✗ 步骤7-12执行异常: {str(e)}")
                last_failure_step = f"[9]执行异常: {str(e)}"
                retry_count += 1
                if retry_count > max_retry_attempts:
                    return False, last_failure_step, None
                continue
        
        # 检查是否所有重试都失败了
        if retry_count > max_retry_attempts:
            if last_failure_step:
                add_bro_log_entry(bro_log_list, browser_id, f"[9]执行步骤7-12失败: {last_failure_step}")
                return False, f"{last_failure_step}", None
            else:
                add_bro_log_entry(bro_log_list, browser_id, "[9]执行步骤7-12失败")
                return False, f"[7]执行步骤7-12失败", None
        
        # 13. 等待订单成功
        # Type 5 任务使用特殊的等待和数据收集逻辑
        mission = task_data.get('mission', {}) if task_data else {}
        mission_type = mission.get('type')
        
        if mission_type == 5 :
            tp3 = mission.get('tp3')
            if tp3 != "1":
                # Type 5 任务：检查是否有 "order failed" 并进行重试
                max_order_retry = 3  # 最多重试3次
                order_retry_count = 0

                # 切换回主页面
                try:
                        all_windows = driver.window_handles
                        for window in all_windows:
                            driver.switch_to.window(window)
                            current_url = driver.current_url
                            if "app.opinion.trade" in current_url:
                                log_print(f"[{browser_id}] ✓ 已切换回主页面")
                                break
                except Exception as e:
                        log_print(f"[{browser_id}] ⚠ 切换回主页面失败: {str(e)}")

                # # 判断是否是任务1，如果是任务1且有tp2，先进行tp2检查
                # tp1 = mission.get('tp1')
                # if not tp1:  # 是任务1
                #     tp2 = mission.get('tp2')
                #     if tp2:
                #         log_msg = f"[OP] 任务一: 检测到tp2，开始tp2时间段检查..."
                #         log_print(f"[{browser_id}] {log_msg}")
                #         add_bro_log_entry(bro_log_list, browser_id, log_msg)
                        
                #         # 进行tp2检查
                #         tp2_success, tp2_msg = check_tp2_position_and_orderbook(
                #             driver, browser_id, task_data, initial_position_count, 
                #             trade_type, option_type, trending_part1, amount, bro_log_list
                #         )
                        
                #         if not tp2_success:
                #             log_msg = f"[OP] 任务一: tp2检查失败: {tp2_msg}"
                #             log_print(f"[{browser_id}] {log_msg}")
                #             add_bro_log_entry(bro_log_list, browser_id, log_msg)
                #             return False, tp2_msg, None

                add_bro_log_entry(bro_log_list, browser_id, "[11]步骤13: Type 5 任务 - 等待订单确认并收集数据")
                log_print(f"[{browser_id}] 步骤13: Type 5 任务 - 等待订单确认并收集数据...")
                success, msg = wait_for_type5_order_and_collect_data(
                driver, 
                mission_type,
                initial_position_count, 
                browser_id, 
                trending_part1,
                task_data,
                trade_type,
                option_type,
                trending,
                amount,
                initial_open_orders_count,
                initial_closed_orders_time
                )


                if not success:
                    add_bro_log_entry(bro_log_list, browser_id, f"Type 5 任务失败: {msg}")
                    log_print(f"[{browser_id}] ========== Type 5 任务失败: {msg} ==========\n")
                    return False, msg, None
                else:
                    add_bro_log_entry(bro_log_list, browser_id, f"Type 5 任务成功: {msg}")
                    log_print(f"[{browser_id}] ========== Type 5 任务成功: {msg} ==========\n")
                    
                    # 监控可用余额变化（即使失败也不影响任务成功状态）
                    final_available_balance = None
                    if initial_available_balance is not None:
                        try:
                            add_bro_log_entry(bro_log_list, browser_id, "[11]开始监控可用余额变化")
                            log_print(f"[{browser_id}] 开始监控可用余额变化...")
                            # 重新获取 trade_box
                            trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                            if trade_box_divs:
                                current_trade_box = trade_box_divs[0]
                                final_available_balance = monitor_available_balance_change(
                                    driver, browser_id, initial_available_balance, current_trade_box, max_wait_time=180
                                )
                                add_bro_log_entry(bro_log_list, browser_id, f"[11]余额监控完成，最终可用余额: {final_available_balance}")
                                log_print(f"[{browser_id}] ✓ 余额监控完成，最终可用余额: {final_available_balance}")
                            else:
                                add_bro_log_entry(bro_log_list, browser_id, "未找到 trade-box，无法监控余额变化")
                                log_print(f"[{browser_id}] ⚠ 未找到 trade-box，无法监控余额变化")
                        except Exception as balance_error:
                            # 余额监控失败不影响任务成功状态
                            log_print(f"[{browser_id}] ⚠ 余额监控过程中发生异常: {str(balance_error)}，但不影响任务成功状态")
                            add_bro_log_entry(bro_log_list, browser_id, f"余额监控异常: {str(balance_error)}，但不影响任务成功")
                    else:
                        add_bro_log_entry(bro_log_list, browser_id, "初始可用余额为 None，跳过余额监控")
                        log_print(f"[{browser_id}] ⚠ 初始可用余额为 None，跳过余额监控")
                    
                    return True, msg, final_available_balance
            else:
                # 快速模式：不查看仓位变化，但仍监控可用余额变化
                add_bro_log_entry(bro_log_list, browser_id, "Type 5 任务快速模式（不查看仓位变化）")
                log_print(f"[{browser_id}] ========== Type 5 任务快速模式（不查看仓位变化）==========\n")
                
                # 监控可用余额变化
                final_available_balance = None
                if initial_available_balance is not None:
                    add_bro_log_entry(bro_log_list, browser_id, "开始监控可用余额变化")
                    log_print(f"[{browser_id}] 开始监控可用余额变化...")
                    # 重新获取 trade_box
                    trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                    if trade_box_divs:
                        current_trade_box = trade_box_divs[0]
                        final_available_balance = monitor_available_balance_change(
                            driver, browser_id, initial_available_balance, current_trade_box, max_wait_time=180
                        )
                        add_bro_log_entry(bro_log_list, browser_id, f"余额监控完成，最终可用余额: {final_available_balance}")
                        log_print(f"[{browser_id}] ✓ 余额监控完成，最终可用余额: {final_available_balance}")
                    else:
                        add_bro_log_entry(bro_log_list, browser_id, "未找到 trade-box，无法监控余额变化")
                        log_print(f"[{browser_id}] ⚠ 未找到 trade-box，无法监控余额变化")
                else:
                    add_bro_log_entry(bro_log_list, browser_id, "初始可用余额为 None，跳过余额监控")
                    log_print(f"[{browser_id}] ⚠ 初始可用余额为 None，跳过余额监控")
                
                return True, '快速模式不查看仓位变化', final_available_balance
        elif mission_type == 1:
            tp3 = mission.get('tp3')
            if tp3 != "1":
                # Type 1 任务使用与 Type 5 一致的等待逻辑
                add_bro_log_entry(bro_log_list, browser_id, "步骤13: Type 1 任务 - 等待订单确认并收集数据")
                log_print(f"[{browser_id}] 步骤13: Type 1 任务 - 等待订单确认并收集数据...")
                success, msg = wait_for_opinion_order_success(
                    driver, 
                    initial_open_orders_count, 
                    initial_position_count, 
                    trade_type,
                    browser_id, 
                    trending_part1,
                    option_type,
                    timeout=600,
                    trending=trending,
                    amount=amount,
                    initial_closed_orders_time=initial_closed_orders_time
                )
                
                if not success:
                    add_bro_log_entry(bro_log_list, browser_id, f"Type 1 任务失败: {msg}")
                    log_print(f"[{browser_id}] ========== Type 1 任务失败: {msg} ==========\n")
                    return False, msg, None
                else:
                    add_bro_log_entry(bro_log_list, browser_id, f"Type 1 任务成功: {msg}")
                    log_print(f"[{browser_id}] ========== Type 1 任务成功: {msg} ==========\n")
                    
                    # 监控可用余额变化
                    final_available_balance = None
                    if initial_available_balance is not None:
                        add_bro_log_entry(bro_log_list, browser_id, "开始监控可用余额变化")
                        log_print(f"[{browser_id}] 开始监控可用余额变化...")
                        # 重新获取 trade_box
                        trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                        if trade_box_divs:
                            current_trade_box = trade_box_divs[0]
                            final_available_balance = monitor_available_balance_change(
                                driver, browser_id, initial_available_balance, current_trade_box, max_wait_time=180
                            )
                            add_bro_log_entry(bro_log_list, browser_id, f"余额监控完成，最终可用余额: {final_available_balance}")
                            log_print(f"[{browser_id}] ✓ 余额监控完成，最终可用余额: {final_available_balance}")
                        else:
                            add_bro_log_entry(bro_log_list, browser_id, "未找到 trade-box，无法监控余额变化")
                            log_print(f"[{browser_id}] ⚠ 未找到 trade-box，无法监控余额变化")
                    else:
                        add_bro_log_entry(bro_log_list, browser_id, "初始可用余额为 None，跳过余额监控")
                        log_print(f"[{browser_id}] ⚠ 初始可用余额为 None，跳过余额监控")
                    
                    return True, msg, final_available_balance
            else:
                # 快速模式：不查看仓位变化，但仍监控可用余额变化
                add_bro_log_entry(bro_log_list, browser_id, "Type 1 任务快速模式（不查看仓位变化）")
                log_print(f"[{browser_id}] ========== Type 1 任务快速模式（不查看仓位变化）==========\n")
                
                # 监控可用余额变化
                final_available_balance = None
                if initial_available_balance is not None:
                    add_bro_log_entry(bro_log_list, browser_id, "开始监控可用余额变化")
                    log_print(f"[{browser_id}] 开始监控可用余额变化...")
                    # 重新获取 trade_box
                    trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                    if trade_box_divs:
                        current_trade_box = trade_box_divs[0]
                        final_available_balance = monitor_available_balance_change(
                            driver, browser_id, initial_available_balance, current_trade_box, max_wait_time=180
                        )
                        add_bro_log_entry(bro_log_list, browser_id, f"余额监控完成，最终可用余额: {final_available_balance}")
                        log_print(f"[{browser_id}] ✓ 余额监控完成，最终可用余额: {final_available_balance}")
                    else:
                        add_bro_log_entry(bro_log_list, browser_id, "未找到 trade-box，无法监控余额变化")
                        log_print(f"[{browser_id}] ⚠ 未找到 trade-box，无法监控余额变化")
                else:
                    add_bro_log_entry(bro_log_list, browser_id, "初始可用余额为 None，跳过余额监控")
                    log_print(f"[{browser_id}] ⚠ 初始可用余额为 None，跳过余额监控")
                
                return True, '快速模式不查看仓位变化', final_available_balance
        elif mission_type == 6 or mission_type == 9:
            add_bro_log_entry(bro_log_list, browser_id, "Type 6 任务 - 等待订单确认并收集数据")
            log_print(f"[{browser_id}] 步骤13: Type 6 任务 - 等待订单确认并收集数据...")
            success, msg = wait_for_type6_order_and_collect_data(
                driver, 
                initial_position_count, 
                browser_id, 
                trending_part1,
                task_data,
                trade_type,
                option_type,
                trending,
                amount,
                initial_open_orders_count,
                initial_closed_orders_time
            )
            return success, msg, None
        
    except Exception as e:
        error_msg = str(e)
        log_print(f"[{browser_id}] ✗✗✗ Opinion Trade 任务执行异常: {error_msg}")
        import traceback
        error_detail = traceback.format_exc()
        log_print(f"[{browser_id}] 错误详情:\n{error_detail}")
        add_bro_log_entry(bro_log_list, browser_id, f"错误详情: {error_detail[:200]}")
        return False, f"执行异常: {error_msg}", None


def process_polymarket_trade(driver, browser_id, trade_type, price_type, option_type, price, amount, is_new_browser, current_ip=None, current_delay=None):
    """
    处理 Polymarket 交易流程
    
    Args:
        is_new_browser: 是否是新启动的浏览器
        current_ip: 当前使用的IP地址（可选）
        current_delay: 当前IP的延迟（可选，单位：毫秒）
    
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
            preopen_okx_wallet(driver, browser_id, current_ip, current_delay)
        else:
            log_print(f"[{browser_id}] 步骤6: 跳过预打开OKX钱包（浏览器已在运行）")
        
        # 6.5 检查driver会话是否有效，如果失效则重新获取trade_box
        log_print(f"[{browser_id}] 步骤6.5: 检查浏览器会话有效性...")
        if not check_driver_session_valid(driver, browser_id):
            log_print(f"[{browser_id}] ⚠ 浏览器会话已失效，尝试重新获取trade_box...")
            # 切换到主窗口
            try:
                all_windows = driver.window_handles
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "polymarket.com" in current_url or "app.polymarket.com" in current_url:
                        log_print(f"[{browser_id}] ✓ 已切换到主页面窗口")
                        break
            except:
                pass
            
            # 重新获取trade_box
            trade_box = wait_for_polymarket_trade_box(driver, browser_id, max_retries=3)
            if not trade_box:
                return False, "浏览器会话失效，重新获取trade_box失败"
            log_print(f"[{browser_id}] ✓ 已重新获取trade_box")
        else:
            # 会话有效，但需要确保在主窗口并重新获取trade_box（因为步骤6可能切换了窗口）
            try:
                all_windows = driver.window_handles
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "polymarket.com" in current_url or "app.polymarket.com" in current_url:
                        log_print(f"[{browser_id}] ✓ 已切换到主页面窗口")
                        break
            except:
                pass
            
            # 重新获取trade_box以确保元素引用有效
            trade_box = wait_for_polymarket_trade_box(driver, browser_id, max_retries=1)
            if not trade_box:
                log_print(f"[{browser_id}] ⚠ 重新获取trade_box失败，使用原有引用继续...")
        
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
        max_retry_time = 60
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


def get_balance_spot_address(driver, browser_id):
    """
    获取 Balance Spot 的地址（通过点击按钮并读取剪切板）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        tuple: (地址字符串, 是否成功)
            - 如果成功获取到0x开头的地址: (address, True)
            - 如果失败: (None, False)
    """
    try:
        log_print(f"[{browser_id}] 等待包含 'Balance Spot' 的 P 标签出现（最多等待60秒）...")
        
        # 1. 在60秒内等待包含 "Balance Spot" 的 P 标签出现
        try:
            target_p = WebDriverWait(driver, 45).until(
                lambda d: next(
                    (p for p in d.find_elements(By.TAG_NAME, "p")
                     if "Balance Spot" in p.text.strip()),
                    None
                )
            )
            log_print(f"[{browser_id}] ✓ 找到包含 'Balance Spot' 的 P 标签")
        except Exception as e:
            log_print(f"[{browser_id}] ⚠ 60秒内未找到包含 'Balance Spot' 的 P 标签: {str(e)}")
            return None, False
        
        # 2. 找到 P 标签的父节点
        parent = target_p.find_element(By.XPATH, "..")
        log_print(f"[{browser_id}] ✓ 找到父节点")
        
        # 3. 从父节点中找到 button
        buttons = parent.find_elements(By.TAG_NAME, "button")
        if not buttons:
            log_print(f"[{browser_id}] ⚠ 父节点中未找到 button")
            return None, False
        
        target_button = buttons[0]
        log_print(f"[{browser_id}] ✓ 找到 button，准备点击...")
        
        # 4. 点击 button
        target_button.click()
        log_print(f"[{browser_id}] ✓ 已点击 button")
        
        # 5. 等待一小段时间，确保剪切板内容已更新
        time.sleep(0.5)
        
        # 6. 获取剪切板内容
        clipboard_content = None
        try:
            # 优先尝试使用 pyperclip
            try:
                import pyperclip
                clipboard_content = pyperclip.paste()
                log_print(f"[{browser_id}] ✓ 使用 pyperclip 获取剪切板内容")
            except ImportError:
                # 如果没有 pyperclip，尝试使用 Windows API
                try:
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    try:
                        clipboard_content = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                        if isinstance(clipboard_content, bytes):
                            clipboard_content = clipboard_content.decode('utf-8', errors='ignore')
                        log_print(f"[{browser_id}] ✓ 使用 win32clipboard 获取剪切板内容")
                    finally:
                        win32clipboard.CloseClipboard()
                except ImportError:
                    log_print(f"[{browser_id}] ⚠ 未安装 pyperclip 或 pywin32，无法获取剪切板内容")
                    return None, False
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ win32clipboard 获取失败: {str(e)}")
                    return None, False
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ pyperclip 获取失败: {str(e)}")
                return None, False
            
            if not clipboard_content:
                log_print(f"[{browser_id}] ⚠ 剪切板内容为空")
                return None, False
            
            log_print(f"[{browser_id}] 剪切板内容: {clipboard_content}")
            
            # 7. 验证是否是 0x 开头的地址
            clipboard_content = clipboard_content.strip()
            if clipboard_content.startswith('0x'):
                address = clipboard_content
                log_print(f"[{browser_id}] ✓ 成功获取到地址: {address}")
                return address, True
            else:
                log_print(f"[{browser_id}] ⚠ 剪切板内容不是有效的地址格式（不是0x开头）")
                return None, False
                
        except Exception as e:
            log_print(f"[{browser_id}] ✗ 获取剪切板内容失败: {str(e)}")
            import traceback
            log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
            return None, False
            
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取 Balance Spot 地址失败: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return None, False


def click_opinion_position_claim_buttons_only(driver, serial_number):
    """
    只点击 Position 按钮并处理所有页面的 Claim 按钮，不获取数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (是否成功, 是否需要刷新重试)
    """
    
    def handle_claim_buttons(driver, serial_number):
        """
        处理Claim按钮：点击第一个Claim按钮，切换到OKX页面点击第二个按钮，循环直到没有Claim按钮
        
        Args:
            driver: Selenium WebDriver对象
            serial_number: 浏览器序列号
        """
        while True:
            try:
                # 重新获取position_div（因为页面可能已更新）
                position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                
                # 在position_div下查找所有内容等于"Claim"的button
                claim_buttons = []
                all_buttons = position_div.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    if button.text.strip() == "Claim":
                        claim_buttons.append(button)
                
                if len(claim_buttons) == 0:
                    # 没有Claim按钮了，退出循环
                    log_print(f"[{serial_number}] [OP] ✓ 没有找到 Claim 按钮，处理完成")
                    break
                
                # 点击第一个Claim按钮
                log_print(f"[{serial_number}] [OP] 找到 {len(claim_buttons)} 个 Claim 按钮，点击第一个...")
                claim_buttons[0].click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击第一个 Claim 按钮")
                
                # 等待3秒
                time.sleep(3)
                
                # 切换到OKX页面
                log_print(f"[{serial_number}] [OP] 切换到 OKX 钱包页面...")
                all_windows = driver.window_handles
                main_window = None
                okx_window = None
                
                # 先找到主窗口
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "app.opinion.trade" in current_url:
                        main_window = window
                        break
                
                # 再找OKX窗口
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                        okx_window = window
                        log_print(f"[{serial_number}] [OP] ✓ 已切换到 OKX 页面")
                        break
                
                if not okx_window:
                    log_print(f"[{serial_number}] [OP] ⚠ 未找到 OKX 页面，跳过本次Claim处理")
                    if main_window:
                        driver.switch_to.window(main_window)
                    break
                
                # 在10秒内查找并点击第二个按钮
                log_print(f"[{serial_number}] [OP] 在10秒内查找 data-testid='okd-button' 的第二个按钮...")
                button_clicked = False
                button_start_time = time.time()
                
                while time.time() - button_start_time < 10:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        if len(buttons) >= 2:
                            buttons[1].click()
                            log_print(f"[{serial_number}] [OP] ✓ 已点击第二个按钮")
                            button_clicked = True
                            break
                        else:
                            time.sleep(0.5)
                    except Exception as e:
                        log_print(f"[{serial_number}] [OP] ⚠ 查找按钮时出错: {str(e)}")
                        time.sleep(0.5)
                
                if not button_clicked:
                    log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到足够的按钮或超时")
                
                # 切换回主界面
                log_print(f"[{serial_number}] [OP] 切换回主界面...")
                if main_window:
                    driver.switch_to.window(main_window)
                    log_print(f"[{serial_number}] [OP] ✓ 已切换回主界面")
                else:
                    # 如果没找到主窗口，尝试通过URL查找
                    for window in all_windows:
                        driver.switch_to.window(window)
                        current_url = driver.current_url
                        if "app.opinion.trade" in current_url:
                            log_print(f"[{serial_number}] [OP] ✓ 已切换回主界面")
                            break
                
                # 等待3秒
                time.sleep(3)
                
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 处理 Claim 按钮时出错: {str(e)}")
                # 尝试切换回主界面
                try:
                    all_windows = driver.window_handles
                    for window in all_windows:
                        driver.switch_to.window(window)
                        current_url = driver.current_url
                        if "app.opinion.trade" in current_url:
                            break
                except:
                    pass
                break
    
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
            return False, False
        
        time.sleep(3)
        
        try:
            # 在180秒内遍历所有页面并点击Claim按钮
            max_retry_time = 180
            retry_start_time = time.time()
            page_num = 1
            
            while time.time() - retry_start_time < max_retry_time:
                try:
                    # 重新获取 position_div（因为分页后内容会刷新）
                    log_print(f"[{serial_number}] [OP] 查找 Position 内容区域（第 {page_num} 页）...")
                    position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                    log_print(f"[{serial_number}] [OP] ✓ 找到 Position 内容区域 (ID: {position_div.get_attribute('id')})")
                    
                    # 处理当前页的Claim按钮
                    log_print(f"[{serial_number}] [OP] 开始处理第 {page_num} 页的 Claim 按钮...")
                    handle_claim_buttons(driver, serial_number)
                    log_print(f"[{serial_number}] [OP] ✓ 第 {page_num} 页的 Claim 按钮处理完成")
                    
                    # 检查是否有下一页
                    try:
                        next_page_button = position_div.find_element(By.CSS_SELECTOR, 'button[aria-label="next page"]')
                        is_disabled = next_page_button.get_attribute("disabled") is not None
                        
                        if is_disabled:
                            log_print(f"[{serial_number}] [OP] ✓ 下一页按钮已禁用，所有页面Claim按钮处理完成")
                            break
                        else:
                            log_print(f"[{serial_number}] [OP] 发现下一页，点击下一页按钮...")
                            next_page_button.click()
                            time.sleep(3)  # 等待页面加载
                            page_num += 1
                            retry_start_time = time.time()  # 重置超时时间，因为开始新的一页
                            continue
                    except Exception as e:
                        # 找不到下一页按钮，说明没有分页或已经是最后一页
                        log_print(f"[{serial_number}] [OP] ✓ 未找到下一页按钮，所有页面Claim按钮处理完成")
                        break
                    
                except Exception as e:
                    elapsed = int(time.time() - retry_start_time)
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Position 内容区域异常: {str(e)}，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                    time.sleep(5)
            
            log_print(f"[{serial_number}] [OP] ✓ 所有页面的 Claim 按钮处理完成")
            return True, False
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 处理 Claim 按钮失败: {str(e)}")
            return False, True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Position 按钮失败: {str(e)}")
        return False, False


def click_opinion_position_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Position 按钮并获取数据，返回标准格式字符串（支持分页）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (标准格式字符串, 是否需要刷新重试, 是否任务失败)
            - 如果正常获取数据: (标准格式字符串, False, False)
            - 如果找到"No data yet": ("", False, False) - 可以提交空数据
            - 如果超时且没有"No data yet"，需要刷新重试: ("", True, False)
            - 如果重试后仍然失败: ("", False, True) - 任务失败，不提交数据
            标准格式: "唯一标题|||方向|||数量|||均价;唯一标题|||方向|||数量|||均价"
    """
    
    def handle_claim_buttons(driver, serial_number):
        """
        处理Claim按钮：点击第一个Claim按钮，切换到OKX页面点击第二个按钮，循环直到没有Claim按钮
        
        Args:
            driver: Selenium WebDriver对象
            serial_number: 浏览器序列号
        """
        while True:
            try:
                # 重新获取position_div（因为页面可能已更新）
                position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                
                # 在position_div下查找所有内容等于"Claim"的button
                claim_buttons = []
                all_buttons = position_div.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    if button.text.strip() == "Claim":
                        claim_buttons.append(button)
                
                if len(claim_buttons) == 0:
                    # 没有Claim按钮了，退出循环
                    log_print(f"[{serial_number}] [OP] ✓ 没有找到 Claim 按钮，处理完成")
                    break
                
                # 点击第一个Claim按钮
                log_print(f"[{serial_number}] [OP] 找到 {len(claim_buttons)} 个 Claim 按钮，点击第一个...")
                claim_buttons[0].click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击第一个 Claim 按钮")
                
                # 等待3秒
                time.sleep(3)
                
                # 切换到OKX页面
                log_print(f"[{serial_number}] [OP] 切换到 OKX 钱包页面...")
                all_windows = driver.window_handles
                main_window = None
                okx_window = None
                
                # 先找到主窗口
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "app.opinion.trade" in current_url:
                        main_window = window
                        break
                
                # 再找OKX窗口
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                        okx_window = window
                        log_print(f"[{serial_number}] [OP] ✓ 已切换到 OKX 页面")
                        break
                
                if not okx_window:
                    log_print(f"[{serial_number}] [OP] ⚠ 未找到 OKX 页面，跳过本次Claim处理")
                    if main_window:
                        driver.switch_to.window(main_window)
                    break
                
                # 在10秒内查找并点击第二个按钮
                log_print(f"[{serial_number}] [OP] 在10秒内查找 data-testid='okd-button' 的第二个按钮...")
                button_clicked = False
                button_start_time = time.time()
                
                while time.time() - button_start_time < 10:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        if len(buttons) >= 2:
                            buttons[1].click()
                            log_print(f"[{serial_number}] [OP] ✓ 已点击第二个按钮")
                            button_clicked = True
                            break
                        else:
                            time.sleep(0.5)
                    except Exception as e:
                        log_print(f"[{serial_number}] [OP] ⚠ 查找按钮时出错: {str(e)}")
                        time.sleep(0.5)
                
                if not button_clicked:
                    log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到足够的按钮或超时")
                
                # 切换回主界面
                log_print(f"[{serial_number}] [OP] 切换回主界面...")
                if main_window:
                    driver.switch_to.window(main_window)
                    log_print(f"[{serial_number}] [OP] ✓ 已切换回主界面")
                else:
                    # 如果没找到主窗口，尝试通过URL查找
                    for window in all_windows:
                        driver.switch_to.window(window)
                        current_url = driver.current_url
                        if "app.opinion.trade" in current_url:
                            log_print(f"[{serial_number}] [OP] ✓ 已切换回主界面")
                            break
                
                # 等待3秒
                time.sleep(3)
                
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 处理 Claim 按钮时出错: {str(e)}")
                # 尝试切换回主界面
                try:
                    all_windows = driver.window_handles
                    for window in all_windows:
                        driver.switch_to.window(window)
                        current_url = driver.current_url
                        if "app.opinion.trade" in current_url:
                            break
                except:
                    pass
                break
    
    def parse_tbody_data(position_div, driver, serial_number):
        """
        解析当前页的tbody数据
        
        Args:
            position_div: Position div元素
            driver: Selenium WebDriver对象
            serial_number: 浏览器序列号
            
        Returns:
            tuple: (解析后的仓位字符串列表, 是否是无数据标记, 是否需要重试)
        """
        result_parts = []
        
        # 先检查是否有"No data yet"
        all_p_tags_in_div = position_div.find_elements(By.TAG_NAME, "p")
        for p in all_p_tags_in_div:
            if "No data yet" in p.text:
                log_print(f"[{serial_number}] [OP] ✓ Position 发现 'No data yet'，无数据")
                return result_parts, True, False  # 返回空列表和"无数据"标记，不需要重试
        
        # 再找这个 div 下的 tbody
        tbody = position_div.find_element(By.TAG_NAME, "tbody")
        tr_tags = tbody.find_elements(By.TAG_NAME, "tr")
        
        if len(tr_tags) == 0:
            # 既没有"No data yet"也没有数据，需要重试
            log_print(f"[{serial_number}] [OP] ⚠ Position 既没有 'No data yet' 也没有数据，需要重试")
            return result_parts, False, True  # 返回空列表，不是"No data yet"，但需要重试
        
        log_print(f"[{serial_number}] [OP] ✓ 当前页找到 {len(tr_tags)} 个 tr 标签")
        
        # 如果tr的个数不等于0，处理Claim按钮
        log_print(f"[{serial_number}] [OP] 开始处理 Claim 按钮...")
        handle_claim_buttons(driver, serial_number)
        
        # 处理完Claim按钮后，重新获取position_div（因为页面可能已更新）
        try:
            position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
            # 重新获取tbody和tr_tags
            tbody = position_div.find_element(By.TAG_NAME, "tbody")
            tr_tags = tbody.find_elements(By.TAG_NAME, "tr")
            log_print(f"[{serial_number}] [OP] 处理Claim后，重新找到 {len(tr_tags)} 个 tr 标签")
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 重新获取position_div失败: {str(e)}")
        
        # 解析tr标签数据
        current_main_title = None
        
        # 使用索引遍历，避免stale element reference问题
        tr_count = len(tr_tags)
        tr_idx = 0
        
        while tr_idx < tr_count:
            try:
                # 每次迭代时重新获取tr元素，避免stale element reference
                try:
                    # 重新获取position_div和tbody（防止页面更新导致元素失效）
                    position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                    tbody = position_div.find_element(By.TAG_NAME, "tbody")
                    current_tr_tags = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    # 如果tr数量发生变化，更新tr_count
                    if len(current_tr_tags) != tr_count:
                        log_print(f"[{serial_number}] [OP] ⚠ tr数量从 {tr_count} 变为 {len(current_tr_tags)}，更新计数")
                        tr_count = len(current_tr_tags)
                        if tr_idx >= tr_count:
                            break
                    
                    tr = current_tr_tags[tr_idx]
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr元素失败: {str(e)}，跳过当前tr")
                    tr_idx += 1
                    continue
                
                td_tags = tr.find_elements(By.TAG_NAME, "td")
                
                if len(td_tags) == 1:
                    # 只有一个td，这是主标题
                    p_text = get_p_tag_text_from_element(td_tags[0])
                    if p_text:
                        current_main_title = p_text.strip()
                        log_print(f"[{serial_number}] [OP] 找到主标题: {current_main_title}")
                
                elif len(td_tags) >= 4 and current_main_title:
                    # 多个td，这是仓位信息
                    # 第一个td：子标题-方向 或 方向
                    first_td_p = get_p_tag_text_from_element(td_tags[0])
                    if not first_td_p:
                        tr_idx += 1
                        continue
                    
                    # 解析第一个td的内容
                    if " - " in first_td_p:
                        # 有子标题，例如 "Kendrick Lamar - YES" 或 "Artist - Song - YES"
                        # 使用 rsplit 以最后一个 " - " 作为分隔符
                        parts = first_td_p.rsplit(" - ", 1)
                        sub_title = parts[0].strip()
                        direction = parts[1].strip()
                        unique_title = f"{current_main_title}###{sub_title}"
                    else:
                        # 没有子标题，直接是方向
                        direction = first_td_p.strip().lower()
                        # 特殊处理：将特定方向转换为标准格式
                        if direction == "monad" or direction == "gold":
                            direction = "YES"
                        elif direction == "megaeth" or direction == "eth":
                            direction = "NO"
                        unique_title = current_main_title
                    
                    # 第二个td：数量
                    second_td_p = get_p_tag_text_from_element(td_tags[1])
                    if not second_td_p:
                        tr_idx += 1
                        continue
                    
                    amount_str = second_td_p.strip()
                    # 根据方向添加正负号
                    if direction.upper() == "YES":
                        amount = f"+{amount_str}"
                    elif direction.upper() == "NO":
                        amount = f"-{amount_str}"
                    else:
                        amount = amount_str
                    
                    # 第四个td：均价
                    fourth_td_p = get_p_tag_text_from_element(td_tags[3])
                    if not fourth_td_p or not fourth_td_p.strip():
                        # 如果p标签中没有文本，尝试直接获取td的文本内容
                        try:
                            fourth_td_text = td_tags[3].text.strip()
                            if fourth_td_text:
                                avg_price = fourth_td_text
                                log_print(f"[{serial_number}] [OP] ⚠ 第四个td的p标签为空，使用td的文本内容作为均价: {avg_price}")
                            else:
                                avg_price = ""
                                log_print(f"[{serial_number}] [OP] ⚠ 第四个td的文本内容也为空，均价将为空")
                        except Exception as e:
                            avg_price = ""
                            log_print(f"[{serial_number}] [OP] ⚠ 获取第四个td的文本内容时出错: {str(e)}，均价将为空")
                    else:
                        avg_price = fourth_td_p.strip()
                    
                    # 拼接标准格式：唯一标题|||方向|||数量|||均价
                    position_str = f"{unique_title}|||{direction}|||{amount}|||{avg_price}"
                    result_parts.append(position_str)
                    log_print(f"[{serial_number}] [OP] 解析仓位: {position_str}")
                
                tr_idx += 1
                
            except Exception as e:
                error_msg = str(e)
                if "stale element" in error_msg.lower():
                    # 遇到stale element reference，重新获取tr列表
                    log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签时遇到stale element，重新获取tr列表...")
                    try:
                        position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                        tbody = position_div.find_element(By.TAG_NAME, "tbody")
                        tr_tags = tbody.find_elements(By.TAG_NAME, "tr")
                        tr_count = len(tr_tags)
                        log_print(f"[{serial_number}] [OP] ✓ 重新获取到 {tr_count} 个 tr 标签，从索引 {tr_idx} 继续")
                        # 不增加tr_idx，重新尝试当前索引
                        continue
                    except Exception as e2:
                        log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr列表失败: {str(e2)}，跳过当前tr")
                        tr_idx += 1
                else:
                    log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签异常: {error_msg}")
                    tr_idx += 1
        
        return result_parts, False, False  # 返回解析结果，不是"No data yet"，不需要重试
    
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
            return "", True, False
        
        # 查找并点击 checkbox（如果未选中）
        try:
            log_print(f"[{serial_number}] [OP] 查找 data-scope='checkbox' 的 label 组件...")
            checkbox_label = driver.find_element(By.CSS_SELECTOR, "label[data-scope='checkbox']")
            data_state = checkbox_label.get_attribute("data-state")
            log_print(f"[{serial_number}] [OP] 找到 checkbox，当前 data-state: {data_state}")
            
            if data_state != "checked":
                log_print(f"[{serial_number}] [OP] checkbox 未选中，点击它...")
                checkbox_label.click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击 checkbox")
            else:
                log_print(f"[{serial_number}] [OP] checkbox 已选中，无需点击")
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 查找或点击 checkbox 时出错: {str(e)}")
        
        time.sleep(3)
        
        try:
            # 在180秒内多次查找tbody和tr标签，如果数量为0则等待5秒后重试
            max_retry_time = 180
            retry_start_time = time.time()
            
            # 所有页面的结果
            all_result_parts = []
            page_num = 1
            
            while time.time() - retry_start_time < max_retry_time:
                try:
                    # 重新获取 position_div（因为分页后内容会刷新）
                    log_print(f"[{serial_number}] [OP] 查找 Position 内容区域（第 {page_num} 页）...")
                    position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                    log_print(f"[{serial_number}] [OP] ✓ 找到 Position 内容区域 (ID: {position_div.get_attribute('id')})")
                    
                    # 解析当前页数据，支持重试逻辑（最多3次）
                    retry_count = 0
                    max_parse_retries = 3
                    page_result_parts = []
                    is_no_data = False
                    need_retry = False
                    
                    while retry_count < max_parse_retries:
                        page_result_parts, is_no_data, need_retry = parse_tbody_data(position_div, driver, serial_number)
                        
                        if not need_retry:
                            # 不需要重试，跳出重试循环
                            break
                        
                        # 需要重试，等待5秒后重新获取position_div
                        retry_count += 1
                        if retry_count < max_parse_retries:
                            log_print(f"[{serial_number}] [OP] ⚠ 第 {retry_count} 次重试：等待5秒后重新获取 Position 数据...")
                            time.sleep(5)
                            # 重新获取 position_div
                            position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                        else:
                            # 超过3次重试，返回任务失败
                            log_print(f"[{serial_number}] [OP] ✗ 重试 {max_parse_retries} 次后仍无数据，返回任务失败")
                            return "", False, True  # 返回空字符串，不需要刷新重试，但任务失败
                    
                    if is_no_data:
                        # 如果是"No data yet"，直接返回（可以提交空数据）
                        if len(all_result_parts) == 0:
                            return "", False, False  # 正常无数据，可以提交
                        else:
                            # 已经有数据了，说明之前有数据，现在没数据了，返回已有数据
                            break
                    
                    if len(page_result_parts) > 0:
                        all_result_parts.extend(page_result_parts)
                        log_print(f"[{serial_number}] [OP] ✓ 第 {page_num} 页解析完成，共 {len(page_result_parts)} 个仓位，累计 {len(all_result_parts)} 个仓位")
                    else:
                        elapsed = int(time.time() - retry_start_time)
                        log_print(f"[{serial_number}] [OP] ⚠ 第 {page_num} 页解析后无有效仓位数据")
                    
                    # 检查是否有下一页（即使当前页没有数据，也可能有下一页）
                    try:
                        next_page_button = position_div.find_element(By.CSS_SELECTOR, 'button[aria-label="next page"]')
                        is_disabled = next_page_button.get_attribute("disabled") is not None
                        
                        if is_disabled:
                            log_print(f"[{serial_number}] [OP] ✓ 下一页按钮已禁用，所有页面数据获取完成")
                            break
                        else:
                            log_print(f"[{serial_number}] [OP] 发现下一页，开始处理下一页数据...")
                            
                            # 点击下一页并检查数据是否重复（最多重试3次）
                            next_page_retry_count = 0
                            max_next_page_retries = 3
                            next_page_success = False
                            
                            while next_page_retry_count < max_next_page_retries:
                                # 点击下一页按钮
                                next_page_button.click()
                                log_print(f"[{serial_number}] [OP] 已点击下一页按钮（重试次数: {next_page_retry_count}/{max_next_page_retries}）")
                                time.sleep(10)  # 等待页面加载
                                
                                # 重新获取position_div并解析下一页数据
                                try:
                                    position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                                    next_page_result_parts, next_page_is_no_data, next_page_need_retry = parse_tbody_data(position_div, driver, serial_number)
                                    
                                    if next_page_is_no_data or len(next_page_result_parts) == 0:
                                        # 下一页没有数据，说明已经是最后一页，退出循环
                                        log_print(f"[{serial_number}] [OP] ✓ 下一页无数据，所有页面数据获取完成")
                                        next_page_success = True
                                        break
                                    
                                    # 检查下一页数据是否与已获取的数据重复
                                    # 如果下一页的所有数据都已经在已获取的数据中，则认为重复
                                    is_duplicate = False
                                    if len(next_page_result_parts) > 0:
                                        duplicate_count = 0
                                        for next_item in next_page_result_parts:
                                            if next_item in all_result_parts:
                                                duplicate_count += 1
                                                log_print(f"[{serial_number}] [OP] ⚠ 检测到重复数据: {next_item}")
                                        
                                        # 如果所有数据都重复，则认为整页重复
                                        if duplicate_count == len(next_page_result_parts):
                                            is_duplicate = True
                                            log_print(f"[{serial_number}] [OP] ⚠ 下一页所有 {len(next_page_result_parts)} 条数据都是重复的")
                                    
                                    if is_duplicate:
                                        # 数据重复，等待3秒后重试点击下一页
                                        next_page_retry_count += 1
                                        if next_page_retry_count < max_next_page_retries:
                                            log_print(f"[{serial_number}] [OP] ⚠ 下一页数据重复，等待3秒后重试点击下一页（{next_page_retry_count}/{max_next_page_retries}）")
                                            time.sleep(3)
                                            # 重新获取下一页按钮（因为页面可能已更新）
                                            try:
                                                position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                                                next_page_button = position_div.find_element(By.CSS_SELECTOR, 'button[aria-label="next page"]')
                                                is_disabled = next_page_button.get_attribute("disabled") is not None
                                                if is_disabled:
                                                    log_print(f"[{serial_number}] [OP] ✓ 下一页按钮已禁用，所有页面数据获取完成")
                                                    next_page_success = True
                                                    break
                                            except Exception as e:
                                                log_print(f"[{serial_number}] [OP] ⚠ 重新获取下一页按钮失败: {str(e)}")
                                                break
                                        else:
                                            # 已重试3次，都是重复数据，返回任务失败
                                            log_print(f"[{serial_number}] [OP] ✗ 连续3次点击下一页都是重复数据，任务失败")
                                            return "", False, True
                                    else:
                                        # 数据不重复，添加到结果中
                                        all_result_parts.extend(next_page_result_parts)
                                        page_num += 1
                                        log_print(f"[{serial_number}] [OP] ✓ 第 {page_num} 页解析完成，共 {len(next_page_result_parts)} 个仓位，累计 {len(all_result_parts)} 个仓位")
                                        next_page_success = True
                                        retry_start_time = time.time()  # 重置超时时间，因为开始新的一页
                                        break
                                    
                                except Exception as e:
                                    log_print(f"[{serial_number}] [OP] ⚠ 解析下一页数据异常: {str(e)}")
                                    next_page_retry_count += 1
                                    if next_page_retry_count < max_next_page_retries:
                                        time.sleep(3)
                                        try:
                                            position_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-position']")
                                            next_page_button = position_div.find_element(By.CSS_SELECTOR, 'button[aria-label="next page"]')
                                            is_disabled = next_page_button.get_attribute("disabled") is not None
                                            if is_disabled:
                                                log_print(f"[{serial_number}] [OP] ✓ 下一页按钮已禁用，所有页面数据获取完成")
                                                next_page_success = True
                                                break
                                        except:
                                            break
                                    else:
                                        log_print(f"[{serial_number}] [OP] ✗ 连续3次解析下一页数据失败，任务失败")
                                        return "", False, True
                            
                            if not next_page_success:
                                # 如果没有成功处理下一页，退出循环
                                break
                            
                            continue
                    except Exception as e:
                        # 找不到下一页按钮，说明没有分页或已经是最后一页
                        log_print(f"[{serial_number}] [OP] ✓ 未找到下一页按钮，所有页面数据获取完成")
                        break
                    
                except Exception as e:
                    elapsed = int(time.time() - retry_start_time)
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Position 数据异常: {str(e)}，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                    time.sleep(5)
            
            # 返回所有页面的结果
            if len(all_result_parts) > 0:
                # 最终去重：移除重复的数据
                original_count = len(all_result_parts)
                unique_result_parts = []
                seen_items = set()
                for item in all_result_parts:
                    if item not in seen_items:
                        unique_result_parts.append(item)
                        seen_items.add(item)
                
                if len(unique_result_parts) < original_count:
                    removed_count = original_count - len(unique_result_parts)
                    log_print(f"[{serial_number}] [OP] ✓ 最终去重完成：原始 {original_count} 个仓位，去重后 {len(unique_result_parts)} 个仓位，移除 {removed_count} 个重复项")
                
                result_str = ";".join(unique_result_parts)
                log_print(f"[{serial_number}] [OP] ✓ Position 所有页面解析完成，共 {len(unique_result_parts)} 个仓位")
                return result_str, False, False
            else:
                log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Position 数据且无'No data yet'，返回任务失败")
                return "", False, True  # 任务失败，不提交数据
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Position 数据失败: {str(e)}，返回任务失败")
            return "", False, True  # 任务失败，不提交数据
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Position 按钮失败: {str(e)}，返回任务失败")
        return "", False, True  # 任务失败，不提交数据


def get_p_tag_text_from_element(element):
    """
    从元素中获取p标签的文本内容（可能有多层嵌套）
    
    Args:
        element: WebElement对象
        
    Returns:
        str: p标签的文本内容，如果找不到则返回空字符串
    """
    try:
        # 使用 XPath 查找所有 p 标签（包括嵌套的）
        p_tags = element.find_elements(By.XPATH, ".//p")
        if p_tags:
            # 返回第一个非空的p标签文本
            for p in p_tags:
                text = p.text.strip()
                if text:
                    return text
        # 如果没有找到p标签或p标签都为空，尝试直接获取元素的文本内容
        element_text = element.text.strip()
        if element_text:
            return element_text
        return ""
    except Exception as e:
        # 如果出现异常，尝试直接获取元素的文本内容
        try:
            element_text = element.text.strip()
            if element_text:
                return element_text
        except:
            pass
        return ""


def cancel_opinion_open_orders_by_tp1(driver, serial_number, tp1):
    """
    根据 tp1 值取消 Opinion Trade Open Orders 中的订单
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        tp1: 目标标题，如果为 "all" 则取消所有订单，否则只取消匹配的订单
        
    Returns:
        bool: 是否成功完成取消操作
    """
    try:
        log_print(f"[{serial_number}] [OP] 开始执行 Type 4 取消订单任务，tp1: {tp1}")
        
        # 先点击 Open Orders 按钮
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
            return False
        
        time.sleep(5)
        
        # 解析 tp1 值
        target_main_title = None
        target_sub_title = None
        
        if tp1 and tp1 != "all":
            if "###" in tp1:
                # 有子标题，格式为主标题###子标题
                parts = tp1.split("###", 1)
                if len(parts) == 2:
                    target_main_title = parts[0].strip()
                    target_sub_title = parts[1].strip()
                    log_print(f"[{serial_number}] [OP] 解析tp1: 主标题='{target_main_title}', 子标题='{target_sub_title}'")
            else:
                # 只有主标题
                target_main_title = tp1.strip()
                log_print(f"[{serial_number}] [OP] 解析tp1: 主标题='{target_main_title}'")
        
        # 循环取消订单
        while True:
            try:
                # 获取 open_orders_div
                log_print(f"[{serial_number}] [OP] 获取 Open Orders 内容区域...")
                open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                
                # 检查是否有 "No data yet"
                all_p_tags_in_div = open_orders_div.find_elements(By.TAG_NAME, "p")
                has_no_data = False
                for p in all_p_tags_in_div:
                    if "No data yet" in p.text:
                        log_print(f"[{serial_number}] [OP] ✓ 发现 'No data yet'，取消订单任务完成")
                        has_no_data = True
                        break
                
                if has_no_data:
                    break
                
                # 获取 tbody 和 tr 列表
                try:
                    tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                    tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                except:
                    log_print(f"[{serial_number}] [OP] ⚠ 未找到 tbody 或 tr 列表")
                    break
                
                if len(tr_list) == 0:
                    log_print(f"[{serial_number}] [OP] ⚠ tr 列表为空")
                    break
                
                # 解析 tr 列表，找到需要取消的订单
                current_main_title = ""
                found_order_to_cancel = False
                i = 0
                tr_count = len(tr_list)
                
                while i < tr_count:
                    try:
                        # 每次迭代时重新获取tr元素，避免stale element reference
                        try:
                            # 重新获取open_orders_div和tbody（防止页面更新导致元素失效）
                            open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                            current_tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                            
                            # 如果tr数量发生变化，更新tr_count
                            if len(current_tr_list) != tr_count:
                                log_print(f"[{serial_number}] [OP] ⚠ tr数量从 {tr_count} 变为 {len(current_tr_list)}，更新计数")
                                tr_count = len(current_tr_list)
                                if i >= tr_count:
                                    break
                            
                            tr = current_tr_list[i]
                        except Exception as e:
                            log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr元素失败: {str(e)}，跳过当前tr")
                            i += 1
                            continue
                        
                        td_list = tr.find_elements(By.TAG_NAME, "td")
                        
                        # 如果只有一个td，这是主标题
                        if len(td_list) == 1:
                            main_title_text = get_p_tag_text_from_element(td_list[0])
                            if main_title_text:
                                current_main_title = main_title_text.strip()
                            i += 1
                            continue
                        
                        # 如果有多个td，这是挂单仓位信息
                        if len(td_list) >= 6 and current_main_title:
                            # 判断是否需要取消这个订单
                            should_cancel = False
                            
                            if tp1 == "all":
                                # 取消所有订单
                                should_cancel = True
                            elif target_main_title:
                                # 检查主标题是否匹配
                                if current_main_title == target_main_title:
                                    if target_sub_title:
                                        # 需要检查子标题
                                        second_td_text = get_p_tag_text_from_element(td_list[1]).strip()
                                        if " - " in second_td_text:
                                            parts = second_td_text.split(" - ", 1)
                                            if len(parts) == 2:
                                                sub_title = parts[0].strip()
                                                if sub_title == target_sub_title:
                                                    should_cancel = True
                                    else:
                                        # 只需要主标题匹配
                                        should_cancel = True
                            
                            if should_cancel:
                                # 找到最后一个td，点击svg
                                last_td = td_list[-1]
                                svg_elements = last_td.find_elements(By.TAG_NAME, "svg")
                                
                                if svg_elements and len(svg_elements) > 0:
                                    log_print(f"[{serial_number}] [OP] 找到需要取消的订单，点击取消按钮...")
                                    svg_elements[0].click()
                                    time.sleep(2)
                                    
                                    # 在10秒内找到"Confirm"按钮并点击
                                    log_print(f"[{serial_number}] [OP] 查找Confirm按钮...")
                                    confirm_found = False
                                    confirm_timeout = 10
                                    confirm_start_time = time.time()
                                    
                                    while time.time() - confirm_start_time < confirm_timeout:
                                        try:
                                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                            for btn in all_buttons:
                                                if btn.text.strip() == "Confirm":
                                                    log_print(f"[{serial_number}] [OP] ✓ 找到Confirm按钮，点击...")
                                                    btn.click()
                                                    confirm_found = True
                                                    break
                                            
                                            if confirm_found:
                                                break
                                            
                                            time.sleep(0.5)
                                        except Exception as e:
                                            log_print(f"[{serial_number}] [OP] ⚠ 查找Confirm按钮时出错: {str(e)}")
                                            time.sleep(0.5)
                                    
                                    if not confirm_found:
                                        log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到Confirm按钮")
                                        return False
                                    
                                    found_order_to_cancel = True
                                    log_print(f"[{serial_number}] [OP] ✓ 订单取消成功")
                                    break
                                else:
                                    log_print(f"[{serial_number}] [OP] ⚠ 未找到svg元素")
                        
                        i += 1
                    except Exception as e:
                        error_msg = str(e)
                        if "stale element" in error_msg.lower():
                            # 遇到stale element reference，重新获取tr列表
                            log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签时遇到stale element，重新获取tr列表...")
                            try:
                                open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                                tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                                tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                                tr_count = len(tr_list)
                                log_print(f"[{serial_number}] [OP] ✓ 重新获取到 {tr_count} 个 tr 标签，从索引 {i} 继续")
                                # 不增加i，重新尝试当前索引
                                continue
                            except Exception as e2:
                                log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr列表失败: {str(e2)}，跳过当前tr")
                                i += 1
                        else:
                            log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签异常: {error_msg}")
                            i += 1
                
                # 如果没有找到需要取消的订单，退出循环
                if not found_order_to_cancel:
                    if tp1 == "all":
                        # tp1=all 时，如果没有找到订单，可能是已经全部取消了
                        # 再次检查是否有 "No data yet"
                        all_p_tags_in_div_check = open_orders_div.find_elements(By.TAG_NAME, "p")
                        has_no_data_check = False
                        for p in all_p_tags_in_div_check:
                            if "No data yet" in p.text:
                                log_print(f"[{serial_number}] [OP] ✓ 所有订单已取消完成（tp1=all）")
                                has_no_data_check = True
                                break
                        if has_no_data_check:
                            break
                        else:
                            log_print(f"[{serial_number}] [OP] ⚠ 未找到需要取消的订单（tp1=all），可能已全部取消")
                            break
                    else:
                        log_print(f"[{serial_number}] [OP] ✓ 未找到匹配tp1的订单，取消任务完成")
                        break
                
                # 等待3秒后重新获取
                log_print(f"[{serial_number}] [OP] 等待3秒后重新获取订单列表...")
                time.sleep(3)
                
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 取消订单过程中出错: {str(e)}")
                break
        
        log_print(f"[{serial_number}] [OP] ✓ Type 4 取消订单任务完成")
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ Type 4 取消订单任务失败: {str(e)}")
        return False


def cancel_expired_open_orders(driver, serial_number, tp5, current_ip=None):
    """
    根据 tp5 值（小时数）取消超时的 Open Orders 订单
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        tp5: 挂单超过XX小时撤单的阈值（小时）
        current_ip: 当前IP地址，用于时区转换（可选）
        
    Returns:
        bool: 是否成功完成操作
    """
    from datetime import datetime
    import pytz
    
    if not tp5:
        log_print(f"[{serial_number}] [OP] tp5 为空，跳过超时撤单检查")
        return True
    
    try:
        tp5_hours = float(tp5)
    except (ValueError, TypeError):
        log_print(f"[{serial_number}] [OP] tp5 值无效: {tp5}，跳过超时撤单检查")
        return True
    
    log_print(f"[{serial_number}] [OP] 开始超时撤单检查，tp5={tp5_hours}小时")
    
    # 预先查询时区（如果需要）
    cached_timezone = None
    if serial_number not in BEIJING_TIME_PAGE_TIMEZONE:
        if current_ip:
            cached_timezone = get_timezone_from_ip(current_ip)
            if cached_timezone:
                log_print(f"[{serial_number}] [OP] ✓ 预先查询时区成功: {cached_timezone}")
    
    try:
        # 先点击 Open Orders 按钮
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
            return False
        
        time.sleep(5)
        
        # 循环检查并取消超时订单
        while True:
            try:
                # 获取 open_orders_div
                log_print(f"[{serial_number}] [OP] 获取 Open Orders 内容区域...")
                open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                
                # 检查是否有 "No data yet"
                all_p_tags_in_div = open_orders_div.find_elements(By.TAG_NAME, "p")
                has_no_data = False
                for p in all_p_tags_in_div:
                    if "No data yet" in p.text:
                        log_print(f"[{serial_number}] [OP] ✓ 发现 'No data yet'，无超时订单需要取消")
                        has_no_data = True
                        break
                
                if has_no_data:
                    break
                
                # 获取 tbody 和 tr 列表
                try:
                    tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                    tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                except:
                    log_print(f"[{serial_number}] [OP] ⚠ 未找到 tbody 或 tr 列表")
                    break
                
                if len(tr_list) == 0:
                    log_print(f"[{serial_number}] [OP] ⚠ tr 列表为空")
                    break
                
                # 解析 tr 列表，找到超时订单
                current_main_title = ""
                found_expired_order = False
                i = 0
                tr_count = len(tr_list)
                
                # 获取当前北京时间
                beijing_tz = pytz.timezone('Asia/Shanghai')
                now_beijing = datetime.now(beijing_tz)
                now_timestamp = int(now_beijing.timestamp() * 1000)  # 毫秒
                
                while i < tr_count:
                    try:
                        # 重新获取tr元素
                        try:
                            open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                            current_tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                            
                            if len(current_tr_list) != tr_count:
                                log_print(f"[{serial_number}] [OP] ⚠ tr数量从 {tr_count} 变为 {len(current_tr_list)}，更新计数")
                                tr_count = len(current_tr_list)
                                if i >= tr_count:
                                    break
                            
                            tr = current_tr_list[i]
                        except Exception as e:
                            log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr元素失败: {str(e)}，跳过当前tr")
                            i += 1
                            continue
                        
                        td_list = tr.find_elements(By.TAG_NAME, "td")
                        
                        # 如果只有一个td，这是主标题
                        if len(td_list) == 1:
                            main_title_text = get_p_tag_text_from_element(td_list[0])
                            if main_title_text:
                                current_main_title = main_title_text.strip()
                            i += 1
                            continue
                        
                        # 如果有多个td（至少8个，因为第8个是时间），这是挂单仓位信息
                        if len(td_list) >= 8 and current_main_title:
                            # 第8个td: 时间（如 Jan 05, 2026 13:30:43）
                            eighth_td_text = get_p_tag_text_from_element(td_list[7]).strip()
                            
                            if eighth_td_text:
                                # 转换时间为北京时间戳
                                original_time, convert_time_timestamp = convert_time_to_beijing(
                                    eighth_td_text, current_ip, serial_number=serial_number, cached_timezone=cached_timezone
                                )
                                
                                if convert_time_timestamp > 0:
                                    # 计算时间差（小时）
                                    time_diff_hours = (now_timestamp - convert_time_timestamp) / (1000 * 60 * 60)
                                    log_print(f"[{serial_number}] [OP] 订单时间: {eighth_td_text} -> 北京时间戳: {convert_time_timestamp}, 距今: {time_diff_hours:.2f}小时")
                                    
                                    if time_diff_hours > tp5_hours:
                                        log_print(f"[{serial_number}] [OP] ⚠ 发现超时订单（{time_diff_hours:.2f}小时 > {tp5_hours}小时），开始取消...")
                                        
                                        # 找到最后一个td，点击svg
                                        last_td = td_list[-1]
                                        svg_elements = last_td.find_elements(By.TAG_NAME, "svg")
                                        
                                        if svg_elements and len(svg_elements) > 0:
                                            log_print(f"[{serial_number}] [OP] 点击取消按钮...")
                                            svg_elements[0].click()
                                            time.sleep(2)
                                            
                                            # 在10秒内找到"Confirm"按钮并点击
                                            log_print(f"[{serial_number}] [OP] 查找Confirm按钮...")
                                            confirm_found = False
                                            confirm_timeout = 10
                                            confirm_start_time = time.time()
                                            
                                            while time.time() - confirm_start_time < confirm_timeout:
                                                try:
                                                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                                    for btn in all_buttons:
                                                        if btn.text.strip() == "Confirm":
                                                            log_print(f"[{serial_number}] [OP] ✓ 找到Confirm按钮，点击...")
                                                            btn.click()
                                                            confirm_found = True
                                                            break
                                                    
                                                    if confirm_found:
                                                        break
                                                    
                                                    time.sleep(0.5)
                                                except Exception as e:
                                                    log_print(f"[{serial_number}] [OP] ⚠ 查找Confirm按钮时出错: {str(e)}")
                                                    time.sleep(0.5)
                                            
                                            if not confirm_found:
                                                log_print(f"[{serial_number}] [OP] ⚠ 10秒内未找到Confirm按钮")
                                                return False
                                            
                                            found_expired_order = True
                                            log_print(f"[{serial_number}] [OP] ✓ 超时订单取消成功，等待5秒后重新检查...")
                                            time.sleep(5)
                                            break  # 取消一个后重新获取列表
                                        else:
                                            log_print(f"[{serial_number}] [OP] ⚠ 未找到svg元素")
                        
                        i += 1
                    except Exception as e:
                        error_msg = str(e)
                        if "stale element" in error_msg.lower():
                            log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签时遇到stale element，重新获取tr列表...")
                            try:
                                open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                                tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                                tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                                tr_count = len(tr_list)
                                continue
                            except Exception as e2:
                                log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr列表失败: {str(e2)}，跳过当前tr")
                                i += 1
                        else:
                            log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签异常: {error_msg}")
                            i += 1
                
                if not found_expired_order:
                    log_print(f"[{serial_number}] [OP] ✓ 没有更多超时订单需要取消")
                    break
                    
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 获取 Open Orders 数据失败: {str(e)}")
                break
        
        log_print(f"[{serial_number}] [OP] ✓ 超时撤单检查完成")
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 超时撤单操作失败: {str(e)}")
        return False


def click_opinion_open_orders_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Open Orders 按钮并获取数据，返回标准格式字符串（支持分页）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (标准格式字符串, 是否需要刷新重试)
            - 如果正常获取数据或找到"No data yet": (标准格式字符串, False)
            - 如果超时且没有"No data yet": ("", True)
            标准格式: "唯一标题|||买卖方向|||选项|||价格|||进度;唯一标题|||买卖方向|||选项|||价格|||进度"
    """
    
    def parse_tbody_data(open_orders_div, serial_number):
        """
        解析当前页的tbody数据
        
        Args:
            open_orders_div: Open Orders div元素
            serial_number: 浏览器序列号
            
        Returns:
            list: 解析后的订单字符串列表
        """
        result_parts = []
        
        # 先检查是否有"No data yet"
        all_p_tags_in_div = open_orders_div.find_elements(By.TAG_NAME, "p")
        for p in all_p_tags_in_div:
            if "No data yet" in p.text:
                log_print(f"[{serial_number}] [OP] ✓ Open Orders 发现 'No data yet'，无数据")
                return result_parts, True  # 返回空列表和"无数据"标记
        
        # 再找这个 div 下的 tbody
        tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        if len(tr_list) == 0:
            time.sleep(10)
             # 先检查是否有"No data yet"
            all_p_tags_in_div = open_orders_div.find_elements(By.TAG_NAME, "p")
            for p in all_p_tags_in_div:
                if "No data yet" in p.text:
                    log_print(f"[{serial_number}] [OP] ✓ Open Orders 发现 'No data yet'，无数据")
                    return result_parts, True  # 返回空列表和"无数据"标记
              # 再找这个 div 下的 tbody
            tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            if len(tr_list) == 0:
                return result_parts, False  # 返回空列表，但不是"No data yet"
        
        log_print(f"[{serial_number}] [OP] ✓ 当前页找到 {len(tr_list)} 个 tr 标签")
        
        # 解析tr标签，构建标准格式字符串
        current_main_title = ""
        i = 0
        tr_count = len(tr_list)
        
        while i < tr_count:
            try:
                # 每次迭代时重新获取tr元素，避免stale element reference
                try:
                    # 重新获取open_orders_div和tbody（防止页面更新导致元素失效）
                    open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                    tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                    current_tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    # 如果tr数量发生变化，更新tr_count
                    if len(current_tr_list) != tr_count:
                        log_print(f"[{serial_number}] [OP] ⚠ tr数量从 {tr_count} 变为 {len(current_tr_list)}，更新计数")
                        tr_count = len(current_tr_list)
                        if i >= tr_count:
                            break
                    
                    tr = current_tr_list[i]
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr元素失败: {str(e)}，跳过当前tr")
                    i += 1
                    continue
                
                td_list = tr.find_elements(By.TAG_NAME, "td")
                
                # 如果只有一个td，这是主标题
                if len(td_list) == 1:
                    main_title_text = get_p_tag_text_from_element(td_list[0])
                    if main_title_text:
                        current_main_title = main_title_text.strip()
                        log_print(f"[{serial_number}] [OP] 找到主标题: {current_main_title}")
                    i += 1
                    continue
                
                # 如果有多个td，这是挂单仓位信息
                if len(td_list) >= 6 and current_main_title:
                    # 第一个td: 买卖方向（"Buy"或"Sell"）
                    first_td_text = get_p_tag_text_from_element(td_list[0]).strip()
                    if not first_td_text:
                        i += 1
                        continue
                    
                    buy_sell_direction = first_td_text  # "Buy" 或 "Sell"
                    
                    # 第二个td: 选项（可能有子标题，例如"90,000 - YES"或"YES"/"NO"）
                    second_td_text = get_p_tag_text_from_element(td_list[1]).strip()
                    if not second_td_text:
                        i += 1
                        continue
                    
                    # 解析选项和子标题
                    option = ""
                    sub_title = ""
                    unique_title = current_main_title
                    
                    if " - " in second_td_text:
                        # 有子标题，例如 "90,000 - YES"
                        parts = second_td_text.split(" - ", 1)
                        if len(parts) == 2:
                            sub_title = parts[0].strip()
                            option = parts[1].strip()
                            unique_title = f"{current_main_title}###{sub_title}"
                    else:
                        # 没有子标题，直接是选项（"YES"或"NO"）
                        option = second_td_text
                    
                    # 第四个td: 价格
                    fourth_td_text = get_p_tag_text_from_element(td_list[3]).strip()
                    if not fourth_td_text:
                        i += 1
                        continue
                    
                    price = fourth_td_text
                    
                    # 第六个td: 所有p标签内容相连，得到进度
                    sixth_td = td_list[5]
                    p_tags_in_sixth = sixth_td.find_elements(By.TAG_NAME, "p")
                    progress_parts = []
                    for p in p_tags_in_sixth:
                        p_text = p.text.strip()
                        if p_text:
                            progress_parts.append(p_text)
                    progress = "".join(progress_parts) if progress_parts else ""
                    
                    # 拼接标准格式: 唯一标题|||买卖方向|||选项|||价格|||进度
                    order_str = f"{unique_title}|||{buy_sell_direction}|||{option}|||{price}|||{progress}"
                    result_parts.append(order_str)
                    log_print(f"[{serial_number}] [OP] 解析到挂单: {order_str}")
                
                i += 1
            except Exception as e:
                error_msg = str(e)
                if "stale element" in error_msg.lower():
                    # 遇到stale element reference，重新获取tr列表
                    log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签时遇到stale element，重新获取tr列表...")
                    try:
                        open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                        tbody = open_orders_div.find_element(By.TAG_NAME, "tbody")
                        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                        tr_count = len(tr_list)
                        log_print(f"[{serial_number}] [OP] ✓ 重新获取到 {tr_count} 个 tr 标签，从索引 {i} 继续")
                        # 不增加i，重新尝试当前索引
                        continue
                    except Exception as e2:
                        log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr列表失败: {str(e2)}，跳过当前tr")
                        i += 1
                else:
                    log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签异常: {error_msg}")
                    i += 1
        
        return result_parts, False  # 返回解析结果，不是"No data yet"
    
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 Open Orders 按钮...")
        
        open_orders_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    log_print(f"[{serial_number}] [OP] ✓ {button.text.strip()}")
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
            log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 Open Orders 按钮，需要刷新页面重试")
            return "", True
        
        time.sleep(5)
        
        try:
            # 在180秒内多次查找tbody和tr标签，如果数量为0则等待5秒后重试
            max_retry_time = 180
            retry_start_time = time.time()
            
            # 所有页面的结果
            all_result_parts = []
            page_num = 1
            
            while time.time() - retry_start_time < max_retry_time:
                try:
                    # 重新获取 open_orders_div（因为分页后内容会刷新）
                    log_print(f"[{serial_number}] [OP] 查找 Open Orders 内容区域（第 {page_num} 页）...")
                    open_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id$='content-open-orders']")
                    log_print(f"[{serial_number}] [OP] ✓ 找到 Open Orders 内容区域 (ID: {open_orders_div.get_attribute('id')})")
                    
                    # 解析当前页数据
                    page_result_parts, is_no_data = parse_tbody_data(open_orders_div, serial_number)
                    
                    if is_no_data:
                        # 如果是"No data yet"，直接返回
                        if len(all_result_parts) == 0:
                            return "", False
                        else:
                            # 已经有数据了，说明之前有数据，现在没数据了，返回已有数据
                            break
                    
                    if len(page_result_parts) > 0:
                        all_result_parts.extend(page_result_parts)
                        log_print(f"[{serial_number}] [OP] ✓ 第 {page_num} 页解析完成，共 {len(page_result_parts)} 个仓位，累计 {len(all_result_parts)} 个仓位")
                    else:
                        elapsed = int(time.time() - retry_start_time)
                        log_print(f"[{serial_number}] [OP] ⚠ 第 {page_num} 页解析后无有效仓位数据")
                    
                    # 检查是否有下一页（即使当前页没有数据，也可能有下一页）
                    try:
                        next_page_button = open_orders_div.find_element(By.CSS_SELECTOR, 'button[aria-label="next page"]')
                        is_disabled = next_page_button.get_attribute("disabled") is not None
                        
                        if is_disabled:
                            log_print(f"[{serial_number}] [OP] ✓ 下一页按钮已禁用，所有页面数据获取完成")
                            break
                        else:
                            log_print(f"[{serial_number}] [OP] 发现下一页，点击下一页按钮...")
                            next_page_button.click()
                            time.sleep(3)  # 等待页面加载
                            page_num += 1
                            retry_start_time = time.time()  # 重置超时时间，因为开始新的一页
                            continue
                    except Exception as e:
                        # 找不到下一页按钮，说明没有分页或已经是最后一页
                        log_print(f"[{serial_number}] [OP] ✓ 未找到下一页按钮，所有页面数据获取完成")
                        break
                    
                except Exception as e:
                    elapsed = int(time.time() - retry_start_time)
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Open Orders 数据异常: {str(e)}，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                    time.sleep(5)
            
            # 返回所有页面的结果
            if len(all_result_parts) > 0:
                result_str = ";".join(all_result_parts)
                log_print(f"[{serial_number}] [OP] ✓ Open Orders 所有页面解析完成，共 {len(all_result_parts)} 个仓位")
                return result_str, False
            else:
                log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Open Orders 数据且无'No data yet'，需要刷新重试")
                return "", True
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Open Orders 数据失败: {str(e)}")
            return "", True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Open Orders 按钮失败: {str(e)}")
        return "", False


def click_opinion_closed_orders_and_get_data(driver, serial_number):
    """
    点击 Opinion Trade Closed Orders 按钮并获取数据，返回标准格式字符串（支持分页，最多3页）
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (标准格式字符串, 是否需要刷新重试)
            - 如果正常获取数据或找到"No data yet": (标准格式字符串, False)
            - 如果超时且没有"No data yet": ("", True)
            标准格式: "唯一标题|||买卖方向|||选项|||限价类型|||价格|||进度|||状态|||时间;唯一标题|||买卖方向|||选项|||限价类型|||价格|||进度|||状态|||时间"
    """
    
    def parse_tbody_data(closed_orders_div, serial_number):
        """
        解析当前页的tbody数据
        
        Args:
            closed_orders_div: Closed Orders div元素
            serial_number: 浏览器序列号
            
        Returns:
            tuple: (解析后的订单字符串列表, 是否是无数据标记)
        """
        result_parts = []
        
        # 先检查是否有"No data yet"
        all_p_tags_in_div = closed_orders_div.find_elements(By.TAG_NAME, "p")
        for p in all_p_tags_in_div:
            if "No data yet" in p.text:
                log_print(f"[{serial_number}] [OP] ✓ Closed Orders 发现 'No data yet'，无数据")
                return result_parts, True  # 返回空列表和"无数据"标记
        
        # 再找这个 div 下的 tbody
        tbody = closed_orders_div.find_element(By.TAG_NAME, "tbody")
        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
        
        if len(tr_list) == 0:
            time.sleep(10)
            # 先检查是否有"No data yet"
            all_p_tags_in_div = closed_orders_div.find_elements(By.TAG_NAME, "p")
            for p in all_p_tags_in_div:
                if "No data yet" in p.text:
                    log_print(f"[{serial_number}] [OP] ✓ Closed Orders 发现 'No data yet'，无数据")
                    return result_parts, True  # 返回空列表和"无数据"标记
            # 再找这个 div 下的 tbody
            tbody = closed_orders_div.find_element(By.TAG_NAME, "tbody")
            tr_list = tbody.find_elements(By.TAG_NAME, "tr")
            if len(tr_list) == 0:
                return result_parts, False  # 返回空列表，但不是"No data yet"
        
        log_print(f"[{serial_number}] [OP] ✓ 当前页找到 {len(tr_list)} 个 tr 标签")
        
        # 解析tr标签，构建标准格式字符串
        current_main_title = ""
        i = 0
        tr_count = len(tr_list)
        
        while i < tr_count:
            try:
                # 每次迭代时重新获取tr元素，避免stale element reference
                try:
                    # 重新获取closed_orders_div和tbody（防止页面更新导致元素失效）
                    closed_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id*='content-closed-orders']")
                    tbody = closed_orders_div.find_element(By.TAG_NAME, "tbody")
                    current_tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                    
                    # 如果tr数量发生变化，更新tr_count
                    if len(current_tr_list) != tr_count:
                        log_print(f"[{serial_number}] [OP] ⚠ tr数量从 {tr_count} 变为 {len(current_tr_list)}，更新计数")
                        tr_count = len(current_tr_list)
                        if i >= tr_count:
                            break
                    
                    tr = current_tr_list[i]
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr元素失败: {str(e)}，跳过当前tr")
                    i += 1
                    continue
                
                td_list = tr.find_elements(By.TAG_NAME, "td")
                
                # 如果只有一个td，这是主标题
                if len(td_list) == 1:
                    main_title_text = get_p_tag_text_from_element(td_list[0])
                    if main_title_text:
                        current_main_title = main_title_text.strip()
                        log_print(f"[{serial_number}] [OP] 找到主标题: {current_main_title}")
                    i += 1
                    continue
                
                # 如果有多个td，这是已关闭订单信息
                if len(td_list) >= 8 and current_main_title:
                    # 第一个td: 买卖方向（"Buy"或"Sell"）
                    first_td_text = get_p_tag_text_from_element(td_list[0]).strip()
                    if not first_td_text:
                        i += 1
                        continue
                    
                    buy_sell_direction = first_td_text  # "Buy" 或 "Sell"
                    
                    # 第二个td: 选项（可能有子标题，例如"90,000 - YES"或"YES"/"NO"）
                    second_td_text = get_p_tag_text_from_element(td_list[1]).strip()
                    if not second_td_text:
                        i += 1
                        continue
                    
                    # 解析选项和子标题
                    option = ""
                    sub_title = ""
                    unique_title = current_main_title
                    
                    if " - " in second_td_text:
                        # 有子标题，例如 "90,000 - YES"
                        parts = second_td_text.rsplit(" - ", 1)
                        if len(parts) == 2:
                            sub_title = parts[0].strip()
                            option = parts[1].strip()
                            unique_title = f"{current_main_title}###{sub_title}"
                    else:
                        # 没有子标题，直接是选项（"YES"或"NO"或其他方向）
                        option = second_td_text
                    
                    # 第三个td: 限价类型（"Limit"或"Market"）
                    third_td_text = get_p_tag_text_from_element(td_list[2]).strip()
                    limit_market_type = third_td_text if third_td_text else ""
                    
                    # 第四个td: 价格（如 18.9¢）
                    fourth_td_text = get_p_tag_text_from_element(td_list[3]).strip()
                    price = fourth_td_text if fourth_td_text else ""
                    
                    # 第五个td: 不管
                    
                    # 第六个td: 进度（所有p标签内容拼接，如 $0/$6.69 或 43.32/55.96shares）
                    sixth_td = td_list[5]
                    p_tags_in_sixth = sixth_td.find_elements(By.TAG_NAME, "p")
                    progress_parts = []
                    for p in p_tags_in_sixth:
                        p_text = p.text.strip()
                        if p_text:
                            progress_parts.append(p_text)
                    progress = "".join(progress_parts) if progress_parts else ""
                    
                    # 第七个td: 状态（可能是"Canceled"或"Filled"）
                    seventh_td_text = get_p_tag_text_from_element(td_list[6]).strip()
                    status = seventh_td_text if seventh_td_text else ""
                    
                    # 第八个td: 时间（如 Jan 05, 2026 13:30:43）
                    eighth_td_text = get_p_tag_text_from_element(td_list[7]).strip()
                    time_str = eighth_td_text if eighth_td_text else ""
                    
                    # 拼接标准格式: 唯一标题|||买卖方向|||选项|||限价类型|||价格|||进度|||状态|||时间
                    order_str = f"{unique_title}|||{buy_sell_direction}|||{option}|||{limit_market_type}|||{price}|||{progress}|||{status}|||{time_str}"
                    result_parts.append(order_str)
                    log_print(f"[{serial_number}] [OP] 解析到已关闭订单: {order_str}")
                
                i += 1
            except Exception as e:
                error_msg = str(e)
                if "stale element" in error_msg.lower():
                    # 遇到stale element reference，重新获取tr列表
                    log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签时遇到stale element，重新获取tr列表...")
                    try:
                        closed_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id*='content-closed-orders']")
                        tbody = closed_orders_div.find_element(By.TAG_NAME, "tbody")
                        tr_list = tbody.find_elements(By.TAG_NAME, "tr")
                        tr_count = len(tr_list)
                        log_print(f"[{serial_number}] [OP] ✓ 重新获取到 {tr_count} 个 tr 标签，从索引 {i} 继续")
                        # 不增加i，重新尝试当前索引
                        continue
                    except Exception as e2:
                        log_print(f"[{serial_number}] [OP] ⚠ 重新获取tr列表失败: {str(e2)}，跳过当前tr")
                        i += 1
                else:
                    log_print(f"[{serial_number}] [OP] ⚠ 解析tr标签异常: {error_msg}")
                    i += 1
        
        return result_parts, False  # 返回解析结果，不是"No data yet"
    
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 Closed Orders 按钮...")
        
        closed_orders_clicked = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    log_print(f"[{serial_number}] [OP] ✓ {button.text.strip()}")
                    if button.text.strip() == "Closed Orders":
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 Closed Orders 按钮")
                        closed_orders_clicked = True
                        break
                
                if closed_orders_clicked:
                    break
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        if not closed_orders_clicked:
            log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 Closed Orders 按钮，需要刷新页面重试")
            return "", True
        
        time.sleep(5)
        
        try:
            # 在180秒内多次查找tbody和tr标签，如果数量为0则等待5秒后重试
            max_retry_time = 180
            retry_start_time = time.time()
            
            # 所有页面的结果
            all_result_parts = []
            page_num = 1
            max_pages = 3  # 最多解析3页
            
            while time.time() - retry_start_time < max_retry_time and page_num <= max_pages:
                try:
                    # 重新获取 closed_orders_div（因为分页后内容会刷新）
                    log_print(f"[{serial_number}] [OP] 查找 Closed Orders 内容区域（第 {page_num} 页）...")
                    closed_orders_div = driver.find_element(By.CSS_SELECTOR, "div[id*='content-closed-orders']")
                    log_print(f"[{serial_number}] [OP] ✓ 找到 Closed Orders 内容区域 (ID: {closed_orders_div.get_attribute('id')})")
                    
                    # 解析当前页数据
                    page_result_parts, is_no_data = parse_tbody_data(closed_orders_div, serial_number)
                    
                    if is_no_data:
                        # 如果是"No data yet"，直接返回
                        if len(all_result_parts) == 0:
                            return "", False
                        else:
                            # 已经有数据了，说明之前有数据，现在没数据了，返回已有数据
                            break
                    
                    if len(page_result_parts) > 0:
                        all_result_parts.extend(page_result_parts)
                        log_print(f"[{serial_number}] [OP] ✓ 第 {page_num} 页解析完成，共 {len(page_result_parts)} 个订单，累计 {len(all_result_parts)} 个订单")
                    else:
                        elapsed = int(time.time() - retry_start_time)
                        log_print(f"[{serial_number}] [OP] ⚠ 第 {page_num} 页解析后无有效订单数据")
                    
                    # 检查是否有下一页（即使当前页没有数据，也可能有下一页）
                    # 但最多只解析3页
                    if page_num >= max_pages:
                        log_print(f"[{serial_number}] [OP] ✓ 已达到最大页数限制（{max_pages}页），停止解析")
                        break
                    
                    try:
                        next_page_button = closed_orders_div.find_element(By.CSS_SELECTOR, 'button[aria-label="next page"]')
                        is_disabled = next_page_button.get_attribute("disabled") is not None
                        
                        if is_disabled:
                            log_print(f"[{serial_number}] [OP] ✓ 下一页按钮已禁用，所有页面数据获取完成")
                            break
                        else:
                            log_print(f"[{serial_number}] [OP] 发现下一页，点击下一页按钮...")
                            next_page_button.click()
                            time.sleep(3)  # 等待页面加载
                            page_num += 1
                            retry_start_time = time.time()  # 重置超时时间，因为开始新的一页
                            continue
                    except Exception as e:
                        # 找不到下一页按钮，说明没有分页或已经是最后一页
                        log_print(f"[{serial_number}] [OP] ✓ 未找到下一页按钮，所有页面数据获取完成")
                        break
                    
                except Exception as e:
                    elapsed = int(time.time() - retry_start_time)
                    log_print(f"[{serial_number}] [OP] ⚠ 查找 Closed Orders 数据异常: {str(e)}，等待5秒后重试... ({elapsed}s/{max_retry_time}s)")
                    time.sleep(5)
            
            # 返回所有页面的结果
            if len(all_result_parts) > 0:
                result_str = ";".join(all_result_parts)
                log_print(f"[{serial_number}] [OP] ✓ Closed Orders 所有页面解析完成，共 {len(all_result_parts)} 个订单")
                return result_str, False
            else:
                log_print(f"[{serial_number}] [OP] ✗ 180秒内未获取到 Closed Orders 数据且无'No data yet'，需要刷新重试")
                return "", True
            
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 获取 Closed Orders 数据失败: {str(e)}")
            return "", True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Closed Orders 按钮失败: {str(e)}")
        return "", False


def parse_progress_string(progress_str):
    """
    解析进度字符串，拆分出成交数量和总共
    
    Args:
        progress_str: 进度字符串，如 "$0/$6.69" 或 "43.32/55.96shares"
        
    Returns:
        tuple: (fillAmt, amt) - (成交数量, 总共)，如果解析失败返回 (None, None)
    """
    if not progress_str:
        return None, None
    
    try:
        # 移除所有空格
        progress_str = progress_str.strip().replace(" ", "")
        
        # 检查是否包含 "/"
        if "/" not in progress_str:
            return None, None
        
        # 分割
        parts = progress_str.split("/")
        if len(parts) != 2:
            return None, None
        
        fill_part = parts[0].strip()
        amt_part = parts[1].strip()
        
        # 移除货币符号、单位和千位分隔符逗号
        fill_part = fill_part.replace("$", "").replace("shares", "").replace(",", "").strip()
        amt_part = amt_part.replace("$", "").replace("shares", "").replace(",", "").strip()
        
        # 转换为浮点数
        try:
            fill_amt = float(fill_part) if fill_part else 0.0
            amt = float(amt_part) if amt_part else 0.0
            return fill_amt, amt
        except ValueError:
            return None, None
            
    except Exception as e:
        log_print(f"[解析进度] ⚠ 解析进度字符串失败: {progress_str}, 错误: {str(e)}")
        return None, None


def get_timezone_from_ip(ip):
    """
    根据IP获取时区信息（使用免费API）
    
    Args:
        ip: IP地址
        
    Returns:
        str: 时区名称（如 "America/New_York"），失败返回 None
    """
    if not ip or ip == "None" or str(ip).strip() == "":
        log_print(f"[时区查询] ⚠ IP地址为空或无效，无法获取时区")
        return None
    
    try:
        # 使用 ip-api.com 免费API获取时区信息
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                timezone = data.get("timezone")
                if timezone:
                    log_print(f"[时区查询] IP {ip} 的时区: {timezone}")
                    return timezone
        
        log_print(f"[时区查询] ⚠ 无法获取IP {ip} 的时区信息")
        return None
    except Exception as e:
        log_print(f"[时区查询] ⚠ 获取IP {ip} 时区失败: {str(e)}")
        return None


def convert_time_to_beijing(original_time_str, ip, serial_number=None, cached_timezone=None):
    """
    将原始时间转换为北京时间时间戳
    
    Args:
        original_time_str: 原始时间字符串，格式如 "Jan 05, 2026 13:30:43"
        ip: IP地址，用于获取时区（备用方案）
        serial_number: 浏览器序列号，用于从页面获取时区（优先方案）
        cached_timezone: 已缓存的时区名称，如果提供则直接使用，不再查询IP
        
    Returns:
        tuple: (原始时间字符串, 转换后的北京时间戳（毫秒）)
               格式: "Jan 05, 2026 13:30:43", 1736086200000
    """
    if not original_time_str:
        return original_time_str, 0
    
    try:
        # 解析原始时间字符串
        # 格式: "Jan 05, 2026 13:30:43" 或 "Dec 26, 2025 19:47:03"
        from datetime import datetime
        import pytz
        import time
        
        # 解析时间字符串
        try:
            original_dt = datetime.strptime(original_time_str, "%b %d, %Y %H:%M:%S")
        except ValueError:
            log_print(f"[时间转换] ⚠ 无法解析时间格式: {original_time_str}")
            return original_time_str, 0
        
        # 优先使用从 beijing_time.html 页面获取的时区
        timezone_name = None
        timezone_source = None
        
        if serial_number and serial_number in BEIJING_TIME_PAGE_TIMEZONE:
            timezone_name = BEIJING_TIME_PAGE_TIMEZONE[serial_number]
            timezone_source = "页面"
            log_print(f"[时间转换] ✓ 使用从 beijing_time.html 页面获取的时区: {timezone_name}")
        
        # 如果页面时区获取失败，则使用缓存的时区或IP查询时区
        if not timezone_name:
            if cached_timezone:
                # 使用已缓存的时区，不再查询
                timezone_name = cached_timezone
                timezone_source = "IP查询（已缓存）"
            elif ip:
                timezone_name = get_timezone_from_ip(ip)
                timezone_source = "IP查询"
                if timezone_name:
                    log_print(f"[时间转换] ✓ 使用IP查询获取的时区: {timezone_name}")
            else:
                log_print(f"[时间转换] ⚠ 无法获取时区（无serial_number和IP），假设原始时间为UTC")
        
        # 设置源时区
        if not timezone_name:
            # 如果无法获取时区，假设原始时间是UTC时间
            log_print(f"[时间转换] ⚠ 无法获取时区，假设原始时间为UTC")
            source_tz = pytz.UTC
            timezone_source = "默认UTC"
        else:
            try:
                source_tz = pytz.timezone(timezone_name)
            except Exception as e:
                log_print(f"[时间转换] ⚠ 时区名称无效: {timezone_name}, 使用UTC: {str(e)}")
                source_tz = pytz.UTC
                timezone_source = "默认UTC（时区无效）"
        
        # 将原始时间设置为源时区
        original_dt = source_tz.localize(original_dt)
        
        # 转换为北京时间（UTC+8）
        beijing_tz = pytz.timezone("Asia/Shanghai")
        beijing_dt = original_dt.astimezone(beijing_tz)
        
        # 转换为时间戳（毫秒）
        beijing_timestamp = int(beijing_dt.timestamp() * 1000)
        
        return original_time_str, beijing_timestamp
        
    except Exception as e:
        log_print(f"[时间转换] ⚠ 时间转换失败: {str(e)}")
        return original_time_str, 0


def upload_closed_orders_data(browser_id, closed_orders_data_str, current_ip):
    """
    上传 Closed Orders 数据到接口
    
    Args:
        browser_id: 浏览器编号
        closed_orders_data_str: Closed Orders 数据字符串，格式: "唯一标题|||买卖方向|||选项|||限价类型|||价格|||进度|||状态|||时间;..."
        current_ip: 当前使用的IP地址
        
    Returns:
        bool: 上传成功返回True，失败返回False
    """
    if not closed_orders_data_str or closed_orders_data_str.strip() == "":
        log_print(f"[{browser_id}] Closed Orders 数据为空，跳过上传")
        return True  # 空数据不算失败
    
    # 如果 current_ip 为 None，尝试从 LAST_PROXY_CONFIG 获取
    if current_ip is None:
        log_print(f"[{browser_id}] ⚠ current_ip 为 None，尝试从 LAST_PROXY_CONFIG 获取...")
        last_config = LAST_PROXY_CONFIG.get(str(browser_id))
        if last_config:
            current_ip = last_config.get("ip")
            if current_ip:
                log_print(f"[{browser_id}] ✓ 从 LAST_PROXY_CONFIG 获取到IP: {current_ip}")
            else:
                log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中的IP也为空")
        else:
            log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中没有该浏览器的配置")
    
    # 如果仍然为 None，记录警告但继续处理（使用空字符串）
    if current_ip is None:
        log_print(f"[{browser_id}] ⚠ 无法获取当前IP，时间转换将使用UTC时区")
    
    # 在开始转换前，先查询一次时区（如果页面时区获取失败的话）
    cached_timezone = None
    if browser_id not in BEIJING_TIME_PAGE_TIMEZONE:
        # 页面时区获取失败，需要查询IP时区
        if current_ip:
            cached_timezone = get_timezone_from_ip(current_ip)
            if cached_timezone:
                log_print(f"[{browser_id}] ✓ 预先查询时区成功: {cached_timezone}，后续转换将使用此缓存")
    
    try:
        # 解析数据字符串
        orders_list = []
        order_strings = closed_orders_data_str.split(";")
        
        for order_str in order_strings:
            if not order_str or not order_str.strip():
                continue
            
            parts = order_str.split("|||")
            if len(parts) < 8:
                log_print(f"[{browser_id}] ⚠ Closed Orders 数据格式不正确，跳过: {order_str}")
                continue
            
            trending = parts[0].strip()  # 唯一标题（事件）
            side = parts[1].strip().upper()  # 买卖方向（SELL/BUY）
            out_come = parts[2].strip().upper()  # 选项（YES/NO）
            type_str = parts[3].strip().upper()  # 限价类型（LIMIT/MARKET）
            price_raw = parts[4].strip()  # 价格（原始，可能包含美分符号）
            progress = parts[5].strip()  # 进度
            status = parts[6].strip().lower()  # 状态（filled/canceled）
            time_str = parts[7].strip()  # 时间
            
            # 处理价格：去掉美分符号（¢），只保留数字
            price = price_raw.replace("¢", "").strip()
            
            # 解析进度，拆分出成交数量和总共
            fill_amt, amt = parse_progress_string(progress)
            if fill_amt is None or amt is None:
                log_print(f"[{browser_id}] ⚠ 无法解析进度字符串: {progress}，跳过该订单")
                continue
            
            # 转换时间（优先使用页面获取的时区，如果失败则使用预先查询的缓存时区）
            original_time, convert_time_timestamp = convert_time_to_beijing(time_str, current_ip, serial_number=browser_id, cached_timezone=cached_timezone)
            
            # 构建订单数据
            order_data = {
                "trending": trending,
                "side": side,
                "type": type_str,
                "outCome": out_come,
                "fillAmt": fill_amt,
                "amt": amt,
                "price": price,
                "status": status,
                "ip": current_ip if current_ip else "",
                "time": original_time,
                "convertTime": convert_time_timestamp
            }
            
            orders_list.append(order_data)
        
        if len(orders_list) == 0:
            log_print(f"[{browser_id}] ⚠ 没有有效的 Closed Orders 数据需要上传")
            return True
        
        # 提交数据到接口
        url = f"{SERVER_BASE_URL}/boost/insertClosedOrder"
        payload = {
            "number": str(browser_id),
            "list": orders_list
        }
        
        log_print(f"[{browser_id}] 开始上传 Closed Orders 数据到 /boost/insertClosedOrder，共 {len(orders_list)} 条...")
        
        # 打印数据详情（用于调试）
        import json
        payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
        log_print(f"[{browser_id}] ==================== Closed Orders 数据详情 ====================")
        log_print(f"[{browser_id}] {payload_str}")
        log_print(f"[{browser_id}] =================================================================")
        
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                log_print(f"[{browser_id}] ✓ Closed Orders 数据上传成功")
                return True
            else:
                log_print(f"[{browser_id}] ✗ Closed Orders 数据上传失败: {result.get('msg', '未知错误')}")
                return False
        else:
            log_print(f"[{browser_id}] ✗ Closed Orders 数据上传失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 上传 Closed Orders 数据异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
        return False


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
                        
                        # P6: 价格/price (索引5)
                        fee = p_tags[5].text.strip()
                        
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
                        
                        if amount != "-" and value != "-" and fee != "-":
                            transaction = {
                                "title": final_title,
                                "direction": direction,
                                "option": final_option,
                                "amount": amount,
                                "value": value,
                                "price": price,
                                "time": trade_time,
                                "fee": fee
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


def get_points_history_data(driver, serial_number):
    """
    获取 Points History 数据
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        
    Returns:
        str: Points History 数据字符串，如果没有数据或获取失败则返回 "0" 或空字符串
    """
    try:
        log_print(f"[{serial_number}] [OP] 步骤10: 进入 Points 页面获取 Points History 数据...")
        
        # 1. 进入 https://app.opinion.trade/points 页面
        points_url = "https://app.opinion.trade/points"
        log_print(f"[{serial_number}] [OP] 导航到 {points_url}...")
        driver.get(points_url)
        time.sleep(3)
        
        # 2. 等待页面加载完成后，在20s内找到是否有内容为 'Your Points History' 的p标签存在
        log_print(f"[{serial_number}] [OP] 在20秒内查找 'Your Points History' p标签...")
        points_history_p = None
        start_time = time.time()
        
        while time.time() - start_time < 20:
            try:
                all_p_tags = driver.find_elements(By.TAG_NAME, "p")
                for p in all_p_tags:
                    if p.text.strip() == "Your Points History":
                        points_history_p = p
                        log_print(f"[{serial_number}] [OP] ✓ 找到 'Your Points History' p标签")
                        break
                
                if points_history_p:
                    break
                
                time.sleep(0.5)
            except Exception as e:
                log_print(f"[{serial_number}] [OP] ⚠ 查找 p 标签时出错: {str(e)}")
                time.sleep(0.5)
        
        if not points_history_p:
            log_print(f"[{serial_number}] [OP] ⚠ 20秒内未找到 'Your Points History' p标签，不记录该数据")
            return ""
        
        # 3. 点击 p标签的父节点的父节点
        try:
            parent = points_history_p.find_element(By.XPATH, "..")
            grandparent = parent.find_element(By.XPATH, "..")
            log_print(f"[{serial_number}] [OP] 点击 p标签的父节点的父节点...")
            grandparent.click()
            time.sleep(5)
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 点击父节点的父节点失败: {str(e)}")
            return ""
        
        # 4. 等待5s后，找到内容为'Your Points History'的p标签，并检查 data-sentry-source-file="pointsHistoryModal.tsx"
        log_print(f"[{serial_number}] [OP] 等待5秒后重新查找 'Your Points History' p标签（需包含 data-sentry-source-file='pointsHistoryModal.tsx'）...")
        time.sleep(5)
        
        points_history_p_after = None
        try:
            all_p_tags = driver.find_elements(By.TAG_NAME, "p")
            for p in all_p_tags:
                if p.text.strip() == "Your Points History":
                    # 检查 data-sentry-source-file 属性
                    data_sentry_source_file = p.get_attribute("data-sentry-source-file")
                    if data_sentry_source_file == "pointsHistoryModal.tsx":
                        points_history_p_after = p
                        log_print(f"[{serial_number}] [OP] ✓ 重新找到 'Your Points History' p标签（包含 data-sentry-source-file='pointsHistoryModal.tsx'）")
                        break
                    else:
                        log_print(f"[{serial_number}] [OP] ⚠ 找到 p 标签但 data-sentry-source-file 不匹配: {data_sentry_source_file}")
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 重新查找 p 标签时出错: {str(e)}")
            return ""
        
        if not points_history_p_after:
            log_print(f"[{serial_number}] [OP] ⚠ 未找到 'Your Points History' p标签")
            return ""
        
        # 5. 找到 p标签的上一级父节点
        try:
            parent_after = points_history_p_after.find_element(By.XPATH, "..")
            
            # 6. 找到父节点下的下一级div子节点，即找到与p标签同级的div标签（A）
            div_children = parent_after.find_elements(By.TAG_NAME, "div")
            div_a = None
            for div in div_children:
                # 检查这个div是否是p标签的兄弟节点（同级的div）
                if div != points_history_p_after:
                    div_a = div
                    log_print(f"[{serial_number}] [OP] ✓ 找到与p标签同级的div标签（A）")
                    break
            
            if not div_a:
                log_print(f"[{serial_number}] [OP] ⚠ 未找到与p标签同级的div标签")
                return ""
            
            # 7. 找到这个div（A）标签下的子div
            div_a_children = div_a.find_elements(By.TAG_NAME, "div")
            
            # 如果A下面的子div的数量不足2个，则判断是否有内容为 "No points history found"的p标签存在
            if len(div_a_children) < 2:
                log_print(f"[{serial_number}] [OP] ⚠ div A 下的子div数量不足2个（共{len(div_a_children)}个），检查是否有 'No points history found'...")
                try:
                    all_p_in_div_a = div_a.find_elements(By.TAG_NAME, "p")
                    for p in all_p_in_div_a:
                        if "No points history found" in p.text.strip():
                            log_print(f"[{serial_number}] [OP] ✓ 找到 'No points history found'，返回 '0'")
                            return "0"
                except:
                    pass
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 'No points history found'，返回空字符串")
                return ""
            
            # 8. 从第二个div开始，获取div中的所有p标签内容
            result_parts = []
            for div_idx in range(1, len(div_a_children)):  # 从第二个div开始（索引1）
                div_child = div_a_children[div_idx]
                try:
                    p_tags_in_div = div_child.find_elements(By.TAG_NAME, "p")
                    p_contents = []
                    for p in p_tags_in_div:
                        p_text = p.text.strip()
                        if p_text:
                            p_contents.append(p_text)
                    
                    # 多个p标签的内容用 ||| 分割拼接
                    if p_contents:
                        div_content = "|||".join(p_contents)
                        result_parts.append(div_content)
                        log_print(f"[{serial_number}] [OP] Div {div_idx + 1}: {div_content[:100]}...")
                except Exception as e:
                    log_print(f"[{serial_number}] [OP] ⚠ 处理 div {div_idx + 1} 时出错: {str(e)}")
                    continue
            
            # 9. 将每个div的内容用分号拼接，得到最终内容
            if result_parts:
                final_result = ";".join(result_parts)
                log_print(f"[{serial_number}] [OP] ✓ Points History 数据获取成功，共 {len(result_parts)} 条记录")
                return final_result
            else:
                log_print(f"[{serial_number}] [OP] ⚠ 未获取到有效的 Points History 数据")
                return ""
                
        except Exception as e:
            log_print(f"[{serial_number}] [OP] ⚠ 处理 Points History 数据时出错: {str(e)}")
            import traceback
            log_print(f"[{serial_number}] [OP] 错误详情:\n{traceback.format_exc()}")
            return ""
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 获取 Points History 数据失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [OP] 错误详情:\n{traceback.format_exc()}")
        return ""


# ============================================================================
# Type 2 任务 - 数据处理和格式化函数
# ============================================================================

def parse_position_string_to_list(position_string):
    """
    将标准格式的 Position 字符串转换为列表格式
    
    Args:
        position_string: str，标准格式字符串，例如 "唯一标题|||方向|||数量|||均价;唯一标题|||方向|||数量|||均价"
        
    Returns:
        list: 格式化后的数据，每项为 {"title": 标题, "option": 选项, "amount": ±数量, "avg_price": 平均价格}
    """
    if not position_string or position_string.strip() == "":
        return []
    
    result = []
    # 按分号分割每个仓位
    positions = position_string.split(';')
    
    for pos_str in positions:
        if not pos_str.strip():
            continue
        
        # 按 ||| 分割
        parts = pos_str.split('|||')
        if len(parts) >= 4:
            unique_title = parts[0].strip()
            direction = parts[1].strip()
            amount_str = parts[2].strip()
            avg_price = parts[3].strip()
            
            # 解析数量（可能已经带正负号）
            try:
                # 处理 <0.01 的情况
                if '<0.01' in amount_str:
                    # 提取正负号
                    if amount_str.startswith('+'):
                        amount = 0.005  # 使用一个很小的正数
                    elif amount_str.startswith('-'):
                        amount = -0.005  # 使用一个很小的负数
                    else:
                        # 没有正负号，根据方向判断
                        amount = 0.005 if direction.upper() == "YES" else -0.005
                else:
                    # 如果数量字符串已经带正负号，直接转换
                    if amount_str.startswith('+') or amount_str.startswith('-'):
                        amount = float(amount_str.replace(',', ''))
                    else:
                        # 如果没有正负号，根据方向添加
                        amount = float(amount_str.replace(',', ''))
                        if direction.upper() == "NO":
                            amount = -amount
                
                # 如果 amount 的绝对值小于 1，跳过该项
                if abs(amount) < 1:
                    continue
            except:
                continue
            
            result.append({
                "title": unique_title,
                "option": direction,
                "amount": amount,
                "avg_price": avg_price
            })
    
    return result


def process_op_position_data(position_data):
    """
    处理 OP Position 数据，格式化为标准格式
    
    Args:
        position_data: list，原始的p标签内容列表（旧格式，已废弃）
                     或 str，标准格式字符串（新格式）
        
    Returns:
        list: 格式化后的数据，每项为 {"title": 标题, "option": 选项, "amount": ±数量, "avg_price": 平均价格}
    """
    # 如果输入是字符串，使用新的解析函数
    if isinstance(position_data, str):
        return parse_position_string_to_list(position_data)
    
    # 以下是旧的解析逻辑（保留用于兼容）
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

def upload_account_config_with_retry(data, browser_id=None, timeout=15, max_retries=5, retry_interval=10):
    """
    上传账户配置到服务器，带重试机制
    
    Args:
        data: 要上传的数据（字典）
        browser_id: 浏览器编号（可选，用于日志）
        timeout: 请求超时时间（秒），默认15秒
        max_retries: 最大重试次数，默认5次
        retry_interval: 重试间隔时间（秒），默认10秒
        
    Returns:
        tuple: (success: bool, response_data: dict or None, error_msg: str or None)
    """
    upload_url = f"{SERVER_BASE_URL}/boost/addAccountConfig"
    log_prefix = f"[{browser_id}]" if browser_id else ""
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                log_print(f"{log_prefix} 第 {attempt} 次尝试上传账户配置...")
            else:
                log_print(f"{log_prefix} 上传账户配置到服务器...")
            
            response = requests.post(upload_url, json=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                if attempt > 1:
                    log_print(f"{log_prefix} ✓ 上传成功（第 {attempt} 次尝试）")
                else:
                    log_print(f"{log_prefix} ✓ 上传成功")
                return True, result, None
            else:
                error_msg = f"HTTP {response.status_code}"
                log_print(f"{log_prefix} ✗ 上传失败: {error_msg}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries:
                    log_print(f"{log_prefix} ⏳ {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                else:
                    return False, None, error_msg
                    
        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            log_print(f"{log_prefix} ✗ 上传失败: {error_msg}")
            if attempt < max_retries:
                log_print(f"{log_prefix} ⏳ {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                return False, None, error_msg
                
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {str(e)}"
            log_print(f"{log_prefix} ✗ 上传失败: {error_msg}")
            if attempt < max_retries:
                log_print(f"{log_prefix} ⏳ {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            log_print(f"{log_prefix} ✗ 上传失败: {error_msg}")
            if attempt < max_retries:
                log_print(f"{log_prefix} ⏳ {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                return False, None, error_msg
    
    # 所有重试都失败
    log_print(f"{log_prefix} ✗✗✗ 上传失败，已重试 {max_retries} 次")
    return False, None, "所有重试均失败"


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
        params = {"no": browser_id,"computeGroup":COMPUTER_GROUP}
        
        response = requests.get(get_url, params=params, timeout=10)
        
        if response.status_code != 200:
            time.sleep(2)
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
        
        # 3. 上传更新（带重试机制）
        success, result, error_msg = upload_account_config_with_retry(
            account_config, 
            browser_id=browser_id, 
            timeout=10
        )
        
        if not success:
            log_print(f"[{browser_id}] ✗ 上传时间戳失败: {error_msg}")
            return False
        
        log_print(f"[{browser_id}] ✓ 时间戳更新成功")
        return True
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 更新时间戳异常: {str(e)}")
        return False

def update_browser_timestamp_q(browser_id, trendingId=''):
    """
    通过API更新浏览器时间戳
    
    Args:
        browser_id: 浏览器编号
        trendingId: 交易主题ID
        
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            log_print(f"[{browser_id}] 更新浏览器时间戳... (尝试 {attempt + 1}/{max_retries})")
            
            # 构建请求URL和参数
            url = f"{SERVER_BASE_URL}/hedge/updateSingleOpenTime"
            timestamp = int(time.time() * 1000)
            
            payload = {
                "number": browser_id,
                "trendingId": trendingId,
                "time": timestamp
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                log_print(f"[{browser_id}] ✓ 时间戳更新成功: {timestamp}")
                return True
            else:
                if attempt < max_retries - 1:
                    log_print(f"[{browser_id}] ⚠ 更新时间戳失败: HTTP {response.status_code}，将重试...")
                    time.sleep(2)
                    continue
                else:
                    log_print(f"[{browser_id}] ✗ 更新时间戳失败: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            if attempt < max_retries - 1:
                log_print(f"[{browser_id}] ⚠ 更新时间戳异常: {str(e)}，将重试...")
                time.sleep(2)
                continue
            else:
                log_print(f"[{browser_id}] ✗ 更新时间戳异常: {str(e)}")
                return False
    
    return False




def upload_type2_data(browser_id, collected_data, exchange_name='', available_balance=None):
    """
    上传 Type 2 任务收集到的数据
    
    Args:
        browser_id: 浏览器编号
        collected_data: 收集到的数据，包含 positions, open_orders, balance, portfolio 等
        exchange_name: 交易所名称（OP 或 Ploy）
        available_balance: 可用余额（可选，用于更新字段 p）
        
    Returns:
        bool: 上传成功返回True，失败返回False
    """
    import time
    max_retries = 3
    retry_interval = 5  # 秒
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                log_print(f"[{browser_id}] 第 {attempt} 次重试上传数据（共 {max_retries} 次重试机会）...")
            else:
                log_print(f"[{browser_id}] 开始上传数据...")
            
            # 1. 先获取现有配置
            log_print(f"[{browser_id}] 步骤1: 获取现有账户配置...")
            get_url = f"{SERVER_BASE_URL}/boost/findAccountConfigByNo"
            params = {"no": browser_id,"computeGroup":COMPUTER_GROUP}
            
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
                # 如果 avg_price 是 None，转换为空字符串
                if avg_price is None:
                    avg_price = ''
                # 记录均价信息，便于调试
                if not avg_price:
                    log_print(f"[{browser_id}] ⚠ 警告：仓位 '{title}' 的均价为空（原始值: {repr(pos.get('avg_price'))}）")
                position_str_list.append(f"{title}|||{option}|||{amount:+.2f}|||{avg_price}")
            position_str = ";".join(position_str_list)
            
            # 3. 格式化 open orders 数据（使用 ||| 作为字段分隔符，避免标题中的逗号）
            open_orders = collected_data.get('open_orders', [])
            
            # 判断 open_orders 的类型：OP 返回的是字符串，Polymarket 返回的是列表
            if isinstance(open_orders, str):
                # OP 交易所：已经是标准格式字符串，直接使用
                open_orders_str = open_orders
                log_print(f"[{browser_id}] Open Orders 数据已经是字符串格式，直接使用")
            elif isinstance(open_orders, list):
                # Polymarket：需要转换为字符串格式
                open_orders_str_list = []
                for order in open_orders:
                    if isinstance(order, dict):
                        title = order.get('title', '')
                        price = order.get('price', '')
                        progress = order.get('progress', '')
                        open_orders_str_list.append(f"{title}|||{price}|||{progress}")
                    else:
                        log_print(f"[{browser_id}] ⚠ Open Orders 列表项不是字典格式，跳过")
                open_orders_str = ";".join(open_orders_str_list)
            else:
                # 其他类型，设为空字符串
                open_orders_str = ""
                log_print(f"[{browser_id}] ⚠ Open Orders 数据类型未知: {type(open_orders)}")
            
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
            portfolio_found = portfolio_str is not None and portfolio_str != ''and portfolio_str != '-'
            
            if balance_found and portfolio_found:
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
            
            # 5.4. 判断：如果 positions 是空的（包括空列表[]），但是 portfolio_found 获取成功且大于0，则不上传数据
            if (not positions or len(positions) == 0) and portfolio_found and portfolio > 5:
                log_print(f"[{browser_id}] ⚠ positions 为空（空列表），但 portfolio 获取成功且大于5（portfolio={portfolio}），不上传数据")
                return False
            
            # 5.5. 判断 balance 和 portfolio 是否都为空或都是 0
            should_skip_balance_and_portfolio = (balance == 0 or balance_str == '' or balance_str is None) and (portfolio == 0 or portfolio_str == '' or portfolio_str is None)
            
            if should_skip_balance_and_portfolio:
                log_print(f"[{browser_id}] ⚠ balance 和 portfolio 都为空或都是 0，不上传 balance 和 c 字段，且不更新 d 字段")
                return False
            
            # 5.6. 解析并验证可用余额（在上传之前进行判断）
            available_balance_value = None  # 用于存储转换后的数值
            
            # 判断1: 如果可用余额为 None，则不上传数据
            if available_balance is None:
                log_print(f"[{browser_id}] ✗ 可用余额为 None，不上传数据")
                return False
            
            # 解析可用余额
            try:
                if isinstance(available_balance, str):
                    available_balance_clean = available_balance.replace('$', '').replace(',', '').strip()
                    if available_balance_clean and available_balance_clean != "-" and available_balance_clean.lower() != "null":
                        try:
                            available_balance_value = float(available_balance_clean)
                        except ValueError:
                            # 无法转换为数字
                            available_balance_value = None
                    else:
                        # 空字符串或无效值
                        available_balance_value = None
                else:
                    # 非字符串类型
                    if available_balance == 0:
                        available_balance_value = 0
                    elif available_balance is not None:
                        try:
                            available_balance_value = float(available_balance)
                        except (ValueError, TypeError):
                            available_balance_value = None
                    else:
                        available_balance_value = None
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 解析可用余额时发生异常: {str(e)}")
                available_balance_value = None
            
            # 判断2: 如果可用余额解析不出来，或者等于0，则不上传数据
            if available_balance_value is None or available_balance_value == 0:
                log_print(f"[{browser_id}] ✗ 可用余额解析不出来或等于0（available_balance_value={available_balance_value}），不上传数据")
                return False
            
            # 判断3: 如果可用余额和余额的相差的绝对值大于0.1，并且open_orders_str是空字符串，则不上传数据
            if open_orders_str == "":
                balance_diff = abs(available_balance_value - balance)
                if balance_diff > 0.1:
                    log_print(f"[{browser_id}] ✗ 可用余额和余额相差过大（可用余额={available_balance_value}, 余额={balance}, 差值={balance_diff}），且open_orders为空，不上传数据")
                    return False
            
            # 6. 更新字段
            # 打印完整的 "a" 字段内容（可能很长）
            log_print(f"[{browser_id}] ========== 完整的 'a' 字段内容 ==========")
            log_print(f"[{browser_id}] {position_str}")
            log_print(f"[{browser_id}] ========================================")
            
            account_config['a'] = position_str
            account_config['b'] = open_orders_str
            
            # 只有在 balance 和 portfolio 不全为空或全为 0 时才更新这些字段
            if not should_skip_balance_and_portfolio:
                account_config['balance'] = balance
                account_config['c'] = str(portfolio)
            else:
                log_print(f"[{browser_id}] ℹ 跳过更新 balance 和 c 字段")
            
            # 更新字段 p（可用余额）
            # 注意：可用余额的有效性已经在前面判断过了，这里直接更新
            if available_balance is not None and available_balance_value is not None:
                try:
                    # 格式化可用余额字符串（保留原始格式用于上传）
                    if isinstance(available_balance, str):
                        available_balance_clean = available_balance.replace('$', '').replace(',', '').strip()
                        if available_balance_clean and available_balance_clean != "-" and available_balance_clean.lower() != "null":
                            account_config['p'] = available_balance_clean
                            log_print(f"[{browser_id}] ✓ 更新字段 p (可用余额): {available_balance_clean}")
                    else:
                        account_config['p'] = str(available_balance)
                        log_print(f"[{browser_id}] ✓ 更新字段 p (可用余额): {available_balance}")
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 更新字段 p 失败: {str(e)}")
            else:
                log_print(f"[{browser_id}] ℹ 未提供可用余额，字段 p 保持不变")
            
            
            
            # 只有在数据收集成功时才更新时间戳 d
            if data_collected_success:
                timestamp = int(time.time() * 1000)
                account_config['d'] = str(timestamp)
                log_print(f"[{browser_id}] ✓ 更新时间戳: {timestamp}")
            else:
                log_print(f"[{browser_id}] ℹ 保持原有时间戳不变")
            
            account_config['e'] = exchange_name  # 平台名称
            
            # 6.5. 处理 Points History 数据（字段 k）
            points_history_data = collected_data.get('k', '')
            if points_history_data:
                # 如果返回的数据是"0"，则判断原本的"k"字段是否包含"|||"
                if points_history_data == "0":
                    original_k = account_config.get('k', '')
                    if original_k and '|||' in original_k:
                        # 服务器有有效数据，不更新无效数据
                        log_print(f"[{browser_id}] ℹ Points History 数据为 '0'，但服务器已有有效数据（包含|||），不更新字段 k")
                    else:
                        # 服务器没有有效数据，更新为"0"
                        account_config['k'] = "0"
                        log_print(f"[{browser_id}] ✓ 更新字段 k: 0（无数据）")
                else:
                    # 有有效数据，直接更新
                    account_config['k'] = points_history_data
                    log_print(f"[{browser_id}] ✓ 更新字段 k: {points_history_data[:100]}...")
            else:
                log_print(f"[{browser_id}] ℹ 未获取到 Points History 数据，字段 k 保持不变")
            
            # 6.6. 如果获取到了 Balance Spot 地址，更新字段 h
            balance_spot_address = collected_data.get('balance_spot_address')
            if balance_spot_address and balance_spot_address.startswith('0x') and account_config['i'] != "1":
                account_config['h'] = balance_spot_address
                log_print(f"[{browser_id}] ✓ 更新字段 h: {balance_spot_address}")
            else:
                log_print(f"[{browser_id}] ℹ 未获取到有效的 Balance Spot 地址，字段 h 保持不变")
            
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
                    cleaned_fee = clean_number_string(trans['fee'])
                    
                    transaction_data = {
                        "trending": trans['title'],
                        "side": trans['direction'],
                        "outCome": trans['option'],
                        "shares": cleaned_shares,    # 原 amount 字段映射到 shares (去除逗号)
                        "amount": cleaned_amount,    # 原 value 字段映射到 amount (去除符号)
                        "price": cleaned_price,      # price (去除符号)
                        "fee": cleaned_fee,          # fee (去除符号)
                        "time": parse_time_to_timestamp(trans['time'])
                    }
                    transactions_list.append(transaction_data)
                    log_print(f"[{browser_id}]   交易 {idx}: {trans['title']} | {trans['direction']} | {trans['option']} | shares={cleaned_shares} (原:{trans['amount']}) | amount={cleaned_amount} (原:{trans['value']}) | price={cleaned_price} (原:{trans['price']}) | fee={cleaned_fee} (原:{trans['fee']}) | time={transaction_data['time']}")
                
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
            
            # 7. 上传更新（带重试机制）
            log_print(f"[{browser_id}] 步骤3: 上传更新到服务器...")
            upload_data = account_config
            
            success, result, error_msg = upload_account_config_with_retry(
                upload_data, 
                browser_id=browser_id, 
                timeout=15
            )
            
            if not success:
                log_print(f"[{browser_id}] ✗ 上传失败: {error_msg}")
                return False
            
            log_print(f"[{browser_id}] ✓ 数据上传成功")
            if result:
                log_print(f"[{browser_id}] 服务器响应: {result}")
            
            return True
            
        except Exception as e:
            log_print(f"[{browser_id}] ✗ 上传数据失败: {str(e)}")
            import traceback
            log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
            
            # 如果还有重试机会，等待后重试
            if attempt < max_retries:
                log_print(f"[{browser_id}] ⏳ 等待 {retry_interval} 秒后进行第 {attempt + 1} 次重试...")
                time.sleep(retry_interval)
                continue
            else:
                # 所有重试都失败，返回False
                log_print(f"[{browser_id}] ✗ 已达到最大重试次数（{max_retries}次），上传失败")
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
        
        # 在 trade-box 中查找 tabs content div
        log_print(f"[{browser_id}] 查找 tabs content div...")
        tabs_content_divs = trade_box.find_elements(By.CSS_SELECTOR, 
            'div[data-scope="tabs"][data-part="content"][data-state="open"]')
        
        if not tabs_content_divs:
            log_print(f"[{browser_id}] ⚠ 未找到 tabs content div")
            return False, None
        
        tabs_content = tabs_content_divs[0]
        log_print(f"[{browser_id}] ✓ 找到 tabs content div")
        
        # 在 tabs content div 中查找前两个 BuySell 按钮
        buttons = tabs_content.find_elements(By.CSS_SELECTOR, 
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
                            refresh_page_with_opinion_check(driver, browser_id)
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
            refresh_page_with_opinion_check(driver, browser_id)
            time.sleep(2)
        
        # 执行数据收集流程（带重试机制）
        max_retries = 2
        button_prefix = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                log_print(f"[{browser_id}] ⚠ 第 {attempt} 次重试，重新加载页面...")
                refresh_page_with_opinion_check(driver, browser_id)
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
        
        # 紧急清理：确保浏览器标记和任务计数被正确更新（双重保险）
        try:
            # 清除浏览器标记
            with active_type3_browsers_lock:
                if browser_id in active_type3_browsers:
                    old_mid = active_type3_browsers.pop(browser_id, None)
                    log_print(f"[{browser_id}] [紧急清理] 已清除浏览器标记（任务ID: {old_mid}）")
            
            # 更新任务完成计数
            with active_tasks_lock:
                if mission_id and mission_id in active_tasks:
                    if active_tasks[mission_id]['completed'] < active_tasks[mission_id]['total']:
                        active_tasks[mission_id]['completed'] += 1
                        log_print(f"[{browser_id}] [紧急清理] 已更新任务 {mission_id} 计数 (completed: {active_tasks[mission_id]['completed']}/{active_tasks[mission_id]['total']})")
        except Exception as cleanup_err:
            log_print(f"[{browser_id}] [紧急清理] 清理失败: {str(cleanup_err)}")


# ============================================================================
# Type 2 任务处理函数
# ============================================================================

def collect_position_data(driver, browser_id, exchange_name, tp3, available_balance=None, tp5=None):
    """
    收集持仓和订单数据（可在 type=1 任务后调用）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器编号
        exchange_name: 交易所名称
        tp3: 任务参数
        available_balance: 可用余额（可选）
        tp5: 挂单超过XX小时撤单（可选）
        
    Returns:
        tuple: (success, collected_data)
    """
    collected_data = {}
    
    # 初始化 current_ip，从 LAST_PROXY_CONFIG 获取
    current_ip = None
    last_config = LAST_PROXY_CONFIG.get(str(browser_id))
    if last_config:
        current_ip = last_config.get("ip")
        if current_ip:
            log_print(f"[{browser_id}] ✓ 从 LAST_PROXY_CONFIG 获取到IP: {current_ip}")
        else:
            log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中的IP为空")
    else:
        log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中没有该浏览器的配置")
    
    try:
        log_print(f"\n[{browser_id}] ========== 额外收集持仓数据 ==========")
        
        # 判断交易所
        if exchange_name.upper() == "OP":
            log_print(f"[{browser_id}] 交易所为 OP，进入 profile 页面...")
            
            # 检查当前网址是否包含 "app.opinion.trade"
            current_url = driver.current_url
            if "app.opinion.trade" not in current_url:
                log_print(f"[{browser_id}] ⚠ 当前页面不是 app.opinion.trade ({current_url[:80]}...)，查找包含 app.opinion.trade 的标签页...")
                
                all_windows = driver.window_handles
                opinion_window = None
                
                # 查找包含 "app.opinion.trade" 的标签页
                for window_handle in all_windows:
                    try:
                        driver.switch_to.window(window_handle)
                        window_url = driver.current_url
                        if "app.opinion.trade" in window_url:
                            opinion_window = window_handle
                            log_print(f"[{browser_id}] ✓ 找到 app.opinion.trade 标签页: {window_url[:80]}...")
                            break
                    except Exception as e:
                        # 某些标签页可能无法访问URL（如chrome://等系统页面），跳过继续查找
                        continue
                
                if opinion_window:
                    # 切换到包含 "app.opinion.trade" 的标签页
                    driver.switch_to.window(opinion_window)
                    log_print(f"[{browser_id}] ✓ 已切换到 app.opinion.trade 标签页")
                else:
                    log_print(f"[{browser_id}] ⚠ 未找到包含 app.opinion.trade 的标签页，将在当前标签页打开")
            
            profile_url = "https://app.opinion.trade/profile"
            driver.get(profile_url)
            log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
            
            time.sleep(30)
            
            # 检查并连接钱包
            log_print(f"[{browser_id}] 检查并连接钱包...")
            connect_wallet_if_needed(driver, browser_id)
            
            
            try:
                # 使用WebDriverWait等待页面readyState为complete
                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(5)
                current_url = driver.current_url
                if 'profile' not in current_url:
                    connected = connect_wallet_if_needed(driver, browser_id)
                    time.sleep(2)
                    driver.get(profile_url)
                else:
                    log_print(f"[{browser_id}] ✓ 页面加载完成")
            except TimeoutException:
                            log_print(f"[{browser_id}] ⚠ 页面加载超时，继续检查...")
                            
            # 获取数据（带重试机制）
            max_data_collection_retries = 3
            retry_attempt = 0
            position_data = []
            open_orders_data = []
            transactions_data = []
            
            while retry_attempt < max_data_collection_retries:
                  # 判断当前页面是否是 profile_url，如果不是则打开
                current_url = driver.current_url
                if current_url == profile_url:
                    log_print(f"[{browser_id}] ✓ 当前页面已经是 profile 页面，跳过打开步骤")
                else:
                    try:
                        time.sleep(15)
                        driver.get(profile_url)
                        log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
                        
                        # 等待页面加载完成
                        log_print(f"[{browser_id}] 等待页面加载完成...")
                        try:
                            # 使用WebDriverWait等待页面readyState为complete
                            WebDriverWait(driver, 30).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                            log_print(f"[{browser_id}] ✓ 页面加载完成")
                        except TimeoutException:
                            log_print(f"[{browser_id}] ⚠ 页面加载超时，继续检查...")
                        
                        # 额外等待2秒确保DOM完全渲染
                        time.sleep(2)
                    except WebDriverException as e:
                        error_msg = str(e)
                        log_print(f"[{browser_id}] ✗ 检测到代理连接错误: {error_msg}")
                        
                try:
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤6.5: 获取 Balance Spot 地址...")
                    balance_spot_address, address_success = get_balance_spot_address(driver, browser_id)
                    if address_success:
                        collected_data['balance_spot_address'] = balance_spot_address
                        log_print(f"[{browser_id}] ✓ Balance Spot 地址已保存: {balance_spot_address}")
                    else:
                        log_print(f"[{browser_id}] ⚠ Balance Spot 地址获取失败，继续执行后续步骤")
                        connect_wallet_if_needed(driver, browser_id)
                        time.sleep(20)
                        current_url = driver.current_url
                        if current_url == profile_url:
                            log_print(f"[{browser_id}] ✓ 当前页面已经是 profile 页面，跳过打开步骤")
                        else:
                            try:
                                driver.get(profile_url)
                                log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
                            except WebDriverException as e:
                                error_msg = str(e)
                                log_print(f"[{browser_id}] ✗ 检测到代理连接错误: {error_msg}")
                        
                        
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}获取 Portfolio 值...")
                    portfolio_value, need_retry_portfolio = get_opinion_portfolio_value(driver, browser_id)
                    collected_data['portfolio'] = portfolio_value
                    
                    if need_retry_portfolio:
                        log_print(f"[{browser_id}] ⚠ Portfolio 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Portfolio 数据获取失败，不提交数据")
                            return False, ""
                    
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}获取 Balance 值...")
                    balance_value, need_retry_balance = get_opinion_balance_value(driver, browser_id)
                    collected_data['balance'] = balance_value
                    
                    if need_retry_balance:
                        log_print(f"[{browser_id}] ⚠ Balance 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Balance 数据获取失败，不提交数据")
                            return False, ""
                    if tp3 != "1":
                        log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}获取 Balance Spot 地址...")
                        balance_spot_address, address_success = get_balance_spot_address(driver, browser_id)
                        if address_success:
                            collected_data['balance_spot_address'] = balance_spot_address
                            log_print(f"[{browser_id}] ✓ Balance Spot 地址已保存: {balance_spot_address}")
                        else:
                            log_print(f"[{browser_id}] ⚠ Balance Spot 地址获取失败，继续执行后续步骤")
                        
                        log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}点击 Position 并获取数据...")
                        position_data, need_retry_position, task_failed = click_opinion_position_and_get_data(driver, browser_id)
                        
                        # 如果任务失败，不提交数据
                        if task_failed:
                            log_print(f"[{browser_id}] ✗ Position 数据获取任务失败，不提交数据")
                            return False, ""
                        
                        collected_data['position'] = position_data
                        
                        if need_retry_position:
                            log_print(f"[{browser_id}] ⚠ Position 数据获取超时，需要刷新页面重试")
                            retry_attempt += 1
                            if retry_attempt < max_data_collection_retries:
                                log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                                driver.get(profile_url)
                                time.sleep(15)
                                # 判断当前页面的网址是否还包含 'profile'
                                current_url = driver.current_url
                                if 'profile' not in current_url:
                                    log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                    connect_wallet_if_needed(driver, browser_id)
                                else:
                                    log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                                time.sleep(2)
                                continue
                            else:
                                log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Position 数据获取失败")
                                return False,""
                    
                    # 如果 tp5 有值，先执行超时撤单检查
                    if tp5:
                        log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}执行超时撤单检查 (tp5={tp5}小时)...")
                        cancel_expired_open_orders(driver, browser_id, tp5, current_ip)
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}点击 Open Orders 并获取数据...")
                    open_orders_data, need_retry_orders = click_opinion_open_orders_and_get_data(driver, browser_id)
                    
                    
                    if need_retry_orders:
                        log_print(f"[{browser_id}] ⚠ Open Orders 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Open Orders 数据获取失败，不提交数据")
                            return False, ""
                    
                    
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤8.5: 点击 Closed Orders 并获取数据...")
                    closed_orders_data, need_retry_closed_orders = click_opinion_closed_orders_and_get_data(driver, browser_id)
                    
                    if need_retry_closed_orders:
                        log_print(f"[{browser_id}] ⚠ Closed Orders 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Closed Orders 数据获取失败，不提交数据")
                            return False, ""
                    
                    # 上传 Closed Orders 数据
                    if closed_orders_data:
                        log_print(f"[{browser_id}] 步骤8.6: 上传 Closed Orders 数据...")
                        # 确保 current_ip 不为 None，如果为 None 则尝试从 LAST_PROXY_CONFIG 获取
                        upload_ip = current_ip
                        if upload_ip is None:
                            log_print(f"[{browser_id}] ⚠ current_ip 为 None，尝试从 LAST_PROXY_CONFIG 获取...")
                            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
                            if last_config:
                                upload_ip = last_config.get("ip")
                                if upload_ip:
                                    log_print(f"[{browser_id}] ✓ 从 LAST_PROXY_CONFIG 获取到IP: {upload_ip}")
                                    # 更新 current_ip 以便后续使用
                                    current_ip = upload_ip
                                else:
                                    log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中的IP也为空")
                            else:
                                log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中没有该浏览器的配置")
                        
                        upload_success = upload_closed_orders_data(browser_id, closed_orders_data, upload_ip)
                        if upload_success:
                            log_print(f"[{browser_id}] ✓ Closed Orders 数据上传完成")
                        else:
                            log_print(f"[{browser_id}] ⚠ Closed Orders 数据上传失败，但继续执行后续步骤")
                    else:
                        log_print(f"[{browser_id}] Closed Orders 数据为空，跳过上传")
                        
                    
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}点击 Transactions 并获取数据...")
                    transactions_data, need_retry_transactions = click_opinion_transactions_and_get_data(driver, browser_id)
                    
                    
                    if need_retry_transactions:
                        log_print(f"[{browser_id}] ⚠ Transactions 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Transactions 数据获取失败，不提交数据")
                            return False, ""
                    
                    if tp3 != "1":
                        # 获取 Points History 数据（仅在周一）
                        current_weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
                        if current_weekday == 0:  # 周一
                            log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}今天是周一，获取 Points History 数据...")
                            points_history_data = get_points_history_data(driver, browser_id)
                            if points_history_data:
                                collected_data['k'] = points_history_data
                                log_print(f"[{browser_id}] ✓ Points History 数据已保存: {points_history_data[:100]}...")
                            else:
                                log_print(f"[{browser_id}] ⚠ Points History 数据获取失败或为空，继续执行后续步骤")
                        else:
                            log_print(f"[{browser_id}] 今天不是周一（当前是周{'一二三四五六日'[current_weekday]}），跳过 Points History 数据获取")
                    
                    # 全部成功，跳出重试循环
                    log_print(f"[{browser_id}] ✓ 所有数据获取成功")
                    
                    # 检查传入的可用余额是否有效
                    if available_balance is None or available_balance == "" or available_balance == 0 or str(available_balance).strip() == "":
                        log_print(f"[{browser_id}] ⚠ 传入的可用余额无效（{available_balance}），将尝试获取可用余额...")
                        
                        # 只对 OP 交易所执行获取可用余额的逻辑
                        if exchange_name.upper() == "OP":
                            try:
                                # 前往指定页面（随机选择一个）
                                target_urls = [
                                    "https://app.opinion.trade/detail?topicId=213&type=multi",
                                    "https://app.opinion.trade/detail?topicId=79&type=multi",
                                    "https://app.opinion.trade/detail?topicId=210&type=multi",
                           
                                ]
                                target_url = random.choice(target_urls)
                                log_print(f"[{browser_id}] 前往页面获取可用余额: {target_url}")
                                driver.get(target_url)
                                time.sleep(3)
                                
                                # 在30s内获取 trade_box_divs
                                start_time = time.time()
                                max_wait_time = 30
                                check_interval = 0.5
                                fetched_available_balance = None
                                
                                while time.time() - start_time < max_wait_time:
                                    try:
                                        # 查找 trade_box_divs
                                        trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                                        if not trade_box_divs:
                                            log_print(f"[{browser_id}] ⚠ 未找到 trade-box div，等待后重试...")
                                            time.sleep(check_interval)
                                            continue
                                        
                                        current_trade_box = trade_box_divs[0]
                                        
                                        # 点击 Buy 按钮以确保显示正确的 tabs_content
                                        if not click_opinion_trade_type_button(current_trade_box, "Buy", browser_id):
                                            log_print(f"[{browser_id}] ⚠ 点击 Buy 按钮失败，等待后重试...")
                                            time.sleep(check_interval)
                                            continue
                                        
                                        # 重新获取 trade_box（点击后可能需要重新获取）
                                        trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                                        if not trade_box_divs:
                                            log_print(f"[{browser_id}] ⚠ 未找到 trade-box div，等待后重试...")
                                            time.sleep(check_interval)
                                            continue
                                        
                                        current_trade_box = trade_box_divs[0]
                                        
                                        # 查找 tabs content div
                                        tabs_content_divs = current_trade_box.find_elements(By.CSS_SELECTOR, 
                                            'div[data-scope="tabs"][data-part="content"][data-state="open"]')
                                        
                                        if not tabs_content_divs:
                                            log_print(f"[{browser_id}] ⚠ 未找到 tabs content div，等待后重试...")
                                            time.sleep(check_interval)
                                            continue
                                        
                                        tabs_content = tabs_content_divs[0]
                                        
                                        # 获取当前可用余额
                                        fetched_available_balance = get_available_balance_from_tabs_content(tabs_content, browser_id)
                                        
                                        if fetched_available_balance is not None:
                                            available_balance = fetched_available_balance
                                            log_print(f"[{browser_id}] ✓ 可用余额已获取: {available_balance}")
                                            break
                                        else:
                                            log_print(f"[{browser_id}] ⚠ 无法获取可用余额，等待后重试...")
                                            time.sleep(check_interval)
                                            continue
                                        
                                    except Exception as e:
                                        log_print(f"[{browser_id}] ⚠ 获取可用余额时发生异常: {str(e)}")
                                        time.sleep(check_interval)
                                        continue
                                
                                if fetched_available_balance is None:
                                    log_print(f"[{browser_id}] ⚠ 30秒内未能获取到可用余额，将使用 None 继续执行")
                                else:
                                    log_print(f"[{browser_id}] ✓ 可用余额获取完成: {available_balance}")
                                    
                            except Exception as e:
                                log_print(f"[{browser_id}] ✗ 获取可用余额执行异常: {str(e)}")
                                import traceback
                                log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
                                log_print(f"[{browser_id}] ⚠ 继续执行后续步骤，使用 None 作为可用余额")
                        else:
                            log_print(f"[{browser_id}] ⚠ 交易所 {exchange_name} 暂不支持自动获取可用余额")
                    else:
                        log_print(f"[{browser_id}] ✓ 使用传入的可用余额: {available_balance}")
                    
                    break
                    
                except Exception as e:
                    log_print(f"[{browser_id}] ✗ 数据获取异常: {str(e)}")
                    retry_attempt += 1
                    if retry_attempt < max_data_collection_retries:
                        log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                        driver.get(profile_url)
                        time.sleep(15)
                        # 判断当前页面的网址是否还包含 'profile'
                        current_url = driver.current_url
                        if 'profile' not in current_url:
                            log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                            connect_wallet_if_needed(driver, browser_id)
                        else:
                            log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                        time.sleep(2)
                    else:
                        log_print(f"[{browser_id}] ✗ 已达到最大重试次数")
                        break
            
            # 处理数据为标准格式
            log_print(f"[{browser_id}] 处理数据为标准格式...")
            processed_positions = process_op_position_data(position_data)
            
            # open_orders_data 已经是标准格式字符串，不需要再处理
            collected_data['positions'] = processed_positions
            collected_data['open_orders'] = open_orders_data
            collected_data['transactions'] = transactions_data
            
            # 打印收集到的数据
            log_print(f"\n[{browser_id}] ========== 收集到的数据 (OP) ==========")
            log_print(f"[{browser_id}] Portfolio: {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Balance: {collected_data.get('balance', 'N/A')}")
            log_print(f"[{browser_id}] Position 数据 ({len(processed_positions)} 项):")
            for i, item in enumerate(processed_positions, 1):
                log_print(f"[{browser_id}]   {i}. {item}")
            log_print(f"[{browser_id}] Open Orders 数据 (标准格式):")
            if open_orders_data:
                # 按分号分割显示每个仓位
                orders = open_orders_data.split(';')
                for i, order in enumerate(orders, 1):
                    log_print(f"[{browser_id}]   {i}. {order}")
            else:
                log_print(f"[{browser_id}]   无数据")
            # 如果是周一，显示 Points History 数据
            current_weekday = datetime.now().weekday()
            if current_weekday == 0 and 'k' in collected_data:
                log_print(f"[{browser_id}] Points History 数据: {collected_data.get('k', 'N/A')[:100]}...")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 上传数据
            log_print(f"[{browser_id}] 上传数据到服务器...")
            upload_success = upload_type2_data(browser_id, collected_data, 'OP', available_balance)
            
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
            upload_success = upload_type2_data(browser_id, collected_data, 'Ploy', available_balance)
            
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
    mission_type = mission.get("type", 2)  # 默认为 Type 2
    
    log_print(f"\n[{browser_id}] ========== 开始处理 Type {mission_type} 任务 {'(重试第' + str(retry_count) + '次)' if retry_count > 0 else ''} ==========")
    log_print(f"[{browser_id}] 任务ID: {mission_id}")
    log_print(f"[{browser_id}] 交易所: {exchange_name}")
    
    driver = None
    collected_data = {}
    
    try:
        # 1. 检查IP并更新代理（仅在第一次进入时更新，重试时跳过因为已经在重试流程中更新过了）
        current_ip = None
        current_delay = None
        if retry_count == 0:
            log_print(f"[{browser_id}] 步骤1: 检查IP并更新代理...")
            _, current_ip, current_delay = try_update_ip_before_start(browser_id, mission_id=mission_id)
        else:
            log_print(f"[{browser_id}] 步骤1: 跳过IP更新（重试中，IP已在重试流程中更新）...")
            # 从 LAST_PROXY_CONFIG 获取当前使用的IP和延迟
            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
            if last_config:
                current_ip = last_config.get("ip")
                current_delay = last_config.get("delay")
                log_print(f"[{browser_id}] 使用已更新的代理配置: IP={current_ip}, Delay={current_delay}")
            else:
                log_print(f"[{browser_id}] ⚠ 无法从 LAST_PROXY_CONFIG 获取IP信息，尝试更新...")
                _, current_ip, current_delay = try_update_ip_before_start(browser_id, mission_id=mission_id)
        
        # 确保 current_ip 和 current_delay 已初始化（用于后续代码使用）
        if current_ip is None:
            log_print(f"[{browser_id}] ⚠ current_ip 为 None，尝试从 LAST_PROXY_CONFIG 获取...")
            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
            if last_config:
                current_ip = last_config.get("ip")
                current_delay = last_config.get("delay")
        
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
            try:
                driver.get(profile_url)
                log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
            except WebDriverException as e:
                    error_msg = str(e)
                # 检查是否是代理连接错误
                    log_print(f"[{browser_id}] ✗ 检测到代理连接错误: {error_msg}")
                    # 如果是代理错误且重试次数小于2，执行换IP重试
                    if retry_count < 2:
                        log_print(f"[{browser_id}] Type=2 任务检测到代理连接失败，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                        
                        # 1. 关闭浏览器
                        log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        close_adspower_browser(browser_id)
                        time.sleep(15)
                        
                        # 2. 根据重试次数获取IP
                        log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                        proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                        
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
                        time.sleep(10)
                        
                        # 4. 递归重试任务（retry_count+1）
                        log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                        return process_type2_mission(task_data, retry_count=retry_count+1)
                    else:
                        log_print(f"[{browser_id}] ✗ 已经重试过2次，不再重试")
                        return False, "代理连接失败且已重试2次", collected_data
            
            time.sleep(2)
            
            # 4.0.4 检查并点击 "I Understand and Agree" p标签（如果存在）
            log_print(f"[{browser_id}] 步骤4.0.4: 检查是否存在 'I Understand and Agree' p标签...")
            if check_and_click_understand_agree(driver, browser_id, timeout=5):
                # 如果存在并点击了，需要换IP重试（重试次数小于2）
                if retry_count < 2:
                    log_print(f"[{browser_id}] Type=2 任务检测到 'I Understand and Agree'，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                    
                    # 调用 changeIpToErr 接口（确保 current_ip 不为 None）
                    ip_to_report = current_ip
                    if not ip_to_report:
                        last_config = LAST_PROXY_CONFIG.get(str(browser_id))
                        if last_config:
                            ip_to_report = last_config.get("ip")
                    call_change_ip_to_err(browser_id, ip_to_report)
                    
                    # 1. 关闭浏览器
                    log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                    try:
                        if driver:
                            driver.quit()
                    except:
                        pass
                    close_adspower_browser(browser_id)
                    log_print(f"[{browser_id}] Type=2 任务换IP：关闭浏览器后等待2分钟...")
                    time.sleep(120)  # Type=2任务等待2分钟
                    
                    # 2. 根据重试次数获取IP
                    log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                    proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                    
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
                    time.sleep(10)
                    
                    # 4. 递归重试任务（retry_count+1）
                    log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                    return process_type2_mission(task_data, retry_count=retry_count+1)
                else:
                    log_print(f"[{browser_id}] ✗ 已经重试过2次，不再重试")
                    return False, "检测到 'I Understand and Agree' 且已重试2次", collected_data
            
            
          
            # 4.0.5 预打开OKX钱包
            log_print(f"[{browser_id}] 步骤4.0.5: 预打开OKX钱包...")
            main_window = preopen_okx_wallet(driver, browser_id, current_ip, current_delay)
            
            # 4.0.6 检查URL并验证Macro标签（仅当URL包含profile或macro时）
            log_print(f"[{browser_id}] 步骤4.0.6: 检查当前URL并验证Macro标签...")
            try:
                current_url = driver.current_url
                log_print(f"[{browser_id}] 当前URL: {current_url}")
                
                # 判断当前网址是否包含 profile 或 macro
                if "profile" in current_url.lower() or "macro" in current_url.lower():
                    log_print(f"[{browser_id}] ✓ URL包含profile或macro，开始验证页面...")
                    
                    # 等待页面加载完成
                    log_print(f"[{browser_id}] 等待页面加载完成...")
                    try:
                        # 使用WebDriverWait等待页面readyState为complete
                        WebDriverWait(driver, 30).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        log_print(f"[{browser_id}] ✓ 页面加载完成")
                    except TimeoutException:
                        log_print(f"[{browser_id}] ⚠ 页面加载超时，继续检查...")
                    
                    # 额外等待2秒确保DOM完全渲染
                    time.sleep(2)
                    
                    # 检查页面上是否有内容为 "Macro" 的 p 标签
                    log_print(f"[{browser_id}] 检查页面上是否存在内容为 'Macro' 的 p 标签...")
                    macro_p_found = False
                    try:
                        p_tags = driver.find_elements(By.TAG_NAME, "p")
                        for p in p_tags:
                            if p.text.strip() == "Macro":
                                macro_p_found = True
                                log_print(f"[{browser_id}] ✓ 找到内容为 'Macro' 的 p 标签")
                                break
                    except Exception as e:
                        log_print(f"[{browser_id}] ⚠ 查找 p 标签时出现异常: {str(e)}")
                    
                    # 如果没有找到 Macro 的 p 标签，执行换IP重试
                    if not macro_p_found:
                        log_print(f"[{browser_id}] ✗ 未找到内容为 'Macro' 的 p 标签，需要换IP重试")
                        
                        # 如果是代理错误且重试次数小于2，执行换IP重试
                        if retry_count < 2:
                            log_print(f"[{browser_id}] Type=2 任务检测到Macro标签缺失，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                            
                            # 1. 关闭浏览器
                            log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                            try:
                                if driver:
                                    driver.quit()
                            except:
                                pass
                            close_adspower_browser(browser_id)
                            time.sleep(15)
                            
                            # 2. 根据重试次数获取IP
                            log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                            proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                            
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
                            time.sleep(10)
                            
                            # 4. 递归重试任务（retry_count+1）
                            log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                            return process_type2_mission(task_data, retry_count=retry_count+1)
                        else:
                            log_print(f"[{browser_id}] ✗ 已经重试过2次，不再重试")
                            return False, "Macro标签缺失且已重试2次", collected_data
                    else:
                        log_print(f"[{browser_id}] ✓ Macro标签验证通过，继续执行后续步骤")
                else:
                    log_print(f"[{browser_id}] URL不包含profile或macro，跳过Macro标签验证")
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 检查URL和Macro标签时出现异常: {str(e)}，继续执行...")
            
            # 4.1 检查并连接钱包
            log_print(f"[{browser_id}] 步骤4.1: 检查并连接钱包...")
            connect_wallet_if_needed(driver, browser_id)
            
              # 6.1.2 检查地区限制
            log_print(f"[{browser_id}] 步骤6.1.2: 检查地区限制...")
            try:
                start_time = time.time()
                region_restricted = False
                while time.time() - start_time < 3:
                    try:
                        # 查找所有div元素
                        all_divs = driver.find_elements(By.TAG_NAME, "div")
                        for div in all_divs:
                            div_text = div.text
                            if "API is not available to persons located in the" in div_text:
                                region_restricted = True
                                log_print(f"[{browser_id}] ✗ 检测到地区限制提示: {div_text[:100]}...")
                                break
                        if region_restricted:
                            break
                        time.sleep(0.2)  # 短暂等待后重试
                    except Exception as e:
                        # 查找过程中出现异常，继续尝试
                        time.sleep(0.2)
                        continue
                
                if region_restricted:
                    log_print(f"[{browser_id}] ✗ IP通畅，但地区不符合")
                     # 调用 changeIpToErr 接口
                    call_change_ip_to_err(browser_id, current_ip)
                    # 如果存在并点击了，需要换IP重试（重试次数小于2）
                    if retry_count < 2:
                        log_print(f"[{browser_id}] Type=2 任务检测到 'API is not available to persons located in the'，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                        
                        # 1. 关闭浏览器
                        log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        close_adspower_browser(browser_id)
                        log_print(f"[{browser_id}] Type=2 任务换IP：关闭浏览器后等待2分钟...")
                        time.sleep(120)  # Type=2任务等待2分钟
                        
                        # 2. 根据重试次数获取IP
                        log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                        proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                        
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
                        time.sleep(10)
                        
                        # 4. 递归重试任务（retry_count+1）
                        log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                        return process_type2_mission(task_data, retry_count=retry_count+1)
                else:
                    log_print(f"[{browser_id}] ✓ 未检测到地区限制")
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 检查地区限制时出现异常: {str(e)}，继续执行...")
            
            
            
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
                    
                    # 检查是否已经重试过（重试次数小于2）
                    if retry_count < 2:
                        log_print(f"[{browser_id}] Type=2 任务需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                        
                        # 1. 关闭浏览器
                        log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        close_adspower_browser(browser_id)
                        time.sleep(2)
                        
                        # 2. 根据重试次数获取IP
                        log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                        proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                        
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
                        log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                        return process_type2_mission(task_data, retry_count=retry_count+1)
                    else:
                        log_print(f"[{browser_id}] ✗ 已经重试过2次，不再重试")
                        return False, "OKX Wallet连接失败且已重试2次", collected_data
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
                # 判断当前页面是否是 profile_url，如果不是则打开
                current_url = driver.current_url
                if current_url == profile_url:
                    log_print(f"[{browser_id}] ✓ 当前页面已经是 profile 页面，跳过打开步骤")
                else:
                    try:
                        time.sleep(15)
                        driver.get(profile_url)
                        log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
                        
                        # 等待页面加载完成
                        log_print(f"[{browser_id}] 等待页面加载完成...")
                        try:
                            # 使用WebDriverWait等待页面readyState为complete
                            WebDriverWait(driver, 30).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                            log_print(f"[{browser_id}] ✓ 页面加载完成")
                        except TimeoutException:
                            log_print(f"[{browser_id}] ⚠ 页面加载超时，继续检查...")
                        
                        # 额外等待2秒确保DOM完全渲染
                        time.sleep(2)
                    except WebDriverException as e:
                        error_msg = str(e)
                        log_print(f"[{browser_id}] ✗ 检测到代理连接错误: {error_msg}")
                    
                try:
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤6.5: 获取 Balance Spot 地址...")
                    balance_spot_address, address_success = get_balance_spot_address(driver, browser_id)
                    if address_success:
                        collected_data['balance_spot_address'] = balance_spot_address
                        log_print(f"[{browser_id}] ✓ Balance Spot 地址已保存: {balance_spot_address}")
                    else:
                        log_print(f"[{browser_id}] ⚠ Balance Spot 地址获取失败，继续执行后续步骤")
                        connect_wallet_if_needed(driver, browser_id)
                        time.sleep(20)
                        current_url = driver.current_url
                        if current_url == profile_url:
                            log_print(f"[{browser_id}] ✓ 当前页面已经是 profile 页面，跳过打开步骤")
                        else:
                            try:
                                driver.get(profile_url)
                                log_print(f"[{browser_id}] ✓ 已打开页面: {profile_url}")
                            except WebDriverException as e:
                                error_msg = str(e)
                                log_print(f"[{browser_id}] ✗ 检测到代理连接错误: {error_msg}")
                       
                        
                        
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤5: 获取 Portfolio 值...")
                    portfolio_value, need_retry_portfolio = get_opinion_portfolio_value(driver, browser_id)
                    collected_data['portfolio'] = portfolio_value
                    
                    if need_retry_portfolio:
                        log_print(f"[{browser_id}] ⚠ Portfolio 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
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
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Balance 数据获取失败")
                            break
                    
                   
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤7: 点击 Position 并获取数据...")
                    position_data, need_retry_position, task_failed = click_opinion_position_and_get_data(driver, browser_id)
                    
                    # 如果任务失败，不提交数据
                    if task_failed:
                        log_print(f"[{browser_id}] ✗ Position 数据获取任务失败，不提交数据")
                        return False, ""
                    
                    collected_data['position'] = position_data
                    
                    if need_retry_position:
                        log_print(f"[{browser_id}] ⚠ Position 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Position 数据获取失败")
                            return False,""
                    
                    # Type 4 任务特殊处理：在获取 Open Orders 数据之前，先执行取消订单操作
                    if mission_type == 4:
                        log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤7.5: Type 4 任务 - 执行取消订单操作...")
                        tp1 = mission.get('tp1')
                        tp5 = mission.get('tp5')
                         # 如果 tp5 有值，先执行超时撤单检查
                        if tp5:
                            log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}执行超时撤单检查 (tp5={tp5}小时)...")
                            cancel_expired_open_orders(driver, browser_id, tp5, current_ip)
                        elif tp1:
                            log_print(f"[{browser_id}] Type 4 任务 tp1 值: {tp1}")
                            cancel_success = cancel_opinion_open_orders_by_tp1(driver, browser_id, tp1)
                            if not cancel_success:
                                log_print(f"[{browser_id}] ⚠ Type 4 任务取消订单操作失败，继续执行后续步骤")
                        else:
                            log_print(f"[{browser_id}] ⚠ Type 4 任务未找到 tp1 值，跳过取消订单操作")
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤8: 点击 Open Orders 并获取数据...")
                    open_orders_data, need_retry_orders = click_opinion_open_orders_and_get_data(driver, browser_id)
                    
                    if need_retry_orders:
                        log_print(f"[{browser_id}] ⚠ Open Orders 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Open Orders 数据获取失败，不提交数据")
                            return False, ""
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤8.5: 点击 Closed Orders 并获取数据...")
                    closed_orders_data, need_retry_closed_orders = click_opinion_closed_orders_and_get_data(driver, browser_id)
                    
                    if need_retry_closed_orders:
                        log_print(f"[{browser_id}] ⚠ Closed Orders 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Closed Orders 数据获取失败，不提交数据")
                            return False, ""
                    
                    # 上传 Closed Orders 数据
                    if closed_orders_data:
                        log_print(f"[{browser_id}] 步骤8.6: 上传 Closed Orders 数据...")
                        # 确保 current_ip 不为 None，如果为 None 则尝试从 LAST_PROXY_CONFIG 获取
                        upload_ip = current_ip
                        if upload_ip is None:
                            log_print(f"[{browser_id}] ⚠ current_ip 为 None，尝试从 LAST_PROXY_CONFIG 获取...")
                            last_config = LAST_PROXY_CONFIG.get(str(browser_id))
                            if last_config:
                                upload_ip = last_config.get("ip")
                                if upload_ip:
                                    log_print(f"[{browser_id}] ✓ 从 LAST_PROXY_CONFIG 获取到IP: {upload_ip}")
                                    # 更新 current_ip 以便后续使用
                                    current_ip = upload_ip
                                else:
                                    log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中的IP也为空")
                            else:
                                log_print(f"[{browser_id}] ⚠ LAST_PROXY_CONFIG 中没有该浏览器的配置")
                        
                        upload_success = upload_closed_orders_data(browser_id, closed_orders_data, upload_ip)
                        if upload_success:
                            log_print(f"[{browser_id}] ✓ Closed Orders 数据上传完成")
                        else:
                            log_print(f"[{browser_id}] ⚠ Closed Orders 数据上传失败，但继续执行后续步骤")
                    else:
                        log_print(f"[{browser_id}] Closed Orders 数据为空，跳过上传")
                    
                    log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤9: 点击 Transactions 并获取数据...")
                    transactions_data, need_retry_transactions = click_opinion_transactions_and_get_data(driver, browser_id)
                    
                    if need_retry_transactions:
                        log_print(f"[{browser_id}] ⚠ Transactions 数据获取超时，需要刷新页面重试")
                        retry_attempt += 1
                        if retry_attempt < max_data_collection_retries:
                            log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                            driver.get(profile_url)
                            time.sleep(15)
                            # 判断当前页面的网址是否还包含 'profile'
                            current_url = driver.current_url
                            if 'profile' not in current_url:
                                log_print(f"[{browser_id}] 当前页面不包含 'profile'，执行连接钱包操作")
                                connect_wallet_if_needed(driver, browser_id)
                            else:
                                log_print(f"[{browser_id}] 当前页面仍包含 'profile'，跳过连接钱包操作")
                            time.sleep(2)
                            continue
                        else:
                            log_print(f"[{browser_id}] ✗ 已达到最大重试次数，Transactions 数据获取失败，不提交数据")
                            return False, ""
                    if mission_type == 2:
                        # 步骤10: 获取 Points History 数据
                        log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤10: 获取 Points History 数据...")
                        points_history_data = get_points_history_data(driver, browser_id)
                        if points_history_data:
                            collected_data['k'] = points_history_data
                            log_print(f"[{browser_id}] ✓ Points History 数据已保存: {points_history_data[:100]}...")
                        else:
                            log_print(f"[{browser_id}] ⚠ Points History 数据获取失败或为空，继续执行后续步骤")
                        
                        # 步骤11: 获取可用余额
                        log_print(f"[{browser_id}] {'第' + str(retry_attempt + 1) + '次尝试 ' if retry_attempt > 0 else ''}步骤11: 获取可用余额...")
                    try:
                            # 前往指定页面（随机选择一个）
                            target_urls = [
                                "https://app.opinion.trade/detail?topicId=213&type=multi",
                                "https://app.opinion.trade/detail?topicId=79&type=multi",
                                "https://app.opinion.trade/detail?topicId=210&type=multi",
                            ]
                            target_url = random.choice(target_urls)
                            log_print(f"[{browser_id}] 前往页面: {target_url}")
                            driver.get(target_url)
                            time.sleep(3)
                            
                            # 在30s内获取 trade_box_divs
                            start_time = time.time()
                            max_wait_time = 30
                            check_interval = 0.5
                            available_balance = None
                            
                            while time.time() - start_time < max_wait_time:
                                try:
                                    # 查找 trade_box_divs
                                    trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                                    if not trade_box_divs:
                                        log_print(f"[{browser_id}] ⚠ 未找到 trade-box div，等待后重试...")
                                        time.sleep(check_interval)
                                        continue
                                    
                                    current_trade_box = trade_box_divs[0]
                                    
                                    # 点击 Buy 按钮以确保显示正确的 tabs_content
                                    if not click_opinion_trade_type_button(current_trade_box, "Buy", browser_id):
                                        log_print(f"[{browser_id}] ⚠ 点击 Buy 按钮失败，等待后重试...")
                                        time.sleep(check_interval)
                                        continue
                                    
                                    # 重新获取 trade_box（点击后可能需要重新获取）
                                    trade_box_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                                    if not trade_box_divs:
                                        log_print(f"[{browser_id}] ⚠ 未找到 trade-box div，等待后重试...")
                                        time.sleep(check_interval)
                                        continue
                                    
                                    current_trade_box = trade_box_divs[0]
                                    
                                    # 查找 tabs content div
                                    tabs_content_divs = current_trade_box.find_elements(By.CSS_SELECTOR, 
                                        'div[data-scope="tabs"][data-part="content"][data-state="open"]')
                                    
                                    if not tabs_content_divs:
                                        log_print(f"[{browser_id}] ⚠ 未找到 tabs content div，等待后重试...")
                                        time.sleep(check_interval)
                                        continue
                                    
                                    tabs_content = tabs_content_divs[0]
                                    
                                    # 获取当前可用余额
                                    available_balance = get_available_balance_from_tabs_content(tabs_content, browser_id)
                                    
                                    if available_balance is not None:
                                        collected_data['p'] = available_balance
                                        log_print(f"[{browser_id}] ✓ 可用余额已获取并保存: {available_balance}")
                                        break
                                    else:
                                        log_print(f"[{browser_id}] ⚠ 无法获取可用余额，等待后重试...")
                                        time.sleep(check_interval)
                                        continue
                                    
                                except Exception as e:
                                    log_print(f"[{browser_id}] ⚠ 获取可用余额时发生异常: {str(e)}")
                                    time.sleep(check_interval)
                                    continue
                            
                            if available_balance is None:
                                log_print(f"[{browser_id}] ⚠ 30秒内未能获取到可用余额，继续执行后续步骤")
                            else:
                                log_print(f"[{browser_id}] ✓ 步骤11完成: 可用余额 = {available_balance}")
                                
                    except Exception as e:
                            log_print(f"[{browser_id}] ✗ 步骤11执行异常: {str(e)}")
                            import traceback
                            log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
                            log_print(f"[{browser_id}] ⚠ 继续执行后续步骤")
                    
                    
                    # 全部成功，跳出重试循环
                    log_print(f"[{browser_id}] ✓ 所有数据获取成功")
                    break
                    
                except Exception as e:
                    log_print(f"[{browser_id}] ✗ 数据获取异常: {str(e)}")
                    retry_attempt += 1
                    if retry_attempt < max_data_collection_retries:
                        log_print(f"[{browser_id}] 刷新页面进行第 {retry_attempt + 1} 次尝试...")
                        driver.get(profile_url)
                        time.sleep(15)
                        # refresh_page_with_opinion_check(driver, browser_id)
                        # time.sleep(5)
                        connect_wallet_if_needed(driver, browser_id)
                        time.sleep(2)
                    else:
                        log_print(f"[{browser_id}] ✗ 已达到最大重试次数")
                        break
            
            # 打印原始数据
            log_print(f"\n[{browser_id}] ========== 原始数据 ==========")
            log_print(f"[{browser_id}] Portfolio (原始): {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Balance (原始): {collected_data.get('balance', 'N/A')}")
            log_print(f"[{browser_id}] Position 原始数据 (标准格式字符串):")
            if position_data:
                # 按分号分割显示每个仓位
                positions = position_data.split(';')
                for i, pos in enumerate(positions, 1):
                    log_print(f"[{browser_id}]   {i}. {pos}")
            else:
                log_print(f"[{browser_id}]   (空)")
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
            
            # open_orders_data 已经是标准格式字符串，不需要再处理
            collected_data['positions'] = processed_positions
            collected_data['open_orders'] = open_orders_data
            collected_data['transactions'] = transactions_data
            
            # 打印收集到的数据
            log_print(f"\n[{browser_id}] ========== 收集到的数据 (OP) ==========")
            log_print(f"[{browser_id}] Portfolio: {collected_data.get('portfolio', 'N/A')}")
            log_print(f"[{browser_id}] Balance: {collected_data.get('balance', 'N/A')}")
            log_print(f"[{browser_id}] Position 数据 ({len(processed_positions)} 项):")
            for i, item in enumerate(processed_positions, 1):
                log_print(f"[{browser_id}]   {i}. {item}")
            log_print(f"[{browser_id}] Open Orders 数据 (标准格式):")
            if open_orders_data:
                # 按分号分割显示每个仓位
                orders = open_orders_data.split(';')
                for i, order in enumerate(orders, 1):
                    log_print(f"[{browser_id}]   {i}. {order}")
            else:
                log_print(f"[{browser_id}]   无数据")
            # 显示 Points History 数据
            if 'k' in collected_data:
                log_print(f"[{browser_id}] Points History 数据: {collected_data.get('k', 'N/A')[:100]}...")
            log_print(f"[{browser_id}] ==========================================\n")
            
            # 上传数据
            log_print(f"[{browser_id}] 步骤10: 上传数据到服务器...")
            # 从 collected_data 中获取可用余额（字段 p）
            available_balance = collected_data.get('p')
            upload_success = upload_type2_data(browser_id, collected_data, 'OP', available_balance)
            
            if upload_success:
                log_print(f"[{browser_id}] ✓ 数据上传成功")
            else:
                log_print(f"[{browser_id}] ⚠ 数据上传失败，但任务继续")
            
            log_print(f"[{browser_id}] ========== Type 2 任务完成 (OP) ==========\n")
            return True, "", collected_data
        
        elif exchange_name.upper() == "PLOY":
            log_print(f"[{browser_id}] 步骤4: 交易所为 Ploy，进入 Polymarket portfolio 页面...")
            
            portfolio_url = "https://polymarket.com/portfolio?tab=positions"
            try:
                driver.get(portfolio_url)
                log_print(f"[{browser_id}] ✓ 已打开页面: {portfolio_url}")
            except WebDriverException as e:
                    error_msg = str(e)
                # 检查是否是代理连接错误
                    log_print(f"[{browser_id}] ✗ 检测到代理连接错误: {error_msg}")
                    # 如果是代理错误且重试次数小于2，执行换IP重试
                    if retry_count < 2:
                        log_print(f"[{browser_id}] Type=2 任务检测到代理连接失败，需要换IP重试（第{retry_count+1}次），开始执行重试流程...")
                        
                        # 1. 关闭浏览器
                        log_print(f"[{browser_id}] 步骤1: 关闭浏览器...")
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        close_adspower_browser(browser_id)
                        time.sleep(15)
                        
                        # 2. 根据重试次数获取IP
                        log_print(f"[{browser_id}] 步骤2: 更换IP（第{retry_count+1}次）...")
                        proxy_config = get_ip_for_retry(browser_id, retry_count, timeout=15, mission_id=mission_id)
                        
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
                        time.sleep(10)
                        
                        # 4. 递归重试任务（retry_count+1）
                        log_print(f"[{browser_id}] 步骤4: 重新执行任务（重试次数: {retry_count+1}）...")
                        return process_type2_mission(task_data, retry_count=retry_count+1)
                    else:
                        log_print(f"[{browser_id}] ✗ 已经重试过2次，不再重试")
                        return False, "代理连接失败且已重试2次", collected_data
                
            
            time.sleep(2)
            
            # 4.0.5 预打开OKX钱包
            log_print(f"[{browser_id}] 步骤4.0.5: 预打开OKX钱包...")
            main_window = preopen_okx_wallet(driver, browser_id, current_ip, current_delay)
            
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
            # 从 collected_data 中获取可用余额（字段 p）
            available_balance = collected_data.get('p')
            upload_success = upload_type2_data(browser_id, collected_data, 'Ploy', available_balance)
            
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
        # Type 2 任务关闭浏览器后调用 removeNumberInUse 接口
        call_remove_number_in_use(browser_id, "Type 2 任务完成，")


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
        try:
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
            elif task_type == 5 or task_type == 1 or task_type == 6 or task_type == 9:
                # Type 1/5/6任务的结果已在单浏览器处理时直接上传，这里只做清理
                log_print(f"[系统] ✓ Type {task_type} 任务 {mission_id} 已完成（结果已直接上传）")
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
            with active_tasks_lock:
                if mission_id in active_tasks:
                    del active_tasks[mission_id]
                    log_print(f"[系统] 任务 {mission_id} 已从活动任务列表中移除")
        except Exception as e:
            log_print(f"[系统] ✗ 提交任务 {mission_id} 结果时发生异常: {str(e)}")
            import traceback
            log_print(f"[系统] 错误详情:\n{traceback.format_exc()}")
            # 即使发生异常，也要从活动任务列表中移除，避免重复处理
            with active_tasks_lock:
                if mission_id in active_tasks:
                    del active_tasks[mission_id]
                    log_print(f"[系统] 任务 {mission_id} 已从活动任务列表中移除（异常情况）")


def process_browser_waiting_queue(browser_id):
    """
    处理浏览器等待队列：当浏览器任务完成时，从等待队列中取出下一个任务执行
    
    Args:
        browser_id: 浏览器ID
    """
    with browser_waiting_queue_lock:
        if browser_id in browser_waiting_queue and browser_waiting_queue[browser_id]:
            # 取出队列中的第一个任务
            next_task_data = browser_waiting_queue[browser_id].pop(0)
            next_mission = next_task_data.get("mission", {})
            next_mission_id = next_mission.get("id")
            next_mission_type = next_mission.get("type")
            
            log_print(f"[{browser_id}] 从等待队列中取出任务 {next_mission_id} (type={next_mission_type})，准备执行")
            
            # 如果队列为空，删除该浏览器的队列
            if not browser_waiting_queue[browser_id]:
                del browser_waiting_queue[browser_id]
            
            # 提交下一个任务到线程池
            submit_mission_to_pool(next_task_data)
        else:
            # 队列为空，清除浏览器标记
            with active_browsers_lock:
                active_browsers.pop(browser_id, None)
                log_print(f"[{browser_id}] 等待队列为空，浏览器标记已清除")


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
    
    # 标记浏览器为繁忙（不区分任务类型）
    if browser_id:
        with active_browsers_lock:
            active_browsers[browser_id] = mission_id
            log_print(f"[{browser_id}] 任务 {mission_id} 开始执行，浏览器已标记为繁忙")
    
    try:
        # 先更新浏览器时间戳
        if browser_id:
            update_browser_timestamp(browser_id)
        
        # 根据任务类型执行
        if mission_type == 1 or mission_type == 5 or mission_type == 6 or mission_type == 9:
            # Type 1: 普通交易任务
            # Type 5: 自动对冲交易任务（带同步机制）
            result = process_trading_mission(task_data, keep_browser_open=True)
            
            if len(result) == 6:
                success, failure_reason, driver, task_browser_id, task_exchange_name, available_balance = result
            elif len(result) == 5:
                success, failure_reason, driver, task_browser_id, task_exchange_name = result
                available_balance = None
            else:
                success, failure_reason = result
                driver = None
                task_browser_id = None
                task_exchange_name = None
                available_balance = None
            
            # 立即上传任务结果（不等待数据收集）
            log_print(f"[{browser_id}] Type {mission_type} 任务{'成功' if success else '失败'}，立即上传结果... {failure_reason}")
            status = 2 if success else 3
            save_mission_result(mission_id, status, failure_reason or '')
            log_print(f"[{browser_id}] ✓ Type {mission_type} 任务结果已上传")
            
            # 记录任务结果到内存（用于统计，但不再用于最终提交）
            with active_tasks_lock:
                if mission_id in active_tasks:
                    active_tasks[mission_id]['results'][browser_id] = {
                        'success': success,
                        'reason': failure_reason,
                        'msg': failure_reason  # 保存完整的 msg（成功或失败都保存）
                    }
                    active_tasks[mission_id]['completed'] += 1
            log_print(f"[{browser_id}] ✓ Type {mission_type} 任务结果已记录到内存")
            
            # Type 5任务特殊处理：任务二失败时通知任务一
            if mission_type == 5:
                tp1 = mission.get('tp1')
                if tp1:
                    if not success:
                        update_mission_tp(tp1, tp9=3)
                        log_print(f"[{browser_id}] Type 5 任务二失败，设置任务一tp9为3...")
                    else:
                        update_mission_tp(tp1, tp9=2)
                        log_print(f"[{browser_id}] Type 5 任务二成功，设置任务一tp9为2...")
            
            # # Type 5任务完成后发送 fingerprint 监控请求
            # if mission_type == 5 and task_browser_id:
            #     log_print(f"[{browser_id}] Type 5 任务完成，发送 fingerprint 监控请求...")
            #     send_fingerprint_monitor_request(task_browser_id)
            
            # Type 1/5任务完成后收集持仓数据（不影响任务结果）
            if driver and task_browser_id and task_exchange_name:
                try:
                    log_print(f"[{browser_id}] 开始额外收集持仓数据（不影响任务结果）...")
                    tp3 = mission.get('tp3')
                    tp5 = mission.get('tp5')
                    collect_position_data(driver, task_browser_id, task_exchange_name, tp3, available_balance, tp5)
                    log_print(f"[{browser_id}] ✓ 额外持仓数据收集完成")
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 额外数据收集异常: {str(e)}，但不影响任务")
                finally:
                    log_print(f"[{browser_id}] 关闭浏览器...")
                    close_adspower_browser(task_browser_id)
                    # Type 5 任务关闭浏览器后调用 removeNumberInUse 接口
                    call_remove_number_in_use(task_browser_id, "Type 5 任务完成，")
            else:
                # 如果 driver 等为 None，说明任务失败，尝试关闭浏览器（可能已被关闭）
                if not success:
                    log_print(f"[{browser_id}] 任务失败且未返回driver，尝试关闭浏览器（兜底）...")
                    close_adspower_browser(browser_id)
                    call_remove_number_in_use(browser_id, "Type 5 任务完成，")
            # Type 1/5 任务结果已经在上面记录了，跳过后面的统一记录
            # 清除浏览器标记并处理等待队列
            if browser_id:
                process_browser_waiting_queue(browser_id)
            return
            
        elif mission_type == 2 or mission_type == 4:
            # Type 2: 数据获取任务
            # 初始化变量（放在最前面，确保即使前面发生异常也能访问）
            success = False
            failure_reason = "未执行"
            
            # Type 2 任务开始时调用 addNumberInUse
            try:
                log_print(f"[{browser_id}] Type {mission_type} 任务开始，调用 addNumberInUse 接口...")
                add_url = "https://sg.bicoin.com.cn/99l/hedge/addNumberInUse"
                add_resp = requests.post(add_url, json={"number": browser_id, "group": COMPUTER_GROUP}, timeout=10)
                log_print(f"[{browser_id}] addNumberInUse 响应: {add_resp.status_code}")
            except Exception as e:
                log_print(f"[{browser_id}] addNumberInUse 调用失败: {str(e)}")
            
            try:
                # 将浏览器ID和任务ID加入正在执行的映射
                with active_type2_browsers_lock:
                    active_type2_browsers[browser_id] = mission_id
                    log_print(f"[{browser_id}] Type {mission_type} 任务 {mission_id} 开始，浏览器已标记为繁忙")
                
                try:
                    success, failure_reason, collected_data = process_type2_mission(task_data)
                finally:
                    # 无论成功还是失败，都从映射中移除浏览器ID
                    with active_type2_browsers_lock:
                        active_type2_browsers.pop(browser_id, None)
                        
                        log_print(f"[{browser_id}] Type 2 任务 {mission_id} 完成，浏览器标记已清除")
            except Exception as e:
                # 如果 process_type2_mission 本身抛出异常，确保清除标记
                with active_type2_browsers_lock:
                    active_type2_browsers.pop(browser_id, None)
                    log_print(f"[{browser_id}] Type 2 任务 {mission_id} 异常，清除浏览器标记")
                raise
            
            # Type 2 任务完成后，清除全局浏览器标记并处理等待队列
            if browser_id:
                process_browser_waiting_queue(browser_id)
            
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
            # 清除浏览器标记并处理等待队列
            if browser_id:
                process_browser_waiting_queue(browser_id)
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
        
        # 如果是 type=2 任务发生异常，确保清除浏览器标记
        if mission_type == 2:
            with active_type2_browsers_lock:
                if browser_id in active_type2_browsers:
                    active_type2_browsers.pop(browser_id, None)
                    log_print(f"[{browser_id}] Type 2 任务 {mission_id} 异常，清除浏览器标记")
        
        # 如果是 type=3 任务发生异常，确保清除浏览器标记
        if mission_type == 3:
            with active_type3_browsers_lock:
                if browser_id in active_type3_browsers:
                    active_type3_browsers.pop(browser_id, None)
                    log_print(f"[{browser_id}] Type 3 任务 {mission_id} 异常，清除浏览器标记")
        
        # 清除全局浏览器标记并处理等待队列（异常情况下也要处理）
        if browser_id:
            process_browser_waiting_queue(browser_id)
        
        # 对于 Type 1/2/5 任务，尝试关闭浏览器（兜底保护，避免浏览器泄漏）
        if mission_type in [1, 2, 5]:
            log_print(f"[{browser_id}] Type {mission_type} 任务异常，尝试关闭浏览器（兜底）...")
            try:
                close_adspower_browser(browser_id)
            except Exception as close_error:
                log_print(f"[{browser_id}] 关闭浏览器时出错: {str(close_error)}")
        
        # 记录失败并确保更新计数（避免线程泄漏）
        with active_tasks_lock:
            if mission_id in active_tasks:
                # 检查是否已经更新过计数（避免重复计数）
                already_counted = browser_id in active_tasks[mission_id]['results']
                
                if not already_counted:
                    # 如果还没有记录过结果，记录失败并更新计数
                    active_tasks[mission_id]['results'][browser_id] = {
                        'success': False,
                        'reason': f"执行异常: {str(e)}"
                    }
                    active_tasks[mission_id]['completed'] += 1
                    log_print(f"[{browser_id}] ✓ 异常任务已标记为完成，避免线程泄漏")
                else:
                    # 如果已经记录过了，只打印日志
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
                
                # 检查浏览器是否正在执行任务（不区分任务类型）
                browser_is_busy = False
                with active_browsers_lock:
                    if browser_id in active_browsers:
                        old_mission_id = active_browsers[browser_id]
                        # 检查旧任务是否真的还在运行
                        with active_tasks_lock:
                            if old_mission_id in active_tasks:
                                # 旧任务还在运行，浏览器确实繁忙
                                browser_is_busy = True
                                log_print(f"[系统] 浏览器 {browser_id} 正在执行任务 {old_mission_id}，将任务 {mission_id} 加入等待队列")
                            else:
                                # 旧任务已完成但标记未清除（幽灵标记），自动清理
                                log_print(f"[系统] ⚠ 检测到幽灵标记：浏览器 {browser_id} 的旧任务 {old_mission_id} 已完成但标记未清除，自动清理")
                                active_browsers.pop(browser_id, None)
                                browser_is_busy = False
                
                if browser_is_busy:
                    # 将任务加入等待队列
                    with browser_waiting_queue_lock:
                        if browser_id not in browser_waiting_queue:
                            browser_waiting_queue[browser_id] = []
                        browser_waiting_queue[browser_id].append(task_data)
                        queue_length = len(browser_waiting_queue[browser_id])
                        log_print(f"[系统] ✓ 任务 {mission_id} 已加入浏览器 {browser_id} 的等待队列（队列长度: {queue_length}）")
                    continue  # 跳过后续处理，继续下一次循环
                
                # 如果是 type=2 任务，检查该浏览器是否已经在执行 type=2 任务
                if mission_type == 2:
                    browser_is_busy = False
                    with active_type2_browsers_lock:
                        if browser_id in active_type2_browsers:
                            old_mission_id = active_type2_browsers[browser_id]
                            # 检查旧任务是否真的还在运行
                            with active_tasks_lock:
                                if old_mission_id in active_tasks:
                                    # 旧任务还在运行，浏览器确实繁忙
                                    browser_is_busy = True
                                    log_print(f"[系统] 浏览器 {browser_id} 正在执行 Type=2 任务 {old_mission_id}")
                                else:
                                    # 旧任务已完成但标记未清除（幽灵标记），自动清理
                                    log_print(f"[系统] ⚠ 检测到幽灵标记：浏览器 {browser_id} 的旧任务 {old_mission_id} 已完成但标记未清除，自动清理")
                                    active_type2_browsers.pop(browser_id, None)
                                    browser_is_busy = False
                    
                    if browser_is_busy:
                        log_print(f"[系统] ⚠ 浏览器 {browser_id} 已有 Type=2 任务正在执行，跳过任务 {mission_id}")
                        # 提交失败结果
                        submit_mission_result(mission_id, 0, 1, {browser_id: "该浏览器已有Type=2任务正在执行"}, status=3)
                        log_print(f"[系统] ✓ Type=2 任务 {mission_id} 已标记为失败")
                        continue  # 跳过后续处理，继续下一次循环
                
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
    mapping_data = """3100	k15mek1c
3099	k15mek1b
3098	k15mek19
3097	k15mek18
3096	k15mek17
3095	k15mek16
3094	k15mek15
3093	k15mek14
3092	k15mek13
3091	k15mek12
3090	k15mek11
3089	k15mek10
3088	k15mek0x
3087	k15mek0w
3086	k15mek0v
3085	k15mek0u
3084	k15mek0t
3083	k15mek0s
3082	k15mek0r
3081	k15mek0q
3080	k15mek0p
3079	k15mek0o
3078	k15mek0m
3077	k15mek0l
3076	k15mek0k
3075	k15mek0j
3074	k15mek0i
3073	k15mek0h
3072	k15mek0g
3071	k15mek0f
3070	k15mek0e
3069	k15mek0d
3068	k15mek0c
3067	k15mek0b
3066	k15mek0a
3065	k15mek09
3064	k15mek08
3063	k15mek07
3062	k15mek06
3061	k15mek04
3060	k15mek03
3059	k15mek02
3058	k15mek00
3057	k15mejyy
3056	k15mejyx
3055	k15mejyv
3054	k15mejyu
3053	k15mejyt
3052	k15mejys
3051	k15mejyr
3050	k15mejyq
3049	k15mejyp
3048	k15mejyo
3047	k15mejyn
3046	k15mejym
3045	k15mejyl
3044	k15mejyk
3043	k15mejyj
3042	k15mejyi
3041	k15mejyh
3040	k15mejyg
3039	k15mejyf
3038	k15mejye
3037	k15mejyd
3036	k15mejyc
3035	k15mejyb
3034	k15mejya
3033	k15mejy9
3032	k15mejy8
3031	k15mejy7
3030	k15mejy6
3029	k15mejy5
3028	k15mejy3
3027	k15mejy0
3026	k15mejxx
3025	k15mejxw
3024	k15mejxv
3023	k15mejxt
3022	k15mejxs
3021	k15mejxr
3020	k15mejxq
3019	k15mejxp
3018	k15mejxo
3017	k15mejxn
3016	k15mejxl
3015	k15mejxk
3014	k15mejxi
3013	k15mejxh
3012	k15mejxg
3011	k15mejxf
3010	k15mejxe
3009	k15mejxd
3008	k15mejxc
3007	k15mejxb
3006	k15mejxa
3005	k15mejx9
3004	k15mejx8
3003	k15mejx7
3002	k15mejx6
3001	k15mejx5
3000	k15mejx4
2999	k15mejx3
2998	k15mejx2
2997	k15mejx1
2996	k15mejx0
2995	k15mejwy
2994	k15mejwx
2993	k15mejww
2992	k15mejwv
2991	k15mejwu
2990	k15mejwt
2989	k15mejws
2988	k15mejwr
2987	k15mejwq
2986	k15mejwp
2985	k15mejwo
2984	k15mejwn
2983	k15mejwm
2982	k15mejwl
2981	k15mejwk
2980	k15mejwj
2979	k15mejwi
2978	k15mejwh
2977	k15mejwg
2976	k15mejwf
2975	k15mejwe
2974	k15mejwd
2973	k15mejwc
2972	k15mejwb
2971	k15mejwa
2970	k15mejw9
2969	k15mejw8
2968	k15mejw7
2967	k15mejw6
2966	k15mejw5
2965	k15mejw4
2964	k15mejw3
2963	k15mejw1
2962	k15mejvy
2961	k15mejvx
2960	k15mejvv
2959	k15mejvu
2958	k15mejvt
2957	k15mejvs
2956	k15mejvr
2955	k15mejvq
2954	k15mejvp
2953	k15mejvo
2952	k15mejvm
2951	k15mejvl
2950	k15mejvk
2949	k15mejvj
2948	k15mejvh
2947	k15mejvg
2946	k15mejvf
2945	k15mejve
2944	k15mejvd
2943	k15mejvb
2942	k15mejva
2941	k15mejv9
2940	k15mejv8
2939	k15mejv7
2938	k15mejv6
2937	k15mejv5
2936	k15mejv3
2935	k15mejv2
2934	k15mejv1
2933	k15mejv0
2932	k15mejuy
2931	k15mejux
2930	k15mejuw
2929	k15mejuv
2928	k15mejuu
2927	k15mejut
2926	k15mejus
2925	k15mejur
2924	k15mejuq
2923	k15mejup
2922	k15mejuo
2921	k15mejum
2920	k15mejul
2919	k15mejuk
2918	k15mejuj
2917	k15mejui
2916	k15mejuh
2915	k15mejug
2914	k15mejuf
2913	k15mejue
2912	k15mejud
2911	k15mejuc
2910	k15mejub
2909	k15mejua
2908	k15meju9
2907	k15meju6
2906	k15meju5
2905	k15meju4
2904	k15meju2
2903	k15meju0
2902	k15mejtx
2901	k15mejtv
2900	k15mejtu
2899	k15mejts
2898	k15mejtr
2897	k15mejtq
2896	k15mejtp
2895	k15mejto
2894	k15mejtn
2893	k15mejtm
2892	k15mejtl
2891	k15mejtk
2890	k15mejtj
2889	k15mejti
2888	k15mejth
2887	k15mejtf
2886	k15mejte
2885	k15mejtd
2884	k15mejtc
2883	k15mejta
2882	k15mejt9
2881	k15mejt8
2880	k15mejt7
2879	k15mejt6
2878	k15mejt5
2877	k15mejt2
2876	k15mejt0
2875	k15mejsy
2874	k15mejsx
2873	k15mejsv
2872	k15mejsu
2871	k15mejss
2870	k15mejsr
2869	k15mejsq
2868	k15mejsp
2867	k15mejso
2866	k15mejsn
2865	k15mejsl
2864	k15mejsk
2863	k15mejsj
2862	k15mejsi
2861	k15mejsh
2860	k15mejsg
2859	k15mejsf
2858	k15mejse
2857	k15mejsd
2856	k15mejsc
2855	k15mejsb
2854	k15mejsa
2853	k15mejs9
2852	k15mejs7
2851	k15mejs6
2850	k15mejs4
2849	k15mejs3
2848	k15mejs2
2847	k15mejs1
2846	k15mejs0
2845	k15mejry
2844	k15mejrx
2843	k15mejru
2842	k15mejrs
2841	k15mejrp
2840	k15mejro
2839	k15mejrn
2838	k15mejrm
2837	k15mejrl
2836	k15mejrk
2835	k15mejrj
2834	k15mejri
2833	k15mejrh
2832	k15mejrg
2831	k15mejrf
2830	k15mejre
2829	k15mejrd
2828	k15mejrb
2827	k15mejra
2826	k15mejr9
2825	k15mejr8
2824	k15mejr7
2823	k15mejr6
2822	k15mejr4
2821	k15mejr2
2820	k15mejr1
2819	k15mejr0
2818	k15mejqy
2817	k15mejqx
2816	k15mejqv
2815	k15mejqt
2814	k15mejqs
2813	k15mejqr
2812	k15mejqq
2811	k15mejqp
2810	k15mejqn
2809	k15mejqm
2808	k15mejql
2807	k15mejqk
2806	k15mejqj
2805	k15mejqi
2804	k15mejqh
2803	k15mejqg
2802	k15mejqf
2801	k15mejqd
2800	k15mejqc
2799	k15mejqb
2798	k15mejqa
2797	k15mejq9
2796	k15mejq7
2795	k15mejq6
2794	k15mejq5
2793	k15mejq4
2792	k15mejq3
2791	k15mejq2
2790	k15mejq1
2789	k15mejq0
2788	k15mejpy
2787	k15mejpx
2786	k15mejpw
2785	k15mejpv
2784	k15mejpu
2783	k15mejpt
2782	k15mejps
2781	k15mejpr
2780	k15mejpq
2779	k15mejpo
2778	k15mejpn
2777	k15mejpm
2776	k15mejpl
2775	k15mejpj
2774	k15mejph
2773	k15mejpg
2772	k15mejpf
2771	k15mejpd
2770	k15mejpc
2769	k15mejpb
2768	k15mejpa
2767	k15mejp9
2766	k15mejp8
2765	k15mejp6
2764	k15mejp5
2763	k15mejp4
2762	k15mejp3
2761	k15mejp2
2760	k15mejp1
2759	k15mejp0
2758	k15mejoy
2757	k15mejox
2756	k15mejow
2755	k15mejov
2754	k15mejou
2753	k15mejos
2752	k15mejor
2751	k15mejoq
2750	k15mejoo
2749	k15mejon
2748	k15mejom
2747	k15mejol
2746	k15mejok
2745	k15mejoj
2744	k15mejoh
2743	k15mejof
2742	k15mejoe
2741	k15mejod
2740	k15mejoc
2739	k15mejob
2738	k15mejoa
2737	k15mejo9
2736	k15mejo6
2735	k15mejo5
2734	k15mejo3
2733	k15mejo2
2732	k15mejo1
2731	k15mejny
2730	k15mejnw
2729	k15mejnv
2728	k15mejnu
2727	k15mejnt
2726	k15mejns
2725	k15mejnr
2724	k15mejno
2723	k15mejnn
2722	k15mejnm
2721	k15mejnl
2720	k15mejnk
2719	k15mejnj
2718	k15mejni
2717	k15mejnh
2716	k15mejnf
2715	k15mejne
2714	k15mejnd
2713	k15mejnb
2712	k15mejna
2711	k15mejn9
2710	k15mejn8
2709	k15mejn7
2708	k15mejn6
2707	k15mejn5
2706	k15mejn4
2705	k15mejn3
2704	k15mejn2
2703	k15mejn1
2702	k15mejn0
2701	k15mejmy
2700	k15mejmx
2699	k15mejmw
2698	k15mejmv
2697	k15mejmu
2696	k15mejmt
2695	k15mejms
2694	k15mejmr
2693	k15mejmq
2692	k15mejmp
2691	k15mejmn
2690	k15mejmm
2689	k15mejml
2688	k15mejmk
2687	k15mejmi
2686	k15mejmh
2685	k15mejmf
2684	k15mejme
2683	k15mejmd
2682	k15mejmc
2681	k15mejmb
2680	k15mejma
2679	k15mejm9
2678	k15mejm8
2677	k15mejm7
2676	k15mejm5
2675	k15mejm4
2674	k15mejm3
2673	k15mejm2
2672	k15mejm1
2671	k15mejm0
2670	k15mejly
2669	k15mejlx
2668	k15mejlw
2667	k15mejlv
2666	k15mejlu
2665	k15mejlt
2664	k15mejls
2663	k15mejlr
2662	k15mejlq
2661	k15mejlp
2660	k15mejlo
2659	k15mejln
2658	k15mejlm
2657	k15mejll
2656	k15mejlk
2655	k15mejli
2654	k15mejlh
2653	k15mejlg
2652	k15mejle
2651	k15mejld
2650	k15mejlc
2649	k15mejlb
2648	k15mejl9
2647	k15mejl7
2646	k15mejl6
2645	k15mejl5
2644	k15mejl4
2643	k15mejl3
2642	k15mejl1
2641	k15mejl0
2640	k15mejky
2639	k15mejkx
2638	k15mejkw
2637	k15mejkv
2636	k15mejku
2635	k15mejkt
2634	k15mejks
2633	k15mejkr
2632	k15mejkq
2631	k15mejkp
2630	k15mejko
2629	k15mejkn
2628	k15mejkm
2627	k15mejkl
2626	k15mejkk
2625	k15mejki
2624	k15mejkf
2623	k15mejkd
2622	k15mejka
2621	k15mejk7
2620	k15mejk5
2619	k15mejk3
2618	k15mejk1
2617	k15mejjy
2616	k15mejjw
2615	k15mejjv
2614	k15mejju
2613	k15mejjt
2612	k15mejjr
2611	k15mejjq
2610	k15mejjp
2609	k15mejjn
2608	k15mejjl
2607	k15mejjk
2606	k15mejjj
2605	k15mejjh
2604	k15mejjg
2603	k15mejjf
2602	k15mejjd
2601	k15mejjc
2600	k15ma7sx
2599	k15ma7sw
2598	k15ma7sv
2597	k15ma7su
2596	k15ma7st
2595	k15ma7ss
2594	k15ma7sq
2593	k15ma7sp
2592	k15ma7so
2591	k15ma7sn
2590	k15ma7sm
2589	k15ma7sl
2588	k15ma7sk
2587	k15ma7si
2586	k15ma7sh
2585	k15ma7sg
2584	k15ma7sf
2583	k15ma7se
2582	k15ma7sd
2581	k15ma7sc
2580	k15ma7sb
2579	k15ma7sa
2578	k15ma7s9
2577	k15ma7s8
2576	k15ma7s7
2575	k15ma7s6
2574	k15ma7s4
2573	k15ma7s3
2572	k15ma7s2
2571	k15ma7s1
2570	k15ma7ry
2569	k15ma7rx
2568	k15ma7rw
2567	k15ma7rv
2566	k15ma7ru
2565	k15ma7rt
2564	k15ma7rs
2563	k15ma7rq
2562	k15ma7rp
2561	k15ma7ro
2560	k15ma7rn
2559	k15ma7rm
2558	k15ma7rl
2557	k15ma7rk
2556	k15ma7rj
2555	k15ma7ri
2554	k15ma7rh
2553	k15ma7rg
2552	k15ma7rf
2551	k15ma7re
2550	k15ma7rd
2549	k15ma7rc
2548	k15ma7rb
2547	k15ma7ra
2546	k15ma7r9
2545	k15ma7r8
2544	k15ma7r7
2543	k15ma7r6
2542	k15ma7r5
2541	k15ma7r3
2540	k15ma7r1
2539	k15ma7r0
2538	k15ma7qy
2537	k15ma7qx
2536	k15ma7qw
2535	k15ma7qv
2534	k15ma7qu
2533	k15ma7qt
2532	k15ma7qs
2531	k15ma7qr
2530	k15ma7qq
2529	k15ma7qp
2528	k15ma7qo
2527	k15ma7qn
2526	k15ma7qm
2525	k15ma7ql
2524	k15ma7qk
2523	k15ma7qj
2522	k15ma7qi
2521	k15ma7qh
2520	k15ma7qg
2519	k15ma7qf
2518	k15ma7qe
2517	k15ma7qd
2516	k15ma7qc
2515	k15ma7qb
2514	k15ma7q9
2513	k15ma7q8
2512	k15ma7q7
2511	k15ma7q6
2510	k15ma7q5
2509	k15ma7q4
2508	k15ma7q3
2507	k15ma7q2
2506	k15ma7q1
2505	k15ma7q0
2504	k15ma7py
2503	k15ma7px
2502	k15ma7pw
2501	k15ma7pv
2500	k15ma7pu
2499	k15ma7pt
2498	k15ma7ps
2497	k15ma7pr
2496	k15ma7pq
2495	k15ma7pp
2494	k15ma7po
2493	k15ma7pn
2492	k15ma7pm
2491	k15ma7pl
2490	k15ma7pi
2489	k15ma7ph
2488	k15ma7pg
2487	k15ma7pf
2486	k15ma7pe
2485	k15ma7pd
2484	k15ma7pc
2483	k15ma7pb
2482	k15ma7pa
2481	k15ma7p9
2480	k15ma7p8
2479	k15ma7p7
2478	k15ma7p6
2477	k15ma7p5
2476	k15ma7p4
2475	k15ma7p3
2474	k15ma7p2
2473	k15ma7p1
2472	k15ma7oy
2471	k15ma7ow
2470	k15ma7ou
2469	k15ma7os
2468	k15ma7op
2467	k15ma7on
2466	k15ma7ol
2465	k15ma7oj
2464	k15ma7og
2463	k15ma7of
2462	k15ma7od
2461	k15ma7oa
2460	k15ma7o9
2459	k15ma7o8
2458	k15ma7o7
2457	k15ma7o6
2456	k15ma7o5
2455	k15ma7o4
2454	k15ma7o3
2453	k15ma7o2
2452	k15ma7o1
2451	k15ma7o0
2450	k15ma7ny
2449	k15ma7nx
2448	k15ma7nw
2447	k15ma7nu
2446	k15ma7ns
2445	k15ma7nr
2444	k15ma7nq
2443	k15ma7np
2442	k15ma7no
2441	k15ma7nn
2440	k15ma7nm
2439	k15ma7nl
2438	k15ma7nk
2437	k15ma7nj
2436	k15ma7ni
2435	k15ma7nh
2434	k15ma7ng
2433	k15ma7nf
2432	k15ma7ne
2431	k15ma7nd
2430	k15ma7nb
2429	k15ma7na
2428	k15ma7n9
2427	k15ma7n8
2426	k15ma7n7
2425	k15ma7n6
2424	k15ma7n5
2423	k15ma7n4
2422	k15ma7n3
2421	k15ma7n2
2420	k15ma7n0
2419	k15ma7my
2418	k15ma7mx
2417	k15ma7mw
2416	k15ma7mv
2415	k15ma7mu
2414	k15ma7mt
2413	k15ma7mq
2412	k15ma7mp
2411	k15ma7mo
2410	k15ma7mn
2409	k15ma7ml
2408	k15ma7mk
2407	k15ma7mj
2406	k15ma7mh
2405	k15ma7mf
2404	k15ma7me
2403	k15ma7md
2402	k15ma7mc
2401	k15ma7mb
2400	k15ma6ji
2399	k15ma6jh
2398	k15ma6jg
2397	k15ma6jf
2396	k15ma6je
2395	k15ma6jd
2394	k15ma6jc
2393	k15ma6jb
2392	k15ma6ja
2391	k15ma6j9
2390	k15ma6j8
2389	k15ma6j7
2388	k15ma6j6
2387	k15ma6j5
2386	k15ma6j4
2385	k15ma6j3
2384	k15ma6j2
2383	k15ma6j1
2382	k15ma6j0
2381	k15ma6iy
2380	k15ma6ix
2379	k15ma6iw
2378	k15ma6iv
2377	k15ma6iu
2376	k15ma6it
2375	k15ma6is
2374	k15ma6ir
2373	k15ma6iq
2372	k15ma6ip
2371	k15ma6in
2370	k15ma6im
2369	k15ma6il
2368	k15ma6ik
2367	k15ma6ij
2366	k15ma6ii
2365	k15ma6ih
2364	k15ma6ig
2363	k15ma6if
2362	k15ma6ie
2361	k15ma6id
2360	k15ma6ic
2359	k15ma6ib
2358	k15ma6i9
2357	k15ma6i8
2356	k15ma6i7
2355	k15ma6i6
2354	k15ma6i5
2353	k15ma6i4
2352	k15ma6i3
2351	k15ma6i2
2350	k15ma6i0
2349	k15ma6hy
2348	k15ma6hx
2347	k15ma6hw
2346	k15ma6hv
2345	k15ma6hu
2344	k15ma6ht
2343	k15ma6hs
2342	k15ma6hr
2341	k15ma6hq
2340	k15ma6ho
2339	k15ma6hn
2338	k15ma6hm
2337	k15ma6hl
2336	k15ma6hk
2335	k15ma6hj
2334	k15ma6hi
2333	k15ma6hh
2332	k15ma6hf
2331	k15ma6he
2330	k15ma6hd
2329	k15ma6hb
2328	k15ma6ha
2327	k15ma6h9
2326	k15ma6h8
2325	k15ma6h6
2324	k15ma6h5
2323	k15ma6h4
2322	k15ma6h3
2321	k15ma6h2
2320	k15ma6h1
2319	k15ma6h0
2318	k15ma6gy
2317	k15ma6gx
2316	k15ma6gw
2315	k15ma6gu
2314	k15ma6gt
2313	k15ma6gs
2312	k15ma6gr
2311	k15ma6gq
2310	k15ma6gp
2309	k15ma6go
2308	k15ma6gn
2307	k15ma6gm
2306	k15ma6gl
2305	k15ma6gk
2304	k15ma6gj
2303	k15ma6gi
2302	k15ma6gh
2301	k15ma6gg
2300	k15ma6gf
2299	k15ma6ge
2298	k15ma6gd
2297	k15ma6gc
2296	k15ma6ga
2295	k15ma6g9
2294	k15ma6g8
2293	k15ma6g7
2292	k15ma6g6
2291	k15ma6g5
2290	k15ma6g4
2289	k15ma6g3
2288	k15ma6g2
2287	k15ma6g0
2286	k15ma6fy
2285	k15ma6fx
2284	k15ma6fv
2283	k15ma6fu
2282	k15ma6ft
2281	k15ma6fs
2280	k15ma6fr
2279	k15ma6fq
2278	k15ma6fp
2277	k15ma6fo
2276	k15ma6fm
2275	k15ma6fl
2274	k15ma6fk
2273	k15ma6fj
2272	k15ma6fi
2271	k15ma6fh
2270	k15ma6fg
2269	k15ma6ff
2268	k15ma6fe
2267	k15ma6fd
2266	k15ma6fc
2265	k15ma6fb
2264	k15ma6fa
2263	k15ma6f9
2262	k15ma6f8
2261	k15ma6f6
2260	k15ma6f5
2259	k15ma6f4
2258	k15ma6f3
2257	k15ma6f2
2256	k15ma6f1
2255	k15ma6ey
2254	k15ma6ew
2253	k15ma6ev
2252	k15ma6eu
2251	k15ma6et
2250	k15ma6er
2249	k15ma6ep
2248	k15ma6eo
2247	k15ma6en
2246	k15ma6em
2245	k15ma6el
2244	k15ma6ek
2243	k15ma6ej
2242	k15ma6ei
2241	k15ma6eh
2240	k15ma6eg
2239	k15ma6ef
2238	k15ma6ee
2237	k15ma6ed
2236	k15ma6eb
2235	k15ma6ea
2234	k15ma6e9
2233	k15ma6e8
2232	k15ma6e7
2231	k15ma6e6
2230	k15ma6e5
2229	k15ma6e4
2228	k15ma6e3
2227	k15ma6e1
2226	k15ma6e0
2225	k15ma6dy
2224	k15ma6dx
2223	k15ma6dw
2222	k15ma6dv
2221	k15ma6du
2220	k15ma6dt
2219	k15ma6ds
2218	k15ma6dr
2217	k15ma6dq
2216	k15ma6dp
2215	k15ma6do
2214	k15ma6dn
2213	k15ma6dm
2212	k15ma6dl
2211	k15ma6dk
2210	k15ma6di
2209	k15ma6dh
2208	k15ma6dg
2207	k15ma6df
2206	k15ma6de
2205	k15ma6dd
2204	k15ma6dc
2203	k15ma6da
2202	k15ma6d9
2201	k15ma6d8
2200	k15jmeyu
2199	k15jmeys
2198	k15jmeyq
2197	k15jmeyn
2196	k15jmeyl
2195	k15jmeyj
2194	k15jmeyh
2193	k15jmeyf
2192	k15jmeyd
2191	k15jmeyb
2190	k15jmey9
2189	k15jmey7
2188	k15jmey6
2187	k15jmey5
2186	k15jmey4
2185	k15jmey3
2184	k15jmey2
2183	k15jmey1
2182	k15jmey0
2181	k15jmexy
2180	k15jmexw
2179	k15jmexv
2178	k15jmexu
2177	k15jmexs
2176	k15jmexr
2175	k15jmexq
2174	k15jmexp
2173	k15jmexo
2172	k15jmexm
2171	k15jmexl
2170	k15jmexj
2169	k15jmexh
2168	k15jmexg
2167	k15jmexf
2166	k15jmexd
2165	k15jmexb
2164	k15jmexa
2163	k15jmex9
2162	k15jmex8
2161	k15jmex7
2160	k15jmex6
2159	k15jmex4
2158	k15jmex3
2157	k15jmex1
2156	k15jmewx
2155	k15jmeww
2154	k15jmewv
2153	k15jmewu
2152	k15jmewt
2151	k15jmews
2150	k15jmewr
2149	k15jmewq
2148	k15jmewp
2147	k15jmewo
2146	k15jmewn
2145	k15jmewm
2144	k15jmewl
2143	k15jmewk
2142	k15jmewi
2141	k15jmewh
2140	k15jmewg
2139	k15jmewf
2138	k15jmewe
2137	k15jmewd
2136	k15jmewc
2135	k15jmewb
2134	k15jmewa
2133	k15jmew9
2132	k15jmew8
2131	k15jmew7
2130	k15jmew6
2129	k15jmew5
2128	k15jmew4
2127	k15jmew2
2126	k15jmew0
2125	k15jmevy
2124	k15jmevx
2123	k15jmevw
2122	k15jmevv
2121	k15jmevu
2120	k15jmevt
2119	k15jmevs
2118	k15jmevr
2117	k15jmevq
2116	k15jmevo
2115	k15jmevm
2114	k15jmevl
2113	k15jmevk
2112	k15jmevj
2111	k15jmevi
2110	k15jmevh
2109	k15jmevg
2108	k15jmevf
2107	k15jmeve
2106	k15jmevd
2105	k15jmevc
2104	k15jmevb
2103	k15jmeva
2102	k15jmev9
2101	k15jmev8
2100	k15jmev7
2099	k15jmev6
2098	k15jmev5
2097	k15jmev4
2096	k15jmev3
2095	k15jmev2
2094	k15jmev1
2093	k15jmev0
2092	k15jmeux
2091	k15jmeuw
2090	k15jmeuv
2089	k15jmeuu
2088	k15jmeut
2087	k15jmeus
2086	k15jmeuq
2085	k15jmeup
2084	k15jmeuo
2083	k15jmeun
2082	k15jmeum
2081	k15jmeul
2080	k15jmeuj
2079	k15jmeui
2078	k15jmeug
2077	k15jmeuf
2076	k15jmeue
2075	k15jmeud
2074	k15jmeub
2073	k15jmeu9
2072	k15jmeu8
2071	k15jmeu7
2070	k15jmeu6
2069	k15jmeu5
2068	k15jmeu3
2067	k15jmeu2
2066	k15jmeu1
2065	k15jmeu0
2064	k15jmety
2063	k15jmetx
2062	k15jmetw
2061	k15jmetu
2060	k15jmett
2059	k15jmets
2058	k15jmetq
2057	k15jmetp
2056	k15jmeto
2055	k15jmetn
2054	k15jmetm
2053	k15jmetl
2052	k15jmetk
2051	k15jmetj
2050	k15jmeti
2049	k15jmeth
2048	k15jmetg
2047	k15jmetf
2046	k15jmete
2045	k15jmetc
2044	k15jmeta
2043	k15jmet7
2042	k15jmet4
2041	k15jmet1
2040	k15jmesx
2039	k15jmesu
2038	k15jmess
2037	k15jmesp
2036	k15jmesm
2035	k15jmesk
2034	k15jmesh
2033	k15jmesd
2032	k15jmesa
2031	k15jmes6
2030	k15jmes3
2029	k15jmery
2028	k15jmeru
2027	k15jmerr
2026	k15jmero
2025	k15jmerl
2024	k15jmeri
2023	k15jmerg
2022	k15jmerd
2021	k15jmera
2020	k15jmer8
2019	k15jmer7
2018	k15jmer6
2017	k15jmer5
2016	k15jmer4
2015	k15jmer3
2014	k15jmer2
2013	k15jmer1
2012	k15jmer0
2011	k15jmeqy
2010	k15jmeqx
2009	k15jmeqw
2008	k15jmeqv
2007	k15jmequ
2006	k15jmeqt
2005	k15jmeqr
2004	k15jmeqq
2003	k15jmeqp
2002	k15jmeqo
2001	k15jmeqn
2000	k15jmeql
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

