import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from auto_trader import process_type21_withdraw_and_send, log_print, ADSPOWER_BASE_URL, ADSPOWER_API_KEY

ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"

def start_adspower_browser(serial_number):
    """
    启动 AdsPower 浏览器
    
    Args:
        serial_number: 浏览器编号
        
    Returns:
        dict: 浏览器数据，包含 webdriver 路径和 ws 地址
    """
    import json
    
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/start"
    params = {
        "serial_number": serial_number,
        "user_id": "",
        "open_tabs": 1,
    }
    launch_args = [f"--window-size={1500},{1700}"]
    params["launch_args"] = json.dumps(launch_args)
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            data = result.get("data", {})
            log_print(f"[{serial_number}] ✓ 浏览器启动成功")
            return data
        else:
            log_print(f"[{serial_number}] ✗ 浏览器启动失败: {result.get('msg')}")
            return None
    else:
        log_print(f"[{serial_number}] ✗ 请求失败: {response.status_code}")
        return None


def create_selenium_driver(browser_data):
    """
    创建 Selenium WebDriver
    
    Args:
        browser_data: AdsPower 返回的浏览器数据
        
    Returns:
        WebDriver: Selenium 驱动对象
    """
    chrome_driver = browser_data.get("webdriver")
    debugger_address = browser_data.get("ws", {}).get("selenium")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", debugger_address)
    
    service = Service(executable_path=chrome_driver)
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.set_page_load_timeout(75)
    driver.set_script_timeout(75)
    
    return driver


def get_browser_list():
    """获取 AdsPower 浏览器列表"""
    url = f"{ADSPOWER_BASE_URL}/api/v1/user/list"
    params = {"page_size": 100}  # 获取最多100个浏览器
    headers = {'Authorization': f'Bearer {ADSPOWER_API_KEY}'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                return result.get("data", {}).get("list", [])
    except Exception as e:
        log_print(f"获取浏览器列表失败: {e}")
    return []


def test_type21(serial_number, tp3_value=None):
    """
    测试 Type 21 函数
    
    Args:
        serial_number: AdsPower 浏览器编号
        tp3_value: None=完整流程, "1"=只提现到OKX, "2"=只从OKX转入新钱包
    """
    driver = None
    browser_data = None
    
    try:
        log_print("=" * 60)
        log_print(f"开始测试 Type 21, 浏览器: {serial_number}, tp3={tp3_value}")
        log_print("=" * 60)
        
        browser_id = serial_number
        
        mission = {
            "tp1": "1000",
            "tp2": "500",
            "tp3": tp3_value
        }
        
        portfolio_value = "$1,500.00"
        balance_value = "$600.00"
        
        log_print(f"\n测试参数:")
        log_print(f"  portfolio: {portfolio_value}")
        log_print(f"  balance: {balance_value}")
        log_print(f"  tp1 (目标保留): {mission['tp1']}")
        log_print(f"  tp2 (最小转出): {mission['tp2']}")
        log_print(f"  tp3 (流程控制): {mission['tp3']}")
        
        log_print(f"\n[1] 启动 AdsPower 浏览器...")
        browser_data = start_adspower_browser(serial_number)
        
        if not browser_data:
            log_print("✗ 浏览器启动失败")
            return
        
        log_print(f"[2] 连接 Selenium WebDriver...")
        driver = create_selenium_driver(browser_data)
        
        # 等待浏览器完全启动
        log_print(f"  等待浏览器初始化...")
        time.sleep(3)
        
        log_print(f"[3] 自动打开 Profile 页面...")
        profile_url = "https://app.opinion.trade/profile"
        
        # 尝试多次导航到目标页面
        for attempt in range(3):
            try:
                driver.get(profile_url)
                log_print(f"  导航尝试 {attempt + 1}/3...")
                time.sleep(5)
                
                current_url = driver.current_url
                log_print(f"  当前页面: {current_url}")
                
                if 'profile' in current_url or 'opinion.trade' in current_url:
                    break
                elif attempt < 2:
                    log_print(f"  页面未跳转，重试...")
                    time.sleep(2)
            except Exception as e:
                log_print(f"  导航出错: {e}")
                if attempt < 2:
                    time.sleep(2)
        
        log_print(f"[4] 等待页面加载...")
        time.sleep(3)
        
        current_url = driver.current_url
        log_print(f"[5] 当前页面: {current_url}")
        
        # 检查是否在登录页面
        if 'login' in current_url:
            log_print(f"\n⚠ 当前在登录页面，需要手动登录")
            log_print(f"  请在浏览器中完成登录操作")
            input("\n  登录完成后按回车键继续...")
            
            # 登录后重新导航到 profile
            log_print(f"  重新导航到 Profile 页面...")
            driver.get(profile_url)
            time.sleep(5)
            current_url = driver.current_url
            log_print(f"  当前页面: {current_url}")
        
        if 'profile' not in current_url and 'opinion.trade' not in current_url:
            log_print(f"\n⚠ 页面未正确加载，请检查:")
            log_print(f"  1. 浏览器是否已登录")
            log_print(f"  2. 网络连接是否正常")
            log_print(f"  3. 是否需要手动登录")
            input("\n  完成后按回车键继续...")
        else:
            log_print(f"\n✓ Profile 页面已加载")
            
            # 检测并点击条款同意弹窗
            log_print(f"[6] 检测条款同意弹窗...")
            try:
                # 等待2秒让弹窗出现
                time.sleep(2)
                
                # 查找 "I Understand and Agree" 按钮
                agree_button = None
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    button_text = button.text.strip()
                    if "Understand" in button_text or "Agree" in button_text or "同意" in button_text:
                        agree_button = button
                        log_print(f"  ✓ 找到同意按钮: {button_text}")
                        break
                
                if agree_button:
                    agree_button.click()
                    log_print(f"  ✓ 已点击同意按钮")
                    time.sleep(2)
                else:
                    log_print(f"  ℹ 未检测到条款弹窗，跳过")
            except Exception as e:
                log_print(f"  ℹ 检测条款弹窗出错: {e}")
            
            # 检查是否需要连接钱包
            log_print(f"[7] 检查是否需要连接钱包...")
            connect_wallet_button = None
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if "Connect" in button.text or "connect" in button.text.lower():
                        connect_wallet_button = button
                        log_print(f"  ✓ 找到连接钱包按钮: {button.text}")
                        break
            except:
                pass
            
            if connect_wallet_button:
                log_print(f"  → 点击连接钱包按钮...")
                connect_wallet_button.click()
                time.sleep(2)
                
                # 查找 OKX Wallet 选项
                log_print(f"  → 查找 OKX Wallet 选项...")
                try:
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    for p in p_tags:
                        if "OKX" in p.text or "okx" in p.text.lower():
                            log_print(f"  ✓ 找到 OKX Wallet 选项")
                            # 点击父节点的父节点
                            parent_parent = p.find_element(By.XPATH, "../..")
                            parent_parent.click()
                            log_print(f"  ✓ 已点击 OKX Wallet")
                            time.sleep(3)
                            break
                except Exception as e:
                    log_print(f"  ⚠ 选择 OKX Wallet 失败: {e}")
                
                log_print(f"  ⚠ 请在弹出的 OKX 钱包窗口中确认连接")
                input("  连接完成后按回车键继续...")
            else:
                log_print(f"  ✓ 钱包已连接")
            
            time.sleep(2)
        
        success, reason = process_type21_withdraw_and_send(
            driver, browser_id, mission, portfolio_value, balance_value
        )
        
        if success:
            log_print(f"\n{'='*60}")
            log_print(f"✓ 测试成功!")
            log_print(f"{'='*60}")
        else:
            log_print(f"\n{'='*60}")
            log_print(f"✗ 测试失败: {reason}")
            log_print(f"{'='*60}")
            
        input("\n按回车键关闭浏览器...")
            
    except Exception as e:
        log_print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        log_print("浏览器已关闭")


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║            Type 21 测试脚本 - AdsPower 指纹浏览器           ║
╠════════════════════════════════════════════════════════════╣
║  测试模式:                                                  ║
║    1. 完整流程 (tp3=None) - 提现到OKX + 转账到新钱包       ║
║    2. 只提现到OKX (tp3="1")                                ║
║    3. 只从OKX转入新钱包 (tp3="2")                          ║
║    4. 查看可用浏览器列表                                    ║
║    5. 退出                                                  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    browser_list = get_browser_list()
    if browser_list:
        print("\n可用浏览器列表:")
        for i, browser in enumerate(browser_list[:10], 1):
            serial_number = browser.get("serial_number", "N/A")
            name = browser.get("name", "N/A")
            status = browser.get("status", "N/A")
            print(f"  {i}. {name} (SN: {serial_number}, 状态: {status})")
    else:
        print("\n⚠ 无法获取浏览器列表，请确保 AdsPower 已启动")
    
    try:
        choice = input("\n请输入选项 (1-5): ").strip()
    except:
        choice = "5"
    
    if choice == "5":
        print("退出")
        return
    
    if choice == "4":
        print("\n可用浏览器列表:")
        for i, browser in enumerate(browser_list, 1):
            serial_number = browser.get("serial_number", "N/A")
            name = browser.get("name", "N/A")
            status = browser.get("status", "N/A")
            print(f"  {i}. {name} (SN: {serial_number}, 状态: {status})")
        return
    
    serial_number = input("请输入浏览器编号 (serial_number): ").strip()
    if not serial_number:
        print("✗ 浏览器编号不能为空")
        return
    
    tp3_map = {
        "1": None,
        "2": "1",
        "3": "2"
    }
    
    if choice in tp3_map:
        test_type21(serial_number, tp3_map[choice])
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
