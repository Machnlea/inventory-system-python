#!/usr/bin/env python3
"""
测试权限冲突检查功能
"""

import sqlite3
import os

def test_permission_conflict_check():
    """测试权限冲突检查"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🧪 测试权限冲突检查...")
        
        # 获取zms用户的器具权限
        cursor.execute('''
            SELECT u.username, ec.name as category_name, uep.equipment_name
            FROM user_equipment_permissions uep
            JOIN users u ON uep.user_id = u.id
            JOIN equipment_categories ec ON uep.category_id = ec.id
            WHERE u.username = 'zms' AND uep.equipment_name = '电子秒表'
        ''')
        
        zms_permission = cursor.fetchone()
        
        if zms_permission:
            print(f"✅ zms用户拥有器具权限:")
            print(f"   用户: {zms_permission[0]}")
            print(f"   类别: {zms_permission[1]}")
            print(f"   器具: {zms_permission[2]}")
        else:
            print("❌ zms用户没有电子秒表器具权限")
            return False
        
        # 获取时间测量类别的信息
        cursor.execute('''
            SELECT id, name, predefined_names
            FROM equipment_categories
            WHERE name = '时间测量类'
        ''')
        
        time_category = cursor.fetchone()
        
        if time_category:
            print(f"\n✅ 时间测量类别信息:")
            print(f"   ID: {time_category[0]}")
            print(f"   名称: {time_category[1]}")
            print(f"   预定义器具: {time_category[2]}")
            
            # 检查是否有其他用户拥有该类别权限
            cursor.execute('''
                SELECT u.username
                FROM user_categories uc
                JOIN users u ON uc.user_id = u.id
                WHERE uc.category_id = ?
            ''', (time_category[0],))
            
            category_users = cursor.fetchall()
            
            if category_users:
                print(f"\n⚠️  以下用户拥有时间测量类别权限:")
                for user in category_users:
                    print(f"   - {user[0]}")
            else:
                print(f"\n✅ 目前没有用户拥有时间测量类别权限")
                
        else:
            print("❌ 未找到时间测量类别")
            return False
        
        # 检查testuser4的权限
        cursor.execute('''
            SELECT u.username, '类别权限' as permission_type, ec.name as permission_name
            FROM user_categories uc
            JOIN users u ON uc.user_id = u.id
            JOIN equipment_categories ec ON uc.category_id = ec.id
            WHERE u.username = 'testuser4'
            UNION ALL
            SELECT u.username, '器具权限' as permission_type, uep.equipment_name as permission_name
            FROM user_equipment_permissions uep
            JOIN users u ON uep.user_id = u.id
            WHERE u.username = 'testuser4'
        ''')
        
        testuser4_permissions = cursor.fetchall()
        
        print(f"\n📋 testuser4用户的权限:")
        if testuser4_permissions:
            for perm in testuser4_permissions:
                print(f"   {perm[1]}: {perm[2]}")
        else:
            print("   无权限")
        
        print(f"\n🎯 权限冲突分析:")
        
        # 分析是否存在冲突
        has_conflict = False
        
        # 检查zms的器具权限是否与他人的类别权限冲突
        if zms_permission and time_category:
            # 检查是否有用户拥有时间测量类别权限
            cursor.execute('''
                SELECT u.username
                FROM user_categories uc
                JOIN users u ON uc.user_id = u.id
                WHERE uc.category_id = ? AND u.username != 'zms'
            ''', (time_category[0],))
            
            category_users = cursor.fetchall()
            
            if category_users:
                has_conflict = True
                print(f"❌ 发现权限冲突:")
                print(f"   zms用户通过器具权限管理: {zms_permission[2]}")
                print(f"   以下用户通过类别权限管理整个时间测量类:")
                for user in category_users:
                    print(f"   - {user[0]}")
            else:
                print(f"✅ 当前无权限冲突")
        
        if not has_conflict:
            print(f"\n💡 建议:")
            print(f"   如果现在给testuser4分配时间测量类别权限，将会与zms用户的电子秒表器具权限产生冲突")
            print(f"   修复后的权限检查应该阻止这种冲突分配")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 测试权限冲突检查功能...")
    print("=" * 60)
    
    success = test_permission_conflict_check()
    
    print("=" * 60)
    if success:
        print("🎉 测试完成！")
        print("💡 现在可以测试权限冲突检查功能是否正常工作")
    else:
        print("⚠️ 测试失败！")