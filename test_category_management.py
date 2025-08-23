#!/usr/bin/env python3
"""
测试用户设备类别权限修复的脚本
验证：每个设备类别只能由一个用户管理
"""

import sqlite3
import sys
import os

def test_category_management():
    """测试设备类别管理权限"""
    
    # 连接数据库
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查是否有重复的设备类别分配
        print("🔍 检查设备类别分配情况...")
        
        cursor.execute("""
            SELECT category_id, COUNT(*) as user_count
            FROM user_categories
            GROUP BY category_id
            HAVING user_count > 1
        """)
        
        duplicate_categories = cursor.fetchall()
        
        if duplicate_categories:
            print("❌ 发现以下设备类别被多个用户管理：")
            for category_id, user_count in duplicate_categories:
                # 获取类别名称和用户名
                cursor.execute("""
                    SELECT ec.name, u.username
                    FROM user_categories uc
                    JOIN equipment_categories ec ON uc.category_id = ec.id
                    JOIN users u ON uc.user_id = u.id
                    WHERE uc.category_id = ?
                """, (category_id,))
                
                assignments = cursor.fetchall()
                category_name = assignments[0][0]
                usernames = [assignment[1] for assignment in assignments]
                
                print(f"   - 类别 '{category_name}' (ID: {category_id}) 被 {user_count} 个用户管理: {', '.join(usernames)}")
            
            return False
        else:
            print("✅ 没有发现重复的设备类别分配")
        
        # 2. 检查用户类别分配统计
        print("\n📊 用户类别分配统计：")
        
        cursor.execute("""
            SELECT u.username, COUNT(uc.category_id) as category_count
            FROM users u
            LEFT JOIN user_categories uc ON u.id = uc.user_id
            GROUP BY u.id, u.username
            ORDER BY category_count DESC
        """)
        
        user_stats = cursor.fetchall()
        
        for username, category_count in user_stats:
            print(f"   - {username}: {category_count} 个类别")
        
        # 3. 检查设备类别管理状态
        print("\n🏷️ 设备类别管理状态：")
        
        cursor.execute("""
            SELECT ec.name, 
                   CASE 
                       WHEN uc.user_id IS NOT NULL THEN u.username
                       ELSE '未分配'
                   END as manager
            FROM equipment_categories ec
            LEFT JOIN user_categories uc ON ec.id = uc.category_id
            LEFT JOIN users u ON uc.user_id = u.id
            ORDER BY ec.name
        """)
        
        category_managers = cursor.fetchall()
        
        for category_name, manager in category_managers:
            print(f"   - {category_name}: {manager}")
        
        print("\n✅ 测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 开始测试用户设备类别权限修复...")
    print("=" * 50)
    
    success = test_category_management()
    
    print("=" * 50)
    if success:
        print("🎉 测试通过！修复成功。")
        sys.exit(0)
    else:
        print("⚠️ 测试失败！需要进一步检查。")
        sys.exit(1)