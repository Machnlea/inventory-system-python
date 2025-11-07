#!/usr/bin/env python3
"""
缓存性能测试脚本

测试API缓存功能的性能提升效果。
"""

import time
import requests
import json
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.cache import cache_service
from app.core.cache_config import CacheConfig, cache_metrics

def login_and_get_session(base_url="http://localhost:8000"):
    """登录并获取会话"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    session = requests.Session()

    try:
        response = session.post(f"{base_url}/api/auth/login/json", json=login_data)
        if response.status_code == 200:
            print("✅ 登录成功")
            return session
        elif response.status_code == 409:
            # 处理会话冲突，强制登录
            print("检测到会话冲突，尝试强制登录...")
            force_login_data = {
                "username": "admin",
                "password": "admin123",
                "force": True
            }
            response = session.post(f"{base_url}/api/auth/login/json", json=force_login_data)
            if response.status_code == 200:
                print("✅ 强制登录成功")
                return session
            else:
                print(f"❌ 强制登录失败: {response.text}")
                return None
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        return None

def test_api_performance(session, base_url="http://localhost:8000"):
    """测试API性能"""

    print("\n🚀 测试API缓存性能")
    print("=" * 60)

    # 测试API端点列表
    test_apis = [
        {
            "name": "仪表盘统计数据",
            "url": f"{base_url}/api/dashboard/stats",
            "description": "获取仪表盘统计信息"
        },
        {
            "name": "部门列表",
            "url": f"{base_url}/api/departments/",
            "description": "获取部门列表"
        },
        {
            "name": "月度待检设备",
            "url": f"{base_url}/api/dashboard/monthly-due-equipments",
            "description": "获取月度待检设备列表"
        },
        {
            "name": "年度待检设备",
            "url": f"{base_url}/api/dashboard/yearly-due-equipments",
            "description": "获取年度待检设备列表"
        }
    ]

    results = []

    for api in test_apis:
        print(f"\n📊 测试 {api['name']}")
        print("-" * 40)

        # 第一次请求（缓存未命中）
        start_time = time.time()
        try:
            response = session.get(api['url'])
            first_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 首次请求: {first_time:.3f}秒")
                if isinstance(data, dict) and 'items' in data:
                    print(f"   返回数据: {len(data.get('items', []))} 条")
                elif isinstance(data, list):
                    print(f"   返回数据: {len(data)} 条")
                else:
                    print(f"   返回数据: {type(data).__name__}")

                # 第二次请求（应该命中缓存）
                start_time = time.time()
                response2 = session.get(api['url'])
                second_time = time.time() - start_time

                if response2.status_code == 200:
                    print(f"✅ 缓存命中: {second_time:.3f}秒")

                    # 计算性能提升
                    if first_time > 0:
                        improvement = ((first_time - second_time) / first_time) * 100
                        print(f"🚀 性能提升: {improvement:.1f}%")

                    results.append({
                        "api": api['name'],
                        "first_time": first_time,
                        "second_time": second_time,
                        "improvement": improvement if first_time > 0 else 0,
                        "url": api['url']
                    })
                else:
                    print(f"❌ 第二次请求失败: {response2.status_code}")
            else:
                print(f"❌ 首次请求失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")

    return results

def test_cache_management(session, base_url="http://localhost:8000"):
    """测试缓存管理功能"""

    print("\n🔧 测试缓存管理功能")
    print("=" * 60)

    # 测试缓存统计
    print("\n📈 获取缓存统计信息:")
    try:
        response = session.get(f"{base_url}/api/dashboard/cache-stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ 缓存统计信息:")

            if 'cache_metrics' in stats:
                metrics = stats['cache_metrics']
                print(f"   命中率: {metrics.get('hit_rate', 'N/A')}")
                print(f"   命中次数: {metrics.get('hits', 0)}")
                print(f"   未命中次数: {metrics.get('misses', 0)}")
                print(f"   总请求数: {metrics.get('total_requests', 0)}")

            if 'redis_info' in stats:
                redis_info = stats['redis_info']
                print(f"\n📊 Redis状态:")
                if 'redis_connected' in redis_info:
                    if redis_info['redis_connected']:
                        print(f"   连接状态: ✅ 已连接")
                        print(f"   使用内存: {redis_info.get('used_memory', 'N/A')}")
                        print(f"   连接客户端: {redis_info.get('connected_clients', 'N/A')}")
                    else:
                        print(f"   连接状态: ⚠️ 使用内存缓存")
                        print(f"   缓存键数: {redis_info.get('cached_keys', 0)}")
        else:
            print(f"❌ 获取缓存统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 缓存统计请求异常: {e}")

    # 测试清空缓存
    print("\n🗑️ 测试清空缓存功能:")
    try:
        response = session.post(f"{base_url}/api/dashboard/clear-cache")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ {result.get('message')}")
            else:
                print(f"❌ 清空缓存失败: {result.get('message')}")
        else:
            print(f"❌ 清空缓存请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 清空缓存请求异常: {e}")

def test_cache_config():
    """测试缓存配置"""

    print("\n⚙️ 缓存配置信息")
    print("=" * 60)

    # 显示所有缓存配置
    configs = CacheConfig.all_cache_configs()

    print(f"📋 共有 {len(configs)} 个API配置了缓存:")
    for api_name, config in configs.items():
        strategy = config['strategy']
        ttl = CacheConfig.get_ttl(strategy)
        prefix = config['prefix']
        description = config['description']

        print(f"\n🔸 {api_name}")
        print(f"   描述: {description}")
        print(f"   策略: {strategy.value}")
        print(f"   TTL: {ttl}秒 ({ttl//60}分钟)")
        print(f"   前缀: {prefix}")

def analyze_results(results):
    """分析测试结果"""

    print("\n📊 性能分析报告")
    print("=" * 60)

    if not results:
        print("❌ 没有有效的测试结果")
        return

    total_improvement = 0
    valid_results = 0

    for result in results:
        improvement = result['improvement']
        if improvement > 0:
            valid_results += 1
            total_improvement += improvement

        status = "🚀" if improvement > 0 else "➖"
        print(f"{status} {result['api']}: {improvement:.1f}% 提升")

    if valid_results > 0:
        avg_improvement = total_improvement / valid_results
        print(f"\n📈 平均性能提升: {avg_improvement:.1f}%")
        print(f"📊 有效缓存API: {valid_results}/{len(results)}")
    else:
        print("\n⚠️ 未检测到明显的性能提升（可能是首次运行）")

def main():
    """主函数"""
    print("🧪 API缓存性能测试工具")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试缓存配置
    test_cache_config()

    # 获取登录会话
    session = login_and_get_session()
    if not session:
        print("❌ 无法登录，退出测试")
        return

    # 测试API性能
    results = test_api_performance(session)

    # 测试缓存管理
    test_cache_management(session)

    # 分析结果
    analyze_results(results)

    print("\n✅ 测试完成！")
    print("\n💡 提示:")
    print("- 首次运行可能不会看到明显的缓存效果")
    print("- 多次运行测试可以观察缓存命中率的提升")
    print("- 生产环境建议启用Redis以获得更好的缓存性能")

if __name__ == "__main__":
    main()