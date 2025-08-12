#!/usr/bin/env python3
"""
测试类别删除功能
"""
import requests
import json

def test_category_deletion():
    print("=== 测试类别删除功能 ===\n")
    
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
    
    # 2. 检查类别列表
    print("\n2. 检查类别列表...")
    try:
        response = requests.get("http://localhost:8000/api/categories/with-counts", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            print("类别列表:")
            for cat in categories:
                print(f"  ID: {cat['id']}, 名称: {cat['name']}, 设备数量: {cat.get('equipment_count', 0)}")
        else:
            print(f"✗ 获取类别列表失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 获取类别列表失败: {e}")
    
    # 3. 尝试删除第一个有设备的类别
    print("\n3. 尝试删除有设备的类别...")
    try:
        response = requests.get("http://localhost:8000/api/categories/with-counts", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            # 找第一个有设备的类别
            category_with_equipment = next((cat for cat in categories if cat.get('equipment_count', 0) > 0), None)
            if category_with_equipment:
                print(f"尝试删除类别: {category_with_equipment['name']} (ID: {category_with_equipment['id']}, 设备数量: {category_with_equipment['equipment_count']})")
                delete_response = requests.delete(f"http://localhost:8000/api/categories/{category_with_equipment['id']}", headers=headers)
                print(f"删除响应状态: {delete_response.status_code}")
                print(f"响应内容: {delete_response.text}")
            else:
                print("没有找到有设备的类别")
        else:
            print(f"✗ 获取类别列表失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 类别删除测试失败: {e}")
    
    # 4. 尝试创建并删除空类别
    print("\n4. 测试创建和删除空类别...")
    try:
        new_category = {
            "name": "测试删除类别",
            "description": "用于测试删除限制"
        }
        create_response = requests.post(
            "http://localhost:8000/api/categories/",
            json=new_category,
            headers=headers
        )
        
        if create_response.status_code == 200:
            created_cat = create_response.json()
            cat_id = created_cat['id']
            print(f"✓ 创建测试类别成功: {created_cat['name']} (ID: {cat_id})")
            
            # 尝试删除这个空类别
            delete_response = requests.delete(f"http://localhost:8000/api/categories/{cat_id}", headers=headers)
            print(f"删除响应状态: {delete_response.status_code}")
            if delete_response.status_code == 200:
                print("✓ 成功删除空类别")
            else:
                print(f"响应内容: {delete_response.text}")
        else:
            print(f"✗ 创建类别失败: {create_response.status_code}")
            print(f"响应内容: {create_response.text}")
    except Exception as e:
        print(f"✗ 类别操作失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_category_deletion()