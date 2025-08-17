#!/usr/bin/env python3
"""
测试Excel导出功能
"""
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000"

def test_excel_export():
    """测试Excel导出功能"""
    
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
            "Authorization": f"Bearer {access_token}"
        }
        
        print("=== 测试Excel导出功能 ===\n")
        
        # 测试Excel导出
        print("测试Excel导出...")
        export_url = f"{BASE_URL}/api/reports/export?format=excel"
        export_response = requests.get(export_url, headers=headers)
        print(f"状态码: {export_response.status_code}")
        print(f"内容类型: {export_response.headers.get('content-type', 'unknown')}")
        print(f"内容长度: {export_response.headers.get('content-length', 'unknown')}")
        print(f"文件名: {export_response.headers.get('content-disposition', 'unknown')}")
        
        if export_response.status_code == 200:
            print("✅ Excel导出成功")
            
            # 保存文件
            filename = "test_export.xlsx"
            with open(filename, 'wb') as f:
                f.write(export_response.content)
            print(f"文件已保存为: {filename}")
            
        else:
            print(f"❌ Excel导出失败: {export_response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用程序正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_excel_export()