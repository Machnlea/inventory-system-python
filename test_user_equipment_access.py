#!/usr/bin/env python3
"""
测试用户设备权限访问功能
"""

import sqlite3
import os

def test_user_equipment_access():
    """测试用户设备访问权限"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🧪 测试用户设备访问权限...")
        
        # 获取zmms用户信息
        cursor.execute("SELECT id, username, is_admin FROM users WHERE username = 'zmms'")
        zmms_user = cursor.fetchone()
        
        if not zmms_user:
            print("❌ 未找到zmms用户")
            return False
        
        user_id, username, is_admin = zmms_user
        print(f"👤 测试用户: {username} (ID: {user_id}, 管理员: {is_admin})")
        
        # 获取zmms的器具权限
        cursor.execute('''
            SELECT ec.name, uep.equipment_name 
            FROM user_equipment_permissions uep
            JOIN equipment_categories ec ON uep.category_id = ec.id
            WHERE uep.user_id = ?
        ''', (user_id,))
        
        permissions = cursor.fetchall()
        print(f"🔑 器具权限:")
        for category_name, equipment_name in permissions:
            print(f"   ✅ {category_name}/{equipment_name}")
        
        # 获取zmms的类别权限
        cursor.execute('''
            SELECT ec.name 
            FROM user_categories uc
            JOIN equipment_categories ec ON uc.category_id = ec.id
            WHERE uc.user_id = ?
        ''', (user_id,))
        
        category_permissions = cursor.fetchall()
        print(f"🏷️ 类别权限:")
        for category_name, in category_permissions:
            print(f"   ✅ {category_name}")
        
        # 模拟权限查询逻辑
        print(f"\\n🔍 模拟权限查询逻辑...")
        
        # 获取授权的类别ID
        if category_permissions:
            authorized_category_ids = []
            for category_name, in category_permissions:
                cursor.execute("SELECT id FROM equipment_categories WHERE name = ?", (category_name,))
                category_id = cursor.fetchone()[0]
                authorized_category_ids.append(category_id)
        else:
            authorized_category_ids = []
        
        # 获取授权的器具名称
        authorized_equipment_names = [equipment_name for _, equipment_name in permissions]
        
        print(f"   授权类别ID: {authorized_category_ids}")
        print(f"   授权器具名称: {authorized_equipment_names}")
        
        # 查询zmms应该能看到的设备
        cursor.execute('''
            SELECT e.id, e.name, e.internal_id, d.name as department, ec.name as category
            FROM equipments e
            JOIN departments d ON e.department_id = d.id
            JOIN equipment_categories ec ON e.category_id = ec.id
            WHERE e.category_id IN ({}) OR e.name IN ({})
        '''.format(
            ','.join(map(str, authorized_category_ids)) if authorized_category_ids else 'NULL',
            ','.join([f"'{name}'" for name in authorized_equipment_names]) if authorized_equipment_names else 'NULL'
        ))
        
        accessible_equipment = cursor.fetchall()
        print(f"\\n📋 zmms应该能看到的设备:")
        for device in accessible_equipment:
            print(f"   ✅ {device[1]} ({device[2]}) - {device[3]}/{device[4]}")
        
        # 验证温湿度计是否在列表中
        humidity_meter_found = any(device[1] == '温湿度计' for device in accessible_equipment)
        print(f"\\n🎯 验证结果:")
        print(f"   温湿度计可见: {'✅ 是' if humidity_meter_found else '❌ 否'}")
        
        if humidity_meter_found:
            print(f"\\n🎉 权限逻辑正确！zmms应该能看到温湿度计设备。")
        else:
            print(f"\\n⚠️ 权限逻辑可能有问题，zmms看不到温湿度计设备。")
        
        return humidity_meter_found
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 测试用户设备访问权限...")
    print("=" * 60)
    
    success = test_user_equipment_access()
    
    print("=" * 60)
    if success:
        print("🎉 测试通过！zmms用户应该能看到温湿度计设备。")
        print("💡 如果前端仍然看不到设备，请检查：")
        print("   1. 前端是否正确调用了API")
        print("   2. API返回的数据是否正确")
        print("   3. 浏览器控制台是否有错误")
    else:
        print("⚠️ 测试失败！需要检查权限逻辑。")