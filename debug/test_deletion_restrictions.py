#!/usr/bin/env python3
"""
测试删除限制功能
"""
import requests
import json

def test_deletion_restrictions():
    print("=== 测试删除限制功能 ===\n")
    
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
    
    # 2. 测试删除有设备的部门（工业漆车间，有8台设备）
    print("\n2. 测试删除有设备的部门...")
    try:
        response = requests.delete("http://localhost:8000/api/departments/2", headers=headers)
        if response.status_code == 400:
            error_detail = response.json().get('detail', '')
            print(f"✓ 正确阻止删除有设备的部门: {error_detail}")
        elif response.status_code == 200:
            print("✗ 错误：允许删除有设备的部门")
        else:
            print(f"✗ 意外响应: {response.status_code}")
    except Exception as e:
        print(f"✗ 删除请求失败: {e}")
    
    # 3. 测试删除没有设备的部门（防腐车间，有0台设备）
    print("\n3. 测试删除没有设备的部门...")
    try:
        response = requests.delete("http://localhost:8000/api/departments/3", headers=headers)
        if response.status_code == 200:
            print("✓ 成功删除没有设备的部门")
        elif response.status_code == 400:
            error_detail = response.json().get('detail', '')
            print(f"✗ 意外阻止删除: {error_detail}")
        else:
            print(f"✗ 意外响应: {response.status_code}")
    except Exception as e:
        print(f"✗ 删除请求失败: {e}")
    
    # 4. 测试删除有设备的类别
    print("\n4. 测试删除有设备的类别...")
    try:
        # 先获取类别列表，找一个有设备的类别
        categories_response = requests.get("http://localhost:8000/api/categories/with-counts", headers=headers)
        if categories_response.status_code == 200:
            categories = categories_response.json()
            # 找第一个有设备的类别
            category_with_equipment = next((cat for cat in categories if cat.get('equipment_count', 0) > 0), None)
            if category_with_equipment:
                response = requests.delete(f"http://localhost:8000/api/categories/{category_with_equipment['id']}", headers=headers)
                if response.status_code == 400:
                    error_detail = response.json().get('detail', '')
                    print(f"✓ 正确阻止删除有设备的类别: {error_detail}")
                elif response.status_code == 200:
                    print("✗ 错误：允许删除有设备的类别")
                else:
                    print(f"✗ 意外响应: {response.status_code}")
            else:
                print("✗ 没有找到有设备的类别")
        else:
            print(f"✗ 获取类别列表失败: {categories_response.status_code}")
    except Exception as e:
        print(f"✗ 类别删除测试失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("删除限制功能测试完成！")

if __name__ == "__main__":
    test_deletion_restrictions()