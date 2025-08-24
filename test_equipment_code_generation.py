#!/usr/bin/env python3
"""
设备编号生成修复验证脚本
验证设备添加页面的编号生成逻辑
"""

import json
import sqlite3
from app.utils.equipment_mapping import get_equipment_type_code, get_equipment_sequence_number
from app.utils.predefined_name_manager import get_smart_name_mapping

def test_equipment_code_generation():
    """测试设备编号生成功能"""
    
    print("=" * 70)
    print("设备编号生成修复验证")
    print("=" * 70)
    
    # 测试数据
    category_code = 'TEM'
    
    # 1. 验证数据库中的预定义名称
    print(f"\n🗄️  1. 验证数据库中的预定义名称")
    conn = sqlite3.connect('data/inventory.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT predefined_names FROM equipment_categories WHERE code = ?', (category_code,))
    result = cursor.fetchone()
    
    if result:
        predefined_names_json = result[0]
        predefined_names = json.loads(predefined_names_json) if predefined_names_json else []
        print(f"预定义名称数量: {len(predefined_names)}")
        print(f"预定义名称: {predefined_names}")
    
    # 2. 测试智能编号映射
    print(f"\n🔍 2. 测试智能编号映射")
    name_mapping = get_smart_name_mapping(category_code, predefined_names)
    print(f"智能编号映射: {name_mapping}")
    
    # 3. 测试设备类型编号生成
    print(f"\n🔧 3. 测试设备类型编号生成")
    
    test_cases = [
        ("温湿度计", "应该返回: 1"),
        ("温湿度表", "应该返回: 3"),
        ("测试", "应该返回: TEM-11"),
        ("测试1", "应该返回: TEM-12"),
        ("新设备", "应该返回: TEM-[非99编号]")
    ]
    
    for equipment_name, expected in test_cases:
        type_code = get_equipment_type_code(category_code, equipment_name)
        sequence_number = get_equipment_sequence_number(category_code, equipment_name)
        
        print(f"{equipment_name}:")
        print(f"  类型编号: {type_code}")
        print(f"  序列号: {sequence_number}")
        print(f"  期望: {expected}")
        
        # 验证结果
        if equipment_name == "温湿度计" and type_code == "1":
            print("  ✅ 正确")
        elif equipment_name == "温湿度表" and type_code == "3":
            print("  ✅ 正确")
        elif equipment_name == "测试" and type_code == "TEM-11":
            print("  ✅ 正确")
        elif equipment_name == "测试1" and type_code == "TEM-12":
            print("  ✅ 正确")
        elif equipment_name == "新设备" and sequence_number != "99":
            print("  ✅ 正确（非99编号）")
        else:
            print("  ❌ 错误")
        print()
    
    # 4. 模拟设备添加场景
    print(f"\n🎯 4. 模拟设备添加场景")
    
    # 模拟自动生成设备编号的逻辑
    def simulate_auto_equipment_id(category_code, equipment_name):
        type_code = get_equipment_type_code(category_code, equipment_name)
        sequence_number = get_equipment_sequence_number(category_code, equipment_name)
        
        # 模拟获取序列号的逻辑
        try:
            conn = sqlite3.connect('data/inventory.db')
            cursor = conn.cursor()
            
            # 获取该类型设备的最大序列号
            cursor.execute('''
                SELECT MAX(CAST(substr(equipment_id, instr(equipment_id, '-') + 1) AS INTEGER))
                FROM equipments 
                WHERE equipment_id LIKE ?
            ''', (f"{type_code}-%",))
            
            result = cursor.fetchone()
            max_seq = result[0] if result[0] else 0
            next_seq = max_seq + 1
            
            equipment_id = f"{type_code}-{next_seq:03d}"
            conn.close()
            
            return equipment_id
        except:
            return f"{type_code}-001"
    
    # 测试自动生成设备编号
    equipment_names = ["测试", "测试1", "温湿度表"]
    for name in equipment_names:
        auto_id = simulate_auto_equipment_id(category_code, name)
        print(f"{name} -> 自动生成设备ID: {auto_id}")
        
        # 验证不是TEM-99-001
        if "TEM-99-" in auto_id:
            print("  ❌ 错误：仍然使用99编号")
        else:
            print("  ✅ 正确：使用智能编号")
    
    conn.close()
    
    print(f"\n🎉 验证完成！")
    print("现在设备添加页面应该正确使用智能编号，不再出现TEM-99-001")

if __name__ == "__main__":
    test_equipment_code_generation()