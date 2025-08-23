#!/usr/bin/env python3
"""
添加测试数据到器具权限表
"""

import sqlite3
import os

def add_test_permissions():
    """添加测试权限数据"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("📝 添加测试权限数据...")
        
        # 获取用户ID
        cursor.execute("SELECT id, username FROM users WHERE username IN ('zmms', 'zms', 'testuser1')")
        users = {username: user_id for user_id, username in cursor.fetchall()}
        
        # 获取温度环境类别的ID
        cursor.execute("SELECT id FROM equipment_categories WHERE name = '温度环境类'")
        category_result = cursor.fetchone()
        
        if not category_result:
            print("❌ 未找到温度环境类别")
            return False
        
        category_id = category_result[0]
        
        # 清理现有数据
        cursor.execute("DELETE FROM user_equipment_permissions WHERE category_id = ?", (category_id,))
        
        # 根据用户需求分配权限
        permissions = [
            ('zmms', ['温湿度计', '温湿度表', '标准水银温度计']),
            ('zms', ['玻璃液体温度计', '数显温度计', '标准水槽', '标准油槽']),
            ('testuser1', ['标准铂电阻温度计'])
        ]
        
        for username, equipment_names in permissions:
            if username in users:
                user_id = users[username]
                for equipment_name in equipment_names:
                    cursor.execute("""
                        INSERT INTO user_equipment_permissions (user_id, category_id, equipment_name)
                        VALUES (?, ?, ?)
                    """, (user_id, category_id, equipment_name))
        
        conn.commit()
        
        print("✅ 测试权限数据添加成功")
        
        # 验证数据
        print("\n🔍 验证权限数据...")
        cursor.execute("""
            SELECT u.username, ec.name as category_name, uep.equipment_name
            FROM user_equipment_permissions uep
            JOIN users u ON uep.user_id = u.id
            JOIN equipment_categories ec ON uep.category_id = ec.id
            ORDER BY u.username, ec.name, uep.equipment_name
        """)
        
        permissions = cursor.fetchall()
        
        print("\n📋 当前权限分配：")
        for username, category_name, equipment_name in permissions:
            print(f"   ✅ {username} -> {category_name}/{equipment_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 添加数据过程中发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("📝 添加测试权限数据...")
    print("=" * 50)
    
    success = add_test_permissions()
    
    print("=" * 50)
    if success:
        print("🎉 测试权限数据添加成功！")
    else:
        print("⚠️ 添加失败！需要进一步检查。")