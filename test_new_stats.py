#!/usr/bin/env python3
"""
测试新的统计数据功能
"""

import requests
import json
from datetime import datetime

# 配置请求以绕过代理
session = requests.Session()
session.trust_env = False

def test_new_stats():
    """测试新的统计数据"""
    print("=== 测试新的统计数据 ===")
    
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
            print("\n测试新的统计数据...")
            
            url = "http://localhost:8000/api/reports/equipment-stats"
            response = session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API调用成功")
                
                # 显示基础统计
                stats = data.get('statistics', {})
                print(f"\n=== 基础统计 ===")
                print(f"计量器具总数: {stats.get('total_count', 0)}")
                
                # 计算在用和停用设备
                status_dist = stats.get('status_distribution', [])
                active_count = sum(s.get('count', 0) for s in status_dist if s.get('status') == '在用')
                inactive_count = sum(s.get('count', 0) for s in status_dist if s.get('status') != '在用')
                print(f"在用设备数量: {active_count}")
                print(f"停用/报废设备数量: {inactive_count}")
                
                # 显示时效监控统计
                print(f"\n=== 时效监控 ===")
                time_monitoring = stats.get('time_monitoring', {})
                print(f"已超期设备数量（红色预警）: {time_monitoring.get('overdue_count', 0)}")
                print(f"30天内即将到期设备数量（黄色预警）: {time_monitoring.get('expiring_soon_count', 0)}")
                print(f"正常有效期设备数量: {time_monitoring.get('valid_count', 0)}")
                
                # 显示合规性指标
                print(f"\n=== 合规性指标 ===")
                compliance = stats.get('compliance_metrics', {})
                print(f"外检设备占比: {compliance.get('external_inspection_rate', 0)}%")
                print(f"强检设备合格率（A级设备占比）: {compliance.get('a_grade_rate', 0)}%")
                print(f"外检设备数量: {compliance.get('external_inspection_count', 0)}")
                print(f"强检设备数量: {compliance.get('mandatory_inspection_count', 0)}")
                print(f"A级设备数量: {compliance.get('a_grade_count', 0)}")
                
                # 显示设备原值统计
                print(f"\n=== 设备原值统计 ===")
                print(f"设备原值总计: {stats.get('total_original_value', 0):.2f}")
                print(f"平均设备原值: {stats.get('avg_original_value', 0):.2f}")
                
                # 显示状态分布详情
                print(f"\n=== 状态分布详情 ===")
                for status in status_dist:
                    print(f"{status.get('status', '未知')}: {status.get('count', 0)}台 (原值: {status.get('total_value', 0):.2f})")
                
                # 显示部门统计
                print(f"\n=== 部门统计 ===")
                dept_stats = stats.get('department_stats', [])
                for dept in dept_stats:
                    print(f"{dept.get('department', '未知部门')}: {dept.get('count', 0)}台")
                
                # 显示类别统计
                print(f"\n=== 类别统计 ===")
                cat_stats = stats.get('category_stats', [])
                for cat in cat_stats:
                    print(f"{cat.get('category', '未知类别')}: {cat.get('count', 0)}台")
                        
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
    print("新的统计数据功能测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_new_stats()
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()