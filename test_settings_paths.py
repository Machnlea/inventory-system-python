#!/usr/bin/env python3
"""
测试设置API路径的脚本
"""
import requests
import json

def test_settings_api():
    """测试设置API"""
    base_url = "http://127.0.0.1:8000"
    
    # 测试不同的API路径
    paths_to_test = [
        "/api/settings",
        "/api/system/settings",
        "/api/settings/settings"
    ]
    
    for path in paths_to_test:
        url = base_url + path
        print(f"\n🔍 测试路径: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ 路径存在，但需要认证")
            elif response.status_code == 404:
                print("❌ 路径不存在")
            elif response.status_code == 200:
                print("✅ 路径存在且返回数据")
                print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"⚠️ 其他状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_settings_api()