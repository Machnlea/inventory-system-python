#!/usr/bin/env python3
"""
测试空部门删除
"""
import requests
import json

def test_empty_department():
    print("=== 测试空部门删除 ===\n")
    
    # 1. 先登录获取token
    print("1. 获取认证token...")
    try:
        login_response = requests.post(
            "http://localhost:8000/api/auth/login/json",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print("✓ 登录成功，获取到token")
        else:
            print(f"✗ 登录失败: {login_response.status_code}")
            return
    except Exception as e:
        print(f"✗ 登录请求失败: {e}")
        return
    
    # 2. 尝试删除汽摩车间（ID: 4，0台设备）
    print("\n2. 尝试删除汽摩车间（ID: 4，0台设备）...")
    try:
        response = requests.delete("http://localhost:8000/api/departments/4", headers=headers)
        print(f"删除响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✓ 成功删除空部门")
        elif response.status_code == 400:
            print("✓ 正确阻止删除（有设备）")
        else:
            print("✗ 意外错误")
    except Exception as e:
        print(f"✗ 删除请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_empty_department()