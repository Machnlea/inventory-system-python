#!/usr/bin/env python3
"""
调试删除限制功能
"""
import requests
import json

def debug_deletion():
    print("=== 调试删除限制功能 ===\n")
    
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
    
    # 2. 创建一个测试部门
    print("\n2. 创建测试部门...")
    try:
        new_department = {
            "name": "测试删除部门",
            "description": "用于测试删除限制"
        }
        response = requests.post(
            "http://localhost:8000/api/departments/",
            json=new_department,
            headers=headers
        )
        
        if response.status_code == 200:
            created_dept = response.json()
            dept_id = created_dept['id']
            print(f"✓ 创建测试部门成功: {created_dept['name']} (ID: {dept_id})")
            
            # 3. 尝试删除这个空部门
            print("\n3. 尝试删除空部门...")
            delete_response = requests.delete(f"http://localhost:8000/api/departments/{dept_id}", headers=headers)
            print(f"删除响应状态: {delete_response.status_code}")
            if delete_response.status_code == 200:
                print("✓ 成功删除空部门")
            else:
                print(f"响应内容: {delete_response.text}")
        else:
            print(f"✗ 创建部门失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 部门操作失败: {e}")
    
    # 4. 测试删除有设备的部门（工业漆车间）
    print("\n4. 测试删除有设备的部门（工业漆车间）...")
    try:
        response = requests.delete("http://localhost:8000/api/departments/2", headers=headers)
        print(f"删除响应状态: {response.status_code}")
        if response.status_code == 400:
            error_detail = response.json().get('detail', '')
            print(f"✓ 正确阻止删除: {error_detail}")
        elif response.status_code == 200:
            print("✗ 错误：允许删除有设备的部门")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 删除请求失败: {e}")
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    debug_deletion()