#!/usr/bin/env python3
"""
测试部门管理功能
"""
import requests
import json

def test_departments():
    print("=== 测试部门管理功能 ===\n")
    
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
    
    # 2. 测试获取部门列表
    print("\n2. 测试获取部门列表...")
    try:
        response = requests.get("http://localhost:8000/api/departments/", headers=headers)
        if response.status_code == 200:
            departments = response.json()
            print(f"✓ 获取部门列表成功，共 {len(departments)} 个部门")
            for dept in departments:
                print(f"  - {dept['name']} (ID: {dept['id']})")
        else:
            print(f"✗ 获取部门列表失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 获取部门列表请求失败: {e}")
    
    # 3. 测试获取部门统计
    print("\n3. 测试获取部门统计...")
    try:
        response = requests.get("http://localhost:8000/api/departments/with-counts", headers=headers)
        if response.status_code == 200:
            departments_with_counts = response.json()
            print(f"✓ 获取部门统计成功，共 {len(departments_with_counts)} 个部门")
            for dept in departments_with_counts:
                equipment_count = dept.get('equipment_count', 0)
                print(f"  - {dept['name']}: {equipment_count} 台设备")
        else:
            print(f"✗ 获取部门统计失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 获取部门统计请求失败: {e}")
    
    # 4. 测试创建部门
    print("\n4. 测试创建部门...")
    try:
        new_department = {
            "name": "测试部门",
            "description": "这是一个测试部门"
        }
        response = requests.post(
            "http://localhost:8000/api/departments/",
            json=new_department,
            headers=headers
        )
        
        if response.status_code == 200:
            created_dept = response.json()
            print(f"✓ 创建部门成功: {created_dept['name']} (ID: {created_dept['id']})")
            
            # 5. 测试更新部门
            print("\n5. 测试更新部门...")
            updated_data = {
                "name": "更新后的测试部门",
                "description": "这是更新后的描述"
            }
            update_response = requests.put(
                f"http://localhost:8000/api/departments/{created_dept['id']}",
                json=updated_data,
                headers=headers
            )
            
            if update_response.status_code == 200:
                updated_dept = update_response.json()
                print(f"✓ 更新部门成功: {updated_dept['name']}")
                
                # 6. 测试删除部门
                print("\n6. 测试删除部门...")
                delete_response = requests.delete(
                    f"http://localhost:8000/api/departments/{created_dept['id']}",
                    headers=headers
                )
                
                if delete_response.status_code == 200:
                    print("✓ 删除部门成功")
                else:
                    print(f"✗ 删除部门失败: {delete_response.status_code}")
            else:
                print(f"✗ 更新部门失败: {update_response.status_code}")
        else:
            print(f"✗ 创建部门失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 部门CRUD操作失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n部门管理功能测试完成！")
    print("现在可以在浏览器中访问: http://localhost:8000/departments")

if __name__ == "__main__":
    test_departments()