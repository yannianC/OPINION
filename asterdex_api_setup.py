#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aster DEX API 自动创建脚本（独立运行，不依赖其他脚本）

从 findAccountConfigCache 接口获取浏览器列表，筛选出本地电脑组且 s/t 为空的账户，
依次为每个浏览器在 Aster DEX 创建 API，并上传 API Key 和 Secret 到服务器。
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ============================================================================
# 配置常量
# ============================================================================
SERVER_BASE_URL = "https://sg.bicoin.com.cn/99l"
ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"
OKX_EXTENSION_ID = "mcohilncbfahbmgdjkbpemcciiolgcge"
ASTERDEX_API_URL = "https://www.asterdex.com/en/api-management"
TRUSTED_IP = "47.88.228.109"
MAX_RETRIES = 3

# 电脑组密码配置（与 auto_trader 一致）
GROUP_PASSWORDS = {
    "0": "Ok123456", "1": "qwer1234", "2": "ywj000805*", "3": "Qrfv*Fjh87gg",
    "4": "@#nsgaSBF224", "5": "Qsst-455fgdf8", "6": "zxcvbnm123#", "7": "cx142359.",
    "8": "ywj000805*", "9": "Qwer009qaz`", "10": "yhCHG^&145", "11": "jhJ89891",
    "12": "Hhgj*liu-khHy5", "13": "shdjjeG@^68Jhg", "14": "gkj^&HGkhh45",
    "15": " kaznb3969*m%", "16": "ggTG*h785Wunj", "21": "kjakln3*zhjql3",
    "22": "ttRo451YU*58", "23": "mj@w2ndJ*kX0g8!rns", "24": "5cx2Wsn#0kQnj*w240",
    "25": "kashg2*dk2F", "26": "cxknwlJK&*f8", "27": "kiIH78hjfi.*+*",
}
SPECIFIC_BROWSER_PASSWORDS = {}  # 可在此扩展特定浏览器密码
DEFAULT_PASSWORD = "Ok123456"

# 全局变量
FINGERPRINT_TO_USERID = {}
LAST_PROXY_CONFIG = {}


# ============================================================================
# 工具函数
# ============================================================================

def log_print(*args, **kwargs):
    """带时间戳的打印"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)


def read_computer_config():
    """从 COMPUTER.txt 读取电脑组、IP线程数、交易线程数"""
    default_group, default_ip, default_trade = "0", 15, 15
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "COMPUTER.txt")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if content:
                parts = [p.strip() for p in content.split(',')]
                group = parts[0] if parts else default_group
                ip_cnt = int(parts[1]) if len(parts) > 1 and parts[1] else default_ip
                trade_cnt = int(parts[2]) if len(parts) > 2 and parts[2] else default_trade
                log_print(f"[系统] 电脑组={group}, IP线程数={ip_cnt}, 交易线程数={trade_cnt}")
                return (group, ip_cnt, trade_cnt)
    except Exception as e:
        log_print(f"[系统] 读取 COMPUTER.txt 失败: {e}")
    return (default_group, default_ip, default_trade)


def get_browser_password(browser_id, computer_group):
    """根据浏览器ID和电脑组获取密码"""
    bid = str(browser_id)
    if bid in SPECIFIC_BROWSER_PASSWORDS:
        return SPECIFIC_BROWSER_PASSWORDS[bid]
    return GROUP_PASSWORDS.get(str(computer_group), DEFAULT_PASSWORD)


def load_fingerprint_mapping():
    """加载 fingerprintNo -> user_id 映射（用于 AdsPower）"""
    global FINGERPRINT_TO_USERID
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(script_dir, "FINGERPRINT_MAPPING.txt")
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        FINGERPRINT_TO_USERID[parts[0]] = parts[1]
            log_print(f"[系统] 从 FINGERPRINT_MAPPING.txt 加载 {len(FINGERPRINT_TO_USERID)} 个映射")
            return
        except Exception as e:
            log_print(f"[系统] 读取映射文件失败: {e}")
    # 尝试从 AdsPower API 获取
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/list"
        headers = {'Authorization': f'Bearer {ADSPOWER_API_KEY}'}
        page, total = 1, 0
        while True:
            r = requests.get(url, params={"page_size": 100, "page": page}, headers=headers, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            if data.get("code") != 0:
                break
            li = data.get("data", {}).get("list", [])
            for u in li:
                sn = str(u.get("serial_number", "") or u.get("fingerprint", ""))
                uid = u.get("user_id", "")
                if sn and uid:
                    FINGERPRINT_TO_USERID[sn] = uid
            total += len(li)
            if len(li) < 100:
                break
            page += 1
        if FINGERPRINT_TO_USERID:
            log_print(f"[系统] 从 AdsPower API 加载 {len(FINGERPRINT_TO_USERID)} 个映射")
            return
    except Exception as e:
        log_print(f"[系统] AdsPower API 加载映射失败: {e}")
    log_print("[系统] ⚠ 未加载到指纹映射，请在脚本同目录创建 FINGERPRINT_MAPPING.txt（每行: 浏览器编号 user_id）")


# ============================================================================
# 代理与浏览器
# ============================================================================

def get_new_ip_for_browser(browser_id, timeout=15, ip_index=0):
    """获取新代理配置"""
    try:
        url = f"{SERVER_BASE_URL}/bro/ipStatusByNumber"
        r = requests.get(url, params={"number": browser_id}, timeout=timeout)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("code") != 0:
            return None
        ip_list = data.get("data", {}).get("list", [])
        if not ip_list:
            return None
        options = []
        for item in ip_list:
            ip, un, pw = item.get("ip"), item.get("username"), item.get("password")
            if not ip or not un or not pw:
                continue
            http_ok = str(item.get("c", "")) == "1"
            socks_ok = str(item.get("f", "")) == "1"
            hp = str(item.get("port") or "50100")
            sp = str(item.get("socketPort") or "50101")
            try:
                hd = int(item.get("h") or 999999) if http_ok else 999999
                sd = int(item.get("i") or 999999) if socks_ok else 999999
            except (ValueError, TypeError):
                hd, sd = 999999, 999999
            if http_ok and socks_ok:
                opt = {"ip": ip, "port": hp if hd <= sd else sp, "username": un, "password": pw,
                       "type": "http" if hd <= sd else "socks5", "delay": min(hd, sd)}
            elif http_ok:
                opt = {"ip": ip, "port": hp, "username": un, "password": pw, "type": "http", "delay": hd}
            elif socks_ok:
                opt = {"ip": ip, "port": sp, "username": un, "password": pw, "type": "socks5", "delay": sd}
            else:
                opt = {"ip": ip, "port": hp, "username": un, "password": pw, "type": "http", "delay": 999999}
            options.append(opt)
        options.sort(key=lambda x: x.get("delay", 999999))
        if ip_index >= len(options):
            return None
        return options[ip_index]
    except Exception as e:
        log_print(f"[{browser_id}] 获取IP失败: {e}")
        return None


def update_adspower_proxy(browser_id, proxy_config):
    """更新 AdsPower 代理"""
    uid = FINGERPRINT_TO_USERID.get(str(browser_id))
    if not uid:
        log_print(f"[{browser_id}] ✗ 无 user_id 映射，跳过代理更新")
        return False
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/update"
        payload = {"user_id": uid, "user_proxy_config": {
            "proxy_host": proxy_config["ip"], "proxy_port": str(proxy_config["port"]),
            "proxy_user": proxy_config["username"], "proxy_password": proxy_config["password"],
            "proxy_type": proxy_config["type"], "proxy_soft": "other"
        }}
        r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {ADSPOWER_API_KEY}'}, timeout=15)
        if r.status_code == 200 and r.json().get("code") == 0:
            LAST_PROXY_CONFIG[str(browser_id)] = proxy_config.copy()
            return True
    except Exception as e:
        log_print(f"[{browser_id}] 更新代理异常: {e}")
    return False


def try_update_ip_before_start(browser_id):
    """打开浏览器前获取并更新代理"""
    cfg = get_new_ip_for_browser(browser_id, timeout=8, ip_index=0)
    if cfg:
        ok = update_adspower_proxy(browser_id, cfg)
        return ok, cfg.get("ip"), cfg.get("delay")
    last = LAST_PROXY_CONFIG.get(str(browser_id))
    if last:
        return False, last.get("ip"), last.get("delay")
    return False, None, None


def start_adspower_browser(serial_number):
    """启动 AdsPower 浏览器"""
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/start"
    params = {"serial_number": serial_number, "user_id": "", "open_tabs": 1,
              "launch_args": json.dumps(["--window-size=1500,1700"])}
    headers = {'Authorization': f'Bearer {ADSPOWER_API_KEY}'}
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            d = r.json()
            if d.get("code") == 0:
                return d.get("data")
            log_print(f"[{serial_number}] 启动失败: {d.get('msg')}")
        except Exception as e:
            log_print(f"[{serial_number}] 启动异常: {e}")
        if i < MAX_RETRIES - 1:
            time.sleep(30 + 30 * i)
    return None


def close_adspower_browser(serial_number, max_retries=3):
    """关闭 AdsPower 浏览器"""
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/stop"
    params = {"serial_number": serial_number}
    headers = {'Authorization': f'Bearer {ADSPOWER_API_KEY}'}
    for i in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            if r.json().get("code") == 0:
                time.sleep(10)
                return True
        except Exception:
            pass
        if i < max_retries - 1:
            time.sleep(10)
    return False


def create_selenium_driver(browser_data):
    """创建 Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", browser_data["ws"]["selenium"])
    service = Service(executable_path=browser_data["webdriver"])
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(75)
    driver.set_script_timeout(75)
    return driver


def open_new_tab_with_url(driver, url, serial_number):
    """新标签页打开 URL"""
    try:
        driver.switch_to.new_window('tab')
        time.sleep(1)
        driver.get(url)
        time.sleep(2)
        return True
    except Exception:
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.CONTROL + 't')
            time.sleep(1)
            driver.get(url)
            time.sleep(2)
            return True
        except Exception:
            pass
    return False


def check_and_unlock_wallet(driver, serial_number, password):
    """检查并解锁 OKX 钱包"""
    try:
        try:
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#ui-ses-iframe"))
            )
            driver.switch_to.frame(iframe)
        except TimeoutException:
            try:
                iframe = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
                driver.switch_to.frame(iframe)
            except TimeoutException:
                pass
        try:
            pwd_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='okd-input']"))
            )
            driver.execute_script("""
                var i=arguments[0],p=arguments[1];
                var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                i.focus(); s.call(i,p);
                i.dispatchEvent(new Event('input',{bubbles:true}));
                i.dispatchEvent(new Event('change',{bubbles:true}));
            """, pwd_input, password)
            time.sleep(1)
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
            )
            btn.click()
            time.sleep(2)
        except TimeoutException:
            pass
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return True
    except Exception as e:
        log_print(f"[{serial_number}] 解锁钱包异常: {e}")
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return False


def preopen_okx_wallet(driver, serial_number, current_ip=None, current_delay=None):
    """预打开 OKX 钱包并解锁、处理确认按钮"""
    main_win = driver.current_window_handle
    okx_url = f"chrome-extension://{OKX_EXTENSION_ID}/popup.html"
    okx_win = None
    for h in driver.window_handles:
        try:
            driver.switch_to.window(h)
            if OKX_EXTENSION_ID in driver.current_url:
                okx_win = h
                break
        except Exception:
            continue
    if not okx_win:
        if open_new_tab_with_url(driver, okx_url, serial_number):
            for h in driver.window_handles:
                if h != main_win:
                    try:
                        driver.switch_to.window(h)
                        if OKX_EXTENSION_ID in driver.current_url:
                            okx_win = h
                            break
                    except Exception:
                        continue
    if okx_win:
        driver.switch_to.window(okx_win)
        password = get_browser_password(serial_number, COMPUTER_GROUP)
        check_and_unlock_wallet(driver, serial_number, password)
        start = time.time()
        while time.time() - start < 15:
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                if btns:
                    btns[0].click()
                    time.sleep(0.5)
                else:
                    break
            except Exception:
                time.sleep(0.5)
    driver.switch_to.window(main_win)
    time.sleep(1)
    return main_win


# ============================================================================
# 重试与点击辅助
# ============================================================================

def retry_click(driver, by, selector, browser_id, timeout=15, desc=""):
    """带重试的点击"""
    for _ in range(3):
        try:
            el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
            el.click()
            log_print(f"[{browser_id}] ✓ 已点击 {desc}")
            return True
        except Exception as e:
            log_print(f"[{browser_id}] ⚠ 点击 {desc} 失败: {e}")
            time.sleep(2)
    return False


def find_connect_wallet_button(driver, browser_id, timeout=15):
    """查找 Connect wallet 按钮（兼容多种选择器）"""
    selectors = [
        (By.XPATH, "//button[contains(text(), 'Connect wallet')]"),
        (By.XPATH, "//button[@aria-label='Connect wallet']"),
        (By.CSS_SELECTOR, "button[aria-label='Connect wallet']"),
        (By.XPATH, "//*[contains(text(), 'Connect wallet')]"),
    ]
    for by, sel in selectors:
        try:
            el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
            return el
        except TimeoutException:
            continue
    return None


def click_okx_second_button(driver, browser_id, timeout=15):
    """在 OKX 窗口点击第二个 okd-button"""
    try:
        btns = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
        )
        if len(btns) >= 2:
            btns[1].click()
        elif btns:
            btns[0].click()
        else:
            return False
        log_print(f"[{browser_id}] ✓ 已点击 okd-button")
        return True
    except Exception as e:
        log_print(f"[{browser_id}] 点击 okd-button 失败: {e}")
        return False


def switch_to_okx_window(driver, browser_id):
    """切换到 OKX 窗口"""
    for h in driver.window_handles:
        try:
            driver.switch_to.window(h)
            if OKX_EXTENSION_ID in driver.current_url:
                return True
        except Exception:
            continue
    return False


def safe_click(driver, element, browser_id="", desc=""):
    """安全点击：先尝试普通点击，被 overlay 拦截时改用 JS 点击"""
    try:
        element.click()
        if browser_id and desc:
            log_print(f"[{browser_id}] ✓ 已点击 {desc}")
        return True
    except Exception as e:
        if "click intercepted" in str(e).lower() or "obscured" in str(e).lower():
            try:
                driver.execute_script("arguments[0].click();", element)
                if browser_id and desc:
                    log_print(f"[{browser_id}] ✓ 已点击 {desc} (JS)")
                return True
            except Exception as e2:
                log_print(f"[{browser_id}] ✗ 点击 {desc} 失败: {e2}")
                return False
        raise


# ============================================================================
# 主流程
# ============================================================================

def fetch_account_list_simple():
    """获取 findAccountConfigCacheSimple 数据（轻量，仅 id/fingerprintNo/computeGroup/d/f）"""
    url = f"{SERVER_BASE_URL}/boost/findAccountConfigCacheSimple"
    try:
        log_print(f"[系统] 正在请求 findAccountConfigCacheSimple...")
        r = requests.get(url, timeout=60)
        log_print(f"[系统] 请求完成，状态码: {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or []
        log_print(f"[系统] 获取到 {len(items)} 条数据")
        return items
    except requests.exceptions.Timeout:
        log_print(f"[系统] ✗ 请求超时")
        return []
    except Exception as e:
        log_print(f"[系统] ✗ 请求失败: {e}")
        return []


def fetch_api_all_bound():
    """获取 api/all 中已绑定 API 的浏览器编号集合"""
    url = f"{SERVER_BASE_URL}/api/all"
    try:
        log_print(f"[系统] 正在请求 api/all 获取已绑定列表...")
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return set()
        data = r.json()
        if data.get("code") != 0:
            return set()
        li = data.get("data", {}).get("list") or []
        bound = {str(x.get("number", "")) for x in li if x.get("number")}
        log_print(f"[系统] 已绑定 API 的浏览器数: {len(bound)}")
        return bound
    except Exception as e:
        log_print(f"[系统] ✗ 请求 api/all 失败: {e}")
        return set()


def filter_target_items(items, computer_group, bound_numbers):
    """筛选：电脑组一致，且未在 api/all 中已绑定"""
    out = []
    for i in items:
        cg = str(i.get("computeGroup") or "").strip()
        fp = str(i.get("fingerprintNo") or i.get("no") or "").strip()
        if cg == str(computer_group) and fp and fp not in bound_numbers:
            out.append(i)
    return out


def extract_api_key_secret(driver, dialog, browser_id):
    """从 dialog 中提取 API Key 和 API Secret Key，带多种选择器尝试"""
    api_key, api_secret = None, None
    selectors_key = [
        ".//p[contains(text(), 'API key') and not(contains(text(), 'API secret'))]/following-sibling::div[1]",
        ".//p[text()='API key']/following-sibling::div[1]",
        ".//*[contains(text(), 'API key') and not(contains(text(), 'secret'))]/../div[last()]",
    ]
    selectors_secret = [
        ".//p[contains(text(), 'API secret key')]/following-sibling::div[1]",
        ".//p[text()='API secret key']/following-sibling::div[1]",
        ".//*[contains(text(), 'API secret key')]/../div[last()]",
    ]
    for sel in selectors_key:
        try:
            div = dialog.find_element(By.XPATH, sel)
            ps = div.find_elements(By.TAG_NAME, "p")
            t = (ps[0].text or "").strip() if ps else ""
            if t and len(t) > 10 and "API key" not in t:
                api_key = t
                log_print(f"[{browser_id}] 提取 API Key 成功 (选择器: {sel[:50]}...)")
                break
        except Exception as e:
            log_print(f"[{browser_id}] 尝试提取 API Key 失败: {e}")
    for sel in selectors_secret:
        try:
            div = dialog.find_element(By.XPATH, sel)
            ps = div.find_elements(By.TAG_NAME, "p")
            t = (ps[0].text or "").strip() if ps else ""
            if t and len(t) > 10 and "API secret" not in t:
                api_secret = t
                log_print(f"[{browser_id}] 提取 API Secret 成功")
                break
        except Exception as e:
            log_print(f"[{browser_id}] 尝试提取 API Secret 失败: {e}")
    if not api_key or not api_secret:
        log_print(f"[{browser_id}] ⚠ 提取结果: APIKey={bool(api_key)}, APISecret={bool(api_secret)}")
    return api_key, api_secret


def bind_api_with_retry(number, api_key, api_secret, browser_id, max_retries=5, retry_interval=10):
    """带重试的 api/bind 绑定"""
    url = f"{SERVER_BASE_URL}/api/bind"
    payload = {"number": str(number), "apiKey": api_key, "apiSecret": api_secret}
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                res = r.json()
                if res.get("code") == 0:
                    return True, res, None
                err = res.get("msg", "unknown")
            else:
                err = f"HTTP {r.status_code}"
        except Exception as e:
            err = str(e)
        log_print(f"[{browser_id}] 绑定失败(第{attempt}次): {err}")
        if attempt < max_retries:
            time.sleep(retry_interval)
    return False, None, err


def process_single_browser(item, computer_group):
    """处理单个浏览器"""
    browser_id = str(item.get("fingerprintNo") or item.get("no", ""))
    if not browser_id:
        return False
    driver = None
    try:
        log_print(f"[{browser_id}] 步骤1: 获取 IP 并更新代理")
        _, current_ip, current_delay = try_update_ip_before_start(browser_id)

        log_print(f"[{browser_id}] 步骤2: 启动浏览器")
        browser_data = start_adspower_browser(browser_id)
        if not browser_data:
            return False

        driver = create_selenium_driver(browser_data)
        time.sleep(4)

        log_print(f"[{browser_id}] 步骤5: 打开 Aster DEX API 页面")
        driver.get(ASTERDEX_API_URL)
        time.sleep(3)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'API management')]"))
            )
        except TimeoutException:
            log_print(f"[{browser_id}] ⚠ 未找到 API management h1，继续执行")

        main_window = driver.current_window_handle

        log_print(f"[{browser_id}] 步骤7: 预打开 OKX 钱包")
        preopen_okx_wallet(driver, browser_id, current_ip, current_delay)
        driver.switch_to.window(main_window)
        time.sleep(2)

        # Connect wallet
        btn = find_connect_wallet_button(driver, browser_id, 15)
        if btn:
            btn.click()
            log_print(f"[{browser_id}] ✓ 已点击 Connect wallet")
            time.sleep(2)

            # OKX Wallet
            try:
                okx_els = driver.find_elements(By.XPATH, "//span[contains(text(), 'OKX Wallet')]")
                if okx_els:
                    okx_els[0].find_element(By.XPATH, "./..").click()
                    log_print(f"[{browser_id}] ✓ 已选择 OKX Wallet")
                    time.sleep(2)
            except Exception as e:
                log_print(f"[{browser_id}] 选择 OKX Wallet 失败: {e}")

            # 切换到 OKX：解锁 -> 点击第二个 okd-button -> 等3s -> 再点击第二个
            if switch_to_okx_window(driver, browser_id):
                password = get_browser_password(browser_id, computer_group)
                check_and_unlock_wallet(driver, browser_id, password)
                click_okx_second_button(driver, browser_id, 15)
                time.sleep(3)
                click_okx_second_button(driver, browser_id, 15)

            driver.switch_to.window(main_window)
            time.sleep(2)

        # Create API（需同时满足文本和 type="submit"）
        create_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Create API') and @type='button']")
        if not create_btns:
            log_print(f"[{browser_id}] ✗ 未找到 Create API 按钮")
            return False
        create_btns[0].click()
        log_print(f"[{browser_id}] ✓ 已点击 Create API")
        time.sleep(2)

        # 填写 API label
        try:
            inp = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='API label']"))
            )
            inp.clear()
            inp.send_keys(browser_id)
            time.sleep(0.5)
        except TimeoutException:
            log_print(f"[{browser_id}] ✗ 未找到 API label 输入框")
            return False

        # 再次点击 Create API（弹窗内确认，type=submit）
        create_btns = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), 'Create API') and @type='submit']"))
        )
        if create_btns:
            create_btns[0].click()
            log_print(f"[{browser_id}] ✓ 已点击 Create API（确认）")
        time.sleep(2)

        if switch_to_okx_window(driver, browser_id):
            click_okx_second_button(driver, browser_id, 15)
        driver.switch_to.window(main_window)
        time.sleep(2)

        # Restrict to trusted IPs only：优先用 id=ip_restrict 的 button，否则找包含文本的 div -> 父的父 A -> A 下 data-state=unchecked 的 button
        try:
            btn = driver.find_elements(By.CSS_SELECTOR, "button#ip_restrict")
            if not btn:
                divs = driver.find_elements(By.XPATH, "//div[contains(., 'Restrict to trusted IPs only')]")
                if divs:
                    a = divs[0].find_element(By.XPATH, "./../..")
                    btns = a.find_elements(By.CSS_SELECTOR, "button[data-state='unchecked']")
                    btn = btns
            if btn and btn[0].get_attribute("data-state") == "unchecked":
                btn[0].click()
                log_print(f"[{browser_id}] ✓ 已点击 Restrict to trusted IPs only")
            else:
                log_print(f"[{browser_id}] ℹ 未找到可点击的 Restrict 按钮（可能已选中）")
            time.sleep(0.5)
        except Exception as e:
            log_print(f"[{browser_id}] Restrict 操作异常: {e}")

        try:
            ip_inp = driver.find_element(
                By.CSS_SELECTOR,
                "input[placeholder='If entering multiple IP addresses, separate them with spaces.']"
            )
            ip_inp.clear()
            ip_inp.send_keys(TRUSTED_IP)
            time.sleep(2)
        except Exception as e:
            log_print(f"[{browser_id}] 填写 IP 失败: {e}")

        # Confirm
        try:
            ps = driver.find_elements(By.XPATH, "//p[contains(text(), 'Confirm')]")
            if ps:
                safe_click(driver, ps[0], browser_id, "Confirm")
        except Exception:
            pass
        time.sleep(1)

        # Checkboxes
        try:
            for b in driver.find_elements(By.CSS_SELECTOR, "button[role='checkbox'][data-state='unchecked']"):
                try:
                    safe_click(driver, b, browser_id=browser_id)
                    time.sleep(0.3)
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(1)

        # 提取 API Key / Secret
        try:
            dialog = driver.find_element(By.CSS_SELECTOR, "div[role='dialog'][data-state='open']")
        except Exception as e:
            log_print(f"[{browser_id}] ✗ 未找到 dialog: {e}")
            return False

        APIKey, APISecretKey = extract_api_key_secret(driver, dialog, browser_id)
        if not APIKey or not APISecretKey:
            log_print(f"[{browser_id}] ✗ 未能提取 API Key/Secret")
            return False

        # Save
        try:
            save_btns = dialog.find_elements(By.XPATH, ".//button[contains(text(), 'Save')]")
            if save_btns:
                safe_click(driver, save_btns[0], browser_id, "Save")
        except Exception as e:
            log_print(f"[{browser_id}] 点击 Save 失败: {e}")
            return False
        time.sleep(2)

        if switch_to_okx_window(driver, browser_id):
            click_okx_second_button(driver, browser_id, 15)
        driver.switch_to.window(main_window)
        time.sleep(3)

        # 验证 td
        try:
            tds = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.TAG_NAME, "td")))
            found = any(browser_id in (t.text or "") for t in tds)
            if not found:
                log_print(f"[{browser_id}] ⚠ 未在页面中找到浏览器编号的 td")
        except TimeoutException:
            pass

        # 调用 api/bind 绑定
        ok, _, err = bind_api_with_retry(browser_id, APIKey, APISecretKey, browser_id)
        if not ok:
            log_print(f"[{browser_id}] ✗ 绑定失败: {err}")
            return False
        log_print(f"[{browser_id}] ✓ 绑定成功")
        return True

    except Exception as e:
        log_print(f"[{browser_id}] ✗ 异常: {e}")
        import traceback
        log_print(traceback.format_exc())
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        log_print(f"[{browser_id}] 关闭浏览器")
        try:
            close_adspower_browser(browser_id)
        except Exception as e:
            log_print(f"[{browser_id}] 关闭异常: {e}")


# 模块级电脑组（main 中设置）
COMPUTER_GROUP = "0"


def main():
    global COMPUTER_GROUP
    log_print("=" * 60)
    log_print("Aster DEX API 自动创建脚本（独立运行）")
    log_print("=" * 60)

    COMPUTER_GROUP, _, thread_limit = read_computer_config()
    load_fingerprint_mapping()

    items = fetch_account_list_simple()
    if not items:
        log_print("[系统] 无数据，退出")
        return

    bound_numbers = fetch_api_all_bound()
    target = filter_target_items(items, COMPUTER_GROUP, bound_numbers)
    log_print(f"[系统] 共 {len(items)} 条，已绑定 {len(bound_numbers)} 个，待处理 {len(target)} 条")
    if not target:
        log_print("[系统] 无待处理项，退出")
        return

    success, fail = 0, 0
    # 每个线程间隔 0.5s 再启动，避免指纹浏览器 API 限流
    with ThreadPoolExecutor(max_workers=thread_limit) as ex:
        futures = {}
        for idx, it in enumerate(target):
            if idx > 0:
                time.sleep(0.5)
            futures[ex.submit(process_single_browser, it, COMPUTER_GROUP)] = it
        for f in as_completed(futures):
            it = futures[f]
            bid = str(it.get("fingerprintNo") or it.get("no", ""))
            try:
                if f.result():
                    success += 1
                else:
                    fail += 1
            except Exception as e:
                log_print(f"[{bid}] 线程异常: {e}")
                fail += 1

    log_print("=" * 60)
    log_print(f"[系统] 完成。成功: {success}, 失败: {fail}")
    log_print("=" * 60)


if __name__ == "__main__":
    main()
