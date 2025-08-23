#!/usr/bin/env python3
"""
创建测试用户
"""

import sqlite3
import os
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users():
    """创建测试用户"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("📝 创建测试用户...")
        
        # 创建测试用户
        test_users = [
            ('zmms', 'zmms123', False),
            ('zms', 'zms123', False),
            ('testuser1', 'test123', False)
        ]
        
        for username, password, is_admin in test_users:
            # 检查用户是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                print(f"⚠️ 用户 {username} 已存在，跳过创建")
                continue
            
            # 加密密码
            hashed_password = pwd_context.hash(password)
            
            # 插入用户
            cursor.execute("""
                INSERT INTO users (username, hashed_password, is_admin)
                VALUES (?, ?, ?)
            """, (username, hashed_password, is_admin))
            
            print(f"✅ 用户 {username} 创建成功")
        
        conn.commit()
        print("🎉 测试用户创建完成！")
        return True
        
    except Exception as e:
        print(f"❌ 创建用户过程中发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("📝 创建测试用户...")
    print("=" * 50)
    
    success = create_test_users()
    
    print("=" * 50)
    if success:
        print("🎉 测试用户创建成功！")
    else:
        print("⚠️ 创建失败！需要进一步检查。")