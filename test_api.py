"""
API 测试脚本
用于验证步数提交 API 是否正常工作
"""

import requests
import time

API_URL = "http://8.140.250.130/king/api/step"
DEFAULT_AUTH = "5aa77abb20f11a5e7f2440747a655a55"
DEFAULT_TIME = "1772274234275"


def submit_steps(phone, password, steps, auth_token=None, time_token=None):
    """
    提交步数到 API
    
    Args:
        phone: 账号（邮箱或手机号）
        password: 密码
        steps: 目标步数
        auth_token: Authorization token（可选，使用默认值）
        time_token: Time token（可选，使用默认值）
    
    Returns:
        (success: bool, message: str, response_code: int)
    """
    headers = {
        "Host": "8.140.250.130",
        "Accept": "*/*",
        "Authorization": auth_token or DEFAULT_AUTH,
        "X-Requested-With": "XMLHttpRequest",
        "time": time_token or DEFAULT_TIME,
        "Accept-Language": "zh-TW,zh-Hant;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "http://8.140.250.130",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
        "Referer": "http://8.140.250.130/bushu/",
        "Connection": "keep-alive"
    }
    
    data = {
        "phone": phone,
        "pwd": password,
        "num": str(steps)
    }
    
    try:
        print(f"正在提交: 账号={phone}, 步数={steps}")
        response = requests.post(API_URL, headers=headers, data=data, timeout=30)
        result = response.json()
        
        print(f"响应: {result}")
        
        success = result.get('code') == 200 and result.get('msg') == 'success'
        message = result.get('data') or result.get('msg', 'Unknown response')
        response_code = result.get('code', 0)
        
        return success, message, response_code
        
    except requests.exceptions.RequestException as e:
        return False, f"网络请求错误: {str(e)}", 0
    except Exception as e:
        return False, f"未知错误: {str(e)}", 0


def test_default_account():
    """测试默认账号"""
    print("=" * 50)
    print("测试默认账号提交")
    print("=" * 50)
    
    phone = "Tbh2356@163.com"
    password = "112233qq"
    steps = 89888
    
    success, message, code = submit_steps(phone, password, steps)
    
    print(f"\n结果:")
    print(f"  成功: {success}")
    print(f"  消息: {message}")
    print(f"  状态码: {code}")
    
    if success:
        print("\n✓ API 测试通过！")
    else:
        print("\n✗ API 测试失败")
    
    return success


if __name__ == "__main__":
    test_default_account()
