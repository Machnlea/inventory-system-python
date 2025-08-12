#!/usr/bin/env python3
"""
测试批量更新检定日期功能的脚本
"""
import requests
import json
from datetime import datetime

# 服务器地址
BASE_URL = "http://localhost:8000"

def test_batch_update_calibration():
    """测试批量更新检定日期功能"""
    
    # 首先登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.status_code} - {login_response.text}")
            return False
        
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("登录响应中没有access_token")
            return False
        
        print("登录成功")
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 测试批量更新检定日期
        test_data = {
            "equipment_ids": [1, 2],  # 假设有设备ID为1和2的设备
            "calibration_date": "2024-01-15"
        }
        
        print("测试批量更新检定日期...")
        update_response = requests.post(
            f"{BASE_URL}/api/equipment/batch/update-calibration",
            json=test_data,
            headers=headers
        )
        
        print(f"响应状态码: {update_response.status_code}")
        print(f"响应内容: {update_response.text}")
        
        if update_response.status_code == 200:
            result = update_response.json()
            print(f"批量更新结果: {result}")
            return True
        else:
            print(f"批量更新失败: {update_response.status_code} - {update_response.text}")
            return False
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("开始测试批量更新检定日期功能...")
    success = test_batch_update_calibration()
    if success:
        print("测试成功！")
    else:
        print("测试失败！")