#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据: 添加部门用户操作日志示例数据
"""

import sqlite3
import os
from datetime import datetime, timedelta

def get_db_path():
    """获取数据库路径"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')

def add_sample_logs():
    """添加示例操作日志"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始添加部门用户操作日志示例数据...")
        
        # 获取所有部门用户
        cursor.execute("SELECT id, username FROM users WHERE user_type = 'department_user' LIMIT 3")
        users = cursor.fetchall()
        
        if not users:
            print("没有找到部门用户，请先创建部门用户")
            return
        
        # 为每个用户添加一些操作日志
        sample_logs = []
        
        for user_id, username in users:
            # 登录日志
            sample_logs.extend([
                (user_id, 'login', f'{username}成功登录系统', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', datetime.now() - timedelta(days=2)),
                (user_id, 'login', f'{username}成功登录系统', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', datetime.now() - timedelta(days=1)),
                (user_id, 'view_equipment', f'{username}查看了部门设备列表', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', datetime.now() - timedelta(hours=6)),
                (user_id, 'password_change', f'{username}修改了登录密码', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', datetime.now() - timedelta(hours=3)),
                (user_id, 'export_data', f'{username}导出了部门设备清单', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', datetime.now() - timedelta(hours=1)),
            ])
        
        # 插入日志数据
        cursor.executemany("""
            INSERT INTO department_user_logs (user_id, action, description, ip_address, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_logs)
        
        conn.commit()
        print(f"✅ 成功添加 {len(sample_logs)} 条操作日志记录")
        
        # 验证插入结果
        cursor.execute("SELECT COUNT(*) FROM department_user_logs")
        total_logs = cursor.fetchone()[0]
        print(f"数据库中共有 {total_logs} 条操作日志")
        
    except Exception as e:
        print(f"❌ 添加示例数据失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_logs()