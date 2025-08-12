#!/usr/bin/env python3
"""
测试包含调试信息的登录页面
"""
import requests
import json

def test_debug_login():
    """测试调试版本的登录页面"""
    print("=== 测试调试版本的登录页面 ===\n")
    
    # 1. 测试页面加载
    print("1. 测试登录页面加载...")
    try:
        response = requests.get("http://localhost:8000/login")
        if response.status_code == 200:
            print("✓ 登录页面加载成功")
            
            # 检查调试信息
            content = response.text
            debug_checks = [
                ('console.log(\'DOMContentLoaded 事件触发\')', 'DOMContentLoaded事件日志'),
                ('console.log(\'找到登录表单，绑定提交事件\')', '表单查找日志'),
                ('console.log(\'开始发送登录请求...\')', 'API请求日志'),
                ('console.log(\'登录响应:\', response)', '响应日志'),
                ('alert(\'登录成功！用户:\')', '成功提示弹窗')
            ]
            
            for check_text, description in debug_checks:
                if check_text in content:
                    print(f"  ✓ {description}存在")
                else:
                    print(f"  ✗ {description}缺失")
                    
        else:
            print(f"✗ 登录页面加载失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问登录页面: {e}")
    
    # 2. 测试API响应格式
    print("\n2. 测试API响应格式...")
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API响应正常")
            print(f"  响应结构: {list(result.keys())}")
            print(f"  用户信息: {result.get('user', {})}")
            print(f"  Token存在: {'access_token' in result}")
        else:
            print(f"✗ API响应失败: {response.status_code}")
    except Exception as e:
        print(f"✗ API测试失败: {e}")
    
    # 3. 测试仪表盘页面
    print("\n3. 测试仪表盘页面...")
    try:
        response = requests.get("http://localhost:8000/dashboard")
        if response.status_code == 200:
            print("✓ 仪表盘页面可以访问")
        else:
            print(f"✗ 仪表盘页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问仪表盘页面: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n现在请在浏览器中:")
    print("1. 访问: http://localhost:8000/login")
    print("2. 打开开发者工具的控制台面板")
    print("3. 输入账号: admin / admin123")
    print("4. 点击登录按钮")
    print("5. 观察控制台输出和弹窗提示")

if __name__ == "__main__":
    test_debug_login()