#!/usr/bin/env python3
"""
测试设备统计报表功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.reports import get_equipment_stats
from app.db.database import get_db
from app.models.models import User

async def test_equipment_stats():
    """测试设备统计API"""
    print("开始测试设备统计API...")
    
    try:
        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)
        
        # 模拟当前用户（使用第一个管理员用户）
        admin_user = db.query(User).filter(User.is_admin == True).first()
        if not admin_user:
            print("错误: 未找到管理员用户")
            return
        
        print(f"使用管理员用户: {admin_user.username}")
        
        # 测试设备统计API
        result = await get_equipment_stats(
            sort_by="original_value",
            sort_order="desc",
            page=1,
            page_size=10,
            db=db,
            current_user=admin_user
        )
        
        print("\n=== 设备统计API测试结果 ===")
        print(f"总设备数: {result.get('total', 0)}")
        print(f"当前页: {result.get('page', 1)}")
        print(f"每页大小: {result.get('page_size', 10)}")
        
        # 显示概览统计
        overview = result.get('overview', {})
        print(f"\n=== 概览统计 ===")
        print(f"设备总数: {overview.get('total_equipment', 0)}")
        print(f"设备原值总计: {overview.get('total_original_value', 0)}")
        print(f"在用设备数: {overview.get('active_equipment', 0)}")
        
        # 显示设备列表
        equipment_list = result.get('equipment', [])
        print(f"\n=== 设备列表 (前5条) ===")
        for i, equipment in enumerate(equipment_list[:5]):
            print(f"{i+1}. {equipment.get('name', '未知')} - 原值: {equipment.get('original_value', 0)}")
        
        # 显示统计分布
        status_dist = result.get('status_distribution', [])
        print(f"\n=== 状态分布 ===")
        for stat in status_dist:
            print(f"{stat.get('status', '未知')}: {stat.get('count', 0)}")
        
        value_dist = result.get('value_distribution', [])
        print(f"\n=== 原值分布 ===")
        for dist in value_dist:
            print(f"{dist.get('range', '未知')}: {dist.get('count', 0)}")
        
        print("\n✅ 设备统计API测试成功!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(test_equipment_stats())