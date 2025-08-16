#!/usr/bin/env python3
"""
调试API路径问题
"""
import requests

def debug_api_paths():
    base_url = "http://localhost:8000"
    
    # 测试token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1NTM1MjcxOH0.4xkkQx09iuiMTzKm_NSWoRmUsPyT8_ZwMX_437j2QM4"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试路径
    paths = [
        "/api/settings/",
        "/api/settings",
        "/api/system/settings"
    ]
    
    print("🔍 调试API路径")
    print("=" * 50)
    
    for path in paths:
        url = base_url + path
        print(f"\n📍 测试路径: {path}")
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ 路径存在，需要认证")
            elif response.status_code == 404:
                print("❌ 路径不存在")
            elif response.status_code == 200:
                print("✅ 路径存在且返回数据")
                try:
                    data = response.json()
                    print(f"响应数据: {data}")
                except:
                    print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"⚠️ 其他状态码: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    debug_api_paths()