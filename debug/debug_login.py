#!/usr/bin/env python3
"""
测试登录功能的简化版本
"""
import requests
import json

def test_login():
    """测试登录功能"""
    print("=== 测试登录功能 ===\n")
    
    # 测试数据
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 测试表单登录
        print("1. 测试表单登录...")
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data=login_data
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✓ 表单登录成功")
        else:
            print("✗ 表单登录失败")
            
    except Exception as e:
        print(f"✗ 表单登录请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    try:
        # 测试JSON登录
        print("2. 测试JSON登录...")
        response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✓ JSON登录成功")
        else:
            print("✗ JSON登录失败")
            
    except Exception as e:
        print(f"✗ JSON登录请求失败: {e}")

if __name__ == "__main__":
    test_login()