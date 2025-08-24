#!/usr/bin/env python3
"""
设备添加页面下拉列表排序修复验证脚本
验证预定义名称按编号顺序显示
"""

import json
import sqlite3
from app.utils.predefined_name_manager import get_smart_name_mapping

def test_dropdown_sorting():
    """测试下拉列表排序功能"""
    
    print("=" * 70)
    print("设备添加页面下拉列表排序修复验证")
    print("=" * 70)
    
    # 测试数据
    category_code = 'TEM'
    
    # 获取数据库中的实际数据
    conn = sqlite3.connect('data/inventory.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT predefined_names FROM equipment_categories WHERE code = ?', (category_code,))
    result = cursor.fetchone()
    
    if result:
        predefined_names_json = result[0]
        predefined_names = json.loads(predefined_names_json) if predefined_names_json else []
        
        print(f"📋 原始预定义名称列表:")
        for i, name in enumerate(predefined_names, 1):
            print(f"  {i}. {name}")
        
        # 获取智能编号映射
        name_mapping = get_smart_name_mapping(category_code, predefined_names)
        print(f"\n🔍 智能编号映射:")
        for name, number in name_mapping.items():
            print(f"  {name}: {number}")
        
        # 模拟前端排序逻辑
        print(f"\n🔄 模拟前端排序逻辑:")
        
        # 创建名称和编号的数组
        nameNumberPairs = []
        for name in predefined_names:
            number = int(name_mapping.get(name, '99'))
            nameNumberPairs.append({'name': name, 'number': number})
        
        # 按编号排序
        nameNumberPairs.sort(key=lambda x: x['number'])
        
        print(f"排序后的下拉列表选项:")
        for i, pair in enumerate(nameNumberPairs, 1):
            print(f"  {i}. {pair['name']} ({pair['number']})")
        
        # 验证关键项目的位置
        print(f"\n✅ 验证关键项目位置:")
        
        key_items = [
            ("温湿度计", 1),
            ("玻璃液体温度计", 2),
            ("温湿度表", 3),
            ("标准水银温度计", 4),
            ("工作用玻璃温度计", 5)
        ]
        
        all_correct = True
        for name, expected_position in key_items:
            actual_position = next((i for i, pair in enumerate(nameNumberPairs) if pair['name'] == name), -1) + 1
            if actual_position == expected_position:
                print(f"  ✅ {name}: 第{actual_position}位 (正确)")
            else:
                print(f"  ❌ {name}: 第{actual_position}位 (期望第{expected_position}位)")
                all_correct = False
        
        # 验证编号顺序
        print(f"\n🔢 验证编号顺序:")
        numbers_are_sequential = all(
            nameNumberPairs[i]['number'] == i + 1 
            for i in range(len(nameNumberPairs))
        )
        
        if numbers_are_sequential:
            print("  ✅ 编号完全按顺序排列")
        else:
            print("  ❌ 编号未按顺序排列")
            all_correct = False
        
        # 模拟下拉选项显示格式
        print(f"\n🎯 模拟下拉选项显示格式:")
        print("下拉列表将显示为:")
        for pair in nameNumberPairs:
            print(f"  {pair['name']} ({pair['number']})")
        
        # 最终结果
        print(f"\n🎉 验证结果:")
        if all_correct:
            print("✅ 所有验证通过！下拉列表排序修复成功")
            print("✅ 温湿度表现在会正确显示在第3位")
            print("✅ 所有项目按编号顺序排列")
            print("✅ 用户体验得到改善")
        else:
            print("❌ 部分验证失败，需要进一步检查")
    
    conn.close()

if __name__ == "__main__":
    test_dropdown_sorting()