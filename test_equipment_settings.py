#!/usr/bin/env python3
"""
测试设备管理页面设置功能
"""
import requests
import json

def test_equipment_settings():
    base_url = "http://localhost:8000"
    
    # 测试token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1NTM1MjcxOH0.4xkkQx09iuiMTzKm_NSWoRmUsPyT8_ZwMX_437j2QM4"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔧 测试设备管理页面设置功能")
    print("=" * 50)
    
    # 1. 先设置一个不同的值
    print("\n1️⃣ 设置每页显示条数为20...")
    try:
        settings = {"pageSize": 20}
        response = requests.put(f"{base_url}/api/settings/", headers=headers, json=settings)
        if response.status_code == 200:
            print("✅ 设置成功")
        else:
            print(f"❌ 设置失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 设置异常: {e}")
        return
    
    # 2. 验证设置是否保存
    print("\n2️⃣ 验证设置是否保存...")
    try:
        response = requests.get(f"{base_url}/api/settings/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            saved_page_size = data.get('data', {}).get('pageSize', 10)
            print(f"✅ 保存的每页显示条数: {saved_page_size}")
        else:
            print(f"❌ 获取设置失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取设置异常: {e}")
    
    # 3. 测试设备API是否能正确使用设置
    print("\n3️⃣ 测试设备API分页...")
    try:
        # 测试默认分页
        response = requests.get(f"{base_url}/api/equipment/?skip=0&limit=20", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 设备API响应正常")
            print(f"   - 总设备数: {data.get('total', 0)}")
            print(f"   - 当前页设备数: {len(data.get('equipment', []))}")
            print(f"   - 请求的limit: 20")
        else:
            print(f"❌ 设备API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 设备API异常: {e}")
    
    # 4. 测试设备管理页面访问
    print("\n4️⃣ 测试设备管理页面访问...")
    try:
        response = requests.get(f"{base_url}/equipment")
        print(f"✅ 设备管理页面状态码: {response.status_code}")
        
        # 检查页面内容
        if response.status_code == 200:
            content = response.text
            if 'api-client.js?v=20240816-2' in content:
                print("✅ 设备管理页面使用了正确的JavaScript版本")
            else:
                print("❌ 设备管理页面JavaScript版本可能不正确")
                
    except Exception as e:
        print(f"❌ 设备管理页面访问异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！")
    print("\n📋 使用说明:")
    print("1. 访问设备管理页面: http://localhost:8000/equipment")
    print("2. 检查分页是否显示20条/页")
    print("3. 如果仍显示10条，请清除浏览器缓存后重试")

if __name__ == "__main__":
    test_equipment_settings()