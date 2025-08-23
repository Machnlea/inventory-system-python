#!/usr/bin/env python3
"""
数据库迁移：添加器具级别权限管理表
允许用户管理具体器具而不是整个大类
"""

import sqlite3
import os
import json

def create_equipment_permissions_table():
    """创建器具权限管理表"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🏗️ 创建器具权限管理表...")
        
        # 创建新的权限表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_equipment_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                equipment_name TEXT NOT NULL,
                UNIQUE(category_id, equipment_name),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (category_id) REFERENCES equipment_categories (id)
            )
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_equipment_permissions_user_id 
            ON user_equipment_permissions (user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_equipment_permissions_category_id 
            ON user_equipment_permissions (category_id)
        """)
        
        conn.commit()
        
        print("✅ 器具权限管理表创建成功")
        
        # 初始化一些示例权限数据
        print("\n📝 初始化示例权限数据...")
        
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
        
        # 删除现有的示例数据（如果存在）
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
        
        print("✅ 示例权限数据初始化完成")
        
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
        print(f"❌ 迁移过程中发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 开始创建器具权限管理表...")
    print("=" * 60)
    
    success = create_equipment_permissions_table()
    
    print("=" * 60)
    if success:
        print("🎉 器具权限管理表创建成功！")
        print("\n📋 新功能特点：")
        print("   ✅ 用户可以管理具体器具而不是整个大类")
        print("   ✅ 每个器具只能由一个用户管理")
        print("   ✅ 一个用户可以管理多个器具")
        print("   ✅ 支持细粒度的权限控制")
        print("\n🚀 接下来需要更新后端API和前端界面")
    else:
        print("⚠️ 创建失败！需要进一步检查。")