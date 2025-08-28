#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本: 修复部门用户密码哈希
- 将SHA256哈希的密码改为bcrypt哈希
"""

import sqlite3
import os
from datetime import datetime

def get_db_path():
    """获取数据库路径"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')

def hash_password_bcrypt(password: str) -> str:
    """使用bcrypt对密码进行哈希加密"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def migrate_up():
    """执行向上迁移"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始修复部门用户密码哈希...")
        
        # 1. 获取所有部门用户
        cursor.execute("SELECT id, username FROM users WHERE user_type = 'department_user'")
        department_users = cursor.fetchall()
        
        if not department_users:
            print("没有找到部门用户，无需修复")
            return
        
        # 2. 为每个部门用户重新哈希密码
        correct_password_hash = hash_password_bcrypt("sxyq123")
        updated_count = 0
        
        for user_id, username in department_users:
            cursor.execute("""
                UPDATE users SET 
                    hashed_password = ?,
                    password_reset_at = ?,
                    first_login = 1
                WHERE id = ?
            """, (correct_password_hash, datetime.now(), user_id))
            updated_count += 1
            print(f"✓ 更新部门用户密码: {username}")
        
        print(f"✓ 共更新 {updated_count} 个部门用户密码")
        
        # 提交事务
        conn.commit()
        print("✅ 部门用户密码修复完成！")
        
        # 验证修复结果
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'department_user'")
        dept_user_count = cursor.fetchone()[0]
        print(f"验证结果: {dept_user_count} 个部门用户密码已修复")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_down():
    """执行向下迁移（回滚）"""
    # 这个迁移没有回滚操作，因为修复是必要的
    print("此迁移不支持回滚操作")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down()
    else:
        migrate_up()