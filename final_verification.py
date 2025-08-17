#!/usr/bin/env python3
"""
设备统计报表功能完整性验证
"""

import requests
import json
from datetime import datetime

# 配置请求以绕过代理
session = requests.Session()
session.trust_env = False  # 禁用环境变量中的代理设置

def verify_system_status():
    """验证系统状态"""
    print("=== 系统状态验证 ===")
    
    try:
        # 测试主页
        response = session.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            print("✅ 系统主页正常访问")
        else:
            print(f"❌ 系统主页访问失败: {response.status_code}")
            
        # 测试reports页面
        response = session.get("http://127.0.0.1:8000/reports")
        if response.status_code == 200:
            print("✅ Reports页面正常访问")
        else:
            print(f"❌ Reports页面访问失败: {response.status_code}")
            
        # 测试API客户端文件
        response = session.get("http://127.0.0.1:8000/static/js/api-client.js")
        if response.status_code == 200:
            print("✅ API客户端文件正常访问")
        else:
            print(f"❌ API客户端文件访问失败: {response.status_code}")
            
        # 测试设备统计API（预期401）
        response = session.get("http://127.0.0.1:8000/api/reports/equipment-stats")
        if response.status_code == 401:
            print("✅ 设备统计API需要认证（安全机制正常）")
        else:
            print(f"⚠️  设备统计API认证状态异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 系统状态验证失败: {str(e)}")

def verify_page_content():
    """验证页面内容"""
    print("\n=== 页面内容验证 ===")
    
    try:
        response = session.get("http://127.0.0.1:8000/reports")
        content = response.text
        
        # 检查关键内容
        checks = [
            ("设备统计", "页面标题正确"),
            ("设备原值", "包含设备原值相关内容"),
            ("排序方式", "包含排序功能"),
            ("getEquipmentStats", "包含设备统计API调用"),
            ("original_value", "包含设备原值字段"),
            ("chart", "包含图表功能"),
            ("equipment-list", "包含设备列表功能")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description}")
            else:
                print(f"❌ 缺少: {description}")
                
    except Exception as e:
        print(f"❌ 页面内容验证失败: {str(e)}")

def verify_api_client():
    """验证API客户端"""
    print("\n=== API客户端验证 ===")
    
    try:
        response = session.get("http://127.0.0.1:8000/static/js/api-client.js")
        content = response.text
        
        # 检查关键方法
        checks = [
            ("getEquipmentStats", "设备统计API方法"),
            ("original_value", "设备原值字段"),
            ("sort_by", "排序功能"),
            ("sort_order", "排序方向"),
            ("equipment-stats", "设备统计API端点")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description}")
            else:
                print(f"❌ 缺少: {description}")
                
    except Exception as e:
        print(f"❌ API客户端验证失败: {str(e)}")

def verify_backend_api():
    """验证后端API"""
    print("\n=== 后端API验证 ===")
    
    try:
        # 读取reports.py文件
        with open("app/api/reports.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查关键功能
        checks = [
            ("equipment-stats", "设备统计API端点"),
            ("get_equipment_stats", "设备统计处理函数"),
            ("original_value", "设备原值排序"),
            ("sort_by", "排序参数"),
            ("sort_order", "排序方向"),
            ("pagination", "分页功能"),
            ("statistics", "统计数据"),
            ("total_original_value", "原值总计"),
            ("avg_original_value", "平均原值")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description}")
            else:
                print(f"❌ 缺少: {description}")
                
    except Exception as e:
        print(f"❌ 后端API验证失败: {str(e)}")

def main():
    """主函数"""
    print("设备统计报表功能完整性验证")
    print("=" * 50)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行验证
    verify_system_status()
    verify_page_content()
    verify_api_client()
    verify_backend_api()
    
    print("\n" + "=" * 50)
    print("验证完成！")
    print("\n说明:")
    print("1. ✅ 表示功能正常")
    print("2. ❌ 表示功能缺失或异常")
    print("3. API返回401是正常的，因为需要用户登录认证")
    print("4. 如需完整测试API功能，请先登录系统获取认证token")

if __name__ == "__main__":
    main()