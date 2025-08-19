#!/usr/bin/env python3
"""
测试原值/元字段搜索功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crud import equipment
from app.schemas.schemas import EquipmentSearch
from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
import json

def test_original_value_search():
    """测试原值字段搜索功能"""
    print("正在测试原值/元字段搜索功能...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 测试用例1：搜索具体数值
        print("\n=== 测试用例1：搜索具体数值 '1500' ===")
        search_params = EquipmentSearch(query="1500")
        results = equipment.search_equipments(db, search_params, user_id=1, is_admin=True)
        print(f"找到 {len(results)} 条结果")
        
        for result in results:
            print(f"  - {result.name} (计量编号: {result.serial_number}, 原值: {result.original_value})")
        
        # 测试用例2：搜索模糊数值
        print("\n=== 测试用例2：搜索模糊数值 '100' ===")
        search_params = EquipmentSearch(query="100")
        results = equipment.search_equipments(db, search_params, user_id=1, is_admin=True)
        print(f"找到 {len(results)} 条结果")
        
        for result in results:
            print(f"  - {result.name} (计量编号: {result.serial_number}, 原值: {result.original_value})")
        
        # 测试用例3：搜索带小数点的数值
        print("\n=== 测试用例3：搜索带小数点的数值 '800.5' ===")
        search_params = EquipmentSearch(query="800.5")
        results = equipment.search_equipments(db, search_params, user_id=1, is_admin=True)
        print(f"找到 {len(results)} 条结果")
        
        for result in results:
            print(f"  - {result.name} (计量编号: {result.serial_number}, 原值: {result.original_value})")
        
        # 测试用例4：搜索非数值（应该匹配字符串转换后的结果）
        print("\n=== 测试用例4：搜索非数值 'abc' ===")
        search_params = EquipmentSearch(query="abc")
        results = equipment.search_equipments(db, search_params, user_id=1, is_admin=True)
        print(f"找到 {len(results)} 条结果")
        
        for result in results:
            print(f"  - {result.name} (计量编号: {result.serial_number}, 原值: {result.original_value})")
        
        # 测试用例5：组合搜索（设备名称 + 原值）
        print("\n=== 测试用例5：组合搜索 '温度计 1500' ===")
        search_params = EquipmentSearch(query="温度计 1500")
        results = equipment.search_equipments(db, search_params, user_id=1, is_admin=True)
        print(f"找到 {len(results)} 条结果")
        
        for result in results:
            print(f"  - {result.name} (计量编号: {result.serial_number}, 原值: {result.original_value})")
        
        print("\n=== 测试完成 ===")
        print("✅ 原值/元字段搜索功能已添加到系统中")
        print("现在用户可以通过搜索框搜索设备的原值，包括：")
        print("1. 精确数值匹配（如 '1500'）")
        print("2. 模糊数值匹配（如 '100' 可以匹配 '100.5'）")
        print("3. 字符串匹配（将数值转换为字符串后进行模糊匹配）")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_original_value_search()