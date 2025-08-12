#!/usr/bin/env python3
"""
调试有设备的部门删除
"""
import requests
import json

def debug_equipment_department():
    print("=== 调试有设备的部门删除 ===\n")
    
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
    
    # 2. 检查部门ID为2的详细信息
    print("\n2. 检查工业漆车间（ID: 2）的详细信息...")
    try:
        response = requests.get("http://localhost:8000/api/departments/2", headers=headers)
        if response.status_code == 200:
            department = response.json()
            print(f"部门信息: {department}")
        else:
            print(f"获取部门信息失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 获取部门信息失败: {e}")
    
    # 3. 检查该部门下的设备
    print("\n3. 检查该部门下的设备...")
    try:
        # 通过设备API检查该部门下的设备
        equipment_response = requests.get("http://localhost:8000/api/equipment/", headers=headers)
        if equipment_response.status_code == 200:
            equipment_data = equipment_response.json()
            equipment_list = equipment_data.get('items', []) if isinstance(equipment_data, dict) else equipment_data
            department_equipment = [eq for eq in equipment_list if eq.get('department_id') == 2]
            print(f"该部门下的设备数量: {len(department_equipment)}")
            for eq in department_equipment[:3]:  # 只显示前3个
                print(f"  - {eq.get('name')} (ID: {eq.get('id')})")
        else:
            print(f"获取设备列表失败: {equipment_response.status_code}")
    except Exception as e:
        print(f"✗ 检查设备失败: {e}")
    
    # 4. 尝试删除该部门
    print("\n4. 尝试删除该部门...")
    try:
        response = requests.delete("http://localhost:8000/api/departments/2", headers=headers)
        print(f"删除响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 删除请求失败: {e}")
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    debug_equipment_department()