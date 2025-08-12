#!/usr/bin/env python3
"""
测试修复后的登录功能
"""
import requests
import json
import time

def test_fixed_login():
    """测试修复后的登录功能"""
    print("=== 测试修复后的登录功能 ===\n")
    
    # 1. 测试API是否正常工作
    print("1. 测试API端点...")
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✓ API服务正常运行")
        else:
            print(f"✗ API服务异常: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 无法连接到API服务: {e}")
        return
    
    # 2. 测试登录API
    print("\n2. 测试登录API...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 登录API正常工作")
            print(f"  用户名: {result['user']['username']}")
            print(f"  管理员权限: {result['user']['is_admin']}")
            print(f"  Token类型: {result['token_type']}")
        else:
            print(f"✗ 登录API失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 登录API请求失败: {e}")
    
    # 3. 测试静态资源
    print("\n3. 测试静态资源...")
    try:
        response = requests.get("http://localhost:8000/static/js/api-client.js")
        if response.status_code == 200:
            print("✓ API客户端JavaScript文件正常")
            print(f"  文件大小: {len(response.text)} 字符")
        else:
            print(f"✗ API客户端文件加载失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问API客户端文件: {e}")
    
    # 4. 测试登录页面
    print("\n4. 测试登录页面...")
    try:
        response = requests.get("http://localhost:8000/login")
        if response.status_code == 200:
            print("✓ 登录页面正常加载")
            if 'api-client.js' in response.text:
                print("✓ 登录页面包含API客户端引用")
            else:
                print("✗ 登录页面缺少API客户端引用")
        else:
            print(f"✗ 登录页面加载失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法访问登录页面: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n现在你可以在浏览器中访问 http://localhost:8000/login 来测试登录功能")
    print("使用用户名: admin, 密码: admin123")

if __name__ == "__main__":
    test_fixed_login()