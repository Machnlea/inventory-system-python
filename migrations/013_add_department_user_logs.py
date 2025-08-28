#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本: 添加部门用户操作日志表
- 创建 department_user_logs 表用于记录部门用户操作
"""

import sqlite3
import os
from datetime import datetime

def get_db_path():
    """获取数据库路径"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')

def migrate_up():
    """执行向上迁移"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始创建部门用户操作日志表...")
        
        # 1. 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='department_user_logs'")
        if cursor.fetchone():
            print("✓ department_user_logs 表已存在，跳过创建")
            return
        
        # 2. 创建 department_user_logs 表
        cursor.execute("""
            CREATE TABLE department_user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # 3. 创建索引提高查询性能
        cursor.execute("CREATE INDEX idx_department_user_logs_user_id ON department_user_logs(user_id)")
        cursor.execute("CREATE INDEX idx_department_user_logs_created_at ON department_user_logs(created_at)")
        cursor.execute("CREATE INDEX idx_department_user_logs_action ON department_user_logs(action)")
        
        print("✓ 创建 department_user_logs 表")
        print("✓ 创建相关索引")
        
        # 提交事务
        conn.commit()
        print("✅ 部门用户操作日志表创建完成！")
        
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
        print("开始删除部门用户操作日志表...")
        
        # 删除表
        cursor.execute("DROP TABLE IF EXISTS department_user_logs")
        print("✓ 删除 department_user_logs 表")
        
        conn.commit()
        print("✅ 部门用户操作日志表删除完成！")
        
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