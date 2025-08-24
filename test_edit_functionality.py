#!/usr/bin/env python3
"""
预定义名称编辑功能测试脚本
验证修复后的编辑API
"""

import json
import sqlite3
from app.utils.predefined_name_manager import update_predefined_name_smart

def test_edit_functionality():
    """测试编辑功能"""
    
    print("=" * 70)
    print("预定义名称编辑功能测试")
    print("=" * 70)
    
    # 测试数据
    category_code = 'TEM'
    
    # 获取当前数据库中的预定义名称
    conn = sqlite3.connect('data/inventory.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT predefined_names FROM equipment_categories WHERE code = ?', (category_code,))
    result = cursor.fetchone()
    
    if result:
        predefined_names_json = result[0]
        predefined_names = json.loads(predefined_names_json) if predefined_names_json else []
        
        print(f"当前预定义名称: {predefined_names}")
        
        # 测试编辑功能
        print(f"\n✏️  测试编辑功能")
        old_name = '测试4'
        new_name = '测试4修改'
        
        if old_name in predefined_names:
            print(f"编辑: {old_name} -> {new_name}")
            
            # 使用智能编辑逻辑
            new_names_list, new_mapping = update_predefined_name_smart(
                category_code, predefined_names, old_name, new_name
            )
            
            print(f"编辑后名称列表: {new_names_list}")
            print(f"编辑后编号映射: {new_mapping}")
            
            # 验证编号保持
            old_number = new_mapping.get(new_name)
            print(f"新名称获得的编号: {old_number}")
            
            # 验证编辑结果
            if old_name not in new_names_list and new_name in new_names_list:
                print("✅ 编辑成功：名称已更新")
            else:
                print("❌ 编辑失败：名称未正确更新")
            
            # 验证编号保持（应该是14，因为测试4是第14个名称）
            if old_number == '14':
                print("✅ 编号保持成功：编辑后编号保持不变")
            else:
                print(f"❌ 编号保持失败：期望14，实际{old_number}")
                
        else:
            print(f"❌ 测试失败：{old_name} 不存在于预定义名称中")
    
    conn.close()
    
    print(f"\n🎯 测试完成")
    print("现在前端应该能够正常编辑预定义名称了")

if __name__ == "__main__":
    test_edit_functionality()