#!/usr/bin/env python3
"""
简单测试删除功能
"""
import requests
import json

def simple_test():
    print("=== 简单测试删除功能 ===\n")
    
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
    
    # 2. 检查部门列表
    print("\n2. 检查部门列表...")
    try:
        response = requests.get("http://localhost:8000/api/departments/with-counts", headers=headers)
        if response.status_code == 200:
            departments = response.json()
            print("部门列表:")
            for dept in departments:
                print(f"  ID: {dept['id']}, 名称: {dept['name']}, 设备数量: {dept.get('equipment_count', 0)}")
        else:
            print(f"✗ 获取部门列表失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 获取部门列表失败: {e}")
    
    # 3. 尝试删除ID为2的部门
    print("\n3. 尝试删除ID为2的部门...")
    try:
        response = requests.delete("http://localhost:8000/api/departments/2", headers=headers)
        print(f"删除响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 删除请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    simple_test()