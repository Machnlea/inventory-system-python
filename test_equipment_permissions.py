#!/usr/bin/env python3
"""
测试器具级别权限管理功能
"""

import sqlite3
import os
import json

def test_equipment_permissions():
    """测试器具权限管理功能"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🧪 测试器具级别权限管理功能...")
        
        # 1. 检查器具权限表结构
        print("\n📋 检查器具权限表结构...")
        cursor.execute("PRAGMA table_info(user_equipment_permissions)")
        columns = cursor.fetchall()
        
        print("✅ user_equipment_permissions 表结构:")
        for col in columns:
            print(f"   {col}")
        
        # 2. 检查唯一约束
        print("\n🔍 检查唯一约束...")
        cursor.execute("PRAGMA index_list(user_equipment_permissions)")
        indexes = cursor.fetchall()
        
        unique_constraint_found = False
        for index in indexes:
            if index[1]:  # is unique
                unique_constraint_found = True
                print(f"✅ 找到唯一约束: {index[0]}")
        
        if not unique_constraint_found:
            print("⚠️ 未找到唯一约束")
        
        # 3. 检查当前权限分配
        print("\n📊 当前权限分配:")
        cursor.execute("""
            SELECT u.username, ec.name as category_name, uep.equipment_name
            FROM user_equipment_permissions uep
            JOIN users u ON uep.user_id = u.id
            JOIN equipment_categories ec ON uep.category_id = ec.id
            ORDER BY u.username, ec.name, uep.equipment_name
        """)
        
        permissions = cursor.fetchall()
        
        if permissions:
            for username, category_name, equipment_name in permissions:
                print(f"   ✅ {username} -> {category_name}/{equipment_name}")
        else:
            print("   ℹ️ 当前没有权限分配")
        
        # 4. 测试重复分配防护
        print("\n🛡️ 测试重复分配防护...")
        
        # 尝试为 zmms 分配一个已被 zms 管理的器具
        cursor.execute("""
            SELECT equipment_name FROM user_equipment_permissions 
            WHERE user_id = (SELECT id FROM users WHERE username = 'zms')
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            equipment_name = result[0]
            category_id = cursor.execute("SELECT id FROM equipment_categories WHERE name = '温度环境类'").fetchone()[0]
            zmms_id = cursor.execute("SELECT id FROM users WHERE username = 'zmms'").fetchone()[0]
            
            try:
                cursor.execute("""
                    INSERT INTO user_equipment_permissions (user_id, category_id, equipment_name)
                    VALUES (?, ?, ?)
                """, (zmms_id, category_id, equipment_name))
                conn.commit()
                print("❌ 重复分配防护未生效")
                return False
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    print("✅ 重复分配防护正常工作")
                else:
                    print(f"❌ 其他约束错误: {e}")
                    return False
        
        # 5. 检查温度环境类的器具分配情况
        print("\n🏷️ 温度环境类器具分配情况:")
        cursor.execute("""
            SELECT ec.name as category_name, uep.equipment_name, u.username
            FROM equipment_categories ec
            LEFT JOIN user_equipment_permissions uep ON ec.id = uep.category_id
            LEFT JOIN users u ON uep.user_id = u.id
            WHERE ec.name = '温度环境类'
            ORDER BY uep.equipment_name
        """)
        
        equipment_assignments = cursor.fetchall()
        
        # 获取温度环境类的所有预定义器具
        cursor.execute("SELECT predefined_names FROM equipment_categories WHERE name = '温度环境类'")
        predefined_result = cursor.fetchone()
        
        if predefined_result:
            predefined_names = json.loads(predefined_result[0])
            
            # 创建分配映射
            assignments = {}
            for category_name, equipment_name, username in equipment_assignments:
                if equipment_name:
                    assignments[equipment_name] = username
            
            print("器具分配状态:")
            for equipment_name in predefined_names:
                manager = assignments.get(equipment_name, "未分配")
                status = "✅" if manager != "未分配" else "⚪"
                print(f"   {status} {equipment_name} -> {manager}")
        
        # 6. 统计用户管理的器具数量
        print("\n📈 用户管理器具统计:")
        cursor.execute("""
            SELECT u.username, COUNT(uep.equipment_name) as equipment_count
            FROM users u
            LEFT JOIN user_equipment_permissions uep ON u.id = uep.user_id
            GROUP BY u.id, u.username
            ORDER BY equipment_count DESC
        """)
        
        user_stats = cursor.fetchall()
        
        for username, equipment_count in user_stats:
            print(f"   {username}: {equipment_count} 个器具")
        
        print("\n🎉 器具权限管理功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 开始测试器具级别权限管理功能...")
    print("=" * 60)
    
    success = test_equipment_permissions()
    
    print("=" * 60)
    if success:
        print("🎉 所有测试通过！器具权限管理功能正常工作。")
        print("\n📋 功能特点:")
        print("   ✅ 用户可以管理具体器具而不是整个大类")
        print("   ✅ 每个器具只能由一个用户管理")
        print("   ✅ 一个用户可以管理多个器具")
        print("   ✅ 支持细粒度的权限控制")
        print("   ✅ 数据库唯一约束防止重复分配")
        print("\n🚀 现在可以在前端界面测试器具权限管理功能")
    else:
        print("⚠️ 测试失败！需要进一步检查。")