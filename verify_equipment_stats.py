#!/usr/bin/env python3
"""
验证设备统计报表功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

# 配置请求以绕过代理
session = requests.Session()
session.trust_env = False  # 禁用环境变量中的代理设置

def test_equipment_stats_api():
    """测试设备统计API"""
    print("=== 测试设备统计API ===")
    
    try:
        # 测试不同的排序方式
        sort_options = [
            ("original_value", "desc"),
            ("original_value", "asc"),
            ("name", "asc"),
            ("created_at", "desc")
        ]
        
        for sort_by, sort_order in sort_options:
            print(f"\n测试排序: {sort_by} {sort_order}")
            
            url = f"http://127.0.0.1:8000/api/reports/equipment-stats?sort_by={sort_by}&sort_order={sort_order}"
            
            response = session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API调用成功")
                print(f"   总设备数: {data.get('statistics', {}).get('total_count', 0)}")
                print(f"   设备原值总计: {data.get('statistics', {}).get('total_original_value', 0)}")
                print(f"   平均设备原值: {data.get('statistics', {}).get('avg_original_value', 0)}")
                
                # 显示前3个设备
                equipment_list = data.get('equipment_list', [])
                if equipment_list:
                    print(f"   前3个设备:")
                    for i, eq in enumerate(equipment_list[:3]):
                        print(f"     {i+1}. {eq.get('name', '未知')} - 原值: {eq.get('original_value', 0)}")
                
            else:
                print(f"❌ API调用失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_reports_page():
    """测试reports页面访问"""
    print("\n=== 测试Reports页面访问 ===")
    
    try:
        response = session.get("http://127.0.0.1:8000/reports")
        
        if response.status_code == 200:
            print("✅ Reports页面访问成功")
            
            # 检查页面内容
            content = response.text
            if "设备统计" in content:
                print("✅ 页面包含设备统计相关内容")
            if "设备原值" in content:
                print("✅ 页面包含设备原值相关内容")
            if "排序方式" in content:
                print("✅ 页面包含排序功能")
                
        else:
            print(f"❌ Reports页面访问失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_api_client():
    """测试API客户端功能"""
    print("\n=== 测试API客户端功能 ===")
    
    try:
        # 测试API客户端js文件
        response = session.get("http://127.0.0.1:8000/static/js/api-client.js")
        
        if response.status_code == 200:
            print("✅ API客户端JS文件访问成功")
            
            # 检查是否包含设备统计相关方法
            content = response.text
            if "getEquipmentStats" in content:
                print("✅ API客户端包含getEquipmentStats方法")
            if "original_value" in content:
                print("✅ API客户端包含设备原值相关代码")
                
        else:
            print(f"❌ API客户端JS文件访问失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    """主函数"""
    print("开始验证设备统计报表功能...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行测试
    test_reports_page()
    test_api_client()
    test_equipment_stats_api()
    
    print("\n=== 测试完成 ===")
    print("如果所有测试都通过，说明设备统计报表功能已正确实现。")

if __name__ == "__main__":
    main()