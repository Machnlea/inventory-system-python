#!/usr/bin/env python3
"""
测试设备类别管理功能
"""
import requests
import json
import time

# 服务器配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_categories_api():
    """测试设备类别API功能"""
    print("=== 测试设备类别管理功能 ===\n")
    
    # 1. 先登录获取token
    print("1. 登录系统...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            print("✓ 登录成功")
        else:
            print(f"✗ 登录失败: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 登录请求失败: {e}")
        return
    
    # 2. 测试获取类别列表
    print("\n2. 测试获取类别列表...")
    try:
        response = requests.get(f"{API_BASE}/categories/with-counts", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            print(f"✓ 获取类别列表成功，共 {len(categories)} 个类别")
            for cat in categories:
                print(f"  - {cat['name']}: {cat.get('equipment_count', 0)} 台设备")
        else:
            print(f"✗ 获取类别列表失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 获取类别列表请求失败: {e}")
    
    # 3. 测试创建新类别
    print("\n3. 测试创建新类别...")
    new_category = {
        "name": f"测试类别_{int(time.time())}",
        "description": "这是一个测试类别"
    }
    
    try:
        response = requests.post(f"{API_BASE}/categories/", json=new_category, headers=headers)
        if response.status_code == 200:
            created_category = response.json()
            category_id = created_category["id"]
            print(f"✓ 创建类别成功: {created_category['name']} (ID: {category_id})")
            
            # 4. 测试更新类别
            print("\n4. 测试更新类别...")
            updated_data = {
                "name": f"{created_category['name']}_更新",
                "description": "这是更新后的描述"
            }
            
            response = requests.put(f"{API_BASE}/categories/{category_id}", json=updated_data, headers=headers)
            if response.status_code == 200:
                updated_category = response.json()
                print(f"✓ 更新类别成功: {updated_category['name']}")
            else:
                print(f"✗ 更新类别失败: {response.status_code}")
            
            # 5. 测试删除类别
            print("\n5. 测试删除类别...")
            response = requests.delete(f"{API_BASE}/categories/{category_id}", headers=headers)
            if response.status_code == 200:
                print(f"✓ 删除类别成功")
            else:
                print(f"✗ 删除类别失败: {response.status_code}")
                
        else:
            print(f"✗ 创建类别失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 创建类别请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_categories_api()