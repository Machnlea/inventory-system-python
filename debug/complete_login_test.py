#!/usr/bin/env python3
"""
完整的登录功能测试
"""
import requests
import json
import time

def complete_login_test():
    """完整的登录功能测试"""
    print("=== 完整的登录功能测试 ===\n")
    
    # 1. 测试原始登录页面
    print("1. 测试原始登录页面...")
    try:
        response = requests.get("http://localhost:8000/login")
        if response.status_code == 200:
            print("✓ 登录页面加载成功")
            
            # 检查关键元素
            content = response.text
            if 'console.log' in content:
                print("✓ 包含调试日志")
            if 'alert(' in content:
                print("✓ 包含弹窗提示")
            if 'DOMContentLoaded' in content:
                print("✓ 包含事件监听器")
        else:
            print(f"✗ 登录页面加载失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问登录页面: {e}")
    
    # 2. 测试API登录
    print("\n2. 测试API登录...")
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API登录成功")
            print(f"  用户: {result['user']['username']}")
            print(f"  管理员: {result['user']['is_admin']}")
            print(f"  Token: {result['access_token'][:20]}...")
            
            # 使用token测试其他API
            token = result['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取用户信息
            user_response = requests.get("http://localhost:8000/api/auth/me", headers=headers)
            if user_response.status_code == 200:
                user_info = user_response.json()
                print(f"  用户信息API: {user_info['username']}")
            else:
                print(f"  用户信息API失败: {user_response.status_code}")
                
        else:
            print(f"✗ API登录失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ API登录测试失败: {e}")
    
    # 3. 测试仪表盘访问
    print("\n3. 测试仪表盘访问...")
    try:
        response = requests.get("http://localhost:8000/dashboard")
        if response.status_code == 200:
            print("✓ 仪表盘页面可以访问")
        else:
            print(f"✗ 仪表盘页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问仪表盘页面: {e}")
    
    # 4. 测试静态资源
    print("\n4. 测试静态资源...")
    try:
        response = requests.get("http://localhost:8000/static/js/api-client.js")
        if response.status_code == 200:
            print("✓ API客户端脚本可访问")
            content = response.text
            if 'class ApiClient' in content:
                print("✓ ApiClient类定义存在")
            if 'const api = new ApiClient()' in content:
                print("✓ 全局api对象创建存在")
            if 'function showNotification' in content:
                print("✓ showNotification函数存在")
        else:
            print(f"✗ API客户端脚本访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问API客户端脚本: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n现在请在浏览器中:")
    print("1. 访问: http://localhost:8000/login")
    print("2. 打开开发者工具 (F12)")
    print("3. 切换到 Console 标签")
    print("4. 输入用户名: admin")
    print("5. 输入密码: admin123")
    print("6. 点击登录按钮")
    print("7. 观察控制台输出和页面反应")
    
    print("\n预期结果:")
    print("- 控制台应该显示多个调试日志")
    print("- 应该弹出成功提示框")
    print("- 1秒后应该跳转到仪表盘页面")

if __name__ == "__main__":
    complete_login_test()