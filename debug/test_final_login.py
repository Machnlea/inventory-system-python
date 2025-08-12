#!/usr/bin/env python3
"""
测试修复后的登录页面
"""
import requests
import json

def test_login_page():
    """测试登录页面是否正确加载"""
    print("=== 测试修复后的登录页面 ===\n")
    
    # 测试登录页面加载
    print("1. 测试登录页面加载...")
    try:
        response = requests.get("http://localhost:8000/login")
        if response.status_code == 200:
            print("✓ 登录页面加载成功")
            
            # 检查关键元素
            content = response.text
            checks = [
                ('login-form', '登录表单'),
                ('username', '用户名输入框'),
                ('password', '密码输入框'),
                ('login-btn', '登录按钮'),
                ('api-client.js', 'API客户端脚本'),
                ('DOMContentLoaded', '事件监听器')
            ]
            
            for check_id, description in checks:
                if check_id in content:
                    print(f"  ✓ {description}存在")
                else:
                    print(f"  ✗ {description}缺失")
                    
            # 检查JavaScript代码结构
            if 'addEventListener(\'submit\'' in content:
                print("  ✓ 表单提交事件绑定正确")
            else:
                print("  ✗ 表单提交事件绑定可能有问题")
                
            if 'typeof api === \'undefined\'' in content:
                print("  ✓ API对象检查逻辑存在")
            else:
                print("  ✗ API对象检查逻辑缺失")
                
        else:
            print(f"✗ 登录页面加载失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问登录页面: {e}")
    
    # 测试API客户端脚本
    print("\n2. 测试API客户端脚本...")
    try:
        response = requests.get("http://localhost:8000/static/js/api-client.js")
        if response.status_code == 200:
            print("✓ API客户端脚本加载成功")
            
            # 检查关键功能
            content = response.text
            checks = [
                ('class ApiClient', 'ApiClient类定义'),
                ('const api = new ApiClient()', '全局api对象'),
                ('window.api = api', 'api对象导出'),
                ('function showNotification', '通知函数'),
                ('async post', 'POST请求方法')
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    print(f"  ✓ {description}存在")
                else:
                    print(f"  ✗ {description}缺失")
                    
        else:
            print(f"✗ API客户端脚本加载失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问API客户端脚本: {e}")
    
    # 测试登录API
    print("\n3. 测试登录API...")
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 登录API正常工作")
            print(f"  用户: {result['user']['username']}")
            print(f"  权限: {'管理员' if result['user']['is_admin'] else '普通用户'}")
        else:
            print(f"✗ 登录API失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 登录API测试失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n现在可以在浏览器中访问以下地址进行测试:")
    print("- 登录页面: http://localhost:8000/login")
    print("- 事件测试: http://localhost:8000/test_events.html")
    print("- 使用账号: admin / admin123")

if __name__ == "__main__":
    test_login_page()