#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aster DEX Deposit 脚本（独立运行）

与 asterdex_api_setup 前面逻辑相同，打开 Spot 交易页面后执行 Deposit 流程。
"""

import os
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
TARGET_URL = "https://www.asterdex.com/en/trade/pro/spot/BTCUSDT"
DEPOSIT_TOKEN = "4"  # 可配置为其他代币
MAX_RETRIES = 3

# 特定浏览器ID的密码配置（与 auto_trader 一致）
SPECIFIC_BROWSER_PASSWORDS = {
    "1": "mj@w2ndJ*kX0g8!rnsf", "2": "mj@w2ndJ*kX0g8!rns", "3": "mj@w2ndJ*kX0g8!rnsf",
    "4": "mj@w2ndJ*kX0g8!rnsf", "9": "qwer1234", "10": "qwer1234", "6": "5cx2Wsn#0kQnj*w240L",
    "2060": "kaznb3969*m%", "2057": "kaznb3969*m%", "2058": "kaznb3969*m%", "2059": "kaznb3969*m%",
    "4001": "Ok123456",
    "941": "cx142359.", "942": "cx142359.", "944": "cx142359.", "945": "cx142359.", "946": "cx142359.",
    "947": "cx142359.", "948": "cx142359.", "949": "cx142359.", "950": "cx142359.", "951": "cx142359.",
    "952": "cx142359.", "953": "cx142359.", "954": "cx142359.", "955": "cx142359.", "956": "cx142359.",
    "957": "cx142359.", "958": "cx142359.", "959": "cx142359.", "960": "cx142359.", "961": "cx142359.",
    "962": "cx142359.", "963": "cx142359.", "964": "cx142359.", "965": "cx142359.", "966": "cx142359.",
    "967": "cx142359.", "968": "cx142359.", "969": "cx142359.", "970": "cx142359.", "971": "cx142359.",
    "972": "cx142359.", "973": "cx142359.", "974": "cx142359.", "975": "cx142359.", "976": "cx142359.",
    "977": "cx142359.", "978": "cx142359.", "979": "cx142359.", "980": "cx142359.", "981": "cx142359.",
    "982": "cx142359.", "983": "cx142359.", "984": "cx142359.", "985": "cx142359.", "986": "cx142359.",
    "987": "cx142359.", "988": "cx142359.", "989": "cx142359.", "990": "cx142359.", "991": "cx142359.",
    "992": "cx142359.", "993": "cx142359.", "994": "cx142359.", "995": "cx142359.", "996": "cx142359.",
    "997": "cx142359.", "998": "cx142359.", "999": "cx142359.", "1000": "cx142359.",
    "206": "cx142359.", "207": "cx142359.", "208": "cx142359.", "209": "cx142359.", "210": "cx142359.",
    "211": "cx142359.", "212": "cx142359.", "213": "cx142359.", "214": "cx142359.", "215": "cx142359.",
    "216": "cx142359.", "217": "cx142359.", "218": "cx142359.", "219": "cx142359.", "220": "cx142359.",
    "221": "cx142359.", "222": "cx142359.", "223": "cx142359.",
}
# 电脑组对应的默认密码配置（与 auto_trader 一致）
GROUP_PASSWORDS = {
    "0": "Ok678910", "1": "qwer1234", "2": "ywj000805*", "3": "Qrfv*Fjh87gg", "4": "@#nsgaSBF224",
    "5": "Qsst-455fgdf8", "6": "zxcvbnm123#", "7": "cx142359.", "8": "ywj000805*", "9": "Qwer009qaz`",
    "10": "yhCHG^&145", "11": "jhJ89891", "12": "Hhgj*liu-khHy5", "13": "shdjjeG@^68Jhg", "14": "gkj^&HGkhh45",
    "15": " kaznb3969*m%", "16": "ggTG*h785Wunj", "21": "kjakln3*zhjql3", "22": "ttRo451YU*58",
    "23": "mj@w2ndJ*kX0g8!rns", "24": "5cx2Wsn#0kQnj*w240", "25": "kashg2*dk2F", "26": "cxknwlJK&*f8",
    "27": "kiIH78hjfi.*+*",
    "900": "Ok123456", "901": "qwer1234", "902": "ywj000805*", "903": "Qrfv*Fjh87gg", "904": "@#nsgaSBF224",
    "905": "Qsst-455fgdf8", "906": "zxcvbnm123#", "907": "cx142359.", "908": "ywj000805*", "909": "Qwer009qaz`",
    "910": "yhCHG^&145", "911": "jhJ89891", "912": "Hhgj*liu-khHy5", "913": "shdjjeG@^68Jhg", "914": "gkj^&HGkhh45",
    "915": " kaznb3969*m%", "916": "ggTG*h785Wunj", "921": "kjakln3*zhjql3", "922": "ttRo451YU*58",
    "923": "mj@w2ndJ*kX0g8!rns", "924": "5cx2Wsn#0kQnj*w240", "925": "kashg2*dk2F", "926": "cxknwlJK&*f8",
    "927": "kiIH78hjfi.*+*",
}
DEFAULT_PASSWORD = "Ok678910"

FINGERPRINT_TO_USERID = {}
LAST_PROXY_CONFIG = {}
COMPUTER_GROUP = "0"


def log_print(*args, **kwargs):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)


def read_computer_config():
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
    bid = str(browser_id)
    if bid in SPECIFIC_BROWSER_PASSWORDS:
        return SPECIFIC_BROWSER_PASSWORDS[bid]
    return GROUP_PASSWORDS.get(str(computer_group), DEFAULT_PASSWORD)


def load_fingerprint_mapping():
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
    try:
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/list"
        headers = {'Authorization': f'Bearer {ADSPOWER_API_KEY}'}
        page = 1
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
            if len(li) < 100:
                break
            page += 1
        if FINGERPRINT_TO_USERID:
            log_print(f"[系统] 从 AdsPower API 加载 {len(FINGERPRINT_TO_USERID)} 个映射")
    except Exception as e:
        log_print(f"[系统] AdsPower API 加载映射失败: {e}")


def get_new_ip_for_browser(browser_id, timeout=15, ip_index=0):
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
    uid = FINGERPRINT_TO_USERID.get(str(browser_id))
    if not uid:
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
    except Exception:
        pass
    return False


def try_update_ip_before_start(browser_id):
    cfg = get_new_ip_for_browser(browser_id, timeout=8, ip_index=0)
    if cfg:
        ok = update_adspower_proxy(browser_id, cfg)
        return ok, cfg.get("ip"), cfg.get("delay")
    last = LAST_PROXY_CONFIG.get(str(browser_id))
    if last:
        return False, last.get("ip"), last.get("delay")
    return False, None, None


def start_adspower_browser(serial_number):
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
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", browser_data["ws"]["selenium"])
    service = Service(executable_path=browser_data["webdriver"])
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(75)
    driver.set_script_timeout(75)
    return driver


def open_new_tab_with_url(driver, url, serial_number):
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
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
            )
            # 用 JS 点击，避免 element click intercepted（即使视觉上无遮挡）
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn
            )
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
                    driver.execute_script("arguments[0].click();", btns[0])
                    time.sleep(0.5)
                else:
                    break
            except Exception:
                time.sleep(0.5)
    driver.switch_to.window(main_win)
    time.sleep(1)
    return main_win


def find_connect_wallet_button(driver, timeout=15):
    """找 Connect wallet 按钮，用 presence 即可（点击处已改为 JS click 避免被遮挡）. """
    selectors = [
        (By.XPATH, "//button[contains(text(), 'Connect wallet')]"),
        (By.XPATH, "//button[@aria-label='Connect wallet']"),
        (By.CSS_SELECTOR, "button[aria-label='Connect wallet']"),
        (By.XPATH, "//*[contains(text(), 'Connect wallet')]"),
    ]
    for by, sel in selectors:
        try:
            el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by, sel)))
            return el
        except TimeoutException:
            continue
    return None


def click_okx_second_button(driver, browser_id, timeout=15):
    try:
        btns = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
        )
        if len(btns) >= 2:
            log_print(f"[{browser_id}] ✓ 已点击 okd-button-1")
            driver.execute_script("arguments[0].click();", btns[1])
        elif btns:
            driver.execute_script("arguments[0].click();", btns[0])
        else:
            return False

        log_print(f"[{browser_id}] ✓ 已点击 okd-button")
        return True
    except Exception as e:
        log_print(f"[{browser_id}] 点击 okd-button 失败: {e}")
        return False


def switch_to_okx_window(driver):
    for h in driver.window_handles:
        try:
            driver.switch_to.window(h)
            if OKX_EXTENSION_ID in driver.current_url:
                return True
        except Exception:
            continue
    return False


# ============================================================================
# 主流程
# ============================================================================

def fetch_account_list_simple():
    url = f"{SERVER_BASE_URL}/boost/findAccountConfigCacheSimple"
    try:
        log_print(f"[系统] 正在请求 findAccountConfigCacheSimple...")
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("data") or []
    except Exception as e:
        log_print(f"[系统] ✗ 请求失败: {e}")
        return []


def fetch_api_all_bound():
    url = f"{SERVER_BASE_URL}/api/all"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return set()
        data = r.json()
        if data.get("code") != 0:
            return set()
        li = data.get("data", {}).get("list") or []
        return {str(x.get("number", "")) for x in li if x.get("number")}
    except Exception as e:
        log_print(f"[系统] ✗ 请求 api/all 失败: {e}")
        return set()


def filter_target_items(items, computer_group, bound_numbers):
    out = []
    for i in items:
        cg = str(i.get("computeGroup") or "").strip()
        fp = str(i.get("fingerprintNo") or i.get("no") or "").strip()
        if cg == str(computer_group) and fp and fp not in bound_numbers:
            out.append(i)
    return out


def process_single_browser(item, computer_group):
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

        log_print(f"[{browser_id}] 步骤3: 打开 Spot 页面")
        driver.get(TARGET_URL)
        time.sleep(3)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Spot overview')]"))
            )
            log_print(f"[{browser_id}] ✓ 页面加载完成（Spot overview）")
        except TimeoutException:
            log_print(f"[{browser_id}] ⚠ 15s 内未找到 Spot overview，继续执行")

        main_window = driver.current_window_handle

        log_print(f"[{browser_id}] 步骤4: 预打开 OKX 钱包")
        preopen_okx_wallet(driver, browser_id, current_ip, current_delay)
        driver.switch_to.window(main_window)
        time.sleep(2)

        # Connect wallet（用 JS 点击，避免顶部导航等遮挡导致 element click intercepted）
        btn = find_connect_wallet_button(driver, 15)
        if btn:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn
            )
            log_print(f"[{browser_id}] ✓ 已点击 Connect wallet")
            time.sleep(2)
            try:
                okx_els = driver.find_elements(By.XPATH, "//span[contains(text(), 'OKX Wallet')]")
                if okx_els:
                    parent = okx_els[0].find_element(By.XPATH, "./..")
                    driver.execute_script("arguments[0].click();", parent)
                    log_print(f"[{browser_id}] ✓ 已选择 OKX Wallet")
                    time.sleep(2)
            except Exception as e:
                log_print(f"[{browser_id}] 选择 OKX Wallet 失败: {e}")

            if switch_to_okx_window(driver):
                password = get_browser_password(browser_id, computer_group)
                check_and_unlock_wallet(driver, browser_id, password)
                click_okx_second_button(driver, browser_id, 15)
                time.sleep(3)
                click_okx_second_button(driver, browser_id, 15)

        driver.switch_to.window(main_window)
        time.sleep(2)

        # Deposit 流程
        log_print(f"[{browser_id}] 步骤5: 点击 Deposit")
        deposit_btns = driver.find_elements(By.XPATH, "//button[text()='Deposit']")
        if not deposit_btns:
            log_print(f"[{browser_id}] ✗ 未找到 Deposit 按钮")
            return False
        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", deposit_btns[0])
        time.sleep(1)

        # 15s 内找到 role="dialog" 的 div (A)
        try:
            a = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
        except TimeoutException:
            log_print(f"[{browser_id}] ✗ 15s 内未找到 dialog A")
            return False

        # A 内是否有 Spot account
        spot_divs = a.find_elements(By.XPATH, ".//div[contains(text(), 'Spot account')]")
        if not spot_divs:
            btns = a.find_elements(By.CSS_SELECTOR, "button[aria-haspopup='dialog']")
            if btns:
                driver.execute_script("arguments[0].click();", btns[0])
                time.sleep(1)
            spot_divs = driver.find_elements(By.XPATH, "//div[contains(text(), 'Spot account')]")
            if spot_divs:
                driver.execute_script("arguments[0].click();", spot_divs[0])
                log_print(f"[{browser_id}] ✓ 已点击 Spot account")
                time.sleep(0.5)

        time.sleep(0.5)

        # A 下是否有内容为 "BNB Chain" 的 div；没有则点第二个 aria-haspopup 按钮并选 BNB Chain
        bnb_in_a = a.find_elements(By.XPATH, ".//div[text()='BNB Chain']")
        if not bnb_in_a:
            a_haspopup_btns = a.find_elements(By.CSS_SELECTOR, "button[aria-haspopup='dialog']")
            if len(a_haspopup_btns) >= 2:
                driver.execute_script("arguments[0].click();", a_haspopup_btns[1])
                time.sleep(0.5)
            bnb_divs = driver.find_elements(By.XPATH, "//div[text()='BNB Chain']")
            if bnb_divs:
                bnb_parent_parent = bnb_divs[0].find_element(By.XPATH, "./../..")
                driver.execute_script("arguments[0].click();", bnb_parent_parent)
                log_print(f"[{browser_id}] ✓ 已选择 BNB Chain")
                time.sleep(2)

        # A 下 class="relative mb-4" 的 div (b)
        try:
            b_divs = a.find_elements(By.CSS_SELECTOR, "div.relative.mb-4")
            if not b_divs:
                b_divs = a.find_elements(By.XPATH, ".//div[contains(@class,'relative') and contains(@class,'mb-4')]")
            if b_divs:
                b_btns = b_divs[0].find_elements(By.CSS_SELECTOR, "button[aria-haspopup='dialog']")
                if b_btns:
                    driver.execute_script("arguments[0].click();", b_btns[0])
                    log_print(f"[{browser_id}] ✓ 已点击 b 下 aria-haspopup 按钮")
        except Exception as e:
            log_print(f"[{browser_id}] b 区域操作异常: {e}")
        time.sleep(0.5)

        # 5s 内找 div c: data-side="bottom" data-align="start" data-state="open" role="dialog"
        try:
            c = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-side='bottom'][data-align='start'][data-state='open'][role='dialog']"
                ))
            )
        except TimeoutException:
            log_print(f"[{browser_id}] ✗ 5s 内未找到 dialog c")
            return False

        # c 下找内容为 DEPOSIT_TOKEN 的 div，取父的父并点击（滚动到可视再点）
        opn_divs = c.find_elements(By.XPATH, f".//div[text()='{DEPOSIT_TOKEN}']")
        if not opn_divs:
            opn_divs = c.find_elements(By.XPATH, f".//div[contains(text(), '{DEPOSIT_TOKEN}')]")
        if not opn_divs:
            log_print(f"[{browser_id}] ✗ 在 c 中未找到 {DEPOSIT_TOKEN} div")
            return False
        target_el = opn_divs[0]
        parent_parent = target_el.find_element(By.XPATH, "./../..")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", parent_parent)
        time.sleep(10)
        log_print(f"[{browser_id}] ✓ 已选择 {DEPOSIT_TOKEN}")

        # 重新获取 A
        try:
            a = driver.find_element(By.CSS_SELECTOR, "div[role='dialog']")
        except Exception:
            log_print(f"[{browser_id}] ✗ 无法重新获取 dialog A")
            return False

        opn_in_a = a.find_elements(By.XPATH, f".//div[text()='{DEPOSIT_TOKEN}']")
        if not opn_in_a:
            opn_in_a = a.find_elements(By.XPATH, f".//div[contains(text(), '{DEPOSIT_TOKEN}')]")
        if not opn_in_a:
            log_print(f"[{browser_id}] ✗ A 内无 {DEPOSIT_TOKEN}，任务失败")
            return False

        # A 下点击 Max
        max_btns = a.find_elements(By.XPATH, ".//button[text()='Max']")
        if max_btns:
            driver.execute_script("arguments[0].click();", max_btns[0])
            log_print(f"[{browser_id}] ✓ 已点击 Max")
        time.sleep(0.5)

        # A 内是否有 Approve 按钮
        approve_btns = a.find_elements(By.XPATH, ".//button[.//span[contains(text(), 'Approve')]]")
        if approve_btns:
            driver.execute_script("arguments[0].click();", approve_btns[0])
            log_print(f"[{browser_id}] ✓ 已点击 Approve")
            time.sleep(3)
            if switch_to_okx_window(driver):
                try:
                    unlim = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='unlimited']"))
                    )
                    driver.execute_script("arguments[0].click();", unlim)
                    log_print(f"[{browser_id}] ✓ 已点击 unlimited")
                except TimeoutException:
                    log_print(f"[{browser_id}] ⚠ 10s 内未找到 unlimited div")
                time.sleep(0.5)
                try:
                    time.sleep(3)
                    confirm_btn = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='okd-dialog-confirm-btn']"))
                    )
                    driver.execute_script("arguments[0].click();", confirm_btn)
                    log_print(f"[{browser_id}] ✓ 已点击 okd-dialog-confirm-btn")
                except TimeoutException:
                    log_print(f"[{browser_id}] ⚠ 未找到 okd-dialog-confirm-btn")
                time.sleep(3)
                click_okx_second_button(driver, browser_id, 10)
            driver.switch_to.window(main_window)
            time.sleep(0.5)

        time.sleep(5)
        # A 内 type="submit" 且内容 Deposit 的 button
        try:
            a = driver.find_element(By.CSS_SELECTOR, "div[role='dialog']")
        except Exception:
            log_print(f"[{browser_id}] ✗ 无法获取 dialog A 以点击 Deposit")
            return False
        submit_btns = a.find_elements(By.XPATH, ".//button[@type='submit' and .//span[text()='Deposit']]")
        if submit_btns:
            driver.execute_script("arguments[0].click();", submit_btns[0])
            log_print(f"[{browser_id}] ✓ 已点击 Deposit 提交")
        else:
            log_print(f"[{browser_id}] ✗ 未找到 Deposit 提交按钮")
            return False

        if switch_to_okx_window(driver):
            time.sleep(5)
            click_okx_second_button(driver, browser_id, 10)
        driver.switch_to.window(main_window)
        time.sleep(2)
        log_print(f"[{browser_id}] ✓ Deposit 流程完成")
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


def main():
    global COMPUTER_GROUP
    log_print("=" * 60)
    log_print("Aster DEX Deposit 脚本（独立运行）")
    log_print("=" * 60)

    COMPUTER_GROUP, _, thread_limit = read_computer_config()
    load_fingerprint_mapping()

    #若本地电脑组 > 900，减去 900 得到真实电脑组（用于与服务器数据比较）
    cg_num = int(COMPUTER_GROUP or 0)
    real_group = str(cg_num - 900) if cg_num > 900 else str(COMPUTER_GROUP or "0")
    log_print(f"[系统] 本地电脑组={COMPUTER_GROUP}, 用于筛选的真实电脑组={real_group}")

    items = fetch_account_list_simple()
    if not items:
        log_print("[系统] 无数据，退出")
        return

    bound_numbers = fetch_api_all_bound()
    target = filter_target_items(items, real_group, bound_numbers)
    log_print(f"[系统] 共 {len(items)} 条，已绑定 {len(bound_numbers)} 个，待处理 {len(target)} 条（电脑组={real_group}）")

    # 【测试模式】固定请求：浏览器编号 4001，电脑组 0
    # TEST_BROWSER_NO = "3700"
    # TEST_COMPUTER_GROUP = "0"
    # target = [{"fingerprintNo": TEST_BROWSER_NO, "no": TEST_BROWSER_NO, "computeGroup": TEST_COMPUTER_GROUP}]
    # COMPUTER_GROUP = TEST_COMPUTER_GROUP
    # log_print(f"[系统] 测试模式：固定账号 浏览器编号={TEST_BROWSER_NO}, 电脑组={TEST_COMPUTER_GROUP}")
    if not target:
        log_print("[系统] 无待处理项，退出")
        return

    success, fail = 0, 0
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
