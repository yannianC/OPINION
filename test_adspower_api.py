import requests

ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"

def test_adspower_connection():
    print(f"测试 AdsPower API 连接...")
    print(f"URL: {ADSPOWER_BASE_URL}")
    print(f"API Key: {ADSPOWER_API_KEY}")
    print()
    
    url = f"{ADSPOWER_BASE_URL}/api/v1/user/list"
    headers = {'Authorization': f'Bearer {ADSPOWER_API_KEY}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:1000]}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                browser_list = data.get("list", [])
                print(f"\n找到 {len(browser_list)} 个浏览器:")
                for i, browser in enumerate(browser_list[:5], 1):
                    serial_number = browser.get("serial_number", "N/A")
                    name = browser.get("name", "N/A")
                    status = browser.get("status", "N/A")
                    print(f"  {i}. {name} (SN: {serial_number}, 状态: {status})")
            else:
                print(f"API 返回错误: {result.get('msg')}")
    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    test_adspower_connection()
