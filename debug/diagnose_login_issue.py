#!/usr/bin/env python3
"""
实时诊断登录页面的问题
"""
import requests
import time

def diagnose_login_issue():
    print("=== 诊断登录页面问题 ===\n")
    
    # 1. 检查API客户端脚本内容
    print("1. 检查API客户端脚本...")
    try:
        response = requests.get("http://localhost:8000/static/js/api-client.js")
        if response.status_code == 200:
            content = response.text
            
            # 检查关键组件
            checks = [
                ('class ApiClient', 'ApiClient类定义'),
                ('const api = new ApiClient()', 'api对象创建'),
                ('window.api = api', '全局api对象导出'),
                ('function showNotification', 'showNotification函数')
            ]
            
            for check, desc in checks:
                if check in content:
                    print(f"  ✓ {desc}")
                else:
                    print(f"  ✗ {desc}缺失")
                    
        else:
            print(f"  ✗ API客户端脚本无法访问: {response.status_code}")
    except Exception as e:
        print(f"  ✗ 无法访问API客户端脚本: {e}")
    
    # 2. 检查登录页面的脚本引用
    print("\n2. 检查登录页面脚本引用...")
    try:
        response = requests.get("http://localhost:8000/login")
        if response.status_code == 200:
            content = response.text
            
            if '/static/js/api-client.js' in content:
                print("  ✓ API客户端脚本引用存在")
            else:
                print("  ✗ API客户端脚本引用缺失")
                
            if 'DOMContentLoaded' in content:
                print("  ✓ DOM事件监听器存在")
            else:
                print("  ✗ DOM事件监听器缺失")
                
        else:
            print(f"  ✗ 登录页面无法访问: {response.status_code}")
    except Exception as e:
        print(f"  ✗ 无法访问登录页面: {e}")
    
    # 3. 测试API端点
    print("\n3. 测试API端点...")
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ API登录成功")
            print(f"    用户: {result['user']['username']}")
            print(f"    Token: {result['access_token'][:20]}...")
        else:
            print(f"  ✗ API登录失败: {response.status_code}")
            print(f"    响应: {response.text}")
    except Exception as e:
        print(f"  ✗ API测试失败: {e}")
    
    print("\n=== 诊断完成 ===")
    print("\n建议的解决方案:")
    print("1. 清除浏览器缓存")
    print("2. 在浏览器中按Ctrl+F5强制刷新页面")
    print("3. 打开开发者工具查看Network标签，检查脚本加载情况")
    print("4. 检查浏览器Console是否有JavaScript错误")

if __name__ == "__main__":
    diagnose_login_issue()