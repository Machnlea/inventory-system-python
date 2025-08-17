#!/usr/bin/env python3
"""
测试统计报表API端点
"""
import requests
import json
from datetime import datetime, date

# 基础URL
BASE_URL = "http://localhost:8000"

def test_reports_endpoints():
    """测试报表相关API端点"""
    
    # 首先获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录获取token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.status_code}")
            print(login_response.text)
            return
        
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("未获取到访问令牌")
            return
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print("=== 测试统计报表API端点 ===\n")
        
        # 测试报表概览
        print("1. 测试报表概览...")
        overview_response = requests.get(f"{BASE_URL}/api/reports/overview", headers=headers)
        print(f"状态码: {overview_response.status_code}")
        if overview_response.status_code == 200:
            overview_data = overview_response.json()
            print("✅ 报表概览API正常")
            print(f"设备总数: {overview_data.get('overview', {}).get('total_equipment', 0)}")
        else:
            print(f"❌ 报表概览API失败: {overview_response.text}")
        
        print()
        
        # 测试检定统计
        print("2. 测试检定统计...")
        today = date.today()
        start_date = (today.replace(day=1)).isoformat()
        end_date = today.isoformat()
        
        calibration_url = f"{BASE_URL}/api/reports/calibration-stats?start_date={start_date}&end_date={end_date}"
        calibration_response = requests.get(calibration_url, headers=headers)
        print(f"状态码: {calibration_response.status_code}")
        if calibration_response.status_code == 200:
            print("✅ 检定统计API正常")
            calibration_data = calibration_response.json()
            print(f"检定方式数量: {len(calibration_data.get('calibration_methods', []))}")
        else:
            print(f"❌ 检定统计API失败: {calibration_response.text}")
        
        print()
        
        # 测试设备趋势
        print("3. 测试设备趋势...")
        trends_response = requests.get(f"{BASE_URL}/api/reports/equipment-trends?months=6", headers=headers)
        print(f"状态码: {trends_response.status_code}")
        if trends_response.status_code == 200:
            print("✅ 设备趋势API正常")
            trends_data = trends_response.json()
            print(f"趋势数据点数: {len(trends_data.get('trends', []))}")
        else:
            print(f"❌ 设备趋势API失败: {trends_response.text}")
        
        print()
        
        # 测试部门对比
        print("4. 测试部门对比...")
        department_response = requests.get(f"{BASE_URL}/api/reports/department-comparison", headers=headers)
        print(f"状态码: {department_response.status_code}")
        if department_response.status_code == 200:
            print("✅ 部门对比API正常")
            department_data = department_response.json()
            print(f"部门数量: {len(department_data.get('department_comparison', []))}")
        else:
            print(f"❌ 部门对比API失败: {department_response.text}")
        
        print()
        
        # 测试检定记录
        print("5. 测试检定记录...")
        records_url = f"{BASE_URL}/api/reports/calibration-records?page=1&page_size=10"
        records_response = requests.get(records_url, headers=headers)
        print(f"状态码: {records_response.status_code}")
        if records_response.status_code == 200:
            print("✅ 检定记录API正常")
            records_data = records_response.json()
            print(f"记录总数: {records_data.get('total', 0)}")
            print(f"当前页记录数: {len(records_data.get('records', []))}")
        else:
            print(f"❌ 检定记录API失败: {records_response.text}")
        
        print()
        
        # 测试导出功能
        print("6. 测试导出功能...")
        export_url = f"{BASE_URL}/api/reports/export?format=excel"
        export_response = requests.get(export_url, headers=headers)
        print(f"状态码: {export_response.status_code}")
        if export_response.status_code == 200:
            print("✅ 导出API正常")
            print(f"内容类型: {export_response.headers.get('content-type', 'unknown')}")
        else:
            print(f"❌ 导出API失败: {export_response.text}")
        
        print("\n=== 测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用程序正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_reports_endpoints()