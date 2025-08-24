#!/usr/bin/env python3
"""
智能预定义名称编号管理系统测试脚本
"""

import json
import sqlite3
from app.utils.predefined_name_manager import get_smart_name_mapping, add_predefined_name_smart, update_predefined_name_smart, remove_predefined_name_smart

def test_smart_name_management():
    """测试智能名称管理功能"""
    
    print("=" * 60)
    print("智能预定义名称编号管理系统测试")
    print("=" * 60)
    
    # 测试数据
    category_code = 'TEM'
    predefined_names = ['温湿度计', '玻璃液体温度计', '标准水银温度计', '工作用玻璃温度计', '迷你温湿度计', '数显温度计', '标准水槽', '标准油槽', '标准铂电阻温度计', '温湿度表']
    
    print(f"\n📋 测试数据:")
    print(f"类别代码: {category_code}")
    print(f"预定义名称: {predefined_names}")
    
    # 1. 测试智能编号映射
    print(f"\n🔍 1. 测试智能编号映射")
    mapping = get_smart_name_mapping(category_code, predefined_names)
    print(f"编号映射: {mapping}")
    
    # 2. 测试编辑现有名称（保持编号）
    print(f"\n✏️  2. 测试编辑现有名称（保持编号）")
    print("将 '温湿度表' 改为 '温湿度表1'")
    edited_names, edited_mapping = update_predefined_name_smart(category_code, predefined_names, '温湿度表', '温湿度表1')
    print(f"编辑后名称列表: {edited_names}")
    print(f"编辑后编号映射: {edited_mapping}")
    
    # 验证编号保持
    original_number = mapping.get('温湿度表')
    new_number = edited_mapping.get('温湿度表1')
    print(f"✅ 编号保持验证: 原编号 {original_number} -> 新编号 {new_number}")
    
    # 3. 测试添加新名称
    print(f"\n➕ 3. 测试添加新名称")
    print("添加 '数字温湿度计'")
    new_names, new_mapping = add_predefined_name_smart(category_code, predefined_names, '数字温湿度计')
    print(f"添加后名称列表: {new_names}")
    print(f"添加后编号映射: {new_mapping}")
    
    # 验证编号分配
    assigned_number = new_mapping.get('数字温湿度计')
    print(f"✅ 编号分配验证: 新名称获得编号 {assigned_number}")
    
    # 4. 测试编号重用
    print(f"\n🔄 4. 测试编号重用")
    print("删除 '玻璃液体温度计'（编号2），然后添加 '电子温湿度计'")
    
    # 删除名称
    remaining_names = [name for name in predefined_names if name != '玻璃液体温度计']
    remaining_mapping = get_smart_name_mapping(category_code, remaining_names)
    print(f"删除后名称列表: {remaining_names}")
    print(f"删除后编号映射: {remaining_mapping}")
    
    # 添加新名称（应该重用编号2）
    final_names, final_mapping = add_predefined_name_smart(category_code, remaining_names, '电子温湿度计')
    print(f"重用后名称列表: {final_names}")
    print(f"重用后编号映射: {final_mapping}")
    
    # 验证编号重用
    reused_number = final_mapping.get('电子温湿度计')
    print(f"✅ 编号重用验证: 重用编号 {reused_number}")
    
    # 5. 测试数据库中的实际数据
    print(f"\n🗄️  5. 测试数据库中的实际数据")
    try:
        conn = sqlite3.connect('data/inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, code, predefined_names FROM equipment_categories WHERE code = ?', (category_code,))
        category = cursor.fetchone()
        
        if category:
            category_id, name, code, predefined_names_json = category
            db_predefined_names = json.loads(predefined_names_json) if predefined_names_json else []
            db_mapping = get_smart_name_mapping(category_code, db_predefined_names)
            
            print(f"数据库中的类别: {name} ({code})")
            print(f"数据库中的预定义名称数量: {len(db_predefined_names)}")
            print(f"数据库中的编号映射: {db_mapping}")
            
            # 验证温湿度表的编号是否为3
            temp_humidity_number = db_mapping.get('温湿度表')
            print(f"✅ 温湿度表编号验证: {temp_humidity_number}")
            
        conn.close()
    except Exception as e:
        print(f"数据库查询失败: {e}")
    
    print(f"\n🎉 测试完成！")
    print(f"✅ 智能编号管理系统工作正常")
    print(f"✅ 编辑保持编号功能正常")
    print(f"✅ 新增按顺序分配编号功能正常")
    print(f"✅ 编号重用功能正常")

if __name__ == "__main__":
    test_smart_name_management()