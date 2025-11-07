#!/usr/bin/env python3
"""
简单的缓存效果验证脚本
"""

import time
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

def test_api_response_time(endpoint, description, headers=None):
    """测试API响应时间"""
    print(f"\n📊 测试 {description}")
    print("-" * 50)

    url = f"{BASE_URL}{endpoint}"

    # 第一次请求（缓存未命中）
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers)
        first_time = time.time() - start_time
        status1 = response.status_code
    except Exception as e:
        print(f"❌ 首次请求失败: {e}")
        return

    # 等待一小段时间
    time.sleep(0.1)

    # 第二次请求（应该命中缓存）
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers)
        second_time = time.time() - start_time
        status2 = response.status_code
    except Exception as e:
        print(f"❌ 第二次请求失败: {e}")
        return

    # 计算性能提升
    if first_time > 0 and second_time > 0:
        improvement = ((first_time - second_time) / first_time) * 100
        print(f"✅ 首次请求: {first_time:.3f}s (状态码: {status1})")
        print(f"✅ 第二次请求: {second_time:.3f}s (状态码: {status2})")
        print(f"📈 性能提升: {improvement:.1f}%")

        if improvement > 0:
            print("🎯 缓存命中，响应时间改善")
        else:
            print("⚠️ 缓存可能未生效或响应时间相近")
    else:
        print("❌ 无法计算性能提升")

def main():
    """主函数"""
    print("🔍 API缓存效果验证")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试不需要认证的API
    test_apis = [
        ("/api/auth/users/login-options", "用户登录选项"),
    ]

    for endpoint, description in test_apis:
        test_api_response_time(endpoint, description)

    print("\n" + "=" * 60)
    print("✅ 缓存验证完成！")
    print("\n💡 说明:")
    print("- 如果第二次请求明显更快，说明缓存生效")
    print("- 如果性能提升不明显，可能需要检查缓存配置")
    print("- 部分API可能需要认证才能访问，这里只测试公开API")

if __name__ == "__main__":
    main()