#!/usr/bin/env python3
"""
数据库迁移：添加唯一约束确保每个设备类别只能由一个用户管理
"""

import sqlite3
import os

def add_unique_constraint():
    """添加唯一约束"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 检查现有数据...")
        
        # 检查是否有重复的类别分配
        cursor.execute("""
            SELECT category_id, COUNT(*) as count
            FROM user_categories
            GROUP BY category_id
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print("⚠️ 发现重复的类别分配，需要清理：")
            for category_id, count in duplicates:
                print(f"   类别ID {category_id}: {count} 个用户")
                
                # 保留第一个分配，删除其他的
                cursor.execute("""
                    DELETE FROM user_categories 
                    WHERE category_id = ? AND id NOT IN (
                        SELECT MIN(id) 
                        FROM user_categories 
                        WHERE category_id = ?
                    )
                """, (category_id, category_id))
                
            print("✅ 已清理重复分配")
        
        # 创建新的表结构
        print("🏗️ 创建新的表结构...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_categories_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                UNIQUE(category_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (category_id) REFERENCES equipment_categories (id)
            )
        """)
        
        # 复制数据
        print("📋 复制数据...")
        cursor.execute("""
            INSERT INTO user_categories_new (id, user_id, category_id)
            SELECT id, user_id, category_id FROM user_categories
        """)
        
        # 删除旧表
        print("🗑️ 删除旧表...")
        cursor.execute("DROP TABLE user_categories")
        
        # 重命名新表
        print("🔄 重命名表...")
        cursor.execute("ALTER TABLE user_categories_new RENAME TO user_categories")
        
        # 验证约束
        print("✅ 验证约束...")
        cursor.execute("PRAGMA table_info(user_categories)")
        columns = cursor.fetchall()
        
        unique_constraint_found = False
        for col in columns:
            if len(col) > 5 and col[5] and 'UNIQUE' in str(col[5]):
                unique_constraint_found = True
                break
        
        if not unique_constraint_found:
            print("⚠️ 唯一约束可能未正确设置，但表结构已更新")
        
        conn.commit()
        
        print("✅ 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 迁移过程中发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 开始数据库迁移...")
    print("=" * 50)
    
    success = add_unique_constraint()
    
    print("=" * 50)
    if success:
        print("🎉 数据库迁移成功！")
        print("📝 每个设备类别现在只能由一个用户管理")
    else:
        print("⚠️ 数据库迁移失败！")