#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本: 添加部门用户功能支持
- 为users表添加部门账户相关字段
- 为每个现有部门自动创建部门用户账户
"""

import sqlite3
import hashlib
import os
from datetime import datetime

def get_db_path():
    """获取数据库路径"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')

def hash_password(password: str) -> str:
    """对密码进行哈希加密"""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_up():
    """执行向上迁移"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始执行部门用户功能迁移...")
        
        # 1. 检查是否已经添加了新字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 2. 添加新字段到users表
        new_fields = [
            ("user_type", "VARCHAR(20) DEFAULT 'manager'"),
            ("department_id", "INTEGER"),
            ("first_login", "BOOLEAN DEFAULT 1"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("last_login", "DATETIME"),
            ("password_reset_at", "DATETIME")
        ]
        
        for field_name, field_definition in new_fields:
            if field_name not in columns:
                alter_sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_definition}"
                cursor.execute(alter_sql)
                print(f"✓ 添加字段: {field_name}")
        
        # 3. 更新现有用户的user_type
        cursor.execute("UPDATE users SET user_type = 'admin' WHERE is_admin = 1")
        cursor.execute("UPDATE users SET user_type = 'manager' WHERE is_admin = 0")
        cursor.execute("UPDATE users SET first_login = 0")  # 现有用户标记为已登录过
        print("✓ 更新现有用户类型")
        
        # 4. 获取所有部门
        cursor.execute("SELECT id, name, code FROM departments")
        departments = cursor.fetchall()
        
        # 5. 为每个部门创建部门用户账户
        default_password_hash = hash_password("sxyq123")
        created_count = 0
        
        for dept_id, dept_name, dept_code in departments:
            # 检查是否已存在同名用户
            cursor.execute("SELECT id FROM users WHERE username = ?", (dept_name,))
            existing_user = cursor.fetchone()
            
            if not existing_user:
                # 创建部门用户
                cursor.execute("""
                    INSERT INTO users (username, hashed_password, is_admin, user_type, 
                                     department_id, first_login, is_active, created_at)
                    VALUES (?, ?, 0, 'department_user', ?, 1, 1, ?)
                """, (dept_name, default_password_hash, dept_id, datetime.now()))
                created_count += 1
                print(f"✓ 创建部门用户: {dept_name}")
        
        print(f"✓ 共创建 {created_count} 个部门用户账户")
        
        # 6. 添加外键约束（如果SQLite支持的话）
        try:
            # 注意：SQLite的ALTER TABLE不支持添加外键约束
            # 这里我们只是记录，实际约束在模型中定义
            print("✓ 外键约束已在模型中定义")
        except Exception as e:
            print(f"注意: 外键约束设置 - {e}")
        
        # 提交事务
        conn.commit()
        print("✅ 部门用户功能迁移完成！")
        
        # 7. 验证迁移结果
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'department_user'")
        dept_user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM departments")
        dept_count = cursor.fetchone()[0]
        
        print(f"验证结果: {dept_user_count}/{dept_count} 个部门拥有用户账户")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_down():
    """执行向下迁移（回滚）"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始回滚部门用户功能迁移...")
        
        # 1. 删除部门用户账户
        cursor.execute("DELETE FROM users WHERE user_type = 'department_user'")
        deleted_count = cursor.rowcount
        print(f"✓ 删除 {deleted_count} 个部门用户账户")
        
        # 2. 重置现有用户的first_login状态
        cursor.execute("UPDATE users SET first_login = 1")
        
        # 注意: SQLite不支持DROP COLUMN，所以新增的字段无法删除
        # 但可以将它们设置为NULL
        cursor.execute("UPDATE users SET user_type = 'manager' WHERE user_type != 'admin'")
        cursor.execute("UPDATE users SET department_id = NULL")
        cursor.execute("UPDATE users SET is_active = NULL")
        cursor.execute("UPDATE users SET last_login = NULL") 
        cursor.execute("UPDATE users SET password_reset_at = NULL")
        
        print("✓ 重置用户字段（注意：字段仍存在但已清空）")
        
        conn.commit()
        print("✅ 部门用户功能回滚完成！")
        
    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down()
    else:
        migrate_up()