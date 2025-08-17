#!/usr/bin/env python3
"""
测试设备统计API的实际功能（需要认证）
"""

import requests
import json
from datetime import datetime

# 配置请求以绕过代理
session = requests.Session()
session.trust_env = False

def test_with_auth():
    """测试带认证的API调用"""
    print("=== 测试带认证的API调用 ===")
    
    # 首先尝试登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录 - 使用JSON端点
        login_response = session.post("http://localhost:8000/api/auth/login/json", json=login_data)
        if login_response.status_code == 200:
            print("✅ 登录成功")
            token_data = login_response.json()
            token = token_data.get("access_token")
            
            # 设置认证头
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试设备统计API
            print("\n测试设备统计API...")
            
            # 测试不同的排序方式
            sort_options = [
                ("original_value", "desc"),
                ("original_value", "asc"),
                ("name", "asc"),
                ("created_at", "desc")
            ]
            
            for sort_by, sort_order in sort_options:
                print(f"\n--- 测试排序: {sort_by} {sort_order} ---")
                
                url = f"http://localhost:8000/api/reports/equipment-stats?sort_by={sort_by}&sort_order={sort_order}&page=1&page_size=5"
                
                response = session.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API调用成功")
                    print(f"   总设备数: {data.get('statistics', {}).get('total_count', 0)}")
                    print(f"   设备原值总计: {data.get('statistics', {}).get('total_original_value', 0)}")
                    print(f"   平均设备原值: {data.get('statistics', {}).get('avg_original_value', 0)}")
                    
                    # 显示设备列表
                    equipment_list = data.get('equipment_list', [])
                    print(f"   返回设备数: {len(equipment_list)}")
                    
                    if equipment_list:
                        print(f"   前3个设备:")
                        for i, eq in enumerate(equipment_list[:3]):
                            print(f"     {i+1}. {eq.get('name', '未知')} - 原值: {eq.get('original_value', 0)}")
                    
                    # 显示状态分布
                    status_dist = data.get('statistics', {}).get('status_distribution', [])
                    print(f"   状态分布:")
                    for status in status_dist:
                        print(f"     {status.get('status', '未知')}: {status.get('count', 0)}台")
                        
                else:
                    print(f"❌ API调用失败: {response.status_code}")
                    print(f"   错误信息: {response.text}")
                    
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"   错误信息: {login_response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    """主函数"""
    print("设备统计API功能测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_with_auth()
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()