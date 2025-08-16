#!/usr/bin/env python3
"""
测试设置API的脚本
"""
import requests
import json

def test_settings_api():
    base_url = "http://localhost:8000"
    
    # 测试获取设置（不需要认证）
    print("测试获取设置API...")
    try:
        response = requests.get(f"{base_url}/api/settings")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试重置设置（不需要认证）
    print("\n测试重置设置API...")
    try:
        response = requests.post(f"{base_url}/api/settings/reset")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_settings_api()